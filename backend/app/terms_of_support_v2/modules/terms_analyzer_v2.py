# backend/app/terms_of_support_v2/modules/terms_analyzer_v2.py
"""
Модуль вспомогательных функций для анализа сроков сопровождения дел (версия 2).

Содержит универсальные функции для обработки данных дел, используемые как в исковом,
так и в приказном производстве. Включает функции для безопасного извлечения данных,
подготовки структурированной информации и анализа сроков обработки документов.

Основные функции:
- safe_get: Безопасное извлечение значений из данных
- prepare_case_data: Подготовка структурированных данных дела
- calculate_documents_term_status: Анализ сроков обработки документов
- build_production_table: Универсальное построение таблиц для производств
"""

import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Any
from backend.app.common.config.column_names import COLUMNS, VALUES
from backend.app.common.config.calendar_config import russian_calendar
from backend.app.common.config.terms_checks_config import LAWSUIT_CHECKS_MAPPING, ORDER_CHECKS_MAPPING
from backend.app.common.modules.utils import get_filing_date, safe_get_column
from backend.app.common.modules.data_manager import data_manager

# ===== ИМПОРТЫ ДЛЯ BUILD_PRODUCTION_TABLE =====
from backend.app.terms_of_support_v2.modules.lawsuit_stage_v2 import assign_lawsuit_stages
from backend.app.terms_of_support_v2.modules.order_stage_v2 import assign_order_stages

# Импорты для lawsuit проверок
from backend.app.terms_of_support_v2.modules.lawsuit_stage_checks_v2 import (
    check_exceptions_stage as check_lawsuit_exceptions_stage,
    check_first_status_changed_stage as check_lawsuit_first_status_changed_stage,
    check_court_reaction_stage as check_lawsuit_court_reaction_stage,
    check_under_consideration_stage as check_lawsuit_under_consideration_stage,
    check_decision_made_stage as check_lawsuit_decision_made_stage,
    check_execution_document_received_stage as check_lawsuit_execution_document_received_stage,
    check_closed_stage as check_lawsuit_closed_stage
)

# Импорты для order проверок
from backend.app.terms_of_support_v2.modules.order_stage_checks_v2 import (
    check_exceptions_stage as check_order_exceptions_stage,
    check_closed_stage as check_order_closed_stage,
    check_execution_document_received_stage as check_order_execution_document_received_stage,
    check_court_reaction_stage as check_order_court_reaction_stage,
    check_first_status_changed_stage as check_order_first_status_changed_stage
)


def safe_get(value: Any, default: str = "Не указано") -> str:
    """
    Безопасно извлекает строковое значение из различных типов данных.

    Обрабатывает pandas Series, DataFrame, NaN значения и исключения,
    возвращая значение по умолчанию в случае ошибок или отсутствия данных.

    Args:
        value (Any): Значение для преобразования в строку
        default (str): Значение по умолчанию при ошибках

    Returns:
        str: Строковое представление значения или значение по умолчанию
    """
    try:
        # Обработка pandas Series и DataFrame
        if isinstance(value, (pd.Series, pd.DataFrame)):
            if len(value) > 0:
                # Извлечение первого значения из структуры pandas
                first_val = value.iloc[0] if hasattr(value, "iloc") else value.values[0]
                return str(first_val) if pd.notna(first_val) else default
            return default
        # Обработка NaN значений
        if pd.isna(value):
            return default
        # Преобразование в строку для остальных типов
        return str(value)
    except Exception:
        # Возврат значения по умолчанию при любых исключениях
        return default


def prepare_case_data(row: pd.Series, stage: str, status: str) -> Dict[str, Any]:
    """
    Подготавливает структурированные данные дела для отображения.

    Собирает ключевую информацию о деле в единый словарь, используя безопасное
    извлечение значений для всех полей.

    Args:
        row (pd.Series): Строка данных дела
        stage (str): Определенный этап дела
        status (str): Статус мониторинга

    Returns:
        Dict[str, Any]: Словарь с структурированными данными дела
    """

    def safe(val):
        """
        Внутренняя функция безопасного извлечения значений.

        Args:
            val: Значение для проверки и преобразования

        Returns:
            Безопасное строковое представление значения
        """
        if pd.isna(val):
            return "Не указано"
        if isinstance(val, float) and (val != val or val == float('inf') or val == float('-inf')):
            return "Не указано"
        return val

    return {
        "caseCode": safe(row.get("caseCode")),
        "responsibleExecutor": safe(row.get("responsibleExecutor")),
        "courtProtectionMethod": safe(row.get("courtProtectionMethod")),
        "filingDate": safe(row.get("filingDate")),
        "gosb": safe(row.get("gosb")),
        "courtReviewingCase": safe(row.get("courtReviewingCase")),
        "caseStatus": safe(row.get("caseStatus")),
        "caseCategory": safe(row.get("caseCategory")),
        "department": safe(row.get("department")),
        "caseStage": safe(stage),
        "monitoringStatus": safe(status)
    }


