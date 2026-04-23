# backend/app/task_manager/modules/task_formatter.py
"""
Модуль форматирования задач в формат модели Task (v3).

Содержит функции для создания задач в соответствии с моделью Task.
"""

from datetime import datetime
from typing import Dict, Any


class TaskFormatter:
    """
    Форматтер для создания задач в формате модели Task.
    """

    def __init__(self):
        """Инициализация форматтера с внутренним счётчиком задач."""
        self._task_counter = 1

    def _generate_task_code(self) -> str:
        """
        Генерирует уникальный код задачи.

        Returns:
            str: Уникальный код задачи в формате TASK_0000001
        """
        task_code = f"TASK_{self._task_counter:07d}"
        self._task_counter += 1
        return task_code

    def reset_counter(self) -> None:
        """Сбрасывает счётчик задач для нового анализа."""
        self._task_counter = 1

    def format_task(
        self,
        check_result_code: str,
        task_text: str,
        reason_text: str,
        created_by: str
    ) -> Dict[str, Any]:
        """
        Создаёт задачу в формате модели Task.

        Args:
            check_result_code: Код результата проверки (связь с check_results)
            task_text: Текст задачи (что нужно сделать)
            reason_text: Причина постановки задачи
            created_by: Логин пользователя, создавшего задачу

        Returns:
            Dict: Словарь с полями модели Task
        """
        return {
            "taskCode": self._generate_task_code(),
            "checkResultCode": check_result_code,
            "taskText": task_text,
            "reasonText": reason_text,
            "createdAt": datetime.now(),
            "isCompleted": False,
            "executionDateTimeFact": None,
            "createdBy": created_by
        }


# Глобальный экземпляр форматтера
task_formatter = TaskFormatter()

