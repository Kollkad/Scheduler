# backend/app/common/modules/data_clean_detailed.py
"""
Модуль очистки данных детального отчета.

Реализует предобработку сырых данных Excel:
- Поиск строки с заголовками таблицы
- Определение и удаление служебной строки нумерации (при наличии)
- Обрезку данных по маркеру итогов
- Удаление полностью пустых колонок без названий
"""

import pandas as pd


def clean_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Выполняет очистку данных детального отчета.

    Функция определяет строку с заголовками таблицы по маркеру "№ п/п",
    корректно обрабатывает наличие или отсутствие служебной строки нумерации,
    а также обрезает данные по строке итогов.

    Пустые колонки сохраняются, если у них присутствует название в заголовке.

    Args:
        raw_df (pd.DataFrame): Сырые данные, считанные из Excel файла

    Returns:
        pd.DataFrame: Очищенный DataFrame с установленными заголовками

    Raises:
        ValueError: Если в данных отсутствует строка с маркером "№ п/п"
    """
    # Приведение значений к строковому виду для поиска строки заголовков
    str_df = raw_df.astype(str)
    mask = (str_df == "№ п/п").any(axis=1)

    # Проверка наличия строки заголовков
    if not mask.any():
        raise ValueError("Не найдена строка с '№ п/п'")

    start_row = mask.idxmax()
    headers = raw_df.iloc[start_row].reset_index(drop=True)

    # Проверка строки после заголовков на наличие служебной нумерации
    first_data_row = raw_df.iloc[start_row + 1]
    first_values = first_data_row.iloc[:3]
    numeric_count = pd.to_numeric(first_values, errors='coerce').notna().sum()

    # Определение начальной строки данных
    if numeric_count >= 2:
        cleaned = raw_df.iloc[start_row + 2:].copy()
    else:
        cleaned = raw_df.iloc[start_row + 1:].copy()

    # Установка заголовков и удаление дублирующихся колонок
    cleaned.columns = headers
    cleaned = cleaned.loc[:, ~cleaned.columns.duplicated()]

    # Поиск строки итогов
    str_cleaned = cleaned.astype(str)
    total_mask = pd.Series(False, index=cleaned.index)

    for col in str_cleaned.columns:
        col_mask = (
            (str_cleaned[col] == "Итого:") |
            (str_cleaned[col] == "Итого") |
            (str_cleaned[col].str.startswith("Итого", na=False))
        )
        total_mask = total_mask | col_mask

    if total_mask.any():
        total_idx = total_mask.idxmax()
        cleaned = cleaned.loc[:total_idx - 1]
        print(f"Найдена строка 'Итого:' в строке {total_idx}, данные обрезаны")
    else:
        print("Строка 'Итого:' не найдена, работаем со всеми данными")

    # Удаление колонок без названия и без данных
    valid_columns = [
        col for col in cleaned.columns
        if not (
            (pd.isna(col) or str(col).strip() == "") and
            cleaned[col].isna().all()
        )
    ]
    cleaned = cleaned[valid_columns]

    # Сброс индекса
    cleaned = cleaned.reset_index(drop=True)

    return cleaned