# backend/app/task_manager/modules/task_text_overrides.py
"""
Модуль с переопределениями текста задач для специфичных проверок.

Каждая функция предназначена для конкретного failed_check_name и содержит
логику определения текста задачи и/или причины на основе данных строки.
"""

import pandas as pd
from backend.app.common.config.column_names import COLUMNS
from typing import Tuple


def get_task_text_for_hearing_check(row: pd.Series, task_config: dict) -> Tuple[str, str]:
    """
    Определяет текст задачи и причину для проверки интервала между заседаниями.

    Args:
        row (pd.Series): Строка данных дела
        task_config (dict): Конфигурация задачи из TASK_MAPPINGS

    Returns:
        Tuple[str, str]: (текст задачи, текст причины)
    """
    default_text = task_config.get("task_text", "")
    default_reason = task_config.get("reason_text", "")

    try:
        prev_hearing = row.get(COLUMNS["PREVIOUS_HEARING_DATE"], None)
        next_hearing = row.get(COLUMNS["NEXT_HEARING_DATE"], None)

        if pd.notna(prev_hearing) and pd.notna(next_hearing):
            prev_date = pd.to_datetime(prev_hearing).date()
            next_date = pd.to_datetime(next_hearing).date()

            if next_date < prev_date:
                return (
                    "Обновить некорректно заполненные даты заседаний",
                    "Задача ставится если 'Дата ближайшего заседания суда' меньше 'Даты предыдущего заседания суда'"
                )

        return default_text, default_reason

    except Exception:
        return default_text, default_reason


def get_task_text_for_decision_check(row: pd.Series, task_config: dict) -> Tuple[str, str]:
    """
    Определяет текст задачи и причину для проверки решения об обжаловании
    в зависимости от заполненности тегов.

    Args:
        row (pd.Series): Строка данных дела
        task_config (dict): Конфигурация задачи из TASK_MAPPINGS

    Returns:
        Tuple[str, str]: (текст задачи, текст причины)
    """
    default_text = task_config.get("task_text", "")
    default_reason = task_config.get("reason_text", "")

    tags = row.get(COLUMNS["TAGS"], "")
    if pd.isna(tags) or str(tags).strip() in ("", "#"):
        return "Указать теги дела", "Задача ставится если в столбце детального отчета \"Теги\" нет данных, либо стоит только знак '#'"
    else:
        return default_text, default_reason


# Словарь для сопоставления failed_check_name с соответствующей функцией
TASK_TEXT_OVERRIDES = {
    "hearingInterval2days": get_task_text_for_hearing_check,
    "decision45days": get_task_text_for_decision_check,
}



