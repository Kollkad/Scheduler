# backend/app/common/modules/data_filter.py
"""
Модуль для фильтрации данных DataFrame.

Предоставляет функции для применения фильтров к данным и получения уникальных значений
для построения интерфейсов фильтрации.
"""
import pandas as pd
from typing import List, Dict
from .filter_factory import FilterFactory


def apply_filters(df: pd.DataFrame, filter_configs: List[Dict]) -> pd.DataFrame:
    """
    Последовательное применение всех активных фильтров к DataFrame.

    Args:
        df (pd.DataFrame): Исходный DataFrame для фильтрации
        filter_configs (List[Dict]): Список конфигураций фильтров

    Returns:
        pd.DataFrame: Отфильтрованный DataFrame после применения всех активных фильтров
    """
    # Создание копии DataFrame для избежания изменения исходных данных
    filtered_df = df.copy()

    # Последовательное применение каждого активного фильтра
    for config in filter_configs:
        if config.get('enabled', False):
            filter_obj = FilterFactory.create_filter(config)
            filtered_df = filter_obj.apply(filtered_df)

    return filtered_df


def get_unique_values(df: pd.DataFrame, column_name: str) -> List:
    """
    Получение списка уникальных значений в столбце для выпадающих списков в UI.

    Args:
        df (pd.DataFrame): DataFrame для анализа
        column_name (str): Название колонки для получения уникальных значений

    Returns:
        List: Список уникальных значений из указанной колонки
    """
    return df[column_name].dropna().unique().tolist()