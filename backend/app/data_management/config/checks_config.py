# backend/app/data_management/config/checks_config.py

"""
Конфигурация проверок для документов и производств.

Определяет, какие проверки на каких этапах выполняются.
"""

from backend.app.data_management.models.check import Check
from backend.app.document_monitoring_v3.modules.document_row_analyzer_v3 import evaluate_documents_dataframe

from backend.app.terms_of_support_v3.modules.lawsuit_dataframe_analyzer_v3 import (
    evaluate_closed_dataframe,
    evaluate_execution_document_received_dataframe,
    evaluate_decision_date_dataframe,
    evaluate_decision_receipt_dataframe,
    evaluate_decision_transfer_dataframe,
    evaluate_next_hearing_present_dataframe,
    evaluate_prev_to_next_hearing_dataframe,
    evaluate_under_consideration_60days_dataframe,
    evaluate_court_reaction_dataframe,
    evaluate_first_status_changed_dataframe,
)
from backend.app.terms_of_support_v3.modules.order_dataframe_analyzer_v3 import (
    evaluate_order_closed_dataframe,
    evaluate_order_execution_document_dataframe,
    evaluate_order_court_reaction_dataframe,
    evaluate_order_first_status_dataframe,
)
from backend.app.terms_of_support_v3.modules.terms_analyzer_v3 import evaluate_exceptions_dataframe

# Реестр функций-проверок (строка → реальная функция)
CHECK_FUNCTION_REGISTRY = {
    # Документы
    "evaluate_documents_dataframe": evaluate_documents_dataframe,
    # Исковое производство
    "evaluate_exceptions_dataframe": evaluate_exceptions_dataframe,
    "evaluate_closed_dataframe": evaluate_closed_dataframe,
    "evaluate_execution_document_received_dataframe": evaluate_execution_document_received_dataframe,
    "evaluate_decision_date_dataframe": evaluate_decision_date_dataframe,
    "evaluate_decision_receipt_dataframe": evaluate_decision_receipt_dataframe,
    "evaluate_decision_transfer_dataframe": evaluate_decision_transfer_dataframe,
    "evaluate_next_hearing_present_dataframe": evaluate_next_hearing_present_dataframe,
    "evaluate_prev_to_next_hearing_dataframe": evaluate_prev_to_next_hearing_dataframe,
    "evaluate_under_consideration_60days_dataframe": evaluate_under_consideration_60days_dataframe,
    "evaluate_court_reaction_dataframe": evaluate_court_reaction_dataframe,
    "evaluate_first_status_changed_dataframe": evaluate_first_status_changed_dataframe,
    # Приказное производство
    "evaluate_order_closed_dataframe": evaluate_order_closed_dataframe,
    "evaluate_order_execution_document_dataframe": evaluate_order_execution_document_dataframe,
    "evaluate_order_court_reaction_dataframe": evaluate_order_court_reaction_dataframe,
    "evaluate_order_first_status_dataframe": evaluate_order_first_status_dataframe,
}

# Проверки для документов
DOCUMENT_CHECKS = [
    Check(
        checkCode="documentTransferConfirmationD",
        checkName="Подтверждение передачи документа",
        stageCode="transferredDocumentD",
        functionName="evaluate_documents_dataframe",
        isActive=True
    ),
]

