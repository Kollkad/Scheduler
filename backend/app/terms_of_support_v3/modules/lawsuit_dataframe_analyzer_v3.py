# backend/app/terms_of_support_v3/modules/lawsuit_dataframe_analyzer_v3.py
"""
Модуль анализа дел для искового производства (v3)

Содержит функции для пакетной оценки соблюдения сроков на различных этапах
искового производства. Каждая функция принимает DataFrame и возвращает
результаты в формате, совместимом с apply_checks_by_stage.

Основные категории проверок:
- Закрытие дела (Closed)
- Получение исполнительного документа (Execution Document Received)
- Вынесение и получение решения (Decision Made)
- Назначение заседаний (Under Consideration)
- Реакция суда (Court Reaction)
- Смена статуса (First Status Changed)
"""

import pandas as pd
from datetime import date, timedelta
from typing import Tuple

from backend.app.common.config.column_names import COLUMNS, VALUES
from backend.app.common.config.calendar_config import russian_calendar
from backend.app.common.modules.utils import get_filing_date, safe_get_column_series


def evaluate_closed_dataframe(df: pd.DataFrame, today: date) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Выполняет пакетную оценку своевременности закрытия дел в исковом производстве.

    Сравнивает дату закрытия дела с дедлайном в 125 календарных дней
    от даты подачи иска. Если дата закрытия отсутствует, проверяет
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

    # Получение даты подачи иска для каждой строки
    filing_dates = df.apply(get_filing_date, axis=1)
    has_filing_date = filing_dates.notna()

    if not has_filing_date.any():
        return monitoring_status, completion_status, execution_date_plan

    # Расчет дедлайна закрытия дела (125 календарных дней от подачи)
    deadline_dates = filing_dates.apply(lambda d: d.date() + timedelta(days=125) if pd.notna(d) else pd.NaT)
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

def evaluate_execution_document_received_dataframe(df: pd.DataFrame, today: date) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    TODO: Определить корректную логику проверки получения исполнительного документа.
    Текущая версия возвращает 'no_data' для всех строк.
    """
    monitoring_status = pd.Series("no_data", index=df.index, dtype=str)
    completion_status = pd.Series(False, index=df.index, dtype=bool)
    execution_date_plan = pd.Series(pd.NaT, index=df.index)

    return monitoring_status, completion_status, execution_date_plan


def evaluate_decision_date_dataframe(df: pd.DataFrame, today: date) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Выполняет пакетную оценку своевременности вынесения решения суда.

    Сравнивает дату вынесения решения с дедлайном в 45 календарных дней
    от даты принятия дела к производству. Если дата решения отсутствует,
    проверяет не истек ли дедлайн на текущую дату.

    Args:
        df (pd.DataFrame): DataFrame с данными дел.
            Ожидаемые колонки:
            - COLUMNS["DECISION_COURT_DATE"]: дата принятия дела к производству
            - COLUMNS["COURT_DECISION_DATE"]: дата вынесения решения
        today (date): Текущая дата для сравнения с дедлайном

    Returns:
        Tuple[pd.Series, pd.Series]:
            - monitoringStatus: Series со значениями 'timely', 'overdue' или 'no_data'
            - completionStatus: Series с булевыми значениями (True если решение вынесено)
    """
    # Инициализация результатов значениями по умолчанию
    monitoring_status = pd.Series("no_data", index=df.index, dtype=str)
    completion_status = pd.Series(False, index=df.index, dtype=bool)
    execution_date_plan = pd.Series(pd.NaT, index=df.index)

    # Получение даты принятия дела к производству
    decision_court_series = pd.to_datetime(
        safe_get_column_series(df, COLUMNS["DECISION_COURT_DATE"]),
        errors='coerce'
    )
    has_decision_court = decision_court_series.notna()

    if not has_decision_court.any():
        return monitoring_status, completion_status, execution_date_plan

    # Расчет дедлайна вынесения решения (45 календарных дней)
    deadline_dates = decision_court_series.dt.date + timedelta(days=45)
    execution_date_plan = deadline_dates
    today_date = pd.Timestamp(today).date()

    # Получение даты вынесения решения
    court_decision_series = pd.to_datetime(
        safe_get_column_series(df, COLUMNS["COURT_DECISION_DATE"]),
        errors='coerce'
    )
    has_court_decision = court_decision_series.notna()

    # ===== СЛУЧАЙ 1: Есть дата вынесения решения =====
    with_decision = has_decision_court & has_court_decision

    if with_decision.any():
        court_decision_date = court_decision_series[with_decision].dt.date
        deadline = deadline_dates[with_decision]

        # Решение вынесено в срок
        timely_mask = with_decision & (court_decision_date <= deadline)
        # Решение вынесено с просрочкой
        overdue_mask = with_decision & (court_decision_date > deadline)

        monitoring_status.loc[timely_mask] = "timely"
        monitoring_status.loc[overdue_mask] = "overdue"
        completion_status.loc[with_decision] = True

    # ===== СЛУЧАЙ 2: Нет даты вынесения решения =====
    without_decision = has_decision_court & ~has_court_decision

    if without_decision.any():
        deadline = deadline_dates[without_decision]

        # Дедлайн истек
        overdue_mask = without_decision & (today_date > deadline)
        # Дедлайн еще не наступил
        timely_mask = without_decision & (today_date <= deadline)

        monitoring_status.loc[overdue_mask] = "overdue"
        monitoring_status.loc[timely_mask] = "timely"
        # completion_status остается False

    return monitoring_status, completion_status, execution_date_plan


