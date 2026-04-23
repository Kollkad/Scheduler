# backend/app/task_manager/modules/task_analyzer.py
"""
Модуль анализа и формирования задач на основе результатов проверок (v3).

Осуществляет анализ данных из check_results и формирует задачи
на основе условий, определенных в конфигурационных маппингах.
"""

import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

from backend.app.common.config.column_names import COLUMNS
from backend.app.task_manager.config.task_mappings import TASK_MAPPINGS
from backend.app.task_manager.modules.task_text_overrides import TASK_TEXT_OVERRIDES
from backend.app.task_manager.modules.task_formatter import task_formatter
from backend.app.data_management.modules.normalized_data_manager import normalized_manager


class TaskAnalyzer:
    """
    Анализатор для формирования задач на основе данных мониторинга (v3).

    Осуществляет анализ данных из check_results и создает задачи
    на основе проверки условий, определенных в конфигурационных маппингах.
    """

    def __init__(self):
        """Инициализация анализатора задач."""
        self.tasks = []

    def analyze_all_tasks(self, created_by: str) -> List[Dict[str, Any]]:
        """
        Основная функция анализа всех типов задач.

        Получает данные из normalized_manager и выполняет анализ
        для всех доступных типов производств и документов.

        Returns:
            List[Dict]: Список всех сформированных задач
        """
        all_tasks = []
        task_formatter.reset_counter()

        # Получение данных из нормализованного менеджера
        check_results_df = normalized_manager.get_check_results_data()
        cases_df = normalized_manager.get_cases_data()
        documents_df = normalized_manager.get_documents_data()

        if check_results_df.empty:
            print("⚠️ Нет результатов проверок для формирования задач")
            return []

        print("🔄 Начинается анализ задач...")

        # ===== Исковое производство =====
        if not cases_df.empty:
            lawsuit_tasks = self._analyze_production_tasks(
                check_results_df=check_results_df,
                source_df=cases_df,
                production_type="lawsuit",
                merge_key="targetId",
                source_key=COLUMNS["CASE_CODE"],
                created_by=created_by
            )
            all_tasks.extend(lawsuit_tasks)
            print(f"✅ Сформировано {len(lawsuit_tasks)} задач искового производства")

        # ===== Приказное производство =====
        if not cases_df.empty:
            order_tasks = self._analyze_production_tasks(
                check_results_df=check_results_df,
                source_df=cases_df,
                production_type="order",
                merge_key="targetId",
                source_key=COLUMNS["CASE_CODE"],
                created_by=created_by
            )
            all_tasks.extend(order_tasks)
            print(f"✅ Сформировано {len(order_tasks)} задач приказного производства")

        # ===== Документы =====
        if not documents_df.empty:
            document_tasks = self._analyze_documents_tasks(
                check_results_df=check_results_df,
                documents_df=documents_df,
                created_by=created_by
            )
            all_tasks.extend(document_tasks)
            print(f"✅ Сформировано {len(document_tasks)} задач по документам")

        # Сохранение задач в менеджер
        if all_tasks:
            tasks_df = pd.DataFrame(all_tasks)
            normalized_manager.set_tasks_data(tasks_df)

        self.tasks = all_tasks
        return all_tasks

    def _analyze_production_tasks(
            self,
            check_results_df: pd.DataFrame,
            source_df: pd.DataFrame,
            production_type: str,
            merge_key: str,
            source_key: str,
            created_by: str
    ) -> List[Dict[str, Any]]:
        """
        Анализ задач для производств (исковое/приказное).

        Args:
            check_results_df: DataFrame с результатами проверок
            source_df: DataFrame с исходными данными дел
            production_type: Тип производства ("lawsuit" или "order")
            merge_key: Ключ в check_results для соединения        source_key: Ключ в source_df для соединения

        Returns:
            List[Dict]: Список сформированных задач
        """
        tasks = []
        task_configs = TASK_MAPPINGS.get(production_type, {})

        if not task_configs:
            return tasks

        # Получение checks_df для связи checkCode → stageCode
        checks_df = normalized_manager.get_checks_data()

        # Фильтрация check_results: только overdue и не выполненные
        failed_results = check_results_df[
            (check_results_df["monitoringStatus"] == "overdue") &
            (check_results_df["completionStatus"] == False)
            ]

        if failed_results.empty:
            return tasks

        # Присоединение stageCode из checks_df
        failed_results = failed_results.merge(
            checks_df[["checkCode", "stageCode"]],
            on="checkCode",
            how="left"
        )

        # Объединение с исходными данными дел
        merged_df = failed_results.merge(
            source_df,
            left_on=merge_key,
            right_on=source_key,
            how="inner",
            suffixes=("", "_source")
        )

        if merged_df.empty:
            return tasks

        # Обработка каждого этапа из конфига
        for stage_code, stage_tasks in task_configs.items():
            # Фильтрация строк по stageCode
            stage_df = merged_df[merged_df["stageCode"] == stage_code]

            if stage_df.empty:
                continue

            for task_config in stage_tasks:
                # Фильтрация по checkCode
                check_code = task_config.get("failed_check_name")
                task_df = stage_df[stage_df["checkCode"] == check_code]

                if task_df.empty:
                    continue

                # Применение специальных условий, если есть
                if "special_conditions" in task_config:
                    task_df = self._apply_special_conditions(task_df, task_config)

                if task_df.empty:
                    continue

                # Получение текстов задачи
                task_text, reason_text = self._get_task_texts(task_config, task_df)

                # Создание задач для каждой строки
                for _, row in task_df.iterrows():
                    task = task_formatter.format_task(
                        check_result_code=row["checkResultCode"],
                        task_text=task_text,
                        reason_text=reason_text,
                        created_by=created_by
                    )
                    tasks.append(task)

        return tasks

    def _analyze_documents_tasks(
            self,
            check_results_df: pd.DataFrame,
            documents_df: pd.DataFrame,
            created_by: str
    ) -> List[Dict[str, Any]]:
        """
        Анализ задач по документам.

        Args:
            check_results_df: DataFrame с результатами проверок
            documents_df: DataFrame с исходными данными документов

        Returns:
            List[Dict]: Список сформированных задач
        """
        tasks = []
        task_configs = TASK_MAPPINGS.get("documents", {})

        if not task_configs:
            return tasks

        # Получение checks_df для связи checkCode → stageCode
        checks_df = normalized_manager.get_checks_data()

        # Фильтрация check_results: только overdue и не выполненные
        failed_results = check_results_df[
            (check_results_df["monitoringStatus"] == "overdue") &
            (check_results_df["completionStatus"] == False)
            ]

        if failed_results.empty:
            return tasks

        # Присоединение stageCode из checks_df
        failed_results = failed_results.merge(
            checks_df[["checkCode", "stageCode"]],
            on="checkCode",
            how="left"
        )

        # Объединение с исходными данными документов
        merged_df = failed_results.merge(
            documents_df,
            left_on="targetId",
            right_on=COLUMNS["TRANSFER_CODE"],
            how="inner",
            suffixes=("", "_source")
        )

        if merged_df.empty:
            return tasks

        # Обработка конфигураций документов
        for stage_code, doc_tasks in task_configs.items():
            # Фильтрация строк по stageCode
            stage_df = merged_df[merged_df["stageCode"] == stage_code]

            if stage_df.empty:
                continue

            # Фильтрация по типу документа
            type_df = stage_df[stage_df[COLUMNS["DOCUMENT_TYPE"]] == "Исполнительный лист"]

            if type_df.empty:
                continue

            for task_config in doc_tasks:
                # Фильтрация по checkCode
                check_code = task_config.get("failed_check_name")
                task_df = type_df[type_df["checkCode"] == check_code]

                if task_df.empty:
                    continue

                # Создание задач для каждой строки
                for _, row in task_df.iterrows():
                    task = task_formatter.format_task(
                        check_result_code=row["checkResultCode"],
                        task_text=task_config.get("task_text", ""),
                        reason_text=task_config.get("reason_text", ""),
                        created_by=created_by
                    )
                    tasks.append(task)

        return tasks

    def _apply_special_conditions(self, df: pd.DataFrame, task_config: Dict) -> pd.DataFrame:
        """
        Применяет специальные условия фильтрации к DataFrame.

        Args:
            df: DataFrame для фильтрации
            task_config: Конфигурация задачи с special_conditions

        Returns:
            pd.DataFrame: Отфильтрованный DataFrame
        """
        special = task_config.get("special_conditions", {})

        if not special:
            return df

        # Тип 1: Проверка значения в колонке
        if "column" in special and "value" in special:
            column_name = special["column"]
            expected_value = special["value"]

            if column_name in df.columns:
                df = df[df[column_name].astype(str).str.strip() == str(expected_value).strip()]

        # Тип 2: Проверка статуса и наличия даты передачи
        elif "status" in special and "has_transfer_date" in special:
            expected_status = special["status"]
            needs_transfer_date = special["has_transfer_date"]

            if COLUMNS["CASE_STATUS"] in df.columns:
                df = df[df[COLUMNS["CASE_STATUS"]].astype(str).str.strip() == expected_status]

            if COLUMNS["ACTUAL_TRANSFER_DATE"] in df.columns:
                has_date = df[COLUMNS["ACTUAL_TRANSFER_DATE"]].notna()
                df = df[has_date == needs_transfer_date]

        # Тип 3: Проверка типа для документов
        elif "check_type" in special:
            check_type = special["check_type"]

            if check_type == "court_order_delivery":
                if COLUMNS["METHOD_OF_PROTECTION"] in df.columns:
                    df = df[df[COLUMNS["METHOD_OF_PROTECTION"]].astype(str).str.contains("Приказное", na=False)]

        return df

    def _get_task_texts(self, task_config: Dict, task_df: pd.DataFrame) -> tuple:
        """
        Получает тексты задачи с учётом возможных переопределений.

        Args:
            task_config: Конфигурация задачи
            task_df: DataFrame с отфильтрованными строками

        Returns:
            tuple: (task_text, reason_text)
        """
        failed_check_name = task_config.get("failed_check_name", "")
        default_text = task_config.get("task_text", "")
        default_reason = task_config.get("reason_text", "")

        # Если есть переопределение, применяем его к первой строке
        if failed_check_name in TASK_TEXT_OVERRIDES and not task_df.empty:
            override_func = TASK_TEXT_OVERRIDES[failed_check_name]
            first_row = task_df.iloc[0]
            return override_func(first_row, task_config)

        return default_text, default_reason


# Глобальный экземпляр анализатора задач
task_analyzer = TaskAnalyzer()

