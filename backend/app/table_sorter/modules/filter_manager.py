# backend/app/table_sorter/modules/filter_manager.py
"""
Модуль управления фильтрами для табличных данных.

Обеспечивает получение уникальных значений для фильтрации данных,
управление настройками фильтров и предоставление метаинформации
о доступных фильтрах для фронтенд-интерфейса.
"""

from typing import Dict, List, Any
import pandas as pd
from backend.app.common.config.column_names import COLUMNS
from backend.app.data_management.modules.normalized_data_manager import normalized_manager


class FilterSettings:
    """
    Класс управления настройками и опциями фильтров.

    Предоставляет функциональность для получения уникальных значений
    из колонок данных и управления метаинформацией о фильтрах.
    """

    def __init__(self):
        """Инициализация с экземпляром нормализованного менеджера данных."""
        self._normalized_manager = normalized_manager

        # Маппинг системных имен фильтров к реальным колонкам в _source_data
        self._filter_column_mapping = {
            "gosb": COLUMNS["GOSB"],
            "responsibleExecutor": COLUMNS["RESPONSIBLE_EXECUTOR"],
            "courtReviewingCase": COLUMNS["COURT"],
            "courtProtectionMethod": COLUMNS["METHOD_OF_PROTECTION"],
            "currentPeriodColor": COLUMNS["CURRENT_PERIOD_COLOR"],
            "caseCode": COLUMNS["CASE_CODE"],
            "caseStatus": COLUMNS["CASE_STATUS"],
        }

        # Список всех доступных системных имен фильтров
        self._available_filter_names = [
            "gosb", "responsibleExecutor", "courtReviewingCase",
            "courtProtectionMethod", "currentPeriodColor"
        ]

    def get_filter_options(self, column_names: List[str] = None) -> Dict[str, List[Dict[str, str]]]:
        """
        Возвращает уникальные значения для указанных колонок.

        Извлекает отсортированные уникальные значения из данных для использования
        в интерфейсе фильтрации. Если колонки не указаны, возвращает все доступные фильтры.

        Args:
            column_names (List[str], optional): Список системных имен фильтров для обработки

        Returns:
            Dict[str, List[Dict[str, str]]]: Словарь с опциями фильтров в формате
                                           {filter_name: [{"name": value, "label": value}]}
        """
        # Получение данных из NormalizedDataManager
        df = self._normalized_manager.get_cases_data()

        if df is None or df.empty:
            return self._get_empty_options()

        # Очистка DataFrame от дубликатов колонок
        df = self._clean_dataframe(df)

        options = {}

        # Определение колонок для обработки
        if column_names:
            columns_to_process = column_names
        else:
            columns_to_process = self._available_filter_names

        for filter_name in columns_to_process:
            # Получение реального имени колонки из маппинга
            column_name = self._filter_column_mapping.get(filter_name)

            if not column_name:
                options[filter_name] = []
                continue

            if column_name in df.columns:
                try:
                    unique_values = self._get_unique_values(df, column_name)
                    options[filter_name] = unique_values
                except Exception as e:
                    print(f"❌ Ошибка обработки колонки {column_name}: {e}")
                    options[filter_name] = []
            else:
                print(f"⚠️ Колонка '{column_name}' не найдена в данных")
                options[filter_name] = []

        return options

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Очищает DataFrame от дубликатов колонок.

        Args:
            df (pd.DataFrame): Исходный DataFrame для очистки

        Returns:
            pd.DataFrame: Очищенный DataFrame
        """
        if df.columns.duplicated().any():
            df = df.loc[:, ~df.columns.duplicated()]
        return df

    def _get_unique_values(self, df: pd.DataFrame, column_name: str) -> List[Dict[str, str]]:
        """
        Извлекает уникальные значения из указанной колонки.

        Выполняет очистку данных, удаление пустых значений и сортировку
        для предоставления корректных опций фильтрации.

        Args:
            df (pd.DataFrame): DataFrame с данными
            column_name (str): Название колонки для извлечения значений

        Returns:
            List[Dict[str, str]]: Список уникальных значений в формате для фронтенда
        """
        # Извлечение колонки с удалением NaN
        series = df[column_name].dropna()

        if series.empty:
            return []

        # Преобразование в строки
        series = series.astype(str)

        # Удаление пустых строк и лишних пробелов
        series = series[series.str.strip() != '']
        series = series.str.strip()

        if series.empty:
            return []

        # Получение уникальных значений и сортировка
        unique_values = series.unique()
        sorted_values = sorted(unique_values, key=lambda x: str(x))

        # Форматирование в структуру для фронтенда
        return [{"name": str(val), "label": str(val)} for val in sorted_values]

    def _get_empty_options(self) -> Dict[str, List]:
        """
        Возвращает пустые опции для всех фильтров.

        Returns:
            Dict[str, List]: Словарь с пустыми списками для всех системных имен фильтров
        """
        return {name: [] for name in self._available_filter_names}

    def get_available_filters(self) -> List[Dict[str, str]]:
        """
        Возвращает метаинформацию о доступных фильтрах.

        Returns:
            List[Dict[str, str]]: Список доступных фильтров с метаданными
        """
        return [
            {
                "name": COLUMNS["GOSB"],
                "type": "dynamic",
                "column": "gosb"
            },
            {
                "name": COLUMNS["RESPONSIBLE_EXECUTOR"],
                "type": "dynamic",
                "column": "responsibleExecutor"
            },
            {
                "name": COLUMNS["COURT"],
                "type": "dynamic",
                "column": "courtReviewingCase"
            },
            {
                "name": COLUMNS["METHOD_OF_PROTECTION"],
                "type": "dynamic",
                "column": "courtProtectionMethod"
            },
            {
                "name": COLUMNS["CURRENT_PERIOD_COLOR"],
                "type": "dynamic",
                "column": "currentPeriodColor"
            }
        ]


# Глобальный экземпляр для использования во всем приложении
filter_settings = FilterSettings()