def calculate_documents_term_status(documents_df: pd.DataFrame, calendar: Any, today: date) -> pd.DataFrame:
    """
    Вычисляет статусы соблюдения сроков обработки документов.

    Анализирует документы на предмет соблюдения 2-дневного срока обработки.
    Разделяет документы на обработанные и находящиеся в работе, вычисляет
    статусы на основе рабочих дней между получением и передачей.

    Args:
        documents_df (pd.DataFrame): DataFrame с данными документов
        calendar: Объект календаря для расчета рабочих дней
        today (date): Текущая дата для расчетов

    Returns:
        pd.DataFrame: Копия входного DataFrame с добавленной колонкой 'documents_status'

    Raises:
        Exception: Возникает при ошибках обработки данных документов
    """
    # Обработка пустого или отсутствующего DataFrame
    if documents_df is None or documents_df.empty:
        if documents_df is None:
            # Возврат пустого DataFrame при отсутствии данных
            return pd.DataFrame(columns=['documents_status'])
        # Установка статуса 'no_data' для всех документов
        documents_df['documents_status'] = 'no_data'
        return documents_df

    try:
        # Создание копии DataFrame для модификаций
        result_df = documents_df.copy()
        # Инициализация колонки статусов значением по умолчанию
        result_df['documents_status'] = 'no_data'

        # Фильтрация документов с указанной датой получения
        documents_df_filtered = result_df.dropna(subset=[COLUMNS["DOCUMENT_RECEIPT_DATE"]])
        if documents_df_filtered.empty:
            return result_df

        # Группировка документов по комбинации код дела/тип/отдел
        grouped_documents = documents_df_filtered.groupby([
            COLUMNS["DOCUMENT_CASE_CODE"],
            COLUMNS["DOCUMENT_TYPE"],
            COLUMNS["DEPARTMENT_CATEGORY"]
        ])

        status_map = {}

        # Обработка каждой группы документов
        for (case_code, doc_type, department), doc_group in grouped_documents:
            # Разделение документов на переданные и непереданные
            group_with_transfer = doc_group.dropna(subset=[COLUMNS["DOCUMENT_TRANSFER_DATE"]])
            group_without_transfer = doc_group[doc_group[COLUMNS["DOCUMENT_TRANSFER_DATE"]].isna()]

            status = "no_data"

            # Блок 1: Анализ документов с датой передачи (уже обработаны)
            if not group_with_transfer.empty:
                try:
                    # Выбор последнего переданного документа в группе
                    latest_document = group_with_transfer.loc[
                        group_with_transfer[COLUMNS["DOCUMENT_TRANSFER_DATE"]].idxmax()]

                    # Расчет рабочих дней между получением и передачей
                    receipt_date = pd.to_datetime(latest_document[COLUMNS["DOCUMENT_RECEIPT_DATE"]]).date()
                    transfer_date = pd.to_datetime(latest_document[COLUMNS["DOCUMENT_TRANSFER_DATE"]]).date()
                    working_days = calendar.get_working_days_between(receipt_date, transfer_date)

                    # Определение статуса на основе соблюдения 2-дневного срока
                    status = "timely" if working_days <= 2 else "overdue"

                except Exception:
                    status = "no_data"

            # Блок 2: Анализ документов без даты передачи (в процессе обработки)
            elif not group_without_transfer.empty:
                try:
                    # Выбор последнего полученного документа в группе
                    latest_document = group_without_transfer.loc[
                        group_without_transfer[COLUMNS["DOCUMENT_RECEIPT_DATE"]].idxmax()]

                    receipt_date = pd.to_datetime(latest_document[COLUMNS["DOCUMENT_RECEIPT_DATE"]]).date()
                    # Расчет прошедших рабочих дней с момента получения
                    working_days_since_receipt = calendar.get_working_days_between(receipt_date, today)
                    # Расчет дедлайна обработки (2 рабочих дня)
                    deadline_date = calendar.add_working_days(receipt_date, 2)
                    # Расчет оставшихся календарных дней до дедлайна
                    calendar_days_until_deadline = (deadline_date - today).days

                    # Логика определения статуса для документов в работе
                    if working_days_since_receipt > 2:
                        status = "overdue"  # Срок обработки превышен
                    else:
                        if today < deadline_date:
                            # Определение приближающегося дедлайна
                            status = "upcoming_deadline" if calendar_days_until_deadline <= 14 else "timely"
                        else:
                            status = "overdue"  # Дедлайн прошел

                except Exception:
                    status = "no_data"

            # Сохранение статуса для всех документов в текущей группе
            for idx in doc_group.index:
                status_map[idx] = status

        # Применение вычисленных статусов к исходному DataFrame
        for idx, status in status_map.items():
            result_df.loc[idx, 'documents_status'] = status

        return result_df

    except Exception as e:
        # Обработка ошибок вычисления статусов
        print(f"❌ Ошибка вычисления статусов документов: {e}")
        documents_df['documents_status'] = 'no_data'
        return documents_df


