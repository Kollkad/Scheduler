# backend/app/common/modules/apply_checks_by_stage.py
"""
Модуль выполнения проверок по этапам

Предоставляет универсальную функцию для применения активных проверок
к подготовленному DataFrame, содержащему колонку stageCode.

Основная функция:
- apply_checks_by_stage: Применяет проверки согласно конфигурации и возвращает результаты
"""

import pandas as pd
from datetime import date, datetime
from typing import Dict, Callable, Optional


def apply_checks_by_stage(
    df: pd.DataFrame,
    checks_df: pd.DataFrame,
    function_registry: Dict[str, Callable],
    today: Optional[date] = None
) -> pd.DataFrame:
    """
    Применяет активные проверки к строкам DataFrame в соответствии с их stageCode.

    Функция выполняет соединение данных с конфигурацией проверок по этапу,
    затем для каждой уникальной функции проверки вызывает её один раз
    для всего подмножества строк, к которым она применяется.

    Args:
        df (pd.DataFrame): Подготовленный DataFrame с сущностями для проверки.
            Обязательные колонки:
            - stageCode: код этапа
            - targetId: идентификатор сущности (transferCode или caseCode)
            - все поля, необходимые функциям проверок
        checks_df (pd.DataFrame): Конфигурация проверок.
            Ожидаемые колонки: checkCode, stageCode, functionName, isActive
        function_registry (Dict[str, Callable]): Словарь, сопоставляющий
            имя функции с реальной функцией Python
        today (Optional[date]): Текущая дата для расчётов.
            Если None, используется datetime.now().date()

    Returns:
        pd.DataFrame: Результаты проверок в формате CheckResult.
            Колонки: checkResultCode, checkCode, targetId, monitoringStatus,
            completionStatus, checkedAt, executionDatePlan
    """
    if df.empty or checks_df.empty:
        return pd.DataFrame(columns=[
            "checkResultCode", "checkCode", "targetId",
            "monitoringStatus", "completionStatus", "checkedAt", "executionDatePlan"
        ])

    if today is None:
        today = datetime.now().date()

    checked_at = datetime.now()

    active_checks = checks_df[checks_df["isActive"] == True].copy()
    if active_checks.empty:
        return pd.DataFrame(columns=[
            "checkResultCode", "checkCode", "targetId",
            "monitoringStatus", "completionStatus", "checkedAt", "executionDatePlan"
        ])

    merged = df.merge(
        active_checks[["checkCode", "stageCode", "functionName"]],
        on="stageCode",
        how="inner"
    )

    if merged.empty:
        return pd.DataFrame(columns=[
            "checkResultCode", "checkCode", "targetId",
            "monitoringStatus", "completionStatus", "checkedAt", "executionDatePlan"
        ])

    processed_parts = []
    unique_functions = merged["functionName"].unique()

    for func_name in unique_functions:
        func = function_registry.get(func_name)
        if func is None:
            print(f"⚠️ Функция '{func_name}' не найдена в реестре, проверка пропущена")
            continue

        mask = merged["functionName"] == func_name
        subset = merged[mask].copy()

        # Вызов функции проверки (теперь возвращает три значения)
        result = func(subset, today)
        if len(result) == 3:
            monitoring, completion, planned = result
            subset["executionDatePlan"] = planned.values
        else:
            monitoring, completion = result
            subset["executionDatePlan"] = pd.NaT

        subset["monitoringStatus"] = monitoring.values
        subset["completionStatus"] = completion.values

        processed_parts.append(subset)

    if not processed_parts:
        return pd.DataFrame(columns=[
            "checkResultCode", "checkCode", "targetId",
            "monitoringStatus", "completionStatus", "checkedAt", "executionDatePlan"
        ])

    result_df = pd.concat(processed_parts, ignore_index=True)
    result_df["checkedAt"] = checked_at

    # Генерация уникальных кодов результатов проверок
    result_df["checkResultCode"] = (
        "RC-" +
        result_df["stageCode"].str.upper() + "-" +
        (result_df.groupby("stageCode").cumcount() + 1).astype(str).str.zfill(7)
    )

    output_columns = [
        "checkResultCode", "checkCode", "targetId",
        "monitoringStatus", "completionStatus", "checkedAt", "executionDatePlan"
    ]

    return result_df[output_columns]


