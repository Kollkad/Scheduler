# backend/app/terms_of_support_v3/modules/terms_analyzer_v3.py
"""
Модуль вспомогательных функций для анализа сроков сопровождения дел (v3)

Содержит универсальные функции для обработки данных дел, используемые как в исковом,
так и в приказном производстве. Функции работают с DataFrame и возвращают
результаты в формате, совместимом с apply_checks_by_stage.
"""

import pandas as pd
from datetime import date
from typing import Tuple

from backend.app.common.config.column_names import COLUMNS, VALUES
from backend.app.common.modules.utils import get_filing_date_series

def evaluate_exceptions_dataframe(df: pd.DataFrame, today: date) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Определяет исключительные статусы дел для пакетной обработки.

    Проверяет колонку CASE_STATUS и возвращает соответствующий тип исключения.
    Используется как для искового, так и для приказного производства.

    Args:
        df (pd.DataFrame): DataFrame с данными дел.
            Ожидаемая колонка: COLUMNS["CASE_STATUS"]
        today (date): Текущая дата (не используется, сохранено для единой сигнатуры)

    Returns:
        Tuple[pd.Series, pd.Series]:
            - monitoringStatus: Series со значениями 'reopened', 'complaint_filed',
              'error_dublicate', 'withdraw_by_the_initiator' или 'no_data'
            - completionStatus: Series со значением False для всех строк
    """
    # Инициализация результатов значениями по умолчанию
    monitoring_status = pd.Series("no_data", index=df.index, dtype=str)
    completion_status = pd.Series(False, index=df.index, dtype=bool)
    execution_date_plan = pd.Series(pd.NaT, index=df.index)

    # Проверка наличия колонки со статусом дела
    case_status_col = COLUMNS["CASE_STATUS"]
    if case_status_col not in df.columns:
        return monitoring_status, completion_status, execution_date_plan

    case_status = df[case_status_col]

    # Определение масок для каждого типа исключения
    monitoring_status.loc[case_status == VALUES["REOPENED"]] = "reopened"
    monitoring_status.loc[case_status == VALUES["COMPLAINT_FILED"]] = "complaint_filed"
    monitoring_status.loc[case_status == VALUES["ERROR_DUBLICATE"]] = "error_dublicate"
    monitoring_status.loc[case_status == VALUES["WITHDRAWN_BY_THE_INITIATOR"]] = "withdraw_by_the_initiator"

    return monitoring_status, completion_status, execution_date_plan

def prepare_filtered_cases_response(df: pd.DataFrame) -> list:
    """
    Подготавливает структурированные данные дел для отображения в таблице.

    Выбирает и переименовывает колонки из объединенного DataFrame
    (дела + check_results) в формат, ожидаемый фронтендом.

    Args:
        df (pd.DataFrame): Объединенный DataFrame с данными дел и результатами проверок.
            Ожидаемые колонки:
            - COLUMNS["CASE_CODE"]
            - COLUMNS["RESPONSIBLE_EXECUTOR"]
            - COLUMNS["METHOD_OF_PROTECTION"]
            - COLUMNS["LAWSUIT_FILING_DATE"]
            - COLUMNS["GOSB"]
            - COLUMNS["COURT"]
            - COLUMNS["CASE_STATUS"]
            - COLUMNS["CATEGORY"]
            - COLUMNS["DEPARTMENT_CATEGORY"]
            - stageCode
            - monitoringStatus

    Returns:
        list: Список словарей с данными дел в формате для фронтенда.
    """
    if "filingDate" not in df.columns:
        df["filingDate"] = get_filing_date_series(df)
    # Колонки для включения в ответ
    columns_to_include = {
        COLUMNS["CASE_CODE"]: "caseCode",
        COLUMNS["RESPONSIBLE_EXECUTOR"]: "responsibleExecutor",
        COLUMNS["METHOD_OF_PROTECTION"]: "courtProtectionMethod",
        COLUMNS["GOSB"]: "gosb",
        COLUMNS["COURT"]: "courtReviewingCase",
        COLUMNS["CASE_STATUS"]: "caseStatus",
        COLUMNS["CATEGORY"]: "caseCategory",
        COLUMNS["DEPARTMENT_CATEGORY"]: "department",
        "stageCode": "caseStage",
        "monitoringStatus": "monitoringStatus",
        "filingDate": "filingDate",
    }

    existing_columns = {k: v for k, v in columns_to_include.items() if k in df.columns}
    result_df = df[list(existing_columns.keys())].rename(columns=existing_columns)
    return result_df.to_dict(orient="records")
