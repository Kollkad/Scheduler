# backend/app/common/modules/data_clean_detailed.py
"""
Модуль очистки данных детального отчета.

Выполняет предобработку сырых данных Excel:
- Определение заголовков таблицы
- Удаление служебных строк и пустых столбцов
- Обрезка данных по маркеру итогов
"""

import pandas as pd


def clean_data(raw_df):
    """
    Очистка данных детального отчета с использованием векторных операций.

    Args:
        raw_df (pd.DataFrame): Сырые данные из Excel файла

    Returns:
        pd.DataFrame: Очищенный DataFrame с корректными заголовками

    Raises:
        ValueError: Если не найдена строка с маркером '№ п/п'
    """
    # Векторизованный поиск '№ п/п' по ВСЕМУ DataFrame за одну операцию
    str_df = raw_df.astype(str)
    mask = (str_df == "№ п/п").any(axis=1)

    if not mask.any():
        raise ValueError("Не найдена строка с '№ п/п'")

    start_row = mask.idxmax()

    # Установка заголовков с обработкой дубликатов
    headers = raw_df.iloc[start_row].reset_index(drop=True)
    cleaned = raw_df.iloc[start_row + 2:].copy()  # Пропуск заголовка и служебной строки
    cleaned.columns = headers
    cleaned = cleaned.loc[:, ~cleaned.columns.duplicated()]  # Удаление дублирующихся колонок

    # Векторизованный поиск 'Итого' - РАЗДЕЛЬНО по колонкам чтобы избежать ошибки выравнивания
    str_cleaned = cleaned.astype(str)
    total_mask = pd.Series(False, index=cleaned.index)

    # Поиск в каждой колонке отдельно и объединение масок
    for col in str_cleaned.columns:
        col_mask = (
                (str_cleaned[col] == "Итого:") |
                (str_cleaned[col] == "Итого") |
                (str_cleaned[col].str.startswith("Итого", na=False))
        )
        total_mask = total_mask | col_mask

    if total_mask.any():
        total_idx = total_mask.idxmax()
        cleaned = cleaned.loc[:total_idx - 1]  # Обрезка ДО строки с "Итого"
        print(f"Найдена строка 'Итого:' в строке {total_idx}, данные обрезаны")
    else:
        print("Строка 'Итого:' не найдена, работаем со всеми данными")

    # Удаление пустых колонок и сброс индекса
    cleaned = cleaned.dropna(axis=1, how='all').reset_index(drop=True)

    return cleaned