def build_production_table(df: pd.DataFrame, production_type: str) -> pd.DataFrame:
    """
    Универсальная функция построения таблицы для искового или приказного производства.

    Выполняет полный цикл обработки данных: определение этапов дела, расчет статусов
    мониторинга, переименование колонок и сохранение результатов в кэш.

    Args:
        df (pd.DataFrame): Исходные отфильтрованные данные с делами
        production_type (str): Тип производства - 'lawsuit' или 'order'

    Returns:
        pd.DataFrame: Итоговая таблица с колонками:
                     [caseCode, caseStage, monitoringStatus, completionStatus,
                     responsibleExecutor, courtProtectionMethod, filingDate, gosb,
                     courtReviewingCase, caseStatus]

    Raises:
        ValueError: Возникает при указании неизвестного типа производства
        Exception: Возникает при ошибках обработки данных
    """
    try:
        # Очистка данных от дублирующихся колонок
        df_clean = df.loc[:, ~df.columns.duplicated()].copy()
        today = datetime.now().date()

        # 1. Определение этапов дела
        if production_type == 'lawsuit':
            staged_df = assign_lawsuit_stages(df_clean)
        elif production_type == 'order':
            staged_df = assign_order_stages(df_clean)
        else:
            raise ValueError(f"Неизвестный тип производства: {production_type}")

        df_clean["caseStage"] = staged_df["caseStage"]
        staged_df = df_clean

        # 2. Расчет статусов мониторинга по этапам
        def calculate_row_status(row):
            """
            Внутренняя функция расчета статусов для отдельной строки данных.

            Args:
                row (pd.Series): Строка данных дела

            Returns:
                tuple: Кортеж (monitoring_status, completion_status)
            """
            stage = row["caseStage"]

            if production_type == 'lawsuit':
                # Получение списка всех этапов из маппинга для искового производства
                stages = list(LAWSUIT_CHECKS_MAPPING.keys())

                # Проверка каждого этапа из маппинга
                if stage == stages[0]:  # "exceptions"
                    return check_lawsuit_exceptions_stage(row, today)
                elif stage == stages[1]:  # "underConsideration"
                    return check_lawsuit_under_consideration_stage(row, today, russian_calendar)
                elif stage == stages[2]:  # "decisionMade"
                    return check_lawsuit_decision_made_stage(row, today)
                elif stage == stages[3]:  # "courtReaction"
                    return check_lawsuit_court_reaction_stage(row, today, russian_calendar)
                elif stage == stages[4]:  # "firstStatusChanged"
                    return check_lawsuit_first_status_changed_stage(row, today)
                elif stage == stages[5]:  # "closed"
                    return check_lawsuit_closed_stage(row, today)
                elif stage == stages[6]:  # "executionDocumentReceived"
                    return check_lawsuit_execution_document_received_stage(row, today)
                else:
                    return "no_data", "false"

            else:  # 'order'
                # Получение списка всех этапов из маппинга для приказного производства
                stages = list(ORDER_CHECKS_MAPPING.keys())

                # Проверка каждого этапа из маппинга
                if stage == stages[0]:  # "exceptions"
                    return check_order_exceptions_stage(row, today)
                elif stage == stages[1]:  # "closed"
                    return check_order_closed_stage(row, today)
                elif stage == stages[2]:  # "executionDocumentReceived"
                    return check_order_execution_document_received_stage(row, today)
                elif stage == stages[3]:  # "courtReaction"
                    return check_order_court_reaction_stage(row, today)
                elif stage == stages[4]:  # "firstStatusChanged"
                    return check_order_first_status_changed_stage(row, today)
                else:
                    return "no_data", "false"

        # Применение функции расчета статусов ко всем строкам
        results = staged_df.apply(calculate_row_status, axis=1)
        staged_df["monitoringStatus"] = results.apply(lambda x: x[0])
        staged_df["completionStatus"] = results.apply(lambda x: x[1])

        # 3. Переименование колонок в стандартный формат
        rename_map = {
            COLUMNS["CASE_CODE"]: "caseCode",
            COLUMNS["RESPONSIBLE_EXECUTOR"]: "responsibleExecutor",
            COLUMNS["METHOD_OF_PROTECTION"]: "courtProtectionMethod",
            COLUMNS["LAWSUIT_FILING_DATE"]: "filingDate",
            COLUMNS["GOSB"]: "gosb",
            COLUMNS["COURT"]: "courtReviewingCase",
            COLUMNS["CASE_STATUS"]: "caseStatus",
        }
        staged_df = staged_df.rename(columns=rename_map)

        # 4. Сохранение обработанных данных в менеджер данных
        data_manager.set_processed_data(f"{production_type}_staged", staged_df)

        # 5. Добавление недостающих полей со значениями по умолчанию
        for col in rename_map.values():
            if col not in staged_df.columns:
                staged_df[col] = "Не указано"

        # 6. Формирование финального набора колонок
        final_columns = ["caseStage", "monitoringStatus", "completionStatus"] + list(rename_map.values())

        # Создание кодов дел при их отсутствии
        if "caseCode" not in staged_df.columns:
            staged_df["caseCode"] = [f"{production_type}_case_{i}" for i in range(len(staged_df))]

        return staged_df[final_columns].copy()

    except Exception as e:
        print(f"❌ Ошибка в build_production_table для {production_type}: {e}")
        raise