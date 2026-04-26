# backend/app/task_manager/modules/task_override_manager.py
"""
Модуль управления пользовательскими переопределениями задач.

Предоставляет функции для:
- Получения плановой даты задачи
- Проверки допустимости причины переноса срока
- Расчета новой плановой даты
- Создания/обновления/удаления оверрайдов
- Получения списка допустимых причин для задачи
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from backend.app.data_management.modules.normalized_data_manager import normalized_manager
from backend.app.task_manager.config.shift_reasons_config import SHIFT_REASONS_BY_CODE


class TaskOverrideManager:
    """Менеджер пользовательских переопределений задач."""

    def __init__(self):
        self._normalized_manager = normalized_manager

    def get_execution_date_plan(self, task_code: str) -> Optional[datetime]:
        """
        Возвращает актуальную плановую дату для задачи.

        Приоритет: оверрайд → check_results.

        Args:
            task_code: Код задачи

        Returns:
            datetime или None, если дата не найдена
        """
        # Проверяем оверрайд
        overrides_df = self._normalized_manager.get_user_overrides_data()
        if not overrides_df.empty:
            override = overrides_df[overrides_df["taskCode"] == task_code]
            if not override.empty and "executionDatePlan" in override.columns:
                val = override.iloc[0]["executionDatePlan"]
                if pd.notna(val):
                    return val

        # Ищем в check_results
        tasks_df = self._normalized_manager.get_tasks_data()
        check_results_df = self._normalized_manager.get_check_results_data()

        if tasks_df.empty or check_results_df.empty:
            return None

        task = tasks_df[tasks_df["taskCode"] == task_code]
        if task.empty:
            return None

        check_result_code = task.iloc[0]["checkResultCode"]
        result = check_results_df[check_results_df["checkResultCode"] == check_result_code]
        if result.empty or "executionDatePlan" not in result.columns:
            return None

        val = result.iloc[0]["executionDatePlan"]
        return val if pd.notna(val) else None

    def get_stage_code(self, task_code: str) -> Optional[str]:
        """
        Возвращает stageCode для задачи.

        Args:
            task_code: Код задачи

        Returns:
            str или None, если этап не найден
        """
        tasks_df = self._normalized_manager.get_tasks_data()
        check_results_df = self._normalized_manager.get_check_results_data()
        checks_df = self._normalized_manager.get_checks_data()

        if tasks_df.empty or check_results_df.empty or checks_df.empty:
            return None

        task = tasks_df[tasks_df["taskCode"] == task_code]
        if task.empty:
            return None

        check_result_code = task.iloc[0]["checkResultCode"]
        result = check_results_df[check_results_df["checkResultCode"] == check_result_code]
        if result.empty:
            return None

        check_code = result.iloc[0]["checkCode"]
        check_info = checks_df[checks_df["checkCode"] == check_code]
        if check_info.empty:
            return None

        return check_info.iloc[0]["stageCode"]

    def is_shift_reason_allowed(self, shift_code: str, stage_code: str) -> bool:
        """
        Проверяет, допустима ли причина переноса для указанного этапа.

        Args:
            shift_code: Код причины
            stage_code: Код этапа

        Returns:
            bool: True если причина допустима
        """
        if shift_code not in SHIFT_REASONS_BY_CODE:
            return False

        allowed_stages = SHIFT_REASONS_BY_CODE[shift_code].get("stageCodes", [])
        return stage_code in allowed_stages

    def calculate_shifted_date(self, current_date: datetime, shift_code: str) -> Optional[datetime]:
        """
        Рассчитывает новую плановую дату с учетом переноса.

        Args:
            current_date: Текущая плановая дата
            shift_code: Код причины переноса

        Returns:
            datetime или None, если причина не найдена
        """
        if shift_code not in SHIFT_REASONS_BY_CODE:
            return None

        days = SHIFT_REASONS_BY_CODE[shift_code].get("daysToAdd", 0)
        return current_date + timedelta(days=days)

    def apply_override(
        self,
        task_code: str,
        created_by: str,
        is_completed: Optional[bool] = None,
        shift_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Создает или обновляет пользовательское переопределение задачи.

        Args:
            task_code: Код задачи
            is_completed: Новый статус выполнения (опционально)
            shift_code: Код причины переноса срока (опционально)

        Returns:
            Dict с обновленными полями задачи

        Raises:
            ValueError: Если задача не найдена или причина недопустима
        """
        tasks_df = self._normalized_manager.get_tasks_data()
        if tasks_df.empty:
            raise ValueError("Нет рассчитанных задач")

        task = tasks_df[tasks_df["taskCode"] == task_code]
        if task.empty:
            raise ValueError(f"Задача {task_code} не найдена")

        original_task = task.iloc[0].to_dict()

        # Получаем текущий оверрайд, если есть
        overrides_df = self._normalized_manager.get_user_overrides_data()
        existing_override = None
        if not overrides_df.empty:
            existing = overrides_df[overrides_df["taskCode"] == task_code]
            if not existing.empty:
                existing_override = existing.iloc[0].to_dict()

        # Базовая задача (оригинал или существующий оверрайд)
        base_task = existing_override if existing_override else original_task

        # Получаем актуальную плановую дату
        current_planned = self.get_execution_date_plan(task_code)

        # Применяем изменения
        updated_task = base_task.copy()
        updated_task["taskCode"] = task_code
        updated_task["createdBy"] = created_by

        # Обработка выполнения
        if is_completed is not None:
            updated_task["isCompleted"] = is_completed
            if is_completed and not updated_task.get("executionDateTimeFact"):
                updated_task["executionDateTimeFact"] = datetime.now()
            else:
                updated_task["executionDateTimeFact"] = None

        # Обработка переноса срока
        if shift_code is not None:
            stage_code = self.get_stage_code(task_code)
            if not stage_code:
                raise ValueError(f"Не удалось определить этап для задачи {task_code}")

            if not self.is_shift_reason_allowed(shift_code, stage_code):
                raise ValueError(
                    f"Причина '{shift_code}' недопустима для этапа '{stage_code}'"
                )

            if current_planned is None:
                raise ValueError(f"Не удалось получить плановую дату для задачи {task_code}")

            new_planned = self.calculate_shifted_date(current_planned, shift_code)
            if new_planned is None:
                raise ValueError(f"Не удалось рассчитать новую дату для причины '{shift_code}'")

            updated_task["executionDatePlan"] = new_planned
            updated_task["shiftCode"] = shift_code

        # Сохраняем оверрайд
        self._normalized_manager.add_user_override(updated_task)

        return updated_task

    def delete_override(self, task_code: str) -> bool:
        """
        Удаляет пользовательское переопределение задачи.

        Args:
            task_code: Код задачи

        Returns:
            bool: True если запись была удалена
        """
        overrides_df = self._normalized_manager.get_user_overrides_data()
        if overrides_df.empty:
            return False

        if task_code not in overrides_df["taskCode"].values:
            return False

        self._normalized_manager._user_overrides = overrides_df[
            overrides_df["taskCode"] != task_code
        ]
        return True

    def get_shift_reasons_for_task(self, task_code: str) -> List[Dict[str, Any]]:
        """
        Возвращает список причин переноса, допустимых для задачи.

        Args:
            task_code: Код задачи

        Returns:
            List[Dict]: Список допустимых причин
        """
        stage_code = self.get_stage_code(task_code)
        if not stage_code:
            return []

        allowed = []
        for reason in SHIFT_REASONS_BY_CODE.values():
            if stage_code in reason.get("stageCodes", []):
                allowed.append({
                    "shiftCode": reason["shiftCode"],
                    "shiftName": reason["shiftName"],
                    "daysToAdd": reason["daysToAdd"]
                })

        return allowed


# Глобальный экземпляр менеджера
task_override_manager = TaskOverrideManager()



