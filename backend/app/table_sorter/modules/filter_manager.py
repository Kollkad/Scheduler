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
from backend.app.common.modules.data_manager import data_manager


class FilterSettings:
    """
    Класс управления настройками и опциями фильтров.

    Предоставляет функциональность для получения уникальных значений
    из колонок данных и управления метаинформацией о фильтрах.
    """

    def __init__(self):
        # Маппинг системных имен фильтров на названия колонок в данных
        self.column_mapping = {
            "gosb": COLUMNS["GOSB"],
            "responsibleExecutor": COLUMNS["RESPONSIBLE_EXECUTOR"],
            "courtReviewingCase": COLUMNS["COURT"],
            "courtProtectionMethod": COLUMNS["METHOD_OF_PROTECTION"],
            "currentPeriodColor": "Цвет (текущий период)"
        }

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
        df = data_manager.get_colored_data("detailed")
        if df is None or df.empty:
            return self._get_empty_options()

        # Очистка DataFrame от дубликатов колонок
        df = self._clean_dataframe(df)

        options = {}

        # Определение колонок для обработки
        columns_to_process = column_names if column_names else self.column_mapping.keys()

        for filter_name in columns_to_process:
            column_name = self.column_mapping.get(filter_name)

            if not column_name:
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
        Очищает DataFrame от дубликатов колонок и нестандартных значений.

        Args:
            df (pd.DataFrame): Исходный DataFrame для очистки

        Returns:
            pd.DataFrame: Очищенный DataFrame
        """
        # Удаление дубликатов колонок
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
        # Извлечение колонки с удалением NaN и преобразованием в строки
        series = df[column_name].dropna().astype(str)

        # Удаление пустых строк и лишних пробелов
        series = series[series.str.strip() != '']
        series = series.str.strip()

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
        return {key: [] for key in self.column_mapping.keys()}

    def get_available_filters(self) -> List[Dict[str, str]]:
        """
        Возвращает метаинформацию о доступных фильтрах.

        Provides information about filter names, types, and corresponding
        database columns for frontend configuration.

        Returns:
            List[Dict[str, str]]: Список словарей с метаинформацией о фильтрах
        """
        return [
            {"name": "ГОСБ", "type": "dynamic", "column": COLUMNS["GOSB"]},
            {"name": "Ответственный исполнитель", "type": "dynamic", "column": COLUMNS["RESPONSIBLE_EXECUTOR"]},
            {"name": "Суд, рассматривающий дело", "type": "dynamic", "column": COLUMNS["COURT"]},
            {"name": "Способ судебной защиты", "type": "dynamic", "column": COLUMNS["METHOD_OF_PROTECTION"]},
            {"name": "Цвет (текущий период)", "type": "dynamic", "column": "Цвет (текущий период)"}
        ]


# Глобальный экземпляр для использования во всем приложении
filter_settings = FilterSettings()