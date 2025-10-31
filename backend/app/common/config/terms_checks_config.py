# backend/app/common/config/terms_checks_config.py
"""
Конфигурация проверок сроков для различных типов производств.

Содержит маппинг категорий проверок на конкретные проверяемые параметры:
- Исковое производство (LAWSUIT_CHECKS_MAPPING)
- Приказное производство (ORDER_CHECKS_MAPPING)

Каждая категория содержит список проверок, которые выполняются
для определения соответствия установленным срокам обработки дел.
"""

LAWSUIT_CHECKS_MAPPING = {
    "exceptions": ["exceptionStatus"],
    "underConsideration": [
        "nextHearing3days",
        "hearingInterval2days",
        "consideration60days"
    ],
    "decisionMade": [
        "decision45days",
        "decisionReceipt3days",
        "decisionTransfer1day"
    ],
    "courtReaction": ["courtReaction7days"],
    "firstStatusChanged": ["firstStatusChanged14days"],
    "closed": ["closed125days"],
    "executionDocumentReceived": ["executionDocumentReceivedL"]
}

ORDER_CHECKS_MAPPING = {
    "exceptions": ["exceptionStatus"],
    "closed": ["closed90Days"],
    "executionDocumentReceived": ["executionDocumentReceivedO"],
    "courtReaction": ["courtReaction60Days"],
    "firstStatusChanged": ["firstStatus14Days"],
}