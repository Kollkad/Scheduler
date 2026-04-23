# backend/app/document_monitoring_v3/modules/document_row_analyzer_v3.py
"""
Модуль анализа документов для системы мониторинга сроков обработки

Содержит функции для оценки своевременности обработки документов
и фильтрации данных с учетом бизнес-логики мониторинга.

Основные функции:
- evaluate_documents_dataframe: Пакетная оценка статусов для множества документов
- filter_exceptions_documents: Фильтрация документов-исключений
- get_latest_document_in_group: Выбор последней записи в группе документов
"""

import pandas as pd
from datetime import date
from typing import Tuple
from backend.app.common.config.column_names import COLUMNS


def evaluate_documents_dataframe(df: pd.DataFrame, today: date) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Выполняет оценку статусов своевременности и завершенности для набора документов.

    Логика расчета для каждого документа:
    1. Если дата запроса отсутствует -> статус 'no_data', завершенность False
    2. Если дата передачи присутствует:
       - Сравнение даты передачи с дедлайном (дата запроса + 14 календарных дней)
       - Передача до дедлайна включительно -> 'timely'
       - Передача после дедлайна -> 'overdue'
       - Завершенность: True если суть ответа равна "Передача подтверждена"
    3. Если дата передачи отсутствует:
       - Сравнение текущей даты с дедлайном
       - Текущая дата превышает дедлайн -> 'overdue', завершенность False
       - Текущая дата не превышает дедлайн -> 'timely', завершенность согласно сути ответа
       - Особый случай: дедлайн прошел, но суть ответа подтверждена -> 'timely', True

    Args:
        df (pd.DataFrame): DataFrame с данными документов.
            Ожидаемые колонки:
            - COLUMNS["DOCUMENT_REQUEST_DATE"]: дата запроса документа
            - COLUMNS["DOCUMENT_TRANSFER_DATE"]: дата передачи документа
            - COLUMNS["ESSENSE_OF_THE_ANSWER"]: суть ответа
        today (date): Текущая дата для сравнения с дедлайном

    Returns:
        Tuple[pd.Series, pd.Series, pd.Series]:
            - monitoringStatus: Series со значениями 'timely', 'overdue' или 'no_data'
            - completionStatus: Series с булевыми значениями
            - executionDatePlan: Series с датами дедлайна (request_date + 14 дней) или NaT
    """
    monitoring_status = pd.Series("no_data", index=df.index, dtype=str)
    completion_status = pd.Series(False, index=df.index, dtype=bool)
    execution_date_plan = pd.Series(pd.NaT, index=df.index)

    request_date_series = pd.to_datetime(
        df[COLUMNS["DOCUMENT_REQUEST_DATE"]],
        errors='coerce'
    )
    transfer_date_series = pd.to_datetime(
        df[COLUMNS["DOCUMENT_TRANSFER_DATE"]],
        errors='coerce'
    )

    has_request_date = request_date_series.notna()

    if not has_request_date.any():
        return monitoring_status, completion_status, execution_date_plan

    # Расчет дедлайна: дата запроса + 14 календарных дней
    execution_date_plan = request_date_series + pd.Timedelta(days=14)
    deadline_series = execution_date_plan.dt.date
    today_date = pd.Timestamp(today).date()

    response_essence = df[COLUMNS["ESSENSE_OF_THE_ANSWER"]]
    is_transfer_confirmed = (response_essence == "Передача подтверждена")
    completion_status = is_transfer_confirmed.copy()

    has_transfer_date = transfer_date_series.notna()

    # ===== СЛУЧАЙ 1: Документы с датой передачи =====
    with_transfer = has_request_date & has_transfer_date

    if with_transfer.any():
        transfer_date = transfer_date_series.dt.date
        deadline = deadline_series

        timely_mask = with_transfer & (transfer_date <= deadline)
        overdue_mask = with_transfer & (transfer_date > deadline)

        monitoring_status.loc[timely_mask] = "timely"
        monitoring_status.loc[overdue_mask] = "overdue"

    # ===== СЛУЧАЙ 2: Документы без даты передачи =====
    without_transfer = has_request_date & ~has_transfer_date

    if without_transfer.any():
        deadline = deadline_series

        deadline_passed = today_date > deadline
        deadline_not_passed = today_date <= deadline

        overdue_mask = without_transfer & deadline_passed
        timely_mask = without_transfer & deadline_not_passed

        monitoring_status.loc[overdue_mask] = "overdue"
        monitoring_status.loc[timely_mask] = "timely"

        special_mask = without_transfer & deadline_passed & is_transfer_confirmed
        if special_mask.any():
            monitoring_status.loc[special_mask] = "timely"
            completion_status.loc[special_mask] = True

    return monitoring_status, completion_status, execution_date_plan


def filter_exceptions_documents(documents_df: pd.DataFrame) -> pd.DataFrame:
    """
    Выполняет фильтрацию документов, являющихся исключениями.

    В текущей реализации функция возвращает исходный DataFrame без изменений.
    Критерии исключений для документов будут определены позднее.

    Args:
        documents_df (pd.DataFrame): DataFrame с исходными данными документов

    Returns:
        pd.DataFrame: DataFrame без документов-исключений
    """
    return documents_df


def get_latest_document_in_group(group: pd.DataFrame) -> pd.Series:
    """
    Определяет последнюю запись в группе документов.

    Выбор осуществляется по следующим правилам:
    1. Приоритет отдается дате передачи документа (наибольшая дата)
    2. При отсутствии дат передачи используется дата получения (наибольшая дата)
    3. При отсутствии обеих дат возвращается первая запись из группы

    Args:
        group (pd.DataFrame): Группа документов, сгруппированная по ключевым полям

    Returns:
        pd.Series: Строка DataFrame, представляющая последний документ в группе.
                   Пустая Series, если группа пуста.
    """
    if group.empty:
        return pd.Series()

    if COLUMNS["DOCUMENT_TRANSFER_DATE"] in group.columns:
        transfer_not_na = group[COLUMNS["DOCUMENT_TRANSFER_DATE"]].notna()
        if transfer_not_na.any():
            latest_idx = group.loc[transfer_not_na, COLUMNS["DOCUMENT_TRANSFER_DATE"]].idxmax()
            return group.loc[latest_idx]

    if COLUMNS["DOCUMENT_RECEIPT_DATE"] in group.columns:
        receipt_not_na = group[COLUMNS["DOCUMENT_RECEIPT_DATE"]].notna()
        if receipt_not_na.any():
            latest_idx = group.loc[receipt_not_na, COLUMNS["DOCUMENT_RECEIPT_DATE"]].idxmax()
            return group.loc[latest_idx]

    return group.iloc[0]

