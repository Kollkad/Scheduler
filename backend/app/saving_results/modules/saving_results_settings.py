# backend/app/saving_results/modules/saving_results_settings.py
"""
Настройки форматирования для сохранения результатов в Excel файлы.

Содержит функции для генерации имен файлов и форматирования Excel отчетов
с использованием xlsxwriter для профессионального внешнего вида.
"""

from datetime import datetime
import pandas as pd
import os
from backend.app.common.config.column_names import COLUMNS

CASE_STAGE_MAPPING = {
    "exceptions": "Исключение",
    "underConsideration": "На рассмотрении",
    "decisionMade": "Решение вынесено",
    "courtReaction": "Ожидание реакции суда",
    "firstStatusChanged": "Подготовка документов",
    "closed": "Закрыто",
    "executionDocumentReceived": "ИД получен",
}


def format_monitoring_status(status_string):
    """Форматирование статуса мониторинга для экспорта"""
    if not status_string or status_string == "no_data":
        return "Нет данных"

    status_mapping = {
        "timely": "в срок",
        "overdue": "просрочено",
        "no_data": "нет данных"
    }

    status_parts = status_string.split(';')
    formatted_parts = []

    for index, status in enumerate(status_parts):
        clean_status = status.strip().lower()
        translated_status = status_mapping.get(clean_status, clean_status)
        formatted_parts.append(f"Проверка {index + 1} - {translated_status}")

    return '; '.join(formatted_parts)

# Форматирование задач
DEFAULT_VALUE_FORMATTERS = {
    COLUMNS["MONITORING_STATUS"]: format_monitoring_status,
    COLUMNS["CASE_STAGE"]: lambda x: CASE_STAGE_MAPPING.get(x, x) if pd.notna(x) else "Не указан"
}

def generate_filename(report_type: str) -> str:
    """
    Генерация уникального имени файла для экспорта с временной меткой.

    Args:
        report_type (str): Тип отчета ('detailed_report', 'documents_report')

    Returns:
        str: Уникальное имя файла с временной меткой
    """
    timestamp = datetime.now().strftime("%d-%m-%Y")
    type_names = {
        "detailed_report": "детальный_отчет",
        "documents_report": "отчет_документов",
        "lawsuit_production": "исковое_производство",
        "order_production": "приказное_производство",
        "documents_analysis": "анализ_документов",
        "tasks": "задачи",
        "rainbow_analysis": "радуга",
        "all_analysis": "все_анализы"
    }

    report_name = type_names.get(report_type, report_type)
    return f"{report_name}_{timestamp}.xlsx"


