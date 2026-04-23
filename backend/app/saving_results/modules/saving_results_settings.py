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


def generate_filename(report_type: str, custom_name: str = None) -> str:
    """
    Генерация имени файла для экспорта по заданному шаблону.

    Args:
        report_type (str): Тип отчета.
        custom_name (str, optional): Дополнительное имя (например, логин пользователя).

    Returns:
        str: Имя файла с расширением .xlsx
    """
    timestamp = datetime.now().strftime("%d-%m-%Y")

    type_names = {
        "detailed_report": f"source_data_Детальный_отчет_{timestamp}",
        "documents_report": f"source_data_Отчет_по_полученным_и_переданным_документам_{timestamp}",
        "stages": "stages_Этапы_документов_и_дел",
        "checks": "checks_Проверки_документов_и_дел",
        "check_results_cases": f"check_results_Проведенные_проверки_для_дел_{timestamp}",
        "check_results_documents": f"check_results_Проведенные_проверки_для_документов_{timestamp}",
        "tasks": f"tasks_Поставленные_задачи_{timestamp}",
        "tasks_by_executor": f"tasks_Поставленные_задачи_для_{custom_name}_{timestamp}" if custom_name else f"tasks_Поставленные_задачи_{timestamp}",
        "user_overrides": f"user_overrides_Изменения_задач_пользователя_{custom_name}" if custom_name else "user_overrides_Изменения_задач_пользователя",
    }

    filename = type_names.get(report_type, f"export_{timestamp}")
    return f"{filename}.xlsx"


