# backend/app/terms_of_support_v3/modules/lawsuit_stage_checks_v3.py
"""
Модуль проверки этапов для искового производства (v3)

Предоставляет функции для анализа дел искового производства и формирования
результатов проверок в формате CheckResult.

Основные функции:
- analyze_lawsuit: Анализ дел, установка stageCode, выполнение проверок
"""

import pandas as pd
from datetime import datetime

from backend.app.common.config.column_names import COLUMNS, VALUES
from backend.app.data_management.config.stages_config import get_stage_codes_by_file_type
from backend.app.data_management.config.checks_config import CHECK_FUNCTION_REGISTRY
from backend.app.common.modules.apply_checks_by_stage import apply_checks_by_stage
from backend.app.data_management.modules.normalized_data_manager import normalized_manager


def analyze_lawsuit(df: pd.DataFrame) -> pd.DataFrame:
    """
    Выполняет анализ дел искового производства и формирует результаты проверок.

    Процесс анализа включает:
    1. Присвоение stageCode для каждого дела через _assign_lawsuit_stages
    2. Проверку допустимости присвоенных этапов для типа файла detailed_report
    3. Добавление колонки targetId для совместимости с apply_checks_by_stage
    4. Выполнение проверок через универсальный исполнитель
    5. Возврат результатов в формате CheckResult

    Args:
        df (pd.DataFrame): DataFrame с данными дел искового производства.
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


def _assign_lawsuit_stages(df: pd.DataFrame) -> pd.Series:
    """
    Определяет этапы сопровождения для дел искового производства.

    Использует маски Pandas для быстрого определения этапа каждого дела на основе
    статуса дела и наличия ключевых дат. Этапы определяются в строгом порядке приоритета
    от исключительных статусов к стандартным этапам сопровождения.

    Args:
        df (pd.DataFrame): Исходный DataFrame с данными дел искового производства

    Returns:
        pd.Series: Series с определенными этапами для каждого дела (с суффиксом L).
                   Возможные значения:
                   - exceptionsL: Исключительные статусы
                   - closedL: Закрытые дела
                   - executionDocumentReceivedL: Получен исполнительный документ
                   - decisionMadeL: Вынесено решение суда
                   - underConsiderationL: Дело находится в стадии рассмотрения
                   - courtReactionL: Ожидается реакция суда
                   - firstStatusChangedL: Стадия подготовки документов
                   - outside_stage_filters: Дела вне фильтров этапов
    """
    # Инициализация значением по умолчанию
    stage_series = pd.Series("outside_stage_filters", index=df.index, dtype=str)

    case_status_col = COLUMNS["CASE_STATUS"]
    has_case_status = case_status_col in df.columns

    if not has_case_status:
        return stage_series

    # ===== 1. Исключения =====
    exception_values = [
        VALUES["REOPENED"],
        VALUES["COMPLAINT_FILED"],
        VALUES["ERROR_DUBLICATE"],
        VALUES["WITHDRAWN_BY_THE_INITIATOR"],
    ]
    exception_mask = df[case_status_col].isin(exception_values)
    stage_series[exception_mask] = "exceptionsL"

    # ===== 2. Закрытые дела =====
    closed_values = [VALUES["CONDITIONALLY_CLOSED"], VALUES["CLOSED"]]
    closed_mask = ~exception_mask & df[case_status_col].isin(closed_values)
    stage_series[closed_mask] = "closedL"

    # ===== 3. Получение исполнительного документа =====
    execution_mask = ~exception_mask & ~closed_mask & (df[case_status_col] == VALUES["COURT_ACT_IN_FORCE"])
    stage_series[execution_mask] = "executionDocumentReceivedL"

    # ===== 4. Вынесение решения =====
    decision_mask = pd.Series(False, index=df.index)
    decision_mask |= (df[case_status_col] == VALUES["DECISION_MADE"])

    characteristics_col = COLUMNS["CHARACTERISTICS_FINAL_COURT_ACT"]
    if characteristics_col in df.columns:
        decision_mask |= df[characteristics_col].notna()

    decision_mask &= ~exception_mask & ~closed_mask & ~execution_mask
    stage_series[decision_mask] = "decisionMadeL"

    # ===== 5. Рассмотрение дела =====
    under_consideration_mask = (
        ~exception_mask & ~closed_mask & ~execution_mask & ~decision_mask &
        (df[case_status_col] == VALUES["UNDER_CONSIDERATION"])
    )
    stage_series[under_consideration_mask] = "underConsiderationL"

    # ===== 6. Ожидание реакции суда =====
    court_reaction_mask = (
        ~exception_mask & ~closed_mask & ~execution_mask & ~decision_mask & ~under_consideration_mask &
        (df[case_status_col] == VALUES["AWAITING_COURT_RESPONSE"])
    )
    stage_series[court_reaction_mask] = "courtReactionL"

    # ===== 7. Подготовка документов =====
    first_status_mask = (
        ~exception_mask & ~closed_mask & ~execution_mask & ~decision_mask & ~under_consideration_mask & ~court_reaction_mask &
        (df[case_status_col] == VALUES["PREPARATION_OF_DOCUMENTS"])
    )
    stage_series[first_status_mask] = "firstStatusChangedL"

    return stage_series


