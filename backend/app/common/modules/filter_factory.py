"""
Фабрика фильтров для обработки данных DataFrame.

Модуль предоставляет классы для создания и применения различных типов фильтров
к pandas DataFrame с поддержкой расширяемой архитектуры.
"""
import pandas as pd
from typing import Dict, Any


class FilterFactory:
    """
    Фабрика для создания фильтров различных типов.

    Обеспечивает централизованное создание объектов фильтров на основе конфигурации.
    """

    @staticmethod
    def create_filter(filter_config: Dict[str, Any]):
        """
        Создание фильтра на основе конфигурации.

        Args:
            filter_config (Dict[str, Any]): Конфигурация фильтра с обязательным
                                          полем 'type'

        Returns:
            BaseFilter: Экземпляр фильтра соответствующего типа

        Raises:
            ValueError: Если указан неизвестный тип фильтра
        """
        filter_type = filter_config.get('type', 'exact_match')

        if filter_type == 'exact_match':
            return ExactMatchFilter(filter_config)
        # Здесь можно добавить другие типы фильтров по мере необходимости

        raise ValueError(f"Unknown filter type: {filter_type}")


class BaseFilter:
    """
    Базовый класс для всех фильтров.

    Определяет общий интерфейс и базовую функциональность для фильтров.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация базового фильтра.

        Args:
            config (Dict[str, Any]): Конфигурация фильтра с обязательными полями:
                                   - column: название колонки для фильтрации
                                   - enabled: флаг активности (опционально)
        """
        self.config = config
        self.column = config['column']
        self.enabled = config.get('enabled', False)

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Применение фильтра к DataFrame.

        Args:
            df (pd.DataFrame): Исходный DataFrame для фильтрации

        Returns:
            pd.DataFrame: Отфильтрованный DataFrame или исходный если фильтр отключен
        """
        if not self.enabled:
            return df
        return self._apply_filter(df)

    def _apply_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Внутренний метод для реализации конкретной логики фильтрации.

        Args:
            df (pd.DataFrame): Исходный DataFrame для фильтрации

        Returns:
            pd.DataFrame: Отфильтрованный DataFrame

        Raises:
            NotImplementedError: Должен быть реализован в дочерних классах
        """
        raise NotImplementedError


class ExactMatchFilter(BaseFilter):
    """
    Фильтр точного совпадения значений.

    Оставляет только строки, где значение в указанной колонке точно совпадает
    с заданным значением.
    """

    def _apply_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Применение фильтра точного совпадения.

        Args:
            df (pd.DataFrame): Исходный DataFrame для фильтрации

        Returns:
            pd.DataFrame: DataFrame с отфильтрованными строками по точному совпадению
        """
        value = self.config['value']
        return df[df[self.column] == value]