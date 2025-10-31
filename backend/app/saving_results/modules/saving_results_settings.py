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
        "overdue": "просрочена",
        "no_data": "нет данных"
    }

    status_parts = status_string.split(';')
    formatted_parts = []

    for index, status in enumerate(status_parts):
        clean_status = status.strip().lower()
        translated_status = status_mapping.get(clean_status, clean_status)
        formatted_parts.append(f"Проверка {index + 1} - {translated_status}")

    return '; '.join(formatted_parts)

def generate_filename(report_type: str) -> str:
    """
    Генерация уникального имени файла для экспорта с временной меткой.

    Args:
        report_type (str): Тип отчета ('detailed_report', 'documents_report')

    Returns:
        str: Уникальное имя файла с временной меткой
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    type_names = {
        "detailed_report": "детальный_отчет",
        "documents_report": "отчет_документов",
    }

    report_name = type_names.get(report_type, report_type)
    return f"{report_name}_{timestamp}.xlsx"


def save_with_xlsxwriter_formatting(dataframe, filepath, sheet_name, data_type=None):
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
        if data_type == "tasks":
            dataframe = apply_task_data_mapping(dataframe)
        # Переименование колонок если указан data_type
        if data_type:
            dataframe = rename_columns_to_russian(dataframe, data_type)

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


def rename_columns_to_russian(dataframe, data_type):
    """
    Переименование столбцов DataFrame с английских названий на русские согласно конфигурации.

    Args:
        dataframe: DataFrame для переименования
        data_type (str): Тип данных для определения набора переименований

    Returns:
        DataFrame: DataFrame с переименованными колонками
    """
    # Словари переименования для разных типов данных
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
            "taskType": COLUMNS["TASK_TYPE"],
            "caseCode": COLUMNS["CASE_CODE"],
            "sourceType": COLUMNS["SOURCE_TYPE"],
            "responsibleExecutor": COLUMNS["RESPONSIBLE_EXECUTOR"],
            "caseStage": COLUMNS["CASE_STAGE"],
            "monitoringStatus": COLUMNS["MONITORING_STATUS"],
            "isCompleted": COLUMNS["IS_COMPLETED"],
            "taskText": COLUMNS["TASK_TEXT"],
            "reasonText": COLUMNS["REASON_TEXT"],
            "failedChecksCount": COLUMNS["FAILED_CHECKS_COUNT"],
            "createdDate": COLUMNS["CREATED_DATE"]
        }
    }

    mapping = rename_mappings.get(data_type, {})

    # Применяем только те переименования, колонки которых существуют в DataFrame
    existing_columns = {eng: rus for eng, rus in mapping.items() if eng in dataframe.columns}

    if existing_columns:
        return dataframe.rename(columns=existing_columns)

    return dataframe


def apply_task_data_mapping(dataframe):
    """
    Применяет маппинг этапов и статусов для данных задач перед экспортом.

    Args:
        dataframe: DataFrame с задачами

    Returns:
        DataFrame: DataFrame с переведенными значениями
    """
    if dataframe is None or dataframe.empty:
        return dataframe

    # Создаем копию чтобы не изменять оригинальные данные
    result_df = dataframe.copy()

    # Маппинг этапов дела
    if 'caseStage' in result_df.columns:
        result_df['caseStage'] = result_df['caseStage'].map(
            lambda x: CASE_STAGE_MAPPING.get(x, x) if pd.notna(x) else "Не указан"
        )

    # Маппинг статусов мониторинга
    if 'monitoringStatus' in result_df.columns:
        result_df['monitoringStatus'] = result_df['monitoringStatus'].apply(format_monitoring_status)

    return result_df