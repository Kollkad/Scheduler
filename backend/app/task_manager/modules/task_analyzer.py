import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
import math  # Добавлен импорт math

from backend.app.common.config.column_names import COLUMNS, VALUES
from backend.app.common.config.task_mappings import TASK_MAPPINGS
from backend.app.common.config.check_display_names import CHECK_DISPLAY_NAMES
from backend.app.task_manager.modules.column_collector import ColumnCollector
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

    def _clean_value(self, value):
        """Очищает NaN и Inf значения для корректной JSON сериализации."""
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return None
        elif pd.isna(value):
            return None
        return value

    def _format_task_dict(self, task_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Применяет очистку ко всем значениям в словаре задачи."""
        return {k: self._clean_value(v) for k, v in task_dict.items()}

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

        # Сброс счетчика при каждом новом расчете
        self._task_counter = 1

        # ШАГ 1: Собрать необходимые колонки из TASK_MAPPINGS
        from backend.app.task_manager.modules.column_collector import ColumnCollector
        column_collector = ColumnCollector()
        detailed_cols, documents_cols = column_collector.collect_from_mappings(TASK_MAPPINGS)

        print(f"📋 Собраны колонки для обогащения: detailed={len(detailed_cols)}, documents={len(documents_cols)}")

        # ШАГ 2: Получить исходные данные
        lawsuit_staged = data_manager.get_processed_data("lawsuit_staged")
        order_staged = data_manager.get_processed_data("order_staged")
        documents_processed = data_manager.get_processed_data("documents_processed")

        detailed_cleaned = data_manager.get_detailed_data()
        documents_cleaned = data_manager.get_documents_data()

        # ШАГ 3: Обогатить данные (если есть нужные колонки)
        lawsuit_enriched = None
        order_enriched = None
        documents_enriched = None

        # 3.1 Обогащение исковых данных
        if lawsuit_staged is not None and detailed_cols and detailed_cleaned is not None:
            lawsuit_enriched = self._enrich_data_with_columns(
                lawsuit_staged, detailed_cleaned, detailed_cols,
                source_type="detailed", left_key="caseCode", right_key="Код дела"
            )
        else:
            lawsuit_enriched = lawsuit_staged

        # 3.2 Обогащение приказных данных (те же колонки из detailed)
        if order_staged is not None and detailed_cols and detailed_cleaned is not None:
            order_enriched = self._enrich_data_with_columns(
                order_staged, detailed_cleaned, detailed_cols,
                source_type="detailed", left_key="caseCode", right_key="Код дела"
            )
        else:
            order_enriched = order_staged

        # 3.3 Обогащение документных данных
        if documents_processed is not None and documents_cols and documents_cleaned is not None:
            documents_enriched = self._enrich_data_with_columns(
                documents_processed, documents_cleaned, documents_cols,
                source_type="documents", left_key="requestCode", right_key="Код запроса"
            )
        else:
            documents_enriched = documents_processed

        # ШАГ 4: Анализ с обогащенными данными
        if lawsuit_enriched is not None:
            print("✅ Анализ задач искового производства...")
            lawsuit_tasks = self._analyze_lawsuit_tasks(lawsuit_enriched)
            all_tasks.extend(lawsuit_tasks)
            print(f"✅ Сформировано {len(lawsuit_tasks)} задач искового производства")

        if order_enriched is not None:
            print("✅ Анализ задач приказного производства...")
            order_tasks = self._analyze_order_tasks(order_enriched)
            all_tasks.extend(order_tasks)
            print(f"✅ Сформировано {len(order_tasks)} задач приказного производства")

        if documents_enriched is not None:
            print("✅ Анализ задач по документам...")
            document_tasks = self._analyze_document_tasks(documents_enriched, documents_cleaned)
            all_tasks.extend(document_tasks)
            print(f"✅ Сформировано {len(document_tasks)} задач по документам")

        # Сохранение задач обратно в data_manager
        if all_tasks:
            tasks_df = pd.DataFrame(all_tasks)
            data_manager.set_processed_data("tasks", tasks_df)

        print(f"✅ Всего сформировано {len(all_tasks)} задач")
        self.tasks = all_tasks
        return all_tasks

    def _enrich_data_with_columns(self, processed_df: pd.DataFrame, cleaned_df: pd.DataFrame,
                                  columns_to_add: List[str], source_type: str,
                                  left_key: str, right_key: str) -> pd.DataFrame:
        """
        Обогащает processed_df колонками из cleaned_df.

        Args:
            processed_df: DataFrame с обработанными данными
            cleaned_df: DataFrame с полными данными
            columns_to_add: Список колонок для добавления
            source_type: Тип источника ("detailed" или "documents")
            left_key: Ключ в processed_df для соединения
            right_key: Ключ в cleaned_df для соединения

        Returns:
            Обогащенный DataFrame
        """
        if processed_df is None or processed_df.empty:
            return processed_df

        if cleaned_df is None or cleaned_df.empty:
            print(f"⚠️ Нет данных для обогащения {source_type}")
            return processed_df

        if not columns_to_add:
            return processed_df

        # Проверяем, что нужные колонки существуют в cleaned_df
        available_columns = []
        for col in columns_to_add:
            if col in cleaned_df.columns:
                available_columns.append(col)
            else:
                print(f"⚠️ Колонка '{col}' не найдена в {source_type} данных")

        if not available_columns:
            print(f"ℹ️ Нет доступных колонок для обогащения {source_type}")
            return processed_df

        # Проверяем ключи
        if left_key not in processed_df.columns:
            print(f"⚠️ Ключ '{left_key}' не найден в processed данных")
            return processed_df

        if right_key not in cleaned_df.columns:
            print(f"⚠️ Ключ '{right_key}' не найден в cleaned данных")
            return processed_df

        # Выбираем только нужные колонки
        columns_for_merge = [right_key] + available_columns

        try:
            # Делаем merge
            enriched_df = processed_df.merge(
                cleaned_df[columns_for_merge],
                left_on=left_key,
                right_on=right_key,
                how='left'
            )

            print(f"✅ Обогащены {source_type} данные: {len(available_columns)} колонок")
            return enriched_df

        except Exception as e:
            print(f"❌ Ошибка при обогащении {source_type} данных: {e}")
            return processed_df

    def _analyze_lawsuit_tasks(self, enriched_df: pd.DataFrame) -> List[Dict[str, Any]]:
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
            for _, row in enriched_df.iterrows():
                case_stage = row.get("caseStage")

                # Проверка наличия этапа дела в маппингах задач
                if case_stage in TASK_MAPPINGS["lawsuit"]:
                    stage_tasks = TASK_MAPPINGS["lawsuit"][case_stage]
                    failed_checks = self._get_failed_checks_for_stage(row, stage_tasks)

                    # Создание задачи при наличии проваленных проверок
                    if failed_checks:
                        task = self._format_lawsuit_task(row, failed_checks, case_stage)
                        lawsuit_tasks.append(self._format_task_dict(task))

            return lawsuit_tasks

        except Exception as e:
            print(f"❌ Ошибка анализа задач искового производства: {e}")
            return []

    def _analyze_order_tasks(self, enriched_df: pd.DataFrame) -> List[Dict[str, Any]]:
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
            for _, row in enriched_df.iterrows():
                case_stage = row.get("caseStage")

                # Проверка наличия этапа дела в маппингах задач
                if case_stage in TASK_MAPPINGS["order"]:
                    stage_tasks = TASK_MAPPINGS["order"][case_stage]
                    failed_checks = self._get_failed_checks_for_stage(row, stage_tasks)

                    # Создание задачи при наличии проваленных проверок
                    if failed_checks:
                        task = self._format_order_task(row, failed_checks, case_stage)
                        order_tasks.append(self._format_task_dict(task))

            return order_tasks

        except Exception as e:
            print(f"❌ Ошибка анализа задач приказного производства: {e}")
            return []

    def _analyze_document_tasks(self, enriched_documents: pd.DataFrame,
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
            if enriched_documents is None or enriched_documents.empty:  # БЫЛО: processed_documents
                return []

            # Итерация по всем строкам ОБОГАЩЕННЫХ документов
            for _, row in enriched_documents.iterrows():  # Используем enriched_documents
                stage_tasks = TASK_MAPPINGS["documents"]["executionDocument"]

                # Проверка условий для каждой конфигурации задачи
                for task_config in stage_tasks:
                    if self._check_document_task_conditions(row, task_config):
                        task = self._format_document_task(row, task_config, original_documents_df)
                        document_tasks.append(self._format_task_dict(task))

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

        document_type = row.get("document", "unknown")
        department = row.get("department", "unknown")
        request_code = row.get("requestCode", "")

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
            "documentType": document_type,
            "department": department,
            "requestCode": request_code,
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
        Теперь может проверять реальные колонки из enriched данных!

        Поддерживает типы условий из TASK_MAPPINGS:
        1. Проверка значения колонки: {"column": "COLUMN", "value": "VALUE"}
        2. Проверка статуса и даты: {"status": "STATUS", "has_transfer_date": True/False}
        3. Проверка типа для документов: {"check_type": "court_order_delivery"}
        """
        try:
            # ТИП 1: Проверка значения в колонке
            # Используется в: TASK_MAPPINGS["lawsuit"]["decisionMade"][0]
            if "column" in special_conditions and "value" in special_conditions:
                column_name = special_conditions["column"]
                expected_value = special_conditions["value"]

                # Проверяем, есть ли колонка в обогащенных данных
                if column_name not in row:
                    # Колонка не была обогащена - возможно, ее нет в исходных данных
                    # Не выводим warning, так как это нормально для задач без special_conditions
                    return False

                actual_value = row[column_name]

                # Обработка NaN значений
                if pd.isna(actual_value):
                    return False

                # Сравнение значений (строковое сравнение)
                return str(actual_value).strip() == str(expected_value).strip()

            # ТИП 2: Проверка статуса и наличия даты передачи
            # Используется в: TASK_MAPPINGS["order"]["executionDocumentReceivedO"][1,2]
            elif "status" in special_conditions and "has_transfer_date" in special_conditions:
                expected_status = special_conditions["status"]
                needs_transfer_date = special_conditions["has_transfer_date"]

                # Получаем текущий статус (проверяем разные возможные названия колонок)
                current_status = None
                status_columns = ["Статус", "STATUS", "status", "CASE_STATUS"]
                for col in status_columns:
                    if col in row:
                        current_status = row[col]
                        break

                # Проверка статуса
                if current_status is None or str(current_status).strip() != expected_status:
                    return False

                # Проверка даты передачи
                transfer_date_columns = ["Фактическая дата передачи ИД", "TRANSFER_DATE", "transfer_date"]
                has_date = False

                for col in transfer_date_columns:
                    if col in row:
                        transfer_date = row[col]
                        if not pd.isna(transfer_date):
                            has_date = True
                            break

                # Условие: должна быть дата ИЛИ не должна быть даты
                return has_date == needs_transfer_date

            # ТИП 3: Проверка типа для документов (например, подтверждение доставки СП)
            # Используется в: TASK_MAPPINGS["order"]["courtReaction"][1]
            elif "check_type" in special_conditions:
                check_type = special_conditions["check_type"]

                if check_type == "court_order_delivery":
                    # Для проверки доставки судебного приказа
                    # Проверяем, что дело приказное и нужна проверка доставки
                    case_type = row.get("METHOD_OF_PROTECTION", "")
                    is_order_production = "Приказное" in str(case_type)

                    return is_order_production

                # Можно добавить другие типы проверок при необходимости
                return False

            # Неизвестный тип условий
            print(f"⚠️ Неизвестный тип special_conditions: {special_conditions}")
            return False

        except Exception as e:
            print(f"❌ Ошибка проверки специальных условий: {e}")
            import traceback
            traceback.print_exc()
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