# Проверки для искового производства
LAWSUIT_CHECKS = [
    # Этап exceptionsL
    Check(
        checkCode="exceptionsL",
        checkName="Исключение",
        stageCode="exceptionsL",
        functionName="evaluate_exceptions_dataframe",
        isActive=True
    ),
    # Этап closedL
    Check(
        checkCode="closedL",
        checkName="Закрытие дела (125 календарных дней)",
        stageCode="closedL",
        functionName="evaluate_closed_dataframe",
        isActive=True
    ),
    # Этап executionDocumentReceivedL
    Check(
        checkCode="executionDocumentReceivedL",
        checkName="Получение исполнительного документа",
        stageCode="executionDocumentReceivedL",
        functionName="evaluate_execution_document_received_dataframe",
        isActive=True
    ),
    # Этап decisionMadeL (3 проверки)
    Check(
        checkCode="decisionDateL",
        checkName="Вынесение решения (45 календарных дней)",
        stageCode="decisionMadeL",
        functionName="evaluate_decision_date_dataframe",
        isActive=True
    ),
    Check(
        checkCode="decisionReceiptL",
        checkName="Получение решения (3 календарных дня)",
        stageCode="decisionMadeL",
        functionName="evaluate_decision_receipt_dataframe",
        isActive=True
    ),
    Check(
        checkCode="decisionTransferL",
        checkName="Передача решения (1 календарный день)",
        stageCode="decisionMadeL",
        functionName="evaluate_decision_transfer_dataframe",
        isActive=True
    ),
    # Этап underConsiderationL (3 проверки)
    Check(
        checkCode="nextHearingPresentL",
        checkName="Назначение следующего заседания (3 рабочих дня)",
        stageCode="underConsiderationL",
        functionName="evaluate_next_hearing_present_dataframe",
        isActive=True
    ),
    Check(
        checkCode="hearingIntervalL",
        checkName="Интервал между заседаниями (2 рабочих дня)",
        stageCode="underConsiderationL",
        functionName="evaluate_prev_to_next_hearing_dataframe",
        isActive=True
    ),
    Check(
        checkCode="consideration60daysL",
        checkName="Рассмотрение дела (60 календарных дней)",
        stageCode="underConsiderationL",
        functionName="evaluate_under_consideration_60days_dataframe",
        isActive=True
    ),
    # Этап courtReactionL
    Check(
        checkCode="courtReactionL",
        checkName="Реакция суда (7 рабочих дней)",
        stageCode="courtReactionL",
        functionName="evaluate_court_reaction_dataframe",
        isActive=True
    ),
    # Этап firstStatusChangedL
    Check(
        checkCode="firstStatusChangedL",
        checkName="Смена статуса подготовки (14 календарных дней)",
        stageCode="firstStatusChangedL",
        functionName="evaluate_first_status_changed_dataframe",
        isActive=True
    ),
]

# Проверки для приказного производства
ORDER_CHECKS = [
    # Этап exceptionsO
    Check(
        checkCode="exceptionsO",
        checkName="Исключение",
        stageCode="exceptionsO",
        functionName="evaluate_exceptions_dataframe",
        isActive=True
    ),
    # Этап closedO
    Check(
        checkCode="closedO",
        checkName="Закрытие дела (90 календарных дней)",
        stageCode="closedO",
        functionName="evaluate_order_closed_dataframe",
        isActive=True
    ),
    # Этап executionDocumentReceivedO
    Check(
        checkCode="executionDocumentReceivedO",
        checkName="Получение исполнительного документа",
        stageCode="executionDocumentReceivedO",
        functionName="evaluate_order_execution_document_dataframe",
        isActive=True
    ),
    # Этап courtReactionO
    Check(
        checkCode="courtReactionO",
        checkName="Реакция суда (60 календарных дней)",
        stageCode="courtReactionO",
        functionName="evaluate_order_court_reaction_dataframe",
        isActive=True
    ),
    # Этап firstStatusChangedO
    Check(
        checkCode="firstStatusChangedO",
        checkName="Смена статуса подготовки (14 календарных дней)",
        stageCode="firstStatusChangedO",
        functionName="evaluate_order_first_status_dataframe",
        isActive=True
    ),
]


# Полный список проверок
ALL_CHECKS = DOCUMENT_CHECKS + LAWSUIT_CHECKS + ORDER_CHECKS

# Словарь для быстрого доступа по checkCode
CHECKS_BY_CODE = {check.checkCode: check for check in ALL_CHECKS}

