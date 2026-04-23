# backend/app/task_manager/config/shift_reasons_config.py
"""
Конфигурация причин переноса плановой даты исполнения задачи.

Каждая причина содержит:
- shiftCode: str — уникальный код причины (например, "judges_vacation")
- stageCodes: List[str] — список кодов этапов, на которых причина может быть применена
- shiftName: str — русское название причины для отображения пользователю
- daysToAdd: int — количество календарных дней, на которое переносится executionDatePlan

Пример:
    {
        "shiftCode": "judges_vacation",
        "stageCodes": ["courtReactionL", "underConsiderationL"],
        "shiftName": "Невозможно получение документа, судья в отпуске",
        "daysToAdd": 14
    }
"""

from typing import List, Dict, Any

SHIFT_REASONS: List[Dict[str, Any]] = [
    {
        "shiftCode": "judges_vacation",
        "stageCodes": ["courtReactionL", "underConsiderationL", "courtReactionO"],
        "shiftName": "Невозможно получение документа, судья в отпуске",
        "daysToAdd": 14
    },
    {
        "shiftCode": "document_lost",
        "stageCodes": ["executionDocumentReceivedL", "executionDocumentReceivedO", "transferredDocumentD"],
        "shiftName": "Потеря документов при передаче",
        "daysToAdd": 7
    },
    {
        "shiftCode": "awaiting_response",
        "stageCodes": ["firstStatusChangedL", "firstStatusChangedO"],
        "shiftName": "Ожидание ответа от смежного подразделения",
        "daysToAdd": 5
    },
]

# Словарь для быстрого доступа по shiftCode
SHIFT_REASONS_BY_CODE: Dict[str, Dict[str, Any]] = {
    reason["shiftCode"]: reason for reason in SHIFT_REASONS
}