def evaluate_decision_receipt_dataframe(df: pd.DataFrame, today: date) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Выполняет пакетную оценку своевременности получения решения суда.

    Сравнивает дату получения решения с дедлайном в 3 календарных дня
    от даты вынесения решения. Если дата получения отсутствует,
    проверяет не истек ли дедлайн на текущую дату.

    Args:
        df (pd.DataFrame): DataFrame с данными дел.
            Ожидаемые колонки:
            - COLUMNS["COURT_DECISION_DATE"]: дата вынесения решения
            - COLUMNS["DECISION_RECEIPT_DATE"]: дата получения решения
        today (date): Текущая дата для сравнения с дедлайном

    Returns:
        Tuple[pd.Series, pd.Series]:
            - monitoringStatus: Series со значениями 'timely', 'overdue' или 'no_data'
            - completionStatus: Series с булевыми значениями (True если решение получено)
    """
    # Инициализация результатов значениями по умолчанию
    monitoring_status = pd.Series("no_data", index=df.index, dtype=str)
    completion_status = pd.Series(False, index=df.index, dtype=bool)
    execution_date_plan = pd.Series(pd.NaT, index=df.index)

    # Получение даты вынесения решения
    court_decision_series = pd.to_datetime(
        safe_get_column_series(df, COLUMNS["COURT_DECISION_DATE"]),
        errors='coerce'
    )
    has_court_decision = court_decision_series.notna()

    if not has_court_decision.any():
        return monitoring_status, completion_status, execution_date_plan

    # Расчет дедлайна получения решения (3 календарных дня)
    deadline_dates = court_decision_series.dt.date + timedelta(days=3)
    execution_date_plan = deadline_dates
    today_date = pd.Timestamp(today).date()

    # Получение даты получения решения
    decision_receipt_series = pd.to_datetime(
        safe_get_column_series(df, COLUMNS["DECISION_RECEIPT_DATE"]),
        errors='coerce'
    )
    has_decision_receipt = decision_receipt_series.notna()

    # ===== СЛУЧАЙ 1: Есть дата получения решения =====
    with_receipt = has_court_decision & has_decision_receipt

    if with_receipt.any():
        receipt_date = decision_receipt_series[with_receipt].dt.date
        deadline = deadline_dates[with_receipt]

        # Решение получено в срок
        timely_mask = with_receipt & (receipt_date <= deadline)
        # Решение получено с просрочкой
        overdue_mask = with_receipt & (receipt_date > deadline)

        monitoring_status.loc[timely_mask] = "timely"
        monitoring_status.loc[overdue_mask] = "overdue"
        completion_status.loc[with_receipt] = True

    # ===== СЛУЧАЙ 2: Нет даты получения решения =====
    without_receipt = has_court_decision & ~has_decision_receipt

    if without_receipt.any():
        deadline = deadline_dates[without_receipt]

        # Дедлайн истек
        overdue_mask = without_receipt & (today_date > deadline)
        # Дедлайн еще не наступил
        timely_mask = without_receipt & (today_date <= deadline)

        monitoring_status.loc[overdue_mask] = "overdue"
        monitoring_status.loc[timely_mask] = "timely"
        # completion_status остается False

    return monitoring_status, completion_status, execution_date_plan


def evaluate_decision_transfer_dataframe(df: pd.DataFrame, today: date) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Выполняет пакетную оценку своевременности передачи решения суда.

    Сравнивает дату передачи решения с дедлайном в 1 календарный день
    от даты вынесения решения. Если дата передачи отсутствует,
    проверяет не истек ли дедлайн на текущую дату.

    Args:
        df (pd.DataFrame): DataFrame с данными дел.
            Ожидаемые колонки:
            - COLUMNS["COURT_DECISION_DATE"]: дата вынесения решения
            - COLUMNS["ACTUAL_TRANSFER_DATE"]: дата передачи решения
        today (date): Текущая дата для сравнения с дедлайном

    Returns:
        Tuple[pd.Series, pd.Series]:
            - monitoringStatus: Series со значениями 'timely', 'overdue' или 'no_data'
            - completionStatus: Series с булевыми значениями (True если решение передано)
    """
    # Инициализация результатов значениями по умолчанию
    monitoring_status = pd.Series("no_data", index=df.index, dtype=str)
    completion_status = pd.Series(False, index=df.index, dtype=bool)
    execution_date_plan = pd.Series(pd.NaT, index=df.index)

    # Получение даты вынесения решения
    court_decision_series = pd.to_datetime(
        safe_get_column_series(df, COLUMNS["COURT_DECISION_DATE"]),
        errors='coerce'
    )
    has_court_decision = court_decision_series.notna()

    if not has_court_decision.any():
        return monitoring_status, completion_status, execution_date_plan

    # Расчет дедлайна передачи решения (1 календарный день)
    deadline_dates = court_decision_series.dt.date + timedelta(days=1)
    execution_date_plan = deadline_dates
    today_date = pd.Timestamp(today).date()

    # Получение даты передачи решения
    actual_transfer_series = pd.to_datetime(
        safe_get_column_series(df, COLUMNS["ACTUAL_TRANSFER_DATE"]),
        errors='coerce'
    )
    has_actual_transfer = actual_transfer_series.notna()

    # ===== СЛУЧАЙ 1: Есть дата передачи решения =====
    with_transfer = has_court_decision & has_actual_transfer

    if with_transfer.any():
        transfer_date = actual_transfer_series[with_transfer].dt.date
        deadline = deadline_dates[with_transfer]

        # Решение передано в срок
        timely_mask = with_transfer & (transfer_date <= deadline)
        # Решение передано с просрочкой
        overdue_mask = with_transfer & (transfer_date > deadline)

        monitoring_status.loc[timely_mask] = "timely"
        monitoring_status.loc[overdue_mask] = "overdue"
        completion_status.loc[with_transfer] = True

    # ===== СЛУЧАЙ 2: Нет даты передачи решения =====
    without_transfer = has_court_decision & ~has_actual_transfer

    if without_transfer.any():
        deadline = deadline_dates[without_transfer]

        # Дедлайн истек
        overdue_mask = without_transfer & (today_date > deadline)
        # Дедлайн еще не наступил
        timely_mask = without_transfer & (today_date <= deadline)

        monitoring_status.loc[overdue_mask] = "overdue"
        monitoring_status.loc[timely_mask] = "timely"
        # completion_status остается False

    return monitoring_status, completion_status, execution_date_plan


