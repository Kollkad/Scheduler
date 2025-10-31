# backend/app/terms_of_support_v2/modules/lawsuit_stage_v2.py
"""
Модуль определения этапов для искового производства (версия 2).

Содержит функции для определения этапов сопровождения дел искового производства
и сохранения результатов анализа в файл Excel.

Основные функции:
- assign_lawsuit_stages: Векторизованное определение этапов дел
- save_stage_table_to_excel: Сохранение результатов в Excel-файл
"""

import pandas as pd
import os
from datetime import datetime
from backend.app.common.config.column_names import COLUMNS, VALUES


def assign_lawsuit_stages(df: pd.DataFrame) -> pd.DataFrame:
    """
    Векторизованное определение этапов сопровождения для дел искового производства.

    Использует маски Pandas для быстрого определения этапа каждого дела на основе
    статуса дела и наличия ключевых дат. Этапы определяются в строгом порядке приоритета
    от исключительных статусов к стандартным этапам сопровождения.

    Args:
        df (pd.DataFrame): Исходный DataFrame с данными дел искового производства

    Returns:
        pd.DataFrame: DataFrame с колонкой caseStage, содержащий определенные этапы
                     для каждого дела в порядке приоритета:
                     - exceptions: Исключительные статусы
                     - closed: Закрытые дела
                     - executionDocumentReceived: Получен исполнительный документ
                     - decisionMade: Вынесено решение суда
                     - underConsideration: Дело находится в стадии рассмотрения
                     - courtReaction: Ожидается реакция суда
                     - firstStatusChanged: Стадия подготовки документов
                     - outside_stage_filters: Дела вне фильтров этапов
    """
    # Создание результирующего DataFrame с кодами дел
    result_df = pd.DataFrame(index=df.index)
    result_df["caseStage"] = "outside_stage_filters"

    # 1. Определение исключений - дела с особыми статусами
    case_status_col = COLUMNS["CASE_STATUS"]
    if case_status_col in df.columns:
        exception_mask = df[case_status_col].isin([
            VALUES["REOPENED"],
            VALUES["COMPLAINT_FILED"],
            VALUES["ERROR_DUBLICATE"],
            VALUES["WITHDRAWN_BY_THE_INITIATOR"],
        ])
        result_df.loc[exception_mask, "caseStage"] = "exceptions"

    # 2. Определение закрытых дел
    case_closing_col = COLUMNS["CASE_CLOSING_DATE"]
    closed_statuses = [VALUES["CONDITIONALLY_CLOSED"], VALUES["CLOSED"]]

    closed_mask = pd.Series(False, index=df.index)

    if case_status_col in df.columns:
        closed_mask |= df[case_status_col].isin(closed_statuses)

    if case_closing_col in df.columns:
        closed_mask |= df[case_closing_col].notna()

    if case_status_col in df.columns:
        result_df.loc[closed_mask & ~exception_mask, "caseStage"] = "closed"

    # 3. Определение дел с получением исполнительного документа
    execution_mask = pd.Series(False, index=df.index)

    court_status_col = COLUMNS["CASE_STATUS"]
    if court_status_col in df.columns:
        execution_mask |= (df[court_status_col] == VALUES["COURT_ACT_IN_FORCE"])

    transfer_col = COLUMNS["ACTUAL_TRANSFER_DATE"]
    if transfer_col in df.columns:
        execution_mask |= df[transfer_col].notna()

    receipt_col = COLUMNS["ACTUAL_RECEIPT_DATE"]
    if receipt_col in df.columns:
        execution_mask |= df[receipt_col].notna()

    if case_status_col in df.columns:
        result_df.loc[execution_mask & ~exception_mask & ~closed_mask, "caseStage"] = "executionDocumentReceived"

    # 4. Определение дел с вынесенным решением
    decision_mask = pd.Series(False, index=df.index)

    if court_status_col in df.columns:
        decision_mask |= (df[court_status_col] == VALUES["DECISION_MADE"])

    characteristics_col = COLUMNS["CHARACTERISTICS_FINAL_COURT_ACT"]
    if characteristics_col in df.columns:
        decision_mask |= df[characteristics_col].notna()

    if case_status_col in df.columns:
        result_df.loc[decision_mask & ~exception_mask & ~closed_mask & ~execution_mask, "caseStage"] = "decisionMade"

    # 5. Определение дел в стадии рассмотрения
    if case_status_col in df.columns:
        under_consideration_mask = (df[case_status_col] == VALUES["UNDER_CONSIDERATION"])
        result_df.loc[
            under_consideration_mask & ~exception_mask & ~closed_mask & ~execution_mask & ~decision_mask, "caseStage"] = "underConsideration"

    # 6. Определение дел в ожидании реакции суда
    if case_status_col in df.columns:
        court_reaction_mask = (df[case_status_col] == VALUES["AWAITING_COURT_RESPONSE"])
        result_df.loc[
            court_reaction_mask & ~exception_mask & ~closed_mask & ~execution_mask & ~decision_mask & ~under_consideration_mask, "caseStage"] = "courtReaction"

    # 7. Определение дел в стадии подготовки документов
    if case_status_col in df.columns:
        first_status_mask = (df[case_status_col] == VALUES["PREPARATION_OF_DOCUMENTS"])
        result_df.loc[
            first_status_mask & ~exception_mask & ~closed_mask & ~execution_mask & ~decision_mask & ~under_consideration_mask & ~court_reaction_mask, "caseStage"] = "firstStatusChanged"

    return result_df


def save_stage_table_to_excel(result_df: pd.DataFrame, base_dir: str = "backend/app/data") -> str:
    """
    Сохраняет таблицу с этапами и мониторингом искового производства в Excel-файл.

    Создает файл с уникальным именем, содержащим дату генерации отчета.
    При возникновении ошибки сохраняет файл с дополнительным timestamp.

    Args:
        result_df (pd.DataFrame): DataFrame с результатами анализа этапов
        base_dir (str): Базовая директория для сохранения файла

    Returns:
        str: Полный путь к сохраненному файлу

    Raises:
        Exception: При ошибках записи файла создается файл с уникальным именем
    """
    # Создание целевой директории, если она не существует
    os.makedirs(base_dir, exist_ok=True)

    # Формирование имени файла с текущей датой
    today_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"stage_and_monitoring_status_{today_str}.xlsx"
    filepath = os.path.join(base_dir, filename)

    # Попытка сохранения DataFrame в Excel
    try:
        # Сохранение данных без индекса в файл Excel
        result_df.to_excel(filepath, index=False)
    except Exception as e:
        # При ошибке создание уникального имени файла с timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stage_and_monitoring_status_{today_str}_{timestamp}.xlsx"
        filepath = os.path.join(base_dir, filename)
        # Повторная попытка сохранения с новым именем файла
        result_df.to_excel(filepath, index=False)

    return filepath