def save_with_xlsxwriter_formatting(dataframe, filepath, sheet_name, data_type=None, value_formatters=None):
    """
    Сохраняет DataFrame с профессиональным форматированием используя xlsxwriter.

    Применяет стили оформления:
    - Зеленые заголовки с белым текстом
    - Чередующуюся заливку строк
    - Серые границы ячеек
    - Автоматическую настройку ширины колонок

    Args:
        dataframe: DataFrame для сохранения
        filepath (str): Путь для сохранения файла
        sheet_name (str): Название листа в Excel
        data_type (str, optional): Тип данных для переименования колонок

    Returns:
        bool: True при успешном сохранении, False при использовании fallback
    """
    try:
        # 1. Переименование колонок, если указано
        if data_type:
            dataframe = rename_columns_to_russian(dataframe, data_type)

        # 2. Авто-применение форматеров
        if value_formatters is None:
            value_formatters = {col: func for col, func in DEFAULT_VALUE_FORMATTERS.items() if col in dataframe.columns}
        for col, func in value_formatters.items():
            dataframe[col] = dataframe[col].apply(func)

        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            dataframe.to_excel(writer, sheet_name=sheet_name, index=False)

            workbook = writer.book
            worksheet = writer.sheets[sheet_name]

            # Определение оптимальных ширин для ключевых колонок
            column_widths = {
                '№ п/п': 10,
                'Код дела': 15,
                'Код передачи': 15,
                'Код запроса': 15,
                'Ответственный исполнитель': 25,
                'Способ судебной защиты': 20,
                'Дата подачи': 12,
                'ГОСБ': 10,
                'Статус дела': 25,
                'Этап дела': 20,
                'Статус мониторинга': 15,
                'Документ': 40,
                'Дата получения': 12,
                'Статус документа': 20,
                'Код задачи': 15,
                'Тип задачи': 20,
                'Тип документа-источника': 25,
                'Завершено': 12,
                'Текст задачи': 40,
                'Причина постановки задачи': 50,
                'Количество неудачных проверок': 25,
                'Дата создания': 12,
                'Статус завершения': 20,
            }

            # Форматы с серой границей и выравниванием по центру
            border_format = {
                'border': 1,
                'border_color': '#D0D0D0'  # Серая граница
            }

            # Формат для заголовков таблицы
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#439639',  # Зеленый фон
                'font_color': 'white',
                'text_wrap': True,
                'valign': 'vcenter',
                'align': 'center',
                **border_format
            })

            # Формат для четных строк
            even_row_format = workbook.add_format({
                'bg_color': 'white',
                'text_wrap': True,
                'valign': 'vcenter',
                'align': 'center',
                **border_format
            })

            # Формат для нечетных строк
            odd_row_format = workbook.add_format({
                'bg_color': '#F8FBFC',  # Светло-голубой фон
                'text_wrap': True,
                'valign': 'vcenter',
                'align': 'center',
                **border_format
            })

            # Применение форматирования к заголовкам
            for col_num, value in enumerate(dataframe.columns.values):
                worksheet.write(0, col_num, value, header_format)

            # Настройка ширины колонок согласно предустановленным значениям
            for col_num, column_name in enumerate(dataframe.columns):
                width = column_widths.get(column_name, 25)  # Значение по умолчанию
                worksheet.set_column(col_num, col_num, width)

            # Применение чередующейся заливки к строкам данных
            for row_num in range(len(dataframe)):
                if row_num % 2 == 0:
                    worksheet.set_row(row_num + 1, None, even_row_format)
                else:
                    worksheet.set_row(row_num + 1, None, odd_row_format)

        size = os.path.getsize(filepath)
        print(f"✅ Файл создан с улучшенным форматированием, размер: {size} байт")
        return True

    except Exception as e:
        print(f"❌ Ошибка форматирования: {e}")
        # Fallback: сохранение без форматирования
        dataframe.to_excel(filepath, index=False, sheet_name=sheet_name)
        return False


def rename_columns_to_russian(dataframe, data_type, value_formatters=None):
    """
    Переименование столбцов DataFrame с английских названий на русские согласно конфигурации.
    Опционально применяет форматирование значений колонок через value_formatters.

    Args:
        dataframe: DataFrame для переименования
        data_type (str): Тип данных для определения набора переименований
        value_formatters (dict, optional): Словарь {русское_имя_колонки: функция},
                                           который применяется к значениям колонок после переименования

    Returns:
        DataFrame: DataFrame с переименованными колонками и отформатированными значениями
    """
    rename_mappings = {
        "production": {
            "caseStage": COLUMNS["CASE_STAGE"],
            "monitoringStatus": COLUMNS["MONITORING_STATUS"],
            "completionStatus": COLUMNS["COMPLETION_STATUS"],
            "caseCode": COLUMNS["CASE_CODE"],
            "responsibleExecutor": COLUMNS["RESPONSIBLE_EXECUTOR"],
            "courtProtectionMethod": COLUMNS["METHOD_OF_PROTECTION"],
            "filingDate": COLUMNS["LAWSUIT_FILING_DATE"],
            "gosb": COLUMNS["GOSB"],
            "courtReviewingCase": COLUMNS["COURT"],
            "caseStatus": COLUMNS["CASE_STATUS"]
        },
        "tasks": {
            "taskCode": COLUMNS["TASK_CODE"],
            "failedCheck": COLUMNS["FAILED_CHECK"],
            "caseCode": COLUMNS["CASE_CODE"],
            "sourceType": COLUMNS["SOURCE_TYPE"],
            "responsibleExecutor": COLUMNS["RESPONSIBLE_EXECUTOR"],
            "caseStage": COLUMNS["CASE_STAGE"],
            "monitoringStatus": COLUMNS["MONITORING_STATUS"],
            "isCompleted": COLUMNS["IS_COMPLETED"],
            "taskText": COLUMNS["TASK_TEXT"],
            "reasonText": COLUMNS["REASON_TEXT"],
            "createdDate": COLUMNS["CREATED_DATE"],
            # Документные колонки:
            "transferCode": COLUMNS["TRANSFER_CODE"],
            "documentType": COLUMNS["DOCUMENT_TYPE"],
            "department": COLUMNS["DEPARTMENT_CATEGORY"],
            "requestCode": COLUMNS["DOCUMENT_REQUEST_CODE"],
        },
        "documents": {
            "requestCode": COLUMNS["DOCUMENT_REQUEST_CODE"],
            "caseCode": COLUMNS["CASE_CODE"],
            "document": COLUMNS["DOCUMENT_TYPE"],
            "department": COLUMNS["DEPARTMENT_CATEGORY"],
            "responseEssence": COLUMNS["ESSENSE_OF_THE_ANSWER"],
            "monitoringStatus": COLUMNS["MONITORING_STATUS"],
        }
    }

    mapping = rename_mappings.get(data_type, {})
    existing_columns = {eng: rus for eng, rus in mapping.items() if eng in dataframe.columns}

    if existing_columns:
        dataframe = dataframe.rename(columns=existing_columns)

    # Применяем форматирование значений колонок
    if value_formatters:
        for col, func in value_formatters.items():
            if col in dataframe.columns:
                dataframe[col] = dataframe[col].apply(func)

    return dataframe

    mapping = rename_mappings.get(data_type, {})

    # Применяем только те переименования, колонки которых существуют в DataFrame
    existing_columns = {eng: rus for eng, rus in mapping.items() if eng in dataframe.columns}

    if existing_columns:
        return dataframe.rename(columns=existing_columns)

    return dataframe


