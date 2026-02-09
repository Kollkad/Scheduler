"""
Модуль для сбора необходимых колонок из конфигурации задач.

ColumnCollector анализирует TASK_MAPPINGS и определяет,
какие колонки из исходных отчетов нужны для проверки специальных условий.
"""

from typing import Set, Tuple, List
from backend.app.common.config.task_mappings import TASK_MAPPINGS
class ColumnCollector:
    """
    Сборщик необходимых колонок из конфигурации задач.

    Основная задача: проанализировать TASK_MAPPINGS и собрать все колонки,
    которые упоминаются в special_conditions задач.
    """

    @staticmethod
    def collect_from_mappings(task_mappings: dict) -> Tuple[List[str], List[str]]:
        """
        Собрать все колонки, необходимые для задач.

        Args:
            task_mappings: Словарь TASK_MAPPINGS с конфигурацией задач

        Returns:
            Кортеж из двух списков:
            - detailed_columns: колонки из детального отчета
            - documents_columns: колонки из отчета документов
        """
        # Множества для уникальных колонок
        detailed_columns: Set[str] = set()
        documents_columns: Set[str] = set()

        # Проходим по всем типам задач
        for task_type, stages in task_mappings.items():
            # Определяем, к какому источнику относится тип задач
            if task_type in ["lawsuit", "order"]:
                # Исковые и приказные задачи → колонки из детального отчета
                target_set = detailed_columns
            elif task_type == "documents":
                # Документные задачи → колонки из отчета документов
                target_set = documents_columns
            else:
                # Неизвестный тип задач, пропускаем
                continue

            # Проходим по всем этапам и задачам
            for stage, tasks in stages.items():
                for task in tasks:
                    # Проверяем специальные условия
                    if "special_conditions" in task:
                        special_conditions = task["special_conditions"]

                        # Если есть поле "column" - это имя колонки
                        if "column" in special_conditions:
                            column_name = special_conditions["column"]
                            target_set.add(column_name)

                        # Дополнительно: если есть check_type для документов
                        # (можно расширить при необходимости)
                        if task_type == "documents" and "check_type" in special_conditions:
                            # Здесь можно добавить логику для разных типов проверок документов
                            pass

        # Преобразуем множества в отсортированные списки для удобства
        return (
            sorted(list(detailed_columns)),
            sorted(list(documents_columns))
        )

    @staticmethod
    def collect_for_task_type(task_mappings: dict, task_type: str) -> List[str]:
        """
        Собрать колонки только для указанного типа задач.

        Args:
            task_mappings: Словарь TASK_MAPPINGS
            task_type: Тип задач ("lawsuit", "order" или "documents")

        Returns:
            Список необходимых колонок для этого типа задач
        """
        if task_type in ["lawsuit", "order"]:
            # Для исковых/приказных нужны колонки из детального отчета
            detailed_cols, _ = ColumnCollector.collect_from_mappings(task_mappings)
            return detailed_cols
        elif task_type == "documents":
            # Для документных - колонки из отчета документов
            _, documents_cols = ColumnCollector.collect_from_mappings(task_mappings)
            return documents_cols
        else:
            # Неизвестный тип
            return []

    @staticmethod
    def explain_collection(task_mappings: dict) -> dict:
        """
        Пояснительный метод: показывает, откуда берутся колонки.

        Args:
            task_mappings: Словарь TASK_MAPPINGS

        Returns:
            Словарь с пояснениями в формате:
            {
                "detailed": [
                    {"column": "COLUMN_NAME", "from_task": "task_name"}
                ],
                "documents": [...]
            }
        """
        explanation = {"detailed": [], "documents": []}

        for task_type, stages in task_mappings.items():
            for stage, tasks in stages.items():
                for task in tasks:
                    if "special_conditions" in task:
                        special = task["special_conditions"]
                        if "column" in special:
                            column_info = {
                                "column": special["column"],
                                "from_task": f"{task_type}.{stage}",
                                "failed_check": task.get("failed_check_name", "unknown")
                            }

                            if task_type in ["lawsuit", "order"]:
                                explanation["detailed"].append(column_info)
                            elif task_type == "documents":
                                explanation["documents"].append(column_info)

        return explanation


