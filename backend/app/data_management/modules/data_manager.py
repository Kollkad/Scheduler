# backend/app/data_management/modules/data_manager.py
"""
Центральный менеджер данных для управления загруженными и обработанными отчетами.

Обеспечивает:
- Загрузку и кэширование данных различных типов
- Нормализацию и очистку данных
- Управление памятью и состоянием данных
- Предоставление данных другим модулям системы через единый интерфейс
- Поддержку хранения файлов через централизованное файловое хранилище
"""

import pandas as pd
from typing import Dict, Optional, Tuple
import gc

from backend.app.data_management.modules.data_import import load_excel_data
from backend.app.data_management.modules.data_clean_detailed import clean_data as clean_detailed
from backend.app.data_management.modules.data_clean_documents import clean_documents_data as clean_documents
from backend.app.data_management.modules.gosb_normalization import normalize_detailed_report
from backend.app.data_management.services.file_storage import file_storage
from backend.app.common.config.column_names import COLUMNS


class DataManager:
    """
    Центральный менеджер данных для управления загруженными и очищенными отчетами.

    Обеспечивает доступ к данным, используя файловое хранилище как источник путей.
    Реализует хранение raw, cleaned, derived и processed данных в памяти.
    """

    def __init__(self):
        """Инициализация внутренних хранилищ данных."""
        # Сырые загруженные данные
        self._raw_data: Dict[str, Optional[pd.DataFrame]] = {
            "detailed_report": None,
            "documents_report": None
        }

        # Очищенные данные после обработки
        self._cleaned_data: Dict[str, Optional[pd.DataFrame]] = {
            "detailed_report": None,
            "documents_report": None
        }

        # Производные данные (derived)
        self._derived_data: Dict[str, Optional[pd.DataFrame]] = {
            "detailed_rainbow": None
        }

        # Кэшированные данные (colored)
        self._cached_data: Dict[str, Optional[pd.DataFrame]] = {
            "detailed_colored": None
        }

        # Обработанные данные, используемые другими модулями
        self._processed_data: Dict[str, Optional[pd.DataFrame]] = {
            "lawsuit_staged": None,
            "order_staged": None,
            "documents_processed": None,
            "tasks": None
        }

    def load_detailed_report(self) -> pd.DataFrame:
        """
        Загружает и очищает детальный отчет из хранилища файлов.

        Returns:
            pd.DataFrame: Очищенный DataFrame с нормализованными значениями

        Raises:
            ValueError: Если файл не найден в хранилище
        """
        if self._cleaned_data["detailed_report"] is not None:
            return self._cleaned_data["detailed_report"]

        # Получение файла из хранилища
        file = file_storage.get("current_detailed_report")
        if file is None:
            raise ValueError("Файл 'current_detailed_report' не загружен")

        filepath = file.server_path
        print("📥 Загрузка и очистка детального отчета...")

        # Загрузка исходного файла
        raw_df = load_excel_data(filepath)

        # Очистка и приведение данных к стандартной форме
        cleaned_df = clean_detailed(raw_df)

        # Нормализация метода защиты: упрощенное производство → исковое
        from backend.app.common.config.column_names import VALUES
        method_col = COLUMNS["METHOD_OF_PROTECTION"]
        simplified_value = VALUES["SIMPLIFIED_PRODUCTION"]
        claim_value = VALUES["CLAIM_PROCEEDINGS"]

        if method_col in cleaned_df.columns:
            cleaned_df[method_col] = cleaned_df[method_col].replace(
                simplified_value, claim_value
            )

        # Применение дополнительной нормализации
        normalized_df = normalize_detailed_report(cleaned_df)

        # Сохранение raw и cleaned данных
        self._raw_data["detailed_report"] = raw_df
        self._cleaned_data["detailed_report"] = normalized_df

        return normalized_df

    def load_documents_report(self) -> pd.DataFrame:
        """
        Загружает и очищает отчет документов из хранилища файлов.

        Returns:
            pd.DataFrame: Очищенный DataFrame документов

        Raises:
            ValueError: Если файл не найден в хранилище
        """
        if self._cleaned_data["documents_report"] is not None:
            return self._cleaned_data["documents_report"]

        # Получение файла из хранилища
        file = file_storage.get("documents_report")
        if file is None:
            raise ValueError("Файл 'documents_report' не загружен")

        filepath = file.server_path
        print("📥 Загрузка и очистка отчета документов...")

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
        from backend.app.common.config.column_names import VALUES
        method_col = COLUMNS["METHOD_OF_PROTECTION"]
        simplified_value = VALUES["SIMPLIFIED_PRODUCTION"]
        claim_value = VALUES["CLAIM_PROCEEDINGS"]

        if method_col in cleaned_df.columns:
            cleaned_df[method_col] = cleaned_df[method_col].replace(
                simplified_value, claim_value
            )

        # Сохранение raw и cleaned данных
        self._raw_data["documents_report"] = raw_df
        self._cleaned_data["documents_report"] = cleaned_df

        return cleaned_df

    def get_detailed_data(self) -> Optional[pd.DataFrame]:
        """Возвращает очищенный детальный отчет."""
        return self._cleaned_data["detailed_report"]

    def get_documents_data(self) -> Optional[pd.DataFrame]:
        """Возвращает очищенный отчет документов."""
        return self._cleaned_data["documents_report"]

    def get_both_data(self) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """Возвращает оба очищенных отчета (детальный + документы)."""
        return self.get_detailed_data(), self.get_documents_data()

    def clear_data(self, data_type: str = "all"):
        """
        Очищает загруженные данные из памяти, включая кэш и derived данные.

        Args:
            data_type (str): Тип данных ('detailed', 'documents', 'all')
        """
        if data_type in ["detailed", "all"]:
            self._cleaned_data["detailed_report"] = None
            self._raw_data["detailed_report"] = None
            self._derived_data["detailed_rainbow"] = None
            self._cached_data["detailed_colored"] = None

        if data_type in ["documents", "all"]:
            self._cleaned_data["documents_report"] = None
            self._raw_data["documents_report"] = None

        gc.collect()
        print("🧹 Память очищена")

    def reload_data(self, data_type: str) -> pd.DataFrame:
        """
        Перезагружает данные указанного типа из хранилища файлов.

        Args:
            data_type (str): 'detailed' или 'documents'

        Returns:
            pd.DataFrame: Перезагруженные данные

        Raises:
            ValueError: При некорректном типе данных
        """
        self.clear_data(data_type)

        if data_type == "detailed":
            return self.load_detailed_report()
        elif data_type == "documents":
            return self.load_documents_report()
        else:
            raise ValueError("Неверный тип данных")

    def set_processed_data(self, data_type: str, dataframe: pd.DataFrame):
        """
        Сохраняет обработанные данные для использования другими модулями.

        Args:
            data_type (str): Тип данных ("lawsuit_staged", "order_staged",
                             "documents_processed", "tasks")
            dataframe (pd.DataFrame): Обработанные данные

        Raises:
            ValueError: При указании неизвестного типа данных
        """
        if data_type in self._processed_data:
            self._processed_data[data_type] = dataframe
        else:
            raise ValueError(f"Неверный тип данных: {data_type}")

    def get_processed_data(self, data_type: str) -> Optional[pd.DataFrame]:
        """
        Возвращает обработанные данные указанного типа.

        Args:
            data_type (str): Тип данных ("lawsuit_staged", "order_staged",
                             "documents_processed", "tasks")

        Returns:
            Optional[pd.DataFrame]: Обработанные данные или None
        """
        return self._processed_data.get(data_type)

    def clear_processed_data(self, data_type: str = "all"):
        """
        Очищает обработанные данные из памяти.

        Args:
            data_type (str): Тип данных или "all" для очистки всех
        """
        if data_type == "all":
            for key in self._processed_data:
                self._processed_data[key] = None
            print("🧹 Все обработанные данные очищены")
        elif data_type in self._processed_data:
            self._processed_data[data_type] = None
            print(f"🧹 Очищены обработанные данные: {data_type}")

    def set_rainbow_data(self, derived_df: pd.DataFrame, cached_df: pd.DataFrame) -> None:
        """
        Сохраняет рассчитанные радугой данные.

        Args:
            derived_df: производные данные цветовой классификации
            cached_df: кэшированные данные для быстрой фильтрации
        """
        self._derived_data["detailed_rainbow"] = derived_df
        self._cached_data["detailed_colored"] = cached_df

    def get_colored_data(self, data_type: str) -> Optional[pd.DataFrame]:
        """
        Возвращает кэшированный DataFrame с цветовой информацией.
        Данные должны быть предварительно рассчитаны через /api/rainbow/analyze.

        Args:
            data_type (str): Поддерживается только "detailed"

        Returns:
            Optional[pd.DataFrame]: Кэшированные данные или None, если не рассчитаны
        """
        if data_type != "detailed":
            return None

        return self._cached_data.get("detailed_colored")

    def get_derived_data(self, data_type: str) -> Optional[pd.DataFrame]:
        """
        Возвращает производные данные цветовой классификации.
        Данные должны быть предварительно рассчитаны через /api/rainbow/analyze.

        Args:
            data_type (str): Поддерживается только "detailed"

        Returns:
            Optional[pd.DataFrame]: Производные данные или None, если не рассчитаны
        """
        if data_type != "detailed":
            return None

        return self._derived_data.get("detailed_rainbow")

# Глобальный экземпляр для использования во всем приложении
data_manager = DataManager()