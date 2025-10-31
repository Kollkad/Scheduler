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
    Очистка данных детального отчета.

    Args:
        raw_df (pd.DataFrame): Сырые данные из Excel файла

    Returns:
        pd.DataFrame: Очищенный DataFrame с корректными заголовками

    Raises:
        ValueError: Если не найдена строка с маркером '№ п/п'
    """
    # Поиск строки с маркером '№ п/п' для определения начала таблицы
    start_row = None
    for col_idx in range(raw_df.shape[1]):
        col_data = raw_df.iloc[:, col_idx].astype(str)
        mask = col_data.str.strip() == "№ п/п"
        if mask.any():
            start_row = mask.idxmax()
            break

    if start_row is None:
        raise ValueError("Не найдена строка с '№ п/п'")

    # Установка заголовков таблицы из найденной строки
    headers = raw_df.iloc[start_row].copy()
    df_with_headers = raw_df.iloc[start_row:].copy()
    df_with_headers.columns = headers

    # Удаление строки заголовков и следующей служебной строки
    cleaned = df_with_headers.drop([start_row, start_row + 1]).copy()

    # Поиск строки с маркером итогов для обрезки данных
    total_idx = None

    # Поиск маркера итогов во всех столбцах
    for col_idx in range(cleaned.shape[1]):
        col_data = cleaned.iloc[:, col_idx].astype(str).str.strip().str.lower()

        # Объединение масок для различных вариантов написания "Итого"
        mask1 = col_data == "итого:"
        mask2 = col_data == "итого"
        mask3 = col_data.str.startswith("итого")

        total_mask = mask1 | mask2 | mask3

        if total_mask.any():
            total_idx = cleaned[total_mask].index[0]
            break

    # Обрезка данных до строки с маркером итогов
    if total_idx is not None:
        cleaned = cleaned.loc[:total_idx - 1]
        print(f"✅ Найдена строка 'Итого:' в строке {total_idx}, данные обрезаны")
    else:
        print("⚠️ Строка 'Итого:' не найдена, работаем со всеми данными")

    # Удаление полностью пустых столбцов
    cleaned = cleaned.dropna(axis=1, how='all')

    return cleaned.reset_index(drop=True)