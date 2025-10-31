# backend/app/terms_of_support_v2/modules/order_stage_v2.py
"""
Модуль определения этапов для приказного производства (версия 2).

Содержит функции для определения этапов сопровождения дел приказного производства
и сохранения результатов анализа в файл Excel.

Основные функции:
- assign_order_stages: Векторизованное определение этапов дел
- save_order_stage_table_to_excel: Сохранение результатов в Excel-файл
"""

import pandas as pd
import os
from datetime import datetime
from backend.app.common.config.column_names import COLUMNS, VALUES


def assign_order_stages(detailed_df: pd.DataFrame) -> pd.DataFrame:
    """
    Векторизованное определение этапов сопровождения для дел приказного производства.

    Использует маски Pandas для определения этапа каждого дела на основе статуса
    и наличия ключевых дат. Этапы определяются в строгом порядке приоритета
    от исключительных статусов к стандартным этапам сопровождения.

    Args:
        detailed_df (pd.DataFrame): Исходный DataFrame с данными дел приказного производства

    Returns:
        pd.DataFrame: DataFrame с колонкой caseStage, содержащий определенные этапы
                     для каждого дела в порядке приоритета:
                     - exceptions: Исключительные статусы
                     - closed: Закрытые дела
                     - executionDocumentReceived: Получен исполнительный документ
                     - courtReaction: Ожидается реакция суда
                     - firstStatusChanged: Стадия подготовки документов
                     - outside_stage_filters: Дела вне фильтров этапов
    """
    # Создание результирующего DataFrame для хранения этапов
    result_df = pd.DataFrame(index=detailed_df.index)
    result_df["caseStage"] = "outside_stage_filters"

    # 1. Определение исключений - дела с особыми статусами
    exception_mask = detailed_df[COLUMNS["CASE_STATUS"]].isin([
        VALUES["REOPENED"],
        VALUES["COMPLAINT_FILED"],
        VALUES["ERROR_DUBLICATE"],
        VALUES["WITHDRAWN_BY_THE_INITIATOR"],
    ])
    result_df.loc[exception_mask, "caseStage"] = "exceptions"

    # 2. Определение закрытых дел
    closed_mask = (detailed_df[COLUMNS["CASE_STATUS"]] == VALUES["CLOSED"])

    # Безопасная проверка даты закрытия дела
    if COLUMNS["CASE_CLOSING_DATE"] in detailed_df.columns:
        closed_mask |= detailed_df[COLUMNS["CASE_CLOSING_DATE"]].notna()

    # Применение маски с исключением уже определенных исключений
    result_df.loc[closed_mask & ~exception_mask, "caseStage"] = "closed"

    # 3. Определение дел с получением исполнительного документа
    execution_mask = (
        (detailed_df[COLUMNS["CASE_STATUS"]] == VALUES["CONDITIONALLY_CLOSED"])
    )

    # Безопасная проверка дат получения и передачи исполнительного документа
    if COLUMNS["ACTUAL_RECEIPT_DATE"] in detailed_df.columns:
        execution_mask |= detailed_df[COLUMNS["ACTUAL_RECEIPT_DATE"]].notna()

    if COLUMNS["ACTUAL_TRANSFER_DATE"] in detailed_df.columns:
        execution_mask |= detailed_df[COLUMNS["ACTUAL_TRANSFER_DATE"]].notna()

    # Применение маски с исключением предыдущих этапов
    result_df.loc[execution_mask & ~exception_mask & ~closed_mask, "caseStage"] = "executionDocumentReceived"

    # 4. Определение дел в ожидании реакции суда
    court_reaction_mask = (detailed_df[COLUMNS["CASE_STATUS"]] == VALUES["AWAITING_COURT_RESPONSE"])
    # Применение маски с исключением предыдущих этапов
    result_df.loc[
        court_reaction_mask & ~exception_mask & ~closed_mask & ~execution_mask,
        "caseStage"
    ] = "courtReaction"

    # 5. Определение дел в стадии подготовки документов
    first_status_mask = (detailed_df[COLUMNS["CASE_STATUS"]] == VALUES["PREPARATION_OF_DOCUMENTS"])
    # Применение маски с исключением всех предыдущих этапов
    result_df.loc[
        first_status_mask & ~exception_mask & ~closed_mask & ~execution_mask & ~court_reaction_mask,
        "caseStage"
    ] = "firstStatusChanged"

    return result_df


def save_order_stage_table_to_excel(result_df: pd.DataFrame, base_dir: str = "backend/app/data") -> str:
    """
    Сохраняет таблицу с этапами и мониторингом приказного производства в Excel-файл.

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
    filename = f"order_stage_and_monitoring_status_{today_str}.xlsx"
    filepath = os.path.join(base_dir, filename)

    # Попытка сохранения DataFrame в Excel
    try:
        # Сохранение данных без индекса в файл Excel
        result_df.to_excel(filepath, index=False)
    except Exception as e:
        # При ошибке создание уникального имени файла с timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"order_stage_and_monitoring_status_{today_str}_{timestamp}.xlsx"
        filepath = os.path.join(base_dir, filename)
        # Повторная попытка сохранения с новым именем файла
        result_df.to_excel(filepath, index=False)

    return filepath