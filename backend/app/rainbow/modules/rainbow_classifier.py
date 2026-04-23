# backend/app/rainbow/modules/rainbow_classifier.py
"""
Модуль классификатора для цветовой категоризации дел (радуга).

Содержит функции для добавления цветовой колонки в DataFrame дел
на основе иерархических правил классификации.
"""

import pandas as pd
from datetime import datetime, timedelta

from backend.app.common.config.column_names import COLUMNS, VALUES
from backend.app.common.modules.utils import safe_get_column_series


def add_rainbow_color_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Добавляет колонку с цветовой категорией в DataFrame дел.

    Применяет иерархические правила для определения цвета каждого дела.
    Порядок правил важен: если дело подходит под несколько правил,
    применяется первое подходящее.

    Правила (в порядке приоритета):
    1. ИК — запрос содержит "залог"
    2. Серый — статус "Переоткрыто"
    3. Зеленый — судебный акт в силе с датой передачи
    4. Желтый — условно закрыто с датой передачи
    5. Оранжевый — судебный акт в силе без даты передачи
    6. Синий — приказное производство старше 90 дней
    7. Красный — дата последнего запроса до 2025 года
    8. Лиловый — исковое производство старше 120 дней
    9. Белый — все остальные дела

    Args:
        df (pd.DataFrame): DataFrame с данными дел (detailed_report).

    Returns:
        pd.DataFrame: Копия DataFrame с добавленной колонкой COLUMNS["CURRENT_PERIOD_COLOR"].
    """
    result_df = df.copy()
    today = datetime.now().date()
    today_timestamp = pd.Timestamp(today)

    # Инициализация колонки значением "Белый" по умолчанию
    color_series = pd.Series("Белый", index=df.index, dtype=str)

    # Получение необходимых колонок
    request_type = safe_get_column_series(df, COLUMNS["REQUEST_TYPE"])
    case_status = safe_get_column_series(df, COLUMNS["CASE_STATUS"])
    method_of_protection = safe_get_column_series(df, COLUMNS["METHOD_OF_PROTECTION"])
    last_request_date = pd.to_datetime(
        safe_get_column_series(df, COLUMNS["LAST_REQUEST_DATE"]),
        errors='coerce'
    )
    actual_transfer_date = pd.to_datetime(
        safe_get_column_series(df, COLUMNS["ACTUAL_TRANSFER_DATE"]),
        errors='coerce'
    )
    next_hearing_date = pd.to_datetime(
        safe_get_column_series(df, COLUMNS["NEXT_HEARING_DATE"]),
        errors='coerce'
    )

    # Маска для уже классифицированных дел (чтобы соблюдать иерархию)
    unclassified = pd.Series(True, index=df.index)

    # ===== Правило 1: ИК (Ипотечные кредиты) =====
    ik_mask = unclassified & request_type.astype(str).str.lower().str.contains("залог", na=False)
    color_series[ik_mask] = "ИК"
    unclassified[ik_mask] = False

    # ===== Правило 2: Серый (Переоткрыто) =====
    gray_mask = unclassified & (case_status == VALUES["REOPENED"])
    color_series[gray_mask] = "Серый"
    unclassified[gray_mask] = False

    # ===== Правило 3: Зеленый (Судебный акт в силе с передачей) =====
    has_transfer = actual_transfer_date.notna()
    court_act_mask = unclassified & (case_status == VALUES["COURT_ACT_IN_FORCE"]) & has_transfer

    if court_act_mask.any():
        # Случай с датой заседания: дата передачи > даты заседания
        has_hearing = next_hearing_date.notna()
        with_hearing = court_act_mask & has_hearing
        if with_hearing.any():
            transfer_after_hearing = actual_transfer_date > next_hearing_date
            green_mask = with_hearing & transfer_after_hearing
            color_series[green_mask] = "Зеленый"
            unclassified[green_mask] = False

        # Случай без даты заседания: достаточно наличия даты передачи
        without_hearing = court_act_mask & ~has_hearing
        if without_hearing.any():
            color_series[without_hearing] = "Зеленый"
            unclassified[without_hearing] = False

    # ===== Правило 4: Желтый (Условно закрыто с передачей) =====
    yellow_mask = (
        unclassified &
        (case_status == VALUES["CONDITIONALLY_CLOSED"]) &
        has_transfer
    )
    color_series[yellow_mask] = "Желтый"
    unclassified[yellow_mask] = False

    # ===== Правило 5: Оранжевый (Судебный акт в силе без передачи) =====
    orange_mask = (
        unclassified &
        (case_status == VALUES["COURT_ACT_IN_FORCE"]) &
        ~has_transfer
    )
    color_series[orange_mask] = "Оранжевый"
    unclassified[orange_mask] = False

    # ===== Правило 6: Синий (Приказное производство > 90 дней) =====
    has_request_date = last_request_date.notna()
    order_mask = (
        unclassified &
        (method_of_protection == VALUES["ORDER_PRODUCTION"]) &
        has_request_date
    )
    if order_mask.any():
        days_since_request = (today_timestamp - last_request_date).dt.days
        blue_mask = order_mask & (days_since_request > 90)
        color_series[blue_mask] = "Синий"
        unclassified[blue_mask] = False

    # ===== Правило 7: Красный (Запрос до 2025 года) =====
    red_mask = unclassified & has_request_date & (last_request_date.dt.year < 2025)
    color_series[red_mask] = "Красный"
    unclassified[red_mask] = False

    # ===== Правило 8: Лиловый (Исковое производство > 120 дней) =====
    lawsuit_mask = (
        unclassified &
        (method_of_protection == VALUES["CLAIM_PROCEEDINGS"]) &
        has_request_date
    )
    if lawsuit_mask.any():
        days_since_request = (today_timestamp - last_request_date).dt.days
        purple_mask = lawsuit_mask & (days_since_request > 120)
        color_series[purple_mask] = "Лиловый"
        unclassified[purple_mask] = False

    # ===== Правило 9: Белый — все неклассифицированные (уже по умолчанию) =====

    result_df[COLUMNS["CURRENT_PERIOD_COLOR"]] = color_series
    return result_df


def get_rainbow_filtered_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Возвращает DataFrame, отфильтрованный по правилам радуги.

    Критерии фильтрации:
    - Категория = CLAIM_FROM_BANK
    - Статус дела НЕ входит в [CLOSED, ERROR_DUBLICATE, WITHDRAWN_BY_THE_INITIATOR]

    Args:
        df (pd.DataFrame): DataFrame с данными дел.

    Returns:
        pd.DataFrame: Отфильтрованный DataFrame.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    category_col = COLUMNS["CATEGORY"]
    status_col = COLUMNS["CASE_STATUS"]

    if category_col not in df.columns or status_col not in df.columns:
        return pd.DataFrame()

    excluded_statuses = [
        VALUES["CLOSED"],
        VALUES["ERROR_DUBLICATE"],
        VALUES["WITHDRAWN_BY_THE_INITIATOR"]
    ]

    mask = (
        (df[category_col] == VALUES["CLAIM_FROM_BANK"]) &
        (~df[status_col].isin(excluded_statuses))
    )

    return df[mask].copy()

