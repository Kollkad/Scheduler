# backend/app/terms_of_support_v3/modules/order_stage_checks_v3.py
"""
Модуль проверки этапов для приказного производства (v3)

Предоставляет функции для анализа дел приказного производства и формирования
результатов проверок в формате CheckResult.

Основные функции:
- analyze_order: Анализ дел, установка stageCode, выполнение проверок
"""

import pandas as pd
from datetime import datetime

from backend.app.common.config.column_names import COLUMNS, VALUES
from backend.app.data_management.config.stages_config import get_stage_codes_by_file_type
from backend.app.data_management.config.checks_config import CHECK_FUNCTION_REGISTRY
from backend.app.common.modules.apply_checks_by_stage import apply_checks_by_stage
from backend.app.data_management.modules.normalized_data_manager import normalized_manager


def _assign_order_stages(df: pd.DataFrame) -> pd.Series:
    """
    Определяет этапы сопровождения для дел приказного производства.

    Использует маски Pandas для определения этапа каждого дела на основе
    статуса и наличия ключевых дат. Этапы определяются в строгом порядке приоритета
    от исключительных статусов к стандартным этапам сопровождения.

    Args:
        df (pd.DataFrame): Исходный DataFrame с данными дел приказного производства

    Returns:
        pd.Series: Series с определенными этапами для каждого дела (с суффиксом O).
                   Возможные значения:
                   - exceptionsO: Исключительные статусы
                   - closedO: Закрытые дела
                   - executionDocumentReceivedO: Получен исполнительный документ
                   - courtReactionO: Ожидается реакция суда
                   - firstStatusChangedO: Стадия подготовки документов
                   - outside_stage_filters: Дела вне фильтров этапов
    """
    stage_series = pd.Series("outside_stage_filters", index=df.index, dtype=str)

    case_status_col = COLUMNS["CASE_STATUS"]
    if case_status_col not in df.columns:
        return stage_series

    # ===== 1. Исключения =====
    exception_values = [
        VALUES["REOPENED"],
        VALUES["COMPLAINT_FILED"],
        VALUES["ERROR_DUBLICATE"],
        VALUES["WITHDRAWN_BY_THE_INITIATOR"],
    ]
    exception_mask = df[case_status_col].isin(exception_values)
    stage_series[exception_mask] = "exceptionsO"

    # ===== 2. Закрытые дела =====
    closed_mask = (df[case_status_col] == VALUES["CLOSED"])

    if COLUMNS["CASE_CLOSING_DATE"] in df.columns:
        closed_mask |= df[COLUMNS["CASE_CLOSING_DATE"]].notna()

    closed_mask &= ~exception_mask
    stage_series[closed_mask] = "closedO"

    # ===== 3. Получение исполнительного документа =====
    execution_mask = (df[case_status_col] == VALUES["CONDITIONALLY_CLOSED"])

    if COLUMNS["ACTUAL_RECEIPT_DATE"] in df.columns:
        execution_mask |= df[COLUMNS["ACTUAL_RECEIPT_DATE"]].notna()

    if COLUMNS["ACTUAL_TRANSFER_DATE"] in df.columns:
        execution_mask |= df[COLUMNS["ACTUAL_TRANSFER_DATE"]].notna()

    execution_mask &= ~exception_mask & ~closed_mask
    stage_series[execution_mask] = "executionDocumentReceivedO"

    # ===== 4. Ожидание реакции суда =====
    court_reaction_mask = (df[case_status_col] == VALUES["AWAITING_COURT_RESPONSE"])
    court_reaction_mask &= ~exception_mask & ~closed_mask & ~execution_mask
    stage_series[court_reaction_mask] = "courtReactionO"

    # ===== 5. Подготовка документов =====
    first_status_mask = (df[case_status_col] == VALUES["PREPARATION_OF_DOCUMENTS"])
    first_status_mask &= ~exception_mask & ~closed_mask & ~execution_mask & ~court_reaction_mask
    stage_series[first_status_mask] = "firstStatusChangedO"

    return stage_series


def analyze_order(df: pd.DataFrame) -> pd.DataFrame:
    """
    Выполняет анализ дел приказного производства и формирует результаты проверок.

    Процесс анализа включает:
    1. Присвоение stageCode для каждого дела через _assign_order_stages
    2. Проверку допустимости присвоенных этапов для типа файла detailed_report
    3. Добавление колонки targetId для совместимости с apply_checks_by_stage
    4. Выполнение проверок через универсальный исполнитель
    5. Возврат результатов в формате CheckResult

    Args:
        df (pd.DataFrame): DataFrame с данными дел приказного производства.
            Модифицируется в процессе: добавляется колонка stageCode.

    Returns:
        pd.DataFrame: DataFrame с результатами проверок в формате CheckResult:
            - checkResultCode: уникальный код результата проверки
            - checkCode: код проверки из конфигурации
            - targetId: caseCode дела
            - monitoringStatus: статус мониторинга (timely/overdue/no_data/исключения)
            - completionStatus: статус завершенности
            - checkedAt: дата и время выполнения проверки
            - executionDatePlan: плановая дата (зарезервировано)
    """
    today = datetime.now().date()

    # Проверка допустимости этапов для типа файла detailed_report
    allowed_stages = get_stage_codes_by_file_type("detailed_report")
    if not allowed_stages:
        raise ValueError("Не найдено ни одного этапа для типа файла 'detailed_report'")

    # ===== 2. Проверка допустимости присвоенных этапов =====
    assigned_stages = df["stageCode"].unique()
    outside_filter_value = "outside_stage_filters"

    for stage in assigned_stages:
        if stage != outside_filter_value and stage not in allowed_stages:
            raise ValueError(f"Этап '{stage}' не зарегистрирован для типа файла 'detailed_report'")

    # ===== 3. Фильтрация дел, оставшихся вне этапов =====
    df_filtered = df[df["stageCode"] != outside_filter_value].copy()

    if df_filtered.empty:
        return pd.DataFrame(columns=[
            "checkResultCode", "checkCode", "targetId",
            "monitoringStatus", "completionStatus", "checkedAt", "executionDatePlan"
        ])

    # ===== 4. Добавление targetId =====
    df_filtered["targetId"] = df_filtered[COLUMNS["CASE_CODE"]].astype(str)

    # ===== 5. Выполнение проверок через универсальный исполнитель =====
    checks_df = normalized_manager.get_checks_data()

    check_results_df = apply_checks_by_stage(
        df=df_filtered,
        checks_df=checks_df,
        function_registry=CHECK_FUNCTION_REGISTRY,
        today=today
    )

    return check_results_df






