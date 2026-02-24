#backend/app/common/modules/data_manager.py
"""
Центральный менеджер данных для управления загруженными и обработанными отчетами.

Обеспечивает:
- Загрузку и кэширование данных различных типов
- Нормализацию и очистку данных
- Управление памятью и состоянием данных
- Предоставление данных другим модулям системы
"""

import pandas as pd
from typing import Dict, Optional, Tuple
from datetime import timedelta, datetime
import gc

from backend.app.common.modules.data_import import load_excel_data
from backend.app.common.modules.data_clean_detailed import clean_data as clean_detailed
from backend.app.common.modules.data_clean_documents import clean_documents_data as clean_documents
from backend.app.rainbow.modules.rainbow_classifier import RainbowClassifier
from backend.app.common.config.column_names import COLUMNS
from backend.app.common.modules.gosb_normalization import normalize_detailed_report

class DataManager:
    """
    Центральный менеджер данных для управления загруженными и очищенными отчетами.

    Гарантирует однократную загрузку и очистку файлов, предоставляет интерфейс
    для доступа к данным в различных состояниях обработки.
    """

    def __init__(self):
        """Инициализация менеджера данных с пустыми хранилищами."""
        # Очищенные данные после обработки
        self._cleaned_data: Dict[str, Optional[pd.DataFrame]] = {
            "detailed_report": None,
            "documents_report": None
        }
        # Исходные сырые данные
        self._raw_data: Dict[str, Optional[pd.DataFrame]] = {
            "detailed_report": None,
            "documents_report": None
        }
        # Результаты сложной обработки данных
        self._processed_data: Dict[str, Optional[pd.DataFrame]] = {
            "lawsuit_staged": None,  # Результаты build_new_table() для искового производства
            "order_staged": None,  # Результаты для приказного производства
            "documents_processed": None,  # Обработанные документы
            "tasks": None  # Рассчитанные задачи
        }
        #Переход cleaned&derived&cached логику
        self._derived_data: Dict[str, Optional[pd.DataFrame]] = {
            "detailed_rainbow": None
        }
        self._cached_data: Dict[str, Optional[pd.DataFrame]] = {
            "detailed_colored": None
        }

    def load_detailed_report(self, filepath: str) -> pd.DataFrame:
        """
        Загружает и очищает детальный отчет.

        Args:
            filepath (str): Путь к файлу детального отчета

        Returns:
            pd.DataFrame: Очищенный DataFrame с добавленным столбцом цвета

        Raises:
            Exception: При ошибках загрузки или обработки файла
        """
        if self._cleaned_data["detailed_report"] is not None:
            return self._cleaned_data["detailed_report"]

        print("📥 Загрузка и очистка детального отчета...")
        raw_df = load_excel_data(filepath)
        cleaned_df = clean_detailed(raw_df)

        # Нормализация данных: замена "Упрощенное производство" на "Исковое производство"
        from backend.app.common.config.column_names import COLUMNS, VALUES
        method_col = COLUMNS["METHOD_OF_PROTECTION"]
        simplified_value = VALUES["SIMPLIFIED_PRODUCTION"]
        claim_value = VALUES["CLAIM_PROCEEDINGS"]

        if method_col in cleaned_df.columns:
            cleaned_df[method_col] = cleaned_df[method_col].replace(
                simplified_value, claim_value
            )
        normalized_df = normalize_detailed_report(cleaned_df)

        self._raw_data["detailed_report"] = raw_df
        self._cleaned_data["detailed_report"] = normalized_df

        return normalized_df

    def load_documents_report(self, filepath: str) -> pd.DataFrame:
        """
        Загружает и очищает отчет документов.

        Args:
            filepath (str): Путь к файлу отчета документов

        Returns:
            pd.DataFrame: Очищенный DataFrame документов

        Raises:
            Exception: При ошибках загрузки или обработки файла
        """
        if self._cleaned_data["documents_report"] is not None:
            return self._cleaned_data["documents_report"]

        print("📥 Загрузка и очистка отчета документов...")
        raw_df = load_excel_data(filepath)
        cleaned_df = clean_documents(raw_df)

        # Нормализация 1: переименование колонки суда для унификации
        from backend.app.common.config.column_names import COLUMNS
        court_alt_name = COLUMNS["COURT_NAME"]
        court_std_name = COLUMNS["COURT"]

        if court_alt_name in cleaned_df.columns and court_std_name not in cleaned_df.columns:
            cleaned_df.rename(columns={court_alt_name: court_std_name}, inplace=True)

        # Нормализация 2: замена "Упрощенное производство" на "Исковое производство"
        from backend.app.common.config.column_names import VALUES
        method_col = COLUMNS["METHOD_OF_PROTECTION"]
        simplified_value = VALUES["SIMPLIFIED_PRODUCTION"]
        claim_value = VALUES["CLAIM_PROCEEDINGS"]

        if method_col in cleaned_df.columns:
            cleaned_df[method_col] = cleaned_df[method_col].replace(
                simplified_value, claim_value
            )

        # Передача текущей даты один раз для всех расчетов
        today = datetime.now().date()

        self._raw_data["documents_report"] = raw_df
        self._cleaned_data["documents_report"] = cleaned_df

        return cleaned_df

    def get_detailed_data(self) -> Optional[pd.DataFrame]:
        """
        Возвращает очищенный детальный отчет.

        Returns:
            Optional[pd.DataFrame]: DataFrame детального отчета или None
        """
        return self._cleaned_data["detailed_report"]

    def get_documents_data(self) -> Optional[pd.DataFrame]:
        """
        Возвращает очищенный отчет документов.

        Returns:
            Optional[pd.DataFrame]: DataFrame отчета документов или None
        """
        return self._cleaned_data["documents_report"]

    def get_both_data(self) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """
        Возвращает оба очищенных отчета.

        Returns:
            Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
                Кортеж (детальный_отчет, отчет_документов)
        """
        return self.get_detailed_data(), self.get_documents_data()

    def is_loaded(self, data_type: str) -> bool:
        """
        Проверяет загрузку данных указанного типа.

        Args:
            data_type (str): Тип данных - 'detailed', 'documents', 'both'

        Returns:
            bool: True если данные загружены, иначе False
        """
        if data_type == "detailed":
            return self._cleaned_data["detailed_report"] is not None
        elif data_type == "documents":
            return self._cleaned_data["documents_report"] is not None
        elif data_type == "both":
            return (self._cleaned_data["detailed_report"] is not None and
                    self._cleaned_data["documents_report"] is not None)
        return False

    def clear_data(self, data_type: str = "all"):
        """
        Освобождает память от данных указанного типа.

        Args:
            data_type (str): Тип данных - 'detailed', 'documents', 'all'
        """
        if data_type in ["detailed", "all"]:
            self._cleaned_data["detailed_report"] = None
            self._raw_data["detailed_report"] = None
            # invalidate derived & cached
            self._derived_data["detailed_rainbow"] = None
            self._cached_data["detailed_colored"] = None

        if data_type in ["documents", "all"]:
            self._cleaned_data["documents_report"] = None
            self._raw_data["documents_report"] = None

        gc.collect()
        print("🧹 Память очищена")

    def reload_data(self, filepath: str, data_type: str) -> pd.DataFrame:
        """
        Перезагружает данные указанного типа.

        Args:
            filepath (str): Путь к файлу для загрузки
            data_type (str): Тип данных - 'detailed' или 'documents'

        Returns:
            pd.DataFrame: Перезагруженные данные

        Raises:
            ValueError: При указании неизвестного типа данных
        """
        self.clear_data(data_type)

        if data_type == "detailed":
            return self.load_detailed_report(filepath)
        elif data_type == "documents":
            return self.load_documents_report(filepath)
        else:
            raise ValueError("Неверный тип данных. Используйте 'detailed' или 'documents'")

    def get_colored_data(self, data_type: str) -> Optional[pd.DataFrame]:
        """
        Возвращает кэшированный DataFrame с цветовой информацией
        для детального отчёта.

        При отсутствии кэша:
        - вычисляет derived-данные через RainbowClassifier,
        - строит цветной кэш на основе cleaned DataFrame,
        - сохраняет результат во внутренний кэш.

        Args:
            data_type (str): Тип данных, поддерживается только "detailed".

        Returns:
            Optional[pd.DataFrame]: Кэшированный DataFrame с цветами
            или None, если тип данных не поддерживается.
        """
        if data_type != "detailed":
            return None

        cached = self._cached_data.get("detailed_colored")
        if cached is not None:
            return cached

        # Если кэш отсутствует — пересчитываем derived и строим кэш
        derived = RainbowClassifier.create_derived_rainbow(self._cleaned_data["detailed_report"])
        self._cached_data["detailed_colored"] = RainbowClassifier.build_colored_cache(
            self._cleaned_data["detailed_report"], derived
        )

        return self._cached_data.get("detailed_colored")

    def set_processed_data(self, data_type: str, dataframe: pd.DataFrame):
        """
        Сохраняет обработанные данные для использования другими модулями.

        Args:
            data_type (str): Тип данных - "lawsuit_staged", "order_staged",
                           "documents_processed", "tasks"
            dataframe (pd.DataFrame): Обработанные данные

        Raises:
            ValueError: При указании неизвестного типа данных
        """
        if data_type in self._processed_data:
            self._processed_data[data_type] = dataframe
            print(f"✅ Обработанные данные сохранены: {data_type}")
        else:
            raise ValueError(f"Неверный тип данных: {data_type}")

    def get_processed_data(self, data_type: str) -> Optional[pd.DataFrame]:
        """
        Возвращает обработанные данные указанного типа.

        Args:
            data_type (str): Тип данных - "lawsuit_staged", "order_staged",
                           "documents_processed", "tasks"

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

# Глобальный экземпляр для использования во всем приложении
data_manager = DataManager()