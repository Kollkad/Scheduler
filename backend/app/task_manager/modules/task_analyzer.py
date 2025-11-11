# backend/app/task_manager/modules/task_analyzer.py
"""
Модуль анализатора задач для системы управления задачами.

Основные функции:
- Анализ задач искового производства
- Анализ задач приказного производства
- Анализ задач по документам
- Формирование единого списка задач
- Генерация уникальных кодов задач
"""

import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

from backend.app.common.config.column_names import COLUMNS, VALUES
from backend.app.common.config.task_mappings import TASK_MAPPINGS
from backend.app.common.config.check_display_names import CHECK_DISPLAY_NAMES

class TaskAnalyzer:
    """
    Анализатор для формирования задач на основе данных мониторинга.

    Осуществляет анализ данных из различных источников и создает задачи
    на основе проверки условий, определенных в конфигурационных маппингах.
    """

    def __init__(self):
        """Инициализация анализатора задач."""
        self.tasks = []
        self._task_counter = 1  # Счетчик для генерации уникальных taskCode

    def _generate_task_code(self) -> str:
        """
        Генерирует уникальный код задачи.

        Returns:
            str: Уникальный код задачи в формате TASK_0000001
        """
        task_code = f"TASK_{self._task_counter:07d}"
        self._task_counter += 1
        return task_code

    def _get_failed_check_display_name(self, failed_check_name: str) -> str:
        return CHECK_DISPLAY_NAMES.get(failed_check_name, failed_check_name)

    def analyze_all_tasks(self) -> List[Dict[str, Any]]:
        """
        Основная функция анализа всех типов задач.

        Получает данные напрямую из data_manager и выполняет анализ
        для всех доступных типов производств и документов.

        Returns:
            List[Dict]: Список всех сформированных задач

        Raises:
            Exception: Возникает при ошибках доступа к данным или анализа
        """
        all_tasks = []
        from backend.app.common.modules.data_manager import data_manager

        print("🔄 Начинаем расчет задач...")

        # Сброс счетчика при каждом новом расчете
        self._task_counter = 1

        # Анализ данных искового производства
        lawsuit_staged = data_manager.get_processed_data("lawsuit_staged")
        if lawsuit_staged is not None:
            print("✅ Анализ задач искового производства...")
            lawsuit_tasks = self._analyze_lawsuit_tasks(lawsuit_staged)
            all_tasks.extend(lawsuit_tasks)
            print(f"✅ Сформировано {len(lawsuit_tasks)} задач искового производства")
        else:
            print("⚠️ Нет данных искового производства для анализа задач")

        # Анализ данных приказного производства
        order_staged = data_manager.get_processed_data("order_staged")
        if order_staged is not None:
            print("✅ Анализ задач приказного производства...")
            order_tasks = self._analyze_order_tasks(order_staged)
            all_tasks.extend(order_tasks)
            print(f"✅ Сформировано {len(order_tasks)} задач приказного производства")
        else:
            print("⚠️ Нет данных приказного производства для анализа задач")

        # Анализ данных документов
        documents_processed = data_manager.get_processed_data("documents_processed")
        documents_original = data_manager.get_documents_data()
        if documents_processed is not None:
            print("✅ Анализ задач по документам...")
            document_tasks = self._analyze_document_tasks(documents_processed, documents_original)
            all_tasks.extend(document_tasks)
            print(f"✅ Сформировано {len(document_tasks)} задач по документам")
        else:
            print("⚠️ Нет данных документов для анализа задач")

        # Сохранение задач обратно в data_manager
        if all_tasks:
            tasks_df = pd.DataFrame(all_tasks)
            data_manager.set_processed_data("tasks", tasks_df)

        print(f"✅ Всего сформировано {len(all_tasks)} задач")
        self.tasks = all_tasks
        return all_tasks

    def _analyze_lawsuit_tasks(self, staged_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Анализ задач для искового производства.

        Args:
            staged_df (pd.DataFrame): Таблица с этапами и статусами из build_new_table()

        Returns:
            List[Dict]: Список задач искового производства

        Raises:
            Exception: Возникает при ошибках анализа данных
        """
        lawsuit_tasks = []

        try:
            # Итерация по всем строкам данных искового производства
            for _, row in staged_df.iterrows():
                case_stage = row.get("caseStage")

                # Проверка наличия этапа дела в маппингах задач
                if case_stage in TASK_MAPPINGS["lawsuit"]:
                    stage_tasks = TASK_MAPPINGS["lawsuit"][case_stage]
                    failed_checks = self._get_failed_checks_for_stage(row, stage_tasks)

                    # Создание задачи при наличии проваленных проверок
                    if failed_checks:
                        task = self._format_lawsuit_task(row, failed_checks, case_stage)
                        lawsuit_tasks.append(task)

            return lawsuit_tasks

        except Exception as e:
            print(f"❌ Ошибка анализа задач искового производства: {e}")
            return []

    def _analyze_order_tasks(self, staged_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Анализ задач для приказного производства.

        Args:
            staged_df (pd.DataFrame): Таблица с этапами и статусами из build_production_table

        Returns:
            List[Dict]: Список задач приказного производства

        Raises:
            Exception: Возникает при ошибках анализа данных
        """
        order_tasks = []

        try:
            # Итерация по всем строкам данных приказного производства
            for _, row in staged_df.iterrows():
                case_stage = row.get("caseStage")

                # Проверка наличия этапа дела в маппингах задач
                if case_stage in TASK_MAPPINGS["order"]:
                    stage_tasks = TASK_MAPPINGS["order"][case_stage]
                    failed_checks = self._get_failed_checks_for_stage(row, stage_tasks)

                    # Создание задачи при наличии проваленных проверок
                    if failed_checks:
                        task = self._format_order_task(row, failed_checks, case_stage)
                        order_tasks.append(task)

            return order_tasks

        except Exception as e:
            print(f"❌ Ошибка анализа задач приказного производства: {e}")
            return []

    def _analyze_document_tasks(self, processed_documents: pd.DataFrame,
                                original_documents_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Анализ задач по документам.

        Args:
            processed_documents (pd.DataFrame): Обработанные документы из document_terms_v2
            original_documents_df (pd.DataFrame): Исходные данные документов

        Returns:
            List[Dict]: Список задач по документам

        Raises:
            Exception: Возникает при ошибках анализа данных документов
        """
        document_tasks = []

        try:
            # Проверка наличия данных для анализа
            if processed_documents is None or processed_documents.empty:
                return []

            # Итерация по всем строкам обработанных документов
            for _, row in processed_documents.iterrows():
                stage_tasks = TASK_MAPPINGS["documents"]["executionDocument"]

                # Проверка условий для каждой конфигурации задачи
                for task_config in stage_tasks:
                    if self._check_document_task_conditions(row, task_config):
                        task = self._format_document_task(row, task_config, original_documents_df)
                        document_tasks.append(task)

            return document_tasks

        except Exception as e:
            print(f"❌ Ошибка анализа задач по документам: {e}")
            return []

    def _format_lawsuit_task(self, row: pd.Series, failed_checks: List[Dict],
                             case_stage: str) -> Dict[str, Any]:
        """
        Форматирует задачу искового производства.

        Args:
            row (pd.Series): Строка данных из staged_df
            failed_checks (List[Dict]): Список проваленных проверок
            case_stage (str): Этап дела

        Returns:
            Dict: Отформатированная задача с полной структурой
        """
        task_data = failed_checks[0]["task_config"]
        reason_text = task_data.get("reason_text", "Причина не указана")

        # Обработка ответственного исполнителя
        responsible_executor = row.get("responsibleExecutor", "unknown")
        if pd.isna(responsible_executor) or responsible_executor == "":
            responsible_executor = "unknown"

        # Обработка кода дела
        case_code = row.get("caseCode", "unknown")
        if pd.isna(case_code) or case_code == "":
            case_code = "unknown"

        return {
            "taskCode": self._generate_task_code(),
            "caseCode": case_code,
            "responsibleExecutor": responsible_executor,
            "caseStage": case_stage,
            "failedCheck": self._get_failed_check_display_name(task_data["failed_check_name"]),
            "taskText": task_data["task_text"],
            "reasonText": task_data["reason_text"],
            "monitoringStatus": row.get("monitoringStatus", "unknown"),
            "sourceType": "detailed",
            "isCompleted": False,
            "createdDate": datetime.now().strftime("%d.%m.%Y")
        }

    def _format_order_task(self, row: pd.Series, failed_checks: List[Dict],
                           case_stage: str) -> Dict[str, Any]:
        """
        Форматирует задачу приказного производства.

        Args:
            row (pd.Series): Строка данных из staged_df
            failed_checks (List[Dict]): Список проваленных проверок
            case_stage (str): Этап дела

        Returns:
            Dict: Отформатированная задача с полной структурой
        """
        task_data = failed_checks[0]["task_config"]
        reason_text = task_data.get("reason_text", "Причина не указана")

        # Обработка ответственного исполнителя
        responsible_executor = row.get("responsibleExecutor", "unknown")
        if pd.isna(responsible_executor) or responsible_executor == "":
            responsible_executor = "unknown"

        # Обработка кода дела
        case_code = row.get("caseCode", "unknown")
        if pd.isna(case_code) or case_code == "":
            case_code = "unknown"

        return {
            "taskCode": self._generate_task_code(),
            "caseCode": case_code,
            "responsibleExecutor": responsible_executor,
            "caseStage": case_stage,
            "failedCheck": self._get_failed_check_display_name(task_data["failed_check_name"]),
            "taskText": task_data["task_text"],
            "reasonText": task_data["reason_text"],
            "monitoringStatus": row.get("monitoringStatus", "unknown"),
            "sourceType": "detailed",
            "isCompleted": False,
            "createdDate": datetime.now().strftime("%d.%m.%Y")
        }

    def _format_document_task(self, row: pd.Series, task_config: Dict,
                              original_documents_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Форматирует задачу по документам.

        Args:
            row (pd.Series): Строка данных из processed_documents
            task_config (Dict): Конфигурация задачи из TASK_MAPPINGS
            original_documents_df (pd.DataFrame): Исходные данные для получения RESPONSIBLE_EXECUTOR

        Returns:
            Dict: Отформатированная задача с полной структурой
        """
        # Обработка кода дела
        case_code = row.get("caseCode", "unknown")
        if pd.isna(case_code) or case_code == "":
            case_code = "unknown"

        # Поиск ответственного исполнителя в исходных данных
        responsible_executor = "unknown"
        if case_code != "unknown" and original_documents_df is not None:
            matching_rows = original_documents_df[original_documents_df[COLUMNS["DOCUMENT_CASE_CODE"]] == case_code]
            if not matching_rows.empty:
                responsible_executor = matching_rows[COLUMNS["RESPONSIBLE_EXECUTOR"]].iloc[0]
                if pd.isna(responsible_executor) or responsible_executor == "":
                    responsible_executor = "unknown"

        reason_text = task_config.get("reason_text", "Причина не указана")

        return {
            "taskCode": self._generate_task_code(),
            "caseCode": case_code,
            "responsibleExecutor": responsible_executor,
            "caseStage": "executionDocumentReceived",
            "failedCheck": self._get_failed_check_display_name(task_config["failed_check_name"]),
            "taskText": task_config["task_text"],
            "reasonText": task_config["reason_text"],
            "monitoringStatus": row.get("monitoringStatus", "unknown"),
            "sourceType": "documents",
            "isCompleted": False,
            "createdDate": datetime.now().strftime("%d.%m.%Y")
        }

    def _check_document_task_conditions(self, row: pd.Series, task_config: Dict) -> bool:
        """
        Проверяет условия формирования задачи для документов.

        Args:
            row (pd.Series): Строка данных документа
            task_config (Dict): Конфигурация задачи из TASK_MAPPINGS

        Returns:
            bool: True если условия выполнены, иначе False
        """
        try:
            monitoring_status = row.get("monitoringStatus", "")
            response_essence = row.get("responseEssence", "")

            # Определение статуса завершения на основе сущности ответа
            is_completed = (response_essence == "Передача подтверждена")
            completion_status = "false" if not is_completed else "true"

            conditions = task_config["conditions"]

            # Проверка условий завершения и мониторинга
            completion_ok = (completion_status == conditions[0])
            monitoring_ok = (monitoring_status.lower() == conditions[1])

            return completion_ok and monitoring_ok

        except Exception as e:
            return False

    def _get_failed_checks_for_stage(self, row: pd.Series, stage_tasks: List[Dict]) -> List[Dict]:
        """
        Определяет проваленные проверки для этапа дела.

        Args:
            row (pd.Series): Строка данных с monitoring_status и completion_status
            stage_tasks (List): Список конфигураций задач для этапа

        Returns:
            List[Dict]: Список проваленных проверок с информацией о задаче
        """
        failed_checks = []

        # Проверка каждой конфигурации задачи на этапе
        for task_config in stage_tasks:
            is_failed = False

            # Проверка специальных условий или стандартных условий
            if "special_conditions" in task_config:
                if self._check_special_conditions(row, task_config["special_conditions"]):
                    is_failed = True
            elif "conditions" in task_config:
                if self._check_task_conditions(row, task_config):
                    is_failed = True

            # Добавление проваленной проверки в результат
            if is_failed:
                failed_checks.append({
                    "task_config": task_config
                })

        return failed_checks

    def _check_special_conditions(self, row: pd.Series, special_conditions: Dict) -> bool:
        """
        Проверяет специальные условия формирования задачи.

        Args:
            row (pd.Series): Строка данных
            special_conditions (Dict): Конфигурация специальных условий

        Returns:
            bool: True если специальные условия выполнены, иначе False
        """
        try:
            # Реализация проверки специальных условий
            return False
        except Exception:
            return False

    def _check_task_conditions(self, row: pd.Series, task_config: Dict) -> bool:
        """
        Проверяет условия формирования задачи для искового/приказного производства.

        Args:
            row (pd.Series): Строка данных
            task_config (Dict): Конфигурация задачи из TASK_MAPPINGS

        Returns:
            bool: True если условия выполнены, иначе False
        """
        try:
            monitoring_status = row.get("monitoringStatus", "")
            completion_status = row.get("completionStatus", "")

            # Разделение статусов на составные части
            monitoring_parts = monitoring_status.split(";")
            completion_parts = completion_status.split(";")

            index = task_config["index"]
            conditions = task_config["conditions"]

            # Проверка условий по индексу
            if (index < len(completion_parts) and
                    index < len(monitoring_parts)):
                completion_ok = (completion_parts[index].lower() == conditions[0])
                monitoring_ok = (monitoring_parts[index].lower() == conditions[1])

                return completion_ok and monitoring_ok

            return False

        except Exception:
            return False


# Синглтон для удобного использования
task_analyzer = TaskAnalyzer()