def evaluate_next_hearing_present_dataframe(df: pd.DataFrame, today: date) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Выполняет пакетную оценку своевременности назначения следующего заседания.

    Сравнивает дату следующего заседания с дедлайном в 3 рабочих дня
    от даты определения суда. Если дата заседания отсутствует,
    проверяет не истек ли дедлайн на текущую дату.

    Args:
        df (pd.DataFrame): DataFrame с данными дел.
            Ожидаемые колонки:
            - COLUMNS["DETERMINATION_DATE"]: дата определения суда
            - COLUMNS["NEXT_HEARING_DATE"]: дата следующего заседания
        today (date): Текущая дата для сравнения с дедлайном

    Returns:
        Tuple[pd.Series, pd.Series]:
            - monitoringStatus: Series со значениями 'timely', 'overdue' или 'no_data'
            - completionStatus: Series с булевыми значениями (True если заседание назначено)
    """
    # Инициализация результатов значениями по умолчанию
    monitoring_status = pd.Series("no_data", index=df.index, dtype=str)
    completion_status = pd.Series(False, index=df.index, dtype=bool)
    execution_date_plan = pd.Series(pd.NaT, index=df.index)

    # Получение даты определения суда
    determination_series = pd.to_datetime(
        safe_get_column_series(df, COLUMNS["DETERMINATION_DATE"]),
        errors='coerce'
    )
    has_determination = determination_series.notna()

    if not has_determination.any():
        return monitoring_status, completion_status, execution_date_plan

    # Расчет дедлайна назначения заседания (3 рабочих дня)
    deadline_dates = determination_series.apply(
        lambda d: russian_calendar.add_working_days(d.date(), 3) if pd.notna(d) else pd.NaT
    )
    execution_date_plan = deadline_dates
    today_date = pd.Timestamp(today).date()

    # Получение даты следующего заседания
    next_hearing_series = pd.to_datetime(
        safe_get_column_series(df, COLUMNS["NEXT_HEARING_DATE"]),
        errors='coerce'
    )
    has_next_hearing = next_hearing_series.notna()

    # ===== СЛУЧАЙ 1: Есть дата следующего заседания =====
    with_hearing = has_determination & has_next_hearing

    if with_hearing.any():
        hearing_date = next_hearing_series[with_hearing].dt.date
        deadline = deadline_dates[with_hearing]

        # Заседание назначено в срок
        timely_mask = with_hearing & (hearing_date <= deadline)
        # Заседание назначено с просрочкой
        overdue_mask = with_hearing & (hearing_date > deadline)

        monitoring_status.loc[timely_mask] = "timely"
        monitoring_status.loc[overdue_mask] = "overdue"
        completion_status.loc[with_hearing] = True

    # ===== СЛУЧАЙ 2: Нет даты следующего заседания =====
    without_hearing = has_determination & ~has_next_hearing

    if without_hearing.any():
        deadline = deadline_dates[without_hearing]

        # Дедлайн истек
        overdue_mask = without_hearing & (today_date > deadline)
        # Дедлайн еще не наступил
        timely_mask = without_hearing & (today_date <= deadline)

        monitoring_status.loc[overdue_mask] = "overdue"
        monitoring_status.loc[timely_mask] = "timely"
        # completion_status остается False

    return monitoring_status, completion_status, execution_date_plan

def evaluate_prev_to_next_hearing_dataframe(df: pd.DataFrame, today: date) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Выполняет пакетную оценку соблюдения интервала между заседаниями.

    Проверяет что интервал между предыдущим и следующим заседанием
    не превышает 2 рабочих дня.

    Args:
        df (pd.DataFrame): DataFrame с данными дел.
            Ожидаемые колонки:
            - COLUMNS["PREVIOUS_HEARING_DATE"]: дата предыдущего заседания
            - COLUMNS["NEXT_HEARING_DATE"]: дата следующего заседания
        today (date): Текущая дата для сравнения (используется в случае отсутствия дат)

    Returns:
        Tuple[pd.Series, pd.Series]:
            - monitoringStatus: Series со значениями 'timely', 'overdue' или 'no_data'
            - completionStatus: Series с булевыми значениями (True если обе даты заполнены и корректны)
    """
    # Инициализация результатов значениями по умолчанию
    monitoring_status = pd.Series("no_data", index=df.index, dtype=str)
    completion_status = pd.Series(False, index=df.index, dtype=bool)
    execution_date_plan = pd.Series(pd.NaT, index=df.index)

    # Получение дат заседаний
    prev_hearing_series = pd.to_datetime(
        safe_get_column_series(df, COLUMNS["PREVIOUS_HEARING_DATE"]),
        errors='coerce'
    )
    next_hearing_series = pd.to_datetime(
        safe_get_column_series(df, COLUMNS["NEXT_HEARING_DATE"]),
        errors='coerce'
    )

    has_prev = prev_hearing_series.notna()
    has_next = next_hearing_series.notna()
    # Плановая дата следующего заседания = предыдущее + 2 рабочих дня
    if has_prev.any():
        execution_date_plan.loc[has_prev] = prev_hearing_series[has_prev].apply(
            lambda d: russian_calendar.add_working_days(d.date(), 2) if pd.notna(d) else pd.NaT
        )
    today_date = pd.Timestamp(today).date()

    # Определение завершенности условия (обе даты заполнены)
    completion_status = has_prev & has_next

    # ===== СЛУЧАЙ 1: Отсутствие данных о заседаниях =====
    no_data_mask = ~has_prev & ~has_next
    monitoring_status.loc[no_data_mask] = "overdue"

    # ===== СЛУЧАЙ 2: Отсутствие даты предыдущего заседания, но есть следующее =====
    only_next_mask = ~has_prev & has_next

    if only_next_mask.any():
        next_date = next_hearing_series[only_next_mask].dt.date
        # Следующее заседание уже прошло или сегодня
        timely_mask = only_next_mask & (next_date <= today_date)
        # Следующее заседание в будущем
        overdue_mask = only_next_mask & (next_date > today_date)

        monitoring_status.loc[timely_mask] = "timely"
        monitoring_status.loc[overdue_mask] = "overdue"

    # ===== СЛУЧАЙ 3 и 4: Наличие даты предыдущего заседания =====
    has_prev_mask = has_prev

    if has_prev_mask.any():
        # СЛУЧАЙ 3: Отсутствие даты следующего заседания
        prev_only_mask = has_prev & ~has_next
        monitoring_status.loc[prev_only_mask] = "overdue"

        # СЛУЧАЙ 4: Обе даты присутствуют
        both_mask = has_prev & has_next

        if both_mask.any():
            prev_date = prev_hearing_series[both_mask].dt.date
            next_date = next_hearing_series[both_mask].dt.date

            # Проверка корректности дат (следующее не раньше предыдущего)
            invalid_mask = both_mask & (next_date < prev_date)
            monitoring_status.loc[invalid_mask] = "overdue"
            completion_status.loc[invalid_mask] = False

            # Для корректных дат расчет рабочих дней
            valid_mask = both_mask & (next_date >= prev_date)

            if valid_mask.any():
                # Расчет рабочих дней между заседаниями
                working_days = df.loc[valid_mask].apply(
                    lambda row: russian_calendar.get_working_days_between(
                        pd.to_datetime(row[COLUMNS["PREVIOUS_HEARING_DATE"]]).date(),
                        pd.to_datetime(row[COLUMNS["NEXT_HEARING_DATE"]]).date()
                    ),
                    axis=1
                )

                timely = working_days <= 2
                overdue = working_days > 2

                valid_indices = valid_mask[valid_mask].index
                monitoring_status.loc[valid_indices[timely.values]] = "timely"
                monitoring_status.loc[valid_indices[overdue.values]] = "overdue"

    return monitoring_status, completion_status, execution_date_plan


