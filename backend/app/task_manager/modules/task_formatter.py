# backend/app/task_manager/modules/task_formatter.py
"""
Модуль форматирования задач в формат модели Task (v3).

Содержит функции для создания задач в соответствии с моделью Task.
"""

import hashlib
from datetime import datetime
from typing import Dict, Any


class TaskFormatter:
    """
    Форматтер для создания задач в формате модели Task.

    Генерирует детерминированные коды задач на основе хеша
    от checkResultCode и checkCode, что обеспечивает одинаковые коды
    при повторных анализах одних и тех же данных.
    """

    @staticmethod
    def _generate_task_code(check_result_code: str, check_code: str) -> str:
        """
        Генерирует уникальный код задачи на основе хеша от содержимого.

        Args:
            check_result_code: Код результата проверки
            check_code: Код проверки

        Returns:
            str: Уникальный код задачи в формате TASK-XXXXXXXXXX
        """
        raw = f"{check_result_code}_{check_code}"
        hash_hex = hashlib.sha256(raw.encode()).hexdigest()[:10].upper()
        return f"TASK-{hash_hex}"

    def format_task(
        self,
        check_result_code: str,
        task_text: str,
        reason_text: str,
        created_by: str,
        check_code: str = ""
    ) -> Dict[str, Any]:
        """
        Создаёт задачу в формате модели Task.

        Args:
            check_result_code: Код результата проверки (связь с check_results)
            task_text: Текст задачи (что нужно сделать)
            reason_text: Причина постановки задачи
            created_by: Логин пользователя, создавшего задачу
            check_code: Код проверки для генерации детерминированного taskCode

        Returns:
            Dict: Словарь с полями модели Task
        """
        return {
            "taskCode": self._generate_task_code(check_result_code, check_code),
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

