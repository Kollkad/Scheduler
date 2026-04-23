# backend/app/terms_of_support_v3/modules/order_dataframe_analyzer_v3.py
"""
Модуль анализа дел для приказного производства (v3)

Содержит функции для пакетной оценки соблюдения сроков на различных этапах
приказного производства. Каждая функция принимает DataFrame и возвращает
результаты в формате, совместимом с apply_checks_by_stage.

Основные категории проверок:
- Закрытие дела (Closed)
- Получение исполнительного документа (Execution Document Received)
- Реакция суда (Court Reaction)
- Смена статуса (First Status Changed)
"""

import pandas as pd
from datetime import date, timedelta
from typing import Tuple

from backend.app.common.config.column_names import COLUMNS, VALUES
from backend.app.common.modules.utils import get_filing_date, safe_get_column_series


def evaluate_order_closed_dataframe(df: pd.DataFrame, today: date) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Выполняет пакетную оценку своевременности закрытия дел в приказном производстве.

    Сравнивает дату закрытия дела с дедлайном в 90 календарных дней
    от даты подачи заявления. Если дата закрытия отсутствует, проверяет
    не истек ли дедлайн на текущую дату.

    Args:
        df (pd.DataFrame): DataFrame с данными дел.
            Ожидаемые колонки: COLUMNS["CASE_CLOSING_DATE"]
        today (date): Текущая дата для сравнения с дедлайном

    Returns:
        Tuple[pd.Series, pd.Series]:
            - monitoringStatus: Series со значениями 'timely', 'overdue' или 'no_data'
            - completionStatus: Series с булевыми значениями (True если дело закрыто)
    """
    # Инициализация результатов значениями по умолчанию
    monitoring_status = pd.Series("no_data", index=df.index, dtype=str)
    completion_status = pd.Series(False, index=df.index, dtype=bool)
    execution_date_plan = pd.Series(pd.NaT, index=df.index)

    # Получение даты подачи заявления для каждой строки
    filing_dates = df.apply(get_filing_date, axis=1)
    has_filing_date = filing_dates.notna()

    if not has_filing_date.any():
        return monitoring_status, completion_status, execution_date_plan

    # Расчет дедлайна закрытия дела (90 календарных дней от подачи)
    deadline_dates = filing_dates.apply(lambda d: d.date() + timedelta(days=90) if pd.notna(d) else pd.NaT)
    execution_date_plan = deadline_dates
    today_date = pd.Timestamp(today).date()

    # Получение даты закрытия дела
    closing_date_series = pd.to_datetime(
        safe_get_column_series(df, COLUMNS["CASE_CLOSING_DATE"]),
        errors='coerce'
    )
    has_closing_date = closing_date_series.notna()

    # ===== СЛУЧАЙ 1: Есть дата закрытия =====
    with_closing = has_filing_date & has_closing_date

    if with_closing.any():
        closing_date = closing_date_series[with_closing].dt.date
        deadline = deadline_dates[with_closing]

        # Закрыто в срок
        timely_mask = with_closing & (closing_date <= deadline)
        # Закрыто с нарушением срока
        overdue_mask = with_closing & (closing_date > deadline)

        monitoring_status.loc[timely_mask] = "timely"
        monitoring_status.loc[overdue_mask] = "overdue"
        completion_status.loc[with_closing] = True

    # ===== СЛУЧАЙ 2: Нет даты закрытия =====
    without_closing = has_filing_date & ~has_closing_date

    if without_closing.any():
        deadline = deadline_dates[without_closing]

        # Дедлайн истек
        overdue_mask = without_closing & (today_date > deadline)
        # Дедлайн еще не наступил
        timely_mask = without_closing & (today_date <= deadline)

        monitoring_status.loc[overdue_mask] = "overdue"
        monitoring_status.loc[timely_mask] = "timely"
        # completion_status остается False

    return monitoring_status, completion_status, execution_date_plan

def evaluate_order_execution_document_dataframe(df: pd.DataFrame, today: date) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    TODO: Определить корректную логику проверки получения исполнительного документа.
    Текущая версия возвращает 'no_data' для всех строк.
    """
    monitoring_status = pd.Series("no_data", index=df.index, dtype=str)
    completion_status = pd.Series(False, index=df.index, dtype=bool)
    execution_date_plan = pd.Series(pd.NaT, index=df.index)
    return monitoring_status, completion_status, execution_date_plan