def evaluate_under_consideration_60days_dataframe(df: pd.DataFrame, today: date) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Выполняет пакетную оценку продолжительности нахождения дела в рассмотрении.

    Проверяет что дело не находится в статусе 'UNDER_CONSIDERATION'
    дольше 60 календарных дней от даты подачи иска.

    Args:
        df (pd.DataFrame): DataFrame с данными дел.
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

    # Получение даты подачи иска для каждой строки
    filing_dates = df.apply(get_filing_date, axis=1)
    has_filing_date = filing_dates.notna()

    if not has_filing_date.any():
        return monitoring_status, completion_status, execution_date_plan

    # Расчет максимального срока рассмотрения (60 календарных дней)
    deadline_dates = filing_dates.apply(lambda d: d.date() + timedelta(days=60) if pd.notna(d) else pd.NaT)
    execution_date_plan = deadline_dates
    today_date = pd.Timestamp(today).date()

    # Превышен максимальный срок рассмотрения
    overdue_mask = has_filing_date & (today_date > deadline_dates)
    # Срок рассмотрения в пределах нормы
    timely_mask = has_filing_date & (today_date <= deadline_dates)

    monitoring_status.loc[overdue_mask] = "overdue"
    monitoring_status.loc[timely_mask] = "timely"

    return monitoring_status, completion_status, execution_date_plan