def save_with_xlsxwriter_formatting(dataframe: pd.DataFrame, filepath: str, sheet_name: str) -> bool:
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

    Returns:
        bool: True при успешном сохранении, False при использовании fallback
    """
    try:
        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            dataframe.to_excel(writer, sheet_name=sheet_name, index=False)

            workbook = writer.book
            worksheet = writer.sheets[sheet_name]

            # Форматы с серой границей
            border_format = {
                'border': 1,
                'border_color': '#D0D0D0'
            }

            # Формат для заголовков таблицы
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#439639',
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
                'bg_color': '#F8FBFC',
                'text_wrap': True,
                'valign': 'vcenter',
                'align': 'center',
                **border_format
            })

            # Применение форматирования к заголовкам
            for col_num, value in enumerate(dataframe.columns.values):
                worksheet.write(0, col_num, value, header_format)

            # Автоматическая ширина колонок
            for col_num, column_name in enumerate(dataframe.columns):
                max_len = len(str(column_name))
                try:
                    col_data = dataframe[column_name].astype(str)
                    max_len = max(max_len, col_data.str.len().max())
                except:
                    pass
                width = min(max(max_len, 10), 50)
                worksheet.set_column(col_num, col_num, width)

            # Применение чередующейся заливки к строкам данных
            for row_num in range(len(dataframe)):
                if row_num % 2 == 0:
                    worksheet.set_row(row_num + 1, None, even_row_format)
                else:
                    worksheet.set_row(row_num + 1, None, odd_row_format)

        size = os.path.getsize(filepath)
        print(f"✅ Файл создан с форматированием, размер: {size} байт")
        return True

    except Exception as e:
        print(f"❌ Ошибка форматирования: {e}")
        # Fallback: сохранение без форматирования
        dataframe.to_excel(filepath, index=False, sheet_name=sheet_name)
        return False


# ==================== ФУНКЦИИ ЗАМЕНЫ ЗНАЧЕНИЙ ====================

def format_monitoring_status(value: str) -> str:
    """
    Заменяет технические значения monitoringStatus на русские.
    Исключения (reopened, complaint_filed, error_dublicate, withdraw_by_the_initiator)
    остаются без изменений.
    """
    if pd.isna(value):
        return "Нет данных"

    status_mapping = {
        "timely": "В срок",
        "overdue": "Просрочено",
        "no_data": "Нет данных",
    }

    return status_mapping.get(str(value).strip().lower(), str(value))


def format_completion_status(value: bool) -> str:
    """Заменяет True/False на русские значения."""
    if pd.isna(value):
        return "—"
    return "Завершено" if value else "Не завершено"


def format_is_completed(value: bool) -> str:
    """Заменяет True/False на русские значения для задач."""
    if pd.isna(value):
        return "—"
    return "Выполнено" if value else "Не выполнено"


def format_is_active(value: bool) -> str:
    """Заменяет True/False на Да/Нет."""
    if pd.isna(value):
        return "—"
    return "Да" if value else "Нет"


def format_stage_code(value: str, stages_df: pd.DataFrame) -> str:
    """
    Заменяет stageCode на stageName из справочника этапов.
    """
    if pd.isna(value):
        return "Не указан"

    if stages_df is None or stages_df.empty:
        return str(value)

    match = stages_df[stages_df["stageCode"] == str(value).strip()]
    if not match.empty:
        return match.iloc[0]["stageName"]

    return str(value)


# ==================== ФУНКЦИИ ОБОГАЩЕНИЯ ДАННЫХ ====================

def enrich_tasks_for_export(
        tasks_df: pd.DataFrame,
        check_results_df: pd.DataFrame,
        checks_df: pd.DataFrame,
        stages_df: pd.DataFrame,
        cases_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Обогащает DataFrame задач дополнительными колонками из связанных данных.

    Добавляет колонки:
    - Из check_results: executionDatePlan, monitoringStatus, completionStatus
    - Из checks: checkName
    - Из stages: stageName (через check_results → checkCode → checks → stageCode → stages)
    - Из cases_df: CASE_NUMBER, RESPONSIBLE_EXECUTOR, COURT, BORROWER, CASE_NAME

    Args:
        tasks_df: DataFrame с задачами (должен содержать checkResultCode)
        check_results_df: DataFrame с результатами проверок
        checks_df: DataFrame с конфигурацией проверок
        stages_df: DataFrame с этапами
        cases_df: DataFrame с делами

    Returns:
        pd.DataFrame: Обогащенный DataFrame задач
    """
    result_df = tasks_df.copy()

    # 1. Присоединяем check_results
    if not check_results_df.empty and "checkResultCode" in result_df.columns:
        check_cols = ["checkResultCode", "checkCode", "targetId", "monitoringStatus", "completionStatus"]
        if "executionDatePlan" in check_results_df.columns:
            check_cols.append("executionDatePlan")

        available = [c for c in check_cols if c in check_results_df.columns]
        result_df = result_df.merge(
            check_results_df[available],
            on="checkResultCode",
            how="left",
            suffixes=("", "_cr")
        )

    # 2. Присоединяем checks_df для checkName и stageCode
    if not checks_df.empty and "checkCode" in result_df.columns:
        result_df = result_df.merge(
            checks_df[["checkCode", "checkName", "stageCode"]],
            on="checkCode",
            how="left",
            suffixes=("", "_ch")
        )

    # 3. Присоединяем stages_df для stageName
    if not stages_df.empty and "stageCode" in result_df.columns:
        result_df = result_df.merge(
            stages_df[["stageCode", "stageName"]],
            on="stageCode",
            how="left",
            suffixes=("", "_st")
        )

    # 4. Присоединяем cases_df для дополнительных колонок
    if not cases_df.empty and "targetId" in result_df.columns:
        case_cols = [
            COLUMNS["CASE_CODE"],
            COLUMNS["CASE_NUMBER"],
            COLUMNS["RESPONSIBLE_EXECUTOR"],
            COLUMNS["COURT"],
            COLUMNS["BORROWER"],
            COLUMNS["CASE_NAME"],
        ]
        available = [c for c in case_cols if c in cases_df.columns]
        if available:
            result_df = result_df.merge(
                cases_df[available],
                left_on="targetId",
                right_on=COLUMNS["CASE_CODE"],
                how="left",
                suffixes=("", "_case")
            )

    return result_df

# ==================== МАППИНГИ ПЕРЕИМЕНОВАНИЙ ====================