def evaluate_order_court_reaction_dataframe(df: pd.DataFrame, today: date) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Выполняет пакетную оценку полноты реакции суда в приказном производстве.

    Проверяет выполнение всех условий реакции суда в течение 60 календарных дней
    от даты подачи заявления. Условия включают: вынесение судебного приказа,
    заполнение дат получения/передачи ИД, установление статуса "Условно закрыто".

    Args:
        df (pd.DataFrame): DataFrame с данными дел.
            Ожидаемые колонки:
            - COLUMNS["COURT_DETERMINATION"]: определение суда
            - COLUMNS["ACTUAL_RECEIPT_DATE"]: дата получения ИД
            - COLUMNS["ACTUAL_TRANSFER_DATE"]: дата передачи ИД
            - COLUMNS["CASE_STATUS"]: статус дела
        today (date): Текущая дата для сравнения с дедлайном

    Returns:
        Tuple[pd.Series, pd.Series]:
            - monitoringStatus: Series со значениями 'timely', 'overdue' или 'no_data'
            - completionStatus: Series с булевыми значениями (True если все условия выполнены)
    """
    # Инициализация результатов значениями по умолчанию
    monitoring_status = pd.Series("no_data", index=df.index, dtype=str)
    completion_status = pd.Series(False, index=df.index, dtype=bool)
    execution_date_plan = pd.Series(pd.NaT, index=df.index)

    # Получение даты подачи заявления для каждой строки
    filing_dates = df.apply(get_filing_date, axis=1)
    has_filing_date = filing_dates.notna()

    if not has_filing_date.any():
        return monitoring_status, completion_status, execution_date_plan

    # Расчет дедлайна реакции суда (60 календарных дней от подачи)
    deadline_dates = filing_dates.apply(lambda d: d.date() + timedelta(days=60) if pd.notna(d) else pd.NaT)
    execution_date_plan = deadline_dates
    today_date = pd.Timestamp(today).date()

    # Проверка условий реакции суда
    court_determination = safe_get_column_series(df, COLUMNS["COURT_DETERMINATION"])
    has_court_order = (court_determination == VALUES["COURT_ORDER"])

    receipt_date = pd.to_datetime(
        safe_get_column_series(df, COLUMNS["ACTUAL_RECEIPT_DATE"]),
        errors='coerce'
    )
    has_receipt_date = receipt_date.notna()

    transfer_date = pd.to_datetime(
        safe_get_column_series(df, COLUMNS["ACTUAL_TRANSFER_DATE"]),
        errors='coerce'
    )
    has_transfer_date = transfer_date.notna()

    case_status = safe_get_column_series(df, COLUMNS["CASE_STATUS"])
    has_correct_status = (case_status == VALUES["CONDITIONALLY_CLOSED"])

    # Все условия выполнены
    all_conditions_met = has_court_order & has_receipt_date & has_transfer_date & has_correct_status
    completion_status = all_conditions_met.copy()

    # Для строк с датой подачи
    valid_mask = has_filing_date

    if valid_mask.any():
        deadline = deadline_dates[valid_mask]
        conditions_met = all_conditions_met[valid_mask]

        # После дедлайна: timely если все условия выполнены, иначе overdue
        after_deadline = valid_mask & (today_date > deadline)
        monitoring_status.loc[after_deadline & conditions_met] = "timely"
        monitoring_status.loc[after_deadline & ~conditions_met] = "overdue"

        # До дедлайна: всегда timely
        before_deadline = valid_mask & (today_date <= deadline)
        monitoring_status.loc[before_deadline] = "timely"

    return monitoring_status, completion_status, execution_date_plan

def evaluate_order_first_status_dataframe(df: pd.DataFrame, today: date) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Выполняет пакетную оценку своевременности смены первоначального статуса дела.

    Контролирует смену статуса с "Подготовка документов" на "Ожидание реакции суда"
    в течение 14 календарных дней от даты подачи заявления.

    Args:
        df (pd.DataFrame): DataFrame с данными дел.
            Ожидаемые колонки:
            - COLUMNS["CASE_STATUS"]: статус дела
        today (date): Текущая дата для сравнения с дедлайном

    Returns:
        Tuple[pd.Series, pd.Series]:
            - monitoringStatus: Series со значениями 'timely', 'overdue' или 'no_data'
            - completionStatus: Series со значением False для всех строк
    """
    # Инициализация результатов значениями по умолчанию
    monitoring_status = pd.Series("no_data", index=df.index, dtype=str)
    completion_status = pd.Series(False, index=df.index, dtype=bool)
    execution_date_plan = pd.Series(pd.NaT, index=df.index)

    # Получение даты подачи заявления для каждой строки
    filing_dates = df.apply(get_filing_date, axis=1)
    has_filing_date = filing_dates.notna()

    if not has_filing_date.any():
        return monitoring_status, completion_status, execution_date_plan

    # Расчет дедлайна смены статуса (14 календарных дней от подачи)
    deadline_dates = filing_dates.apply(lambda d: d.date() + timedelta(days=14) if pd.notna(d) else pd.NaT)
    execution_date_plan = deadline_dates
    today_date = pd.Timestamp(today).date()

    # Получение текущего статуса дела
    current_status = safe_get_column_series(df, COLUMNS["CASE_STATUS"])

    # Статус уже сменился на ожидание реакции суда
    status_changed = (current_status == VALUES["AWAITING_COURT_RESPONSE"])

    # Статус все еще подготовка документов
    still_preparing = (current_status == VALUES["PREPARATION_OF_DOCUMENTS"])

    # Маски для разных случаев
    valid_mask = has_filing_date

    if valid_mask.any():
        deadline = deadline_dates[valid_mask]

        # Статус уже сменился — своевременно
        monitoring_status.loc[valid_mask & status_changed] = "timely"

        # Дедлайн истек и статус все еще подготовка — просрочено
        overdue_mask = valid_mask & (today_date > deadline) & still_preparing
        monitoring_status.loc[overdue_mask] = "overdue"

        # Остальные случаи (время есть или статус другой) — своевременно
        remaining_mask = valid_mask & ~status_changed & ~overdue_mask
        monitoring_status.loc[remaining_mask] = "timely"

    return monitoring_status, completion_status, execution_date_plan