def evaluate_court_reaction_dataframe(df: pd.DataFrame, today: date) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Выполняет пакетную оценку своевременности получения реакции суда.

    Проверяет получение определения суда в течение 7 рабочих дней
    от даты подачи иска.

    Args:
        df (pd.DataFrame): DataFrame с данными дел.
            Ожидаемые колонки:
            - COLUMNS["DETERMINATION_DATE"]: дата определения суда
        today (date): Текущая дата для сравнения с дедлайном

    Returns:
        Tuple[pd.Series, pd.Series]:
            - monitoringStatus: Series со значениями 'timely', 'overdue' или 'no_data'
            - completionStatus: Series с булевыми значениями (True если определение получено)
    """
    # Инициализация результатов значениями по умолчанию
    monitoring_status = pd.Series("no_data", index=df.index, dtype=str)
    completion_status = pd.Series(False, index=df.index, dtype=bool)
    execution_date_plan = pd.Series(pd.NaT, index=df.index)

    # Проверка наличия даты определения суда
    determination_series = pd.to_datetime(
        safe_get_column_series(df, COLUMNS["DETERMINATION_DATE"]),
        errors='coerce'
    )
    has_determination = determination_series.notna()

    # Реакция суда уже получена
    monitoring_status.loc[has_determination] = "timely"
    completion_status.loc[has_determination] = True

    # Для строк без определения суда — проверка дедлайна
    without_determination = ~has_determination

    if without_determination.any():
        # Получение даты подачи иска
        filing_dates = df.loc[without_determination].apply(get_filing_date, axis=1)
        has_filing = filing_dates.notna()

        if has_filing.any():
            # Расчет дедлайна получения реакции суда (7 рабочих дней)
            deadline_dates = filing_dates.apply(
                lambda d: russian_calendar.add_working_days(d.date(), 7) if pd.notna(d) else pd.NaT
            )
            # Присваиваем только тем строкам, для которых вычисляли
            execution_date_plan.loc[filing_dates.index] = deadline_dates

            deadline_series = deadline_dates.reindex(df.index)
            today_date = pd.Timestamp(today).date()

            # Маски для строк без определения, но с датой подачи
            valid_mask = without_determination & has_filing

            # Дедлайн истек
            overdue_mask = valid_mask & (today_date > deadline_series)
            # Дедлайн еще не наступил
            timely_mask = valid_mask & (today_date <= deadline_series)

            monitoring_status.loc[overdue_mask] = "overdue"
            monitoring_status.loc[timely_mask] = "timely"
            # completion_status для этих строк остается False

    return monitoring_status, completion_status, execution_date_plan

def evaluate_first_status_changed_dataframe(df: pd.DataFrame, today: date) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Выполняет пакетную оценку своевременности смены первоначального статуса дела.

    Проверяет смену статуса с 'PREPARING_DOCUMENTS' в течение
    14 календарных дней от даты подачи иска.

    Args:
        df (pd.DataFrame): DataFrame с данными дел.
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

    # Получение даты подачи иска для каждой строки
    filing_dates = df.apply(get_filing_date, axis=1)
    has_filing_date = filing_dates.notna()

    if not has_filing_date.any():
        return monitoring_status, completion_status, execution_date_plan

    # Расчет дедлайна смены статуса (14 календарных дней)
    deadline_dates = filing_dates.apply(lambda d: d.date() + timedelta(days=14) if pd.notna(d) else pd.NaT)
    execution_date_plan = deadline_dates
    today_date = pd.Timestamp(today).date()

    # Просрочена смена статуса
    overdue_mask = has_filing_date & (today_date > deadline_dates)
    # Время на смену статуса еще есть
    timely_mask = has_filing_date & (today_date <= deadline_dates)

    monitoring_status.loc[overdue_mask] = "overdue"
    monitoring_status.loc[timely_mask] = "timely"

    return monitoring_status, completion_status, execution_date_plan





