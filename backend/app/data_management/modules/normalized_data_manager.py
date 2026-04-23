# backend/app/data_management/modules/normalized_data_manager.py

"""
Нормализованный менеджер данных.

Хранит нормализованные данные в виде DataFrame.
Обеспечивает загрузку, доступ и сохранение данных.
"""

import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime

from backend.app.data_management.models.check_result import CheckResult
from backend.app.data_management.models.task import Task
from backend.app.data_management.models.case import Case
from backend.app.data_management.models.document import Document
from backend.app.data_management.models.user_task_override import UserTaskOverride
from backend.app.data_management.services.file_storage import file_storage

from backend.app.common.config.column_names import COLUMNS, VALUES
from backend.app.data_management.config.stages_config import ALL_STAGES
from backend.app.data_management.config.checks_config import ALL_CHECKS
from backend.app.data_management.modules.data_import import load_excel_data
from backend.app.data_management.modules.data_clean_documents import clean_documents_data as clean_documents
from backend.app.data_management.modules.data_clean_detailed import clean_data as clean_detailed
from backend.app.data_management.modules.gosb_normalization import normalize_detailed_report

class NormalizedDataManager:
    """
    Нормализованный менеджер данных.

    Хранит данные из загруженных файлов в словаре _source_data, где ключом является тип файла.
    Результаты проверок, задачи, этапы и проверки хранятся отдельно.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Инициализация пустых хранилищ данных."""
        if hasattr(self, '_initialized') and self._initialized:
            return

        # проверка времени загрузки данных из файлов
        self._data_loaded_at: Dict[str, datetime] = {}

        # Исходные данные из файлов (ключ = file_type)
        self._source_data: Dict[str, pd.DataFrame] = {}

        # Конфигурационные данные (загружаются из конфигов при инициализации)
        self._stages: pd.DataFrame = self._load_stages_from_config()
        self._checks: pd.DataFrame = self._load_checks_from_config()

        # Результаты работы
        self._check_results: pd.DataFrame = pd.DataFrame()
        self._tasks: pd.DataFrame = pd.DataFrame()

        # пользовательские изменения в задачах
        self._user_overrides = pd.DataFrame(columns=[
            "taskCode", "checkResultCode", "taskText", "reasonText",
            "createdAt", "isCompleted", "executionDateTimeFact", "executionDatePlan",
            "shiftCode", "createdBy"
        ])

        self._initialized = True

    def _load_stages_from_config(self) -> pd.DataFrame:
        """
        Загружает этапы из конфигурационного файла.

        Returns:
            pd.DataFrame: DataFrame с колонками stageCode, stageName, fileType
        """
        stages_list = [stage.model_dump() for stage in ALL_STAGES]
        return pd.DataFrame(stages_list)

    def _load_checks_from_config(self) -> pd.DataFrame:
        """
        Загружает проверки из конфигурационного файла.

        Returns:
            pd.DataFrame: DataFrame с колонками checkCode, checkName, stageCode, functionName, isActive
        """
        checks_list = [check.model_dump() for check in ALL_CHECKS]
        return pd.DataFrame(checks_list)

    # ===================== ЗАГРУЗКА ДАННЫХ =====================
    def get_or_load_detailed_report(self) -> pd.DataFrame:
        """
        Возвращает актуальные данные детального отчета.

        Если данные уже загружены и файл не обновлялся, возвращает кэш.
        Иначе загружает файл заново.
        """
        file = file_storage.get("current_detailed_report")
        if file is None:
            raise ValueError("Файл 'current_detailed_report' не загружен")

        # Проверка актуальности кэша
        if "detailed_report" in self._source_data and "detailed_report" in self._data_loaded_at:
            if self._data_loaded_at["detailed_report"] == file.uploaded_at:
                print("Данные детального отчета актуальны, используется кэш")
                return self._source_data["detailed_report"]

        # Данные устарели или отсутствуют = загрузить заново
        return self.load_detailed_report()

    def get_or_load_documents_report(self) -> pd.DataFrame:
        """
        Возвращает актуальные данные отчета документов.

        Если данные уже загружены и файл не обновлялся, возвращает кэш.
        Иначе загружает файл заново.
        """
        file = file_storage.get("documents_report")
        if file is None:
            raise ValueError("Файл 'documents_report' не загружен")

        # Проверка актуальности кэша
        if "documents_report" in self._source_data and "documents_report" in self._data_loaded_at:
            if self._data_loaded_at["documents_report"] == file.uploaded_at:
                print("Данные отчета документов актуальны, используется кэш")
                return self._source_data["documents_report"]

        # Данные устарели или отсутствуют = загрузить заново
        return self.load_documents_report()

    def load_detailed_report(self) -> pd.DataFrame:
        """
        Загружает и нормализует детальный отчет по делам из хранилища файлов.

        Returns:
            pd.DataFrame: Очищенный и нормализованный DataFrame с делами

        Raises:
            ValueError: Если файл не найден в хранилище
        """
        file = file_storage.get("current_detailed_report")
        if file is None:
            raise ValueError("Файл 'current_detailed_report' не загружен")

        filepath = file.server_path
        print("Загрузка и очистка детального отчета")

        raw_df = load_excel_data(filepath)
        cleaned_df = clean_detailed(raw_df)

        from backend.app.common.config.column_names import VALUES
        method_col = COLUMNS["METHOD_OF_PROTECTION"]
        simplified_value = VALUES["SIMPLIFIED_PRODUCTION"]
        claim_value = VALUES["CLAIM_PROCEEDINGS"]

        if method_col in cleaned_df.columns:
            cleaned_df[method_col] = cleaned_df[method_col].replace(
                simplified_value, claim_value
            )

        normalized_df = normalize_detailed_report(cleaned_df)

        self._validate_dataframe_against_model(normalized_df, Case)
        self._source_data["detailed_report"] = normalized_df
        self._data_loaded_at["detailed_report"] = file.uploaded_at
        return normalized_df

    def load_documents_report(self) -> pd.DataFrame:
        """
        Загружает и нормализует отчет документов из хранилища файлов.

        Returns:
            pd.DataFrame: Плоский DataFrame со всеми колонками отчёта

        Raises:
            ValueError: Если файл не найден в хранилище
        """
        file = file_storage.get("documents_report")
        if file is None:
            raise ValueError("Файл 'documents_report' не загружен")

        filepath = file.server_path
        print("Загрузка и очистка отчета документов")

        # Загрузка исходного файла
        raw_df = load_excel_data(filepath)

        # Очистка документации
        cleaned_df = clean_documents(raw_df)

        # Нормализация названия колонки суда для унификации
        court_alt_name = COLUMNS["COURT_NAME"]
        court_std_name = COLUMNS["COURT"]

        if court_alt_name in cleaned_df.columns and court_std_name not in cleaned_df.columns:
            cleaned_df.rename(columns={court_alt_name: court_std_name}, inplace=True)

        # Нормализация метода защиты
        method_col = COLUMNS["METHOD_OF_PROTECTION"]
        simplified_value = VALUES["SIMPLIFIED_PRODUCTION"]
        claim_value = VALUES["CLAIM_PROCEEDINGS"]

        if method_col in cleaned_df.columns:
            cleaned_df[method_col] = cleaned_df[method_col].replace(
                simplified_value, claim_value
            )

        self._validate_dataframe_against_model(cleaned_df, Document)

        # Сохранение в словарь _source_data с ключом "documents_report"
        self._source_data["documents_report"] = cleaned_df
        self._data_loaded_at["documents_report"] = file.uploaded_at
        return cleaned_df

    # ===================== МЕТОДЫ ДОСТУПА К ДАННЫМ =====================

    def get_documents_data(self) -> pd.DataFrame:
        """
        Возвращает DataFrame с документами из отчета документов.

        Returns:
            pd.DataFrame: Данные документов или пустой DataFrame
        """
        return self._source_data.get("documents_report", pd.DataFrame())

    def get_cases_data(self) -> pd.DataFrame:
        """
        Возвращает DataFrame с делами из подробного отчета.

        Returns:
            pd.DataFrame: Данные дел или пустой DataFrame
        """
        return self._source_data.get("detailed_report", pd.DataFrame())

    def get_stages_data(self) -> pd.DataFrame:
        """
        Возвращает DataFrame с этапами.

        Returns:
            pd.DataFrame: Данные этапов
        """
        return self._stages

    def get_checks_data(self) -> pd.DataFrame:
        """
        Возвращает DataFrame с проверками.

        Returns:
            pd.DataFrame: Данные проверок
        """
        return self._checks

    def get_check_results_data(self) -> pd.DataFrame:
        """
        Возвращает DataFrame с результатами проверок.

        Returns:
            pd.DataFrame: Результаты проверок или пустой DataFrame
        """
        return self._check_results

    def get_tasks_data(self) -> pd.DataFrame:
        """
        Возвращает DataFrame с задачами.

        Returns:
            pd.DataFrame: Задачи или пустой DataFrame
        """
        return self._tasks

    # ===================== МЕТОДЫ ЗАПИСИ ДАННЫХ =====================

    def set_documents_data(self, dataframe: pd.DataFrame) -> None:
        """
        Сохраняет DataFrame с документами.

        Args:
            dataframe: DataFrame с данными документов
        """
        self._source_data["documents_report"] = dataframe

    def set_cases_data(self, dataframe: pd.DataFrame) -> None:
        """
        Сохраняет DataFrame с делами.

        Args:
            dataframe: DataFrame с данными дел
        """
        self._source_data["detailed_report"] = dataframe

    def set_check_results_data(self, dataframe: pd.DataFrame, analysis_type: str = None) -> None:
        """
        Добавляет результаты проверок в хранилище.

        Args:
            dataframe: DataFrame с новыми результатами
            analysis_type: Тип анализа ("lawsuit", "order", "documents").
                          Старые записи для этого типа удаляются перед добавлением.
        """
        if analysis_type and not self._check_results.empty:
            if analysis_type == "lawsuit":
                self._check_results = self._check_results[
                    ~self._check_results["checkCode"].str.endswith("L", na=False)
                ]
            elif analysis_type == "order":
                self._check_results = self._check_results[
                    ~self._check_results["checkCode"].str.endswith("O", na=False)
                ]
            elif analysis_type == "documents":
                self._check_results = self._check_results[
                    ~self._check_results["checkCode"].str.endswith("D", na=False)
                ]

        self._check_results = pd.concat([self._check_results, dataframe], ignore_index=True)

    def set_tasks_data(self, dataframe: pd.DataFrame) -> None:
        """
        Сохраняет DataFrame с задачами.

        Args:
            dataframe: DataFrame с задачами
        """
        self._tasks = dataframe

    # ===================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ =====================

    def get_document_by_transfer_code(self, transfer_code: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает документ по коду передачи.

        Args:
            transfer_code: Уникальный код передачи документа

        Returns:
            Optional[Dict[str, Any]]: Документ в виде словаря или None
        """
        documents_df = self.get_documents_data()
        if documents_df.empty:
            return None

        mask = documents_df[COLUMNS["TRANSFER_CODE"]] == transfer_code
        filtered = documents_df[mask]

        if filtered.empty:
            return None

        return filtered.iloc[0].to_dict()

    def get_check_results_by_target(self, target_id: str) -> pd.DataFrame:
        """
        Возвращает результаты проверок для указанного документа или дела.

        Args:
            target_id: transferCode (для документа) или caseCode (для дела)

        Returns:
            pd.DataFrame: Результаты проверок
        """
        if self._check_results.empty:
            return pd.DataFrame()

        return self._check_results[self._check_results["targetId"] == target_id]

    def get_tasks_by_check_result(self, check_result_code: str) -> pd.DataFrame:
        """
        Возвращает задачи для указанного результата проверки.

        Args:
            check_result_code: Уникальный код результата проверки

        Returns:
            pd.DataFrame: Задачи
        """
        if self._tasks.empty:
            return pd.DataFrame()

        return self._tasks[self._tasks["checkResultCode"] == check_result_code]

    def get_user_overrides_data(self) -> pd.DataFrame:
        """Возвращает DataFrame с пользовательскими переопределениями задач."""
        return self._user_overrides

    def set_user_overrides_data(self, dataframe: pd.DataFrame) -> None:
        """Сохраняет DataFrame с пользовательскими переопределениями."""
        self._validate_dataframe_against_model(dataframe, UserTaskOverride)
        self._user_overrides = dataframe

    def add_user_override(self, override: Dict[str, Any]) -> None:
        """
        Добавляет или обновляет пользовательское переопределение задачи.

        Если запись с таким taskCode уже существует, она заменяется новой.
        """
        new_row = pd.DataFrame([override])

        # Удаляем старую запись по taskCode
        if not self._user_overrides.empty:
            self._user_overrides = self._user_overrides[
                self._user_overrides["taskCode"] != override["taskCode"]
                ]

        # Добавляем новую запись
        if self._user_overrides.empty:
            self._user_overrides = new_row
        else:
            self._user_overrides = pd.concat(
                [self._user_overrides, new_row],
                ignore_index=True
            )

    def reset_data_loaded_at(self) -> None:
        """
        Сбрасывает время загрузки данных из файлов.

        Используется после импорта данных из Parquet, чтобы
        get_or_load_* не считали данные устаревшими.
        """
        self._data_loaded_at = {}
        print("🔄 Время загрузки данных сброшено")

    def clear_data(self, data_type: str = "all") -> None:
        """
        Очищает указанные хранилища данных.

        Args:
            data_type (str): Тип данных для очистки:
                - "documents": только документы (удаляет ключ "documents_report")
                - "cases": только дела (удаляет ключ "detailed_report")
                - "check_results": только результаты проверок
                - "tasks": только задачи
                - "all": все данные
        """
        if data_type in ["documents", "all"]:
            self._source_data.pop("documents_report", None)
        if data_type in ["cases", "all"]:
            self._source_data.pop("detailed_report", None)
        if data_type in ["check_results", "all"]:
            self._check_results = pd.DataFrame()
        if data_type in ["tasks", "all"]:
            self._tasks = pd.DataFrame()
        if data_type in ["user_overrides", "all"]:
            self._user_overrides = pd.DataFrame(columns=[
                "taskCode", "checkResultCode", "taskText", "reasonText",
                "createdAt", "isCompleted", "executionDateTimeFact", "executionDatePlan",
                "shiftCode", "createdBy"
            ])

        print(f"🧹 Очищены данные: {data_type}")

    def _validate_dataframe_against_model(self, df: pd.DataFrame, model) -> None:
        """
        Проверяет наличие в DataFrame колонок, соответствующих алиасам полей модели.
        Поля без алиаса пропускаются. При отсутствии колонки выводит предупреждение.

        Args:
            df: Проверяемый DataFrame.
            model: Класс Pydantic модели.
        """
        for field_name, field_info in model.model_fields.items():
            alias = field_info.alias
            if alias is None:
                continue
            if alias not in df.columns:
                print(f"⚠️ DataFrame не соответствует модели {model.__name__}. Отсутствует колонка: {alias}")

# Глобальный экземпляр для использования во всем приложении
normalized_manager = NormalizedDataManager()