def add_source_columns_to_tasks(tasks_df: pd.DataFrame,
                                detailed_cleaned: pd.DataFrame,
                                documents_cleaned: pd.DataFrame) -> pd.DataFrame:
    """
    Добавляет дополнительные колонки из исходных отчетов в DataFrame задач.

    Для задач с sourceType == "detailed" данные берутся из detailed_cleaned по ключу caseCode.
    Для задач с sourceType == "documents" данные берутся из documents_cleaned по ключу transferCode.

    Args:
        tasks_df (pd.DataFrame): DataFrame исходных задач.
        detailed_cleaned (pd.DataFrame): DataFrame детального отчета.
        documents_cleaned (pd.DataFrame): DataFrame документов.

    Returns:
        pd.DataFrame: DataFrame задач с добавленными колонками.
    """
    import pandas as pd

    # Колонки для добавления
    columns_to_add = [
        COLUMNS.get("REQUEST_TYPE"),
        COLUMNS.get("COURT"),
        COLUMNS.get("BORROWER"),
        COLUMNS.get("CASE_NAME")
    ]

    result_df = tasks_df.copy()

    # Инициализация колонок
    for col in columns_to_add:
        if col is not None and col not in result_df.columns:
            result_df[col] = pd.NA

    # Добавление для детальных задач
    mask_detailed = result_df["sourceType"] == "detailed"
    if mask_detailed.any() and detailed_cleaned is not None and COLUMNS.get("CASE_CODE") in detailed_cleaned.columns:
        detailed_indexed = detailed_cleaned.drop_duplicates(
            subset=[COLUMNS["CASE_CODE"]],
            keep="last"
        ).set_index(COLUMNS["CASE_CODE"])

        for col in columns_to_add:
            if col in detailed_indexed.columns:
                result_df.loc[mask_detailed, col] = result_df.loc[mask_detailed, "caseCode"].map(detailed_indexed[col])

    # Добавление для документных задач
    mask_documents = result_df["sourceType"] == "documents"
    transfer_col = COLUMNS.get("TRANSFER_CODE")

    if mask_documents.any() and documents_cleaned is not None and transfer_col in documents_cleaned.columns:
        documents_indexed = documents_cleaned.drop_duplicates(
            subset=[transfer_col],
            keep="last"
        ).set_index(transfer_col)

        for col in columns_to_add:
            if col in documents_indexed.columns:
                result_df.loc[mask_documents, col] = result_df.loc[mask_documents, "transferCode"].map(
                    documents_indexed[col])

    # Порядок колонок
    column_order = [
        "taskCode",
        "caseCode",
        "responsibleExecutor",
        COLUMNS["REQUEST_TYPE"],
        COLUMNS["COURT"],
        COLUMNS["BORROWER"],
        COLUMNS["CASE_NAME"],
        "caseStage",
        "failedCheck",
        "taskText",
        "reasonText",
        "monitoringStatus",
        "sourceType",
        "documentType",
        "department",
        "transferCode",
        "requestCode",
        "isCompleted",
        "createdDate",
    ]

    existing_columns = [col for col in column_order if col in result_df.columns]
    other_columns = [col for col in result_df.columns if col not in existing_columns]

    return result_df[existing_columns + other_columns]