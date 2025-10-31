# backend/app/document_monitoring_v2/modules/document_stage_checks_v2.py
"""
Модуль проверки этапов документов для системы мониторинга (версия 2).

Предоставляет функции для анализа документов и сохранения результатов
мониторинга с оптимизированной обработкой данных.

Основные функции:
- analyze_documents: Анализ документов с группировкой и оценкой статусов
- save_document_monitoring_status: Сохранение результатов анализа в Excel
"""

import pandas as pd
from datetime import datetime
import os
from backend.app.document_monitoring_v2.modules.document_row_analyzer_v2 import (
    evaluate_document_row,
    filter_exceptions_documents,
    get_latest_document_in_group
)
from backend.app.common.config.column_names import COLUMNS, VALUES


def analyze_documents(documents_df: pd.DataFrame) -> pd.DataFrame:
    """
    Выполняет оптимизированный анализ документов с группировкой и оценкой статусов.

    Процесс анализа включает:
    1. Фильтрацию документов-исключений
    2. Группировку по ключевым полям (код дела, тип документа, подразделение)
    3. Оценку статуса своевременности для каждой группы
    4. Формирование результата с сохранением структуры колонок

    Args:
        documents_df (pd.DataFrame): DataFrame с исходными данными документов

    Returns:
        pd.DataFrame: Результат анализа со следующими колонками:
            - requestCode: Код запроса документа
            - caseCode: Код дела
            - document: Тип документа
            - department: Подразделение
            - responseEssence: Суть ответа
            - monitoringStatus: Статус мониторинга (timely/overdue/no_data)
    """
    today = datetime.now().date()

    try:
        # Фильтрация документов-исключений
        filtered_df = filter_exceptions_documents(documents_df)
        if filtered_df.empty:
            return pd.DataFrame(
                columns=["requestCode", "caseCode", "document", "department", "responseEssence", "monitoringStatus"])

        # Формирование списка колонок для группировки
        grouping_columns = []
        for col in [COLUMNS["DOCUMENT_CASE_CODE"], COLUMNS["DOCUMENT_TYPE"], COLUMNS["DEPARTMENT_CATEGORY"]]:
            if col in filtered_df.columns:
                grouping_columns.append(col)

        # Обработка случая отсутствия стандартных колонок группировки
        if not grouping_columns:
            # Поиск альтернативных колонок по ключевым словам
            grouping_columns = [col for col in filtered_df.columns
                                if any(
                    keyword in col.lower() for keyword in ["код дела", "документ", "категория подразделения"])]

        if not grouping_columns:
            # Обработка без группировки с использованием apply для производительности
            result_df = filtered_df.copy()
            result_df["monitoringStatus"] = result_df.apply(
                lambda row: evaluate_document_row(row, today),
                axis=1
            )

            return pd.DataFrame({
                "requestCode": result_df.get("DOCUMENT_REQUEST_CODE", result_df.index.astype(str)),
                "caseCode": result_df.get("DOCUMENT_CASE_CODE", result_df.get("Код дела", "unknown")),
                "document": result_df.get("DOCUMENT_TYPE", result_df.get("Документ", "unknown")),
                "department": result_df.get("DEPARTMENT_CATEGORY", result_df.get("Категория подразделения", "unknown")),
                "responseEssence": result_df.get("ESSENSE_OF_THE_ANSWER", result_df.get("Суть ответа", "unknown")),
                "monitoringStatus": result_df["monitoringStatus"]
            })
        else:
            # Обработка с группировкой по ключевым полям
            results = []

            def process_group(group_df):
                """
                Обрабатывает отдельную группу документов.

                Для каждой группы выбирается последний документ и оценивается его статус.
                """
                if group_df.empty:
                    return []

                # Выбор последнего документа в группе
                latest_document = get_latest_document_in_group(group_df)
                if latest_document.empty:
                    return []

                # Оценка статуса своевременности
                status = evaluate_document_row(latest_document, today)

                # Формирование результата с сохранением структуры колонок
                return [{
                    "requestCode": latest_document.get(COLUMNS["DOCUMENT_REQUEST_CODE"], "unknown"),
                    "caseCode": latest_document.get(COLUMNS["DOCUMENT_CASE_CODE"], "unknown"),
                    "document": latest_document.get(COLUMNS["DOCUMENT_TYPE"], "unknown"),
                    "department": latest_document.get(COLUMNS["DEPARTMENT_CATEGORY"], "unknown"),
                    "responseEssence": latest_document.get(COLUMNS["ESSENSE_OF_THE_ANSWER"], "unknown"),
                    "monitoringStatus": status
                }]

            # Обработка всех групп документов
            for group_key, group_df in filtered_df.groupby(grouping_columns):
                group_results = process_group(group_df)
                results.extend(group_results)

            return pd.DataFrame(results)

    except Exception as e:
        print(f"❌ Ошибка анализа документов: {e}")
        return pd.DataFrame(columns=["requestCode", "caseCode", "document", "department", "monitoringStatus"])


def save_document_monitoring_status(df: pd.DataFrame, base_dir: str = "backend/app/data") -> str:
    """
    Сохраняет результаты анализа документов в Excel файл.

    TODO: Перенести логику в модуль сохранений и обновить тесты

    Args:
        df (pd.DataFrame): DataFrame с результатами анализа документов
        base_dir (str): Базовая директория для сохранения файла

    Returns:
        str: Путь к сохраненному файлу или строка с ошибкой
    """
    try:
        # Создание целевой директории при отсутствии
        os.makedirs(base_dir, exist_ok=True)

        # Формирование имени файла с текущей датой
        today_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"document_monitoring_status_{today_str}.xlsx"
        filepath = os.path.join(base_dir, filename)

        # Сохранение DataFrame в Excel формат
        df.to_excel(filepath, index=False)

        # Резервное сохранение при ошибке записи файла
        if not os.path.exists(filepath):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"document_monitoring_status_{today_str}_{timestamp}.xlsx"
            filepath = os.path.join(base_dir, filename)
            df.to_excel(filepath, index=False)

        return filepath

    except Exception as e:
        print(f"❌ Ошибка сохранения документа: {e}")
        # Попытка сохранения в текущую директорию как резервный вариант
        try:
            filename = f"document_monitoring_status_emergency_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(filename, index=False)
            return filename
        except:
            return "error_saving_file"