# Детальный отчет и отчет документов (переименование + замена stageCode → stageName)
DETAILED_AND_DOCUMENTS_RENAME_MAP = {
    "stageCode": COLUMNS["CASE_STAGE"],
}

# Этапы
STAGES_RENAME_MAP = {
    "stageCode": COLUMNS["STAGE_CODE"],
    "stageName": COLUMNS["CASE_STAGE"],
    "fileType": COLUMNS["SOURCE_TYPE"],
}

# Проверки
CHECKS_RENAME_MAP = {
    "checkCode": COLUMNS["CHECK_CODE"],
    "checkName": COLUMNS["CHECK_NAME"],
    "stageCode": COLUMNS["STAGE_CODE"],
    "functionName": COLUMNS["FUNCTION_NAME_IN_CODE"],
    "isActive": COLUMNS["IS_CHECK_ACTIVE"],
}

# Результаты проверок
CHECK_RESULTS_RENAME_MAP = {
    "checkResultCode": COLUMNS["CHECK_RESULT_CODE"],
    "checkCode": COLUMNS["CHECK_CODE"],
    "targetId": COLUMNS["TARGET_ID"],
    "monitoringStatus": COLUMNS["MONITORING_STATUS"],
    "completionStatus": COLUMNS["COMPLETION_STATUS"],
    "checkedAt": COLUMNS["DATA_TIME_CHECK_EXECUTION"],
    "executionDatePlan": COLUMNS["PLANNED_DATE_FOR_TASK_EXECUTION"],
}

# Задачи (основные колонки)
TASKS_RENAME_MAP = {
    "taskCode": COLUMNS["TASK_CODE"],
    "checkResultCode": COLUMNS["CHECK_RESULT_CODE"],
    "taskText": COLUMNS["TASK_TEXT"],
    "reasonText": COLUMNS["REASON_TEXT"],
    "createdAt": COLUMNS["DATA_TIME_TASK_CREATE"],
    "isCompleted": COLUMNS["IS_COMPLETED"],
    "executionDateTimeFact": COLUMNS["FACT_DATE_OF_TASK_EXECUTION"],
    "createdBy": COLUMNS["AUTHOR_OF_THE_TASK"],
}

# Дополнительные колонки для обогащения задач
TASKS_EXTRA_RENAME_MAP = {
    "executionDatePlan": COLUMNS["EXECUTION_DATE_PLAN"],
    "monitoringStatus": COLUMNS["MONITORING_STATUS"],
    "completionStatus": COLUMNS["COMPLETION_STATUS"],
    "checkName": COLUMNS["CHECK_NAME"],
    "stageName": COLUMNS["CASE_STAGE"],
    COLUMNS["CASE_NUMBER"]: COLUMNS["CASE_NUMBER"],
    COLUMNS["RESPONSIBLE_EXECUTOR"]: COLUMNS["RESPONSIBLE_EXECUTOR"],
    COLUMNS["COURT"]: COLUMNS["COURT"],
    COLUMNS["BORROWER"]: COLUMNS["BORROWER"],
    COLUMNS["CASE_NAME"]: COLUMNS["CASE_NAME"],
}

# Пользовательские переопределения (основные колонки)
USER_OVERRIDES_RENAME_MAP = {
    "taskCode": COLUMNS["TASK_CODE"],
    "checkResultCode": COLUMNS["CHECK_RESULT_CODE"],
    "taskText": COLUMNS["TASK_TEXT"],
    "reasonText": COLUMNS["REASON_TEXT"],
    "createdAt": COLUMNS["DATA_TIME_TASK_CREATE"],
    "isCompleted": COLUMNS["IS_COMPLETED"],
    "executionDateTimeFact": COLUMNS["FACT_DATE_OF_TASK_EXECUTION"],
    "createdBy": COLUMNS["AUTHOR_OF_THE_TASK"],
    "executionDatePlan": COLUMNS["EXECUTION_DATE_PLAN"],
    "shiftCode": COLUMNS["SHIFT_CODE"],
}

