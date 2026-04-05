# backend/app/document_monitoring_v2/modules/document_row_analyzer_v2.py
"""
Модуль анализа строк документов для системы мониторинга сроков обработки

Предоставляет функции для оценки своевременности обработки документов
и фильтрации данных с учетом бизнес-логики мониторинга.

Основные функции:
- evaluate_document_row: Оценка статуса своевременности и завершенности документа
- filter_exceptions_documents: Фильтрация документов-исключений
- get_latest_document_in_group: Выбор последней записи в группе документов
"""

import pandas as pd
from datetime import date
from typing import Tuple
from backend.app.common.config.column_names import COLUMNS, VALUES


def evaluate_document_row(row: pd.Series, today: date) -> Tuple[str, bool]:
    """
    Оценивает статус своевременности обработки документа и статус завершенности.

    Логика расчета:
    1. Если Дата запроса отсутствует -> no_data, False
    2. Если есть Дата передачи:
       - Сравниваем Дата передачи с дедлайном (14 дней от Дата запроса)
       - Определяем monitoringStatus (timely/overdue) по факту передачи
       - completionStatus = (Суть ответа == "Передача подтверждена")
    3. Если нет Даты передачи:
       - Сравниваем текущую дату (today) с дедлайном
       - Определяем monitoringStatus по текущей ситуации
       - completionStatus = (Суть ответа == "Передача подтверждена")

    Args:
        row (pd.Series): Строка данных документа для оценки
        today (date): Текущая дата для сравнения с дедлайном

    Returns:
        Tuple[str, bool]: Статус документа (monitoringStatus, completionStatus):
            monitoringStatus:
                - 'timely': В срок (передача выполнена до дедлайна или дедлайн не наступил)
                - 'overdue': Просрочен (дедлайн прошел, передача не выполнена)
                - 'no_data': Недостаточно данных для оценки
            completionStatus:
                - True: Суть ответа = "Передача подтверждена"
                - False: Иначе или нет данных
    """
    try:
        # Извлечение даты запроса документа
        request_date_value = row.get(COLUMNS["DOCUMENT_REQUEST_DATE"])
        if pd.isna(request_date_value):
            return "no_data", False

        # Преобразование даты запроса в объект date
        request_date = pd.to_datetime(request_date_value).date()

        # Расчет дедлайна (14 календарных дней от даты запроса)
        deadline_date = request_date + pd.Timedelta(days=14)

        # Проверка подтверждения передачи в поле "Суть ответа"
        response_essence = row.get(COLUMNS["ESSENSE_OF_THE_ANSWER"])
        is_transfer_confirmed = (response_essence == "Передача подтверждена")

        # Извлечение даты передачи документа
        transfer_date_value = row.get(COLUMNS["DOCUMENT_TRANSFER_DATE"])

        # Случай 1: Есть дата передачи
        if not pd.isna(transfer_date_value):
            transfer_date = pd.to_datetime(transfer_date_value).date()

            # Сравнение даты передачи с дедлайном
            if transfer_date <= deadline_date:
                # Передача выполнена до или в день дедлайна
                return "timely", is_transfer_confirmed
            else:
                # Передача выполнена после дедлайна
                return "overdue", is_transfer_confirmed
        # Случай 2: Нет даты передачи, используем текущую дату
        else:
            # Сравнение текущей даты с дедлайном
            if today > deadline_date:
                # Дедлайн прошел, передача отсутствует
                if is_transfer_confirmed:
                    # Не может быть подтверждения без даты передачи, но на всякий случай
                    return "timely", True
                else:
                    return "overdue", False
            else:
                # Дедлайн еще не наступил
                return "timely", is_transfer_confirmed

    except Exception:
        return "no_data", False


def filter_exceptions_documents(documents_df: pd.DataFrame) -> pd.DataFrame:
    """
    Фильтрует документы-исключения из отчета по аналогии с исковым производством.

    Args:
        documents_df (pd.DataFrame): DataFrame с исходными данными документов

    Returns:
        pd.DataFrame: Отфильтрованный DataFrame без документов-исключений
    """
    try:
        # TODO: Определить критерии исключений для документов
        return documents_df
    except Exception:
        return documents_df


def get_latest_document_in_group(group: pd.DataFrame) -> pd.Series:
    """
    Выбирает последнюю запись в группе документов на основе дат передачи или получения.

    Приоритет отдается дате передачи документа. Если даты передачи отсутствуют,
    используется дата получения. При отсутствии обеих дат возвращается первая запись.

    Args:
        group (pd.DataFrame): Группа документов для анализа

    Returns:
        pd.Series: Последняя запись в группе документов
    """
    try:
        if group.empty:
            return pd.Series()

        # Поиск по дате передачи
        if COLUMNS["DOCUMENT_TRANSFER_DATE"] in group.columns:
            transfer_not_na_mask = group[COLUMNS["DOCUMENT_TRANSFER_DATE"]].notna()
            if transfer_not_na_mask.any():
                latest_transfer_idx = group.loc[transfer_not_na_mask, COLUMNS["DOCUMENT_TRANSFER_DATE"]].idxmax()
                return group.loc[latest_transfer_idx]

        # Поиск по дате получения при отсутствии дат передачи
        if COLUMNS["DOCUMENT_RECEIPT_DATE"] in group.columns:
            receipt_not_na_mask = group[COLUMNS["DOCUMENT_RECEIPT_DATE"]].notna()
            if receipt_not_na_mask.any():
                latest_receipt_idx = group.loc[receipt_not_na_mask, COLUMNS["DOCUMENT_RECEIPT_DATE"]].idxmax()
                return group.loc[latest_receipt_idx]

        # Возврат первой записи при отсутствии дат
        return group.iloc[0]

    except Exception:
        return group.iloc[0] if not group.empty else pd.Series()