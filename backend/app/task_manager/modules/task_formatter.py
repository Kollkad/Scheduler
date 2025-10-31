# backend/app/task_manager/modules/task_formatter.py
"""
Модуль форматирования задач в единый формат.

Осуществляет приведение задач из разных источников к единой структуре
для последующей обработки и отображения на фронтенде.
"""


def format_task(task_data: dict, source_type: str, original_row: dict) -> dict:
    """
    Форматирует задачу в единый формат для фронтенда.

    Args:
        task_data (dict): Данные задачи из TASK_MAPPINGS
        source_type (str): Тип источника ("lawsuit", "order", "documents")
        original_row (dict): Исходная строка данных

    Returns:
        dict: Отформатированная задача с унифицированной структурой
    """
    # Определение ответственного исполнителя в зависимости от типа источника
    responsible_executor = "unknown"
    if source_type in ["lawsuit", "order"]:
        responsible_executor = original_row.get("Ответственный исполнитель", "unknown")
    elif source_type == "documents":
        responsible_executor = original_row.get("Ответственный исполнитель", "unknown")

    # Определение этапа дела
    case_stage = "executionDocumentReceived"  # Значение по умолчанию для документов
    if source_type in ["lawsuit", "order"]:
        case_stage = original_row.get("case_stage", "unknown")

    # Формирование задачи в едином формате
    return {
        "taskCode": task_data["task_code"],
        "caseCode": original_row.get("Код дела", "unknown"),
        "sourceType": "detailed" if source_type in ["lawsuit", "order"] else "documents",
        "responsibleExecutor": responsible_executor,
        "caseStage": case_stage,
        "monitoringStatus": original_row.get("monitoring_status", "unknown"),
        "isCompleted": False,  # Все новые задачи помечаются как невыполненные
        "taskText": task_data["task_text"]
    }