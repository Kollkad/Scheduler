# backend/app/document_monitoring_v3/modules/document_stage_checks_v3.py
"""
Модуль проверки этапов документов для системы мониторинга

Предоставляет функции для анализа документов и формирования результатов
проверок в формате CheckResult.

Основные функции:
- analyze_documents: Анализ документов, установка stageCode, выполнение проверок
- save_document_monitoring_status: Сохранение результатов анализа (устаревшая)
"""

import pandas as pd
from datetime import datetime
import os

from backend.app.document_monitoring_v3.modules.document_row_analyzer_v3 import (
    filter_exceptions_documents,
    get_latest_document_in_group
)
from backend.app.common.config.column_names import COLUMNS
from backend.app.data_management.config.stages_config import get_stage_codes_by_file_type
from backend.app.data_management.config.checks_config import CHECK_FUNCTION_REGISTRY
from backend.app.common.modules.apply_checks_by_stage import apply_checks_by_stage
from backend.app.data_management.modules.normalized_data_manager import normalized_manager

def analyze_documents(documents_df: pd.DataFrame) -> pd.DataFrame:
    """
    Выполняет анализ документов и формирует результаты проверок.

    Процесс анализа включает:
    1. Установку stageCode для документов, имеющих transferCode
    2. Проверку допустимости назначенного этапа для типа файла documents_report
    3. Фильтрацию документов-исключений
    4. Группировку по ключевым полям (код дела, тип документа, подразделение)
    5. Выбор последней передачи в каждой группе
    6. Передачу подготовленных данных в универсальный исполнитель проверок
    7. Возврат результатов в формате CheckResult

    Args:
        documents_df (pd.DataFrame): DataFrame с данными документов.
            Модифицируется в процессе: добавляется колонка stageCode.

    Returns:
        pd.DataFrame: DataFrame с результатами проверок в формате CheckResult:
            - checkResultCode: уникальный код результата проверки
            - checkCode: код проверки из конфигурации
            - targetId: transferCode документа
            - monitoringStatus: статус мониторинга (timely/overdue/no_data)
            - completionStatus: статус завершенности
            - checkedAt: дата и время выполнения проверки
            - executionDatePlan: плановая дата (зарезервировано)
    """
    today = datetime.now().date()

    # Проверка допустимости этапов для типа файла documents_report
    allowed_stages = get_stage_codes_by_file_type("documents_report")
    if not allowed_stages:
        raise ValueError("Не найдено ни одного этапа для типа файла 'documents_report'")

    # ===== 1. Установка stageCode для документов =====
    # Этап назначается только документам, имеющим код передачи
    if COLUMNS["TRANSFER_CODE"] in documents_df.columns:
        stage_to_assign = "transferredDocumentD"
        if stage_to_assign not in allowed_stages:
            raise ValueError(
                f"Этап '{stage_to_assign}' не зарегистрирован для типа файла 'documents_report'"
            )
        documents_df["stageCode"] = stage_to_assign
    else:
        # Отсутствует ключевая колонка — анализ невозможен
        return pd.DataFrame(columns=[
            "checkResultCode", "checkCode", "targetId",
            "monitoringStatus", "completionStatus", "checkedAt", "executionDatePlan"
        ])

    # ===== 2. Фильтрация документов-исключений =====
    filtered_df = filter_exceptions_documents(documents_df)
    if filtered_df.empty:
        return pd.DataFrame(columns=[
            "checkResultCode", "checkCode", "targetId",
            "monitoringStatus", "completionStatus", "checkedAt", "executionDatePlan"
        ])

    # ===== 3. Определение колонок для группировки =====
    grouping_columns = []
    for col in [COLUMNS["DOCUMENT_CASE_CODE"], COLUMNS["DOCUMENT_TYPE"], COLUMNS["DEPARTMENT_CATEGORY"]]:
        if col in filtered_df.columns:
            grouping_columns.append(col)

    # ===== 4. Подготовка DataFrame с сущностями для проверки =====
    rows_for_check = []

    if not grouping_columns:
        # Группировка невозможна — каждая строка считается отдельной сущностью
        print("⚠️ Нет колонок для группировки документов, каждая строка обрабатывается отдельно")

        for _, row in filtered_df.iterrows():
            transfer_code = row.get(COLUMNS["TRANSFER_CODE"])
            if pd.isna(transfer_code):
                continue
            rows_for_check.append(row)

        if not rows_for_check:
            return pd.DataFrame(columns=[
                "checkResultCode", "checkCode", "targetId",
                "monitoringStatus", "completionStatus", "checkedAt", "executionDatePlan"
            ])

        prepared_df = pd.DataFrame(rows_for_check)
        # Добавление колонки targetId для универсального исполнителя
        prepared_df["targetId"] = prepared_df[COLUMNS["TRANSFER_CODE"]].astype(str)

    else:
        # Группировка и выбор последнего документа в каждой группе
        for _, group_df in filtered_df.groupby(grouping_columns):
            latest_document = get_latest_document_in_group(group_df)
            if latest_document.empty:
                continue

            transfer_code = latest_document.get(COLUMNS["TRANSFER_CODE"])
            if pd.isna(transfer_code):
                continue

            rows_for_check.append(latest_document)

        if not rows_for_check:
            return pd.DataFrame(columns=[
                "checkResultCode", "checkCode", "targetId",
                "monitoringStatus", "completionStatus", "checkedAt", "executionDatePlan"
            ])

        prepared_df = pd.DataFrame(rows_for_check)
        # Добавление колонки targetId для универсального исполнителя
        prepared_df["targetId"] = prepared_df[COLUMNS["TRANSFER_CODE"]].astype(str)

    # ===== 5. Выполнение проверок через универсальный исполнитель =====
    checks_df = normalized_manager.get_checks_data()

    check_results_df = apply_checks_by_stage(
        df=prepared_df,
        checks_df=checks_df,
        function_registry=CHECK_FUNCTION_REGISTRY,
        today=today
    )

    return check_results_df


