# backend/app/common/modules/data_clean_documents.py
"""
Модуль очистки данных отчета по полученным и переданным документам.

Выполняет предобработку данных документов:
- Загрузка данных с нужного листа Excel
- Определение строки заголовков по маркеру 'Код передачи'
- Удаление полностью пустых колонок без заголовков
- Сохранение колонок с заголовками, даже если данные пустые
"""

import pandas as pd


def clean_documents_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Очистка данных отчета документов.

    Args:
        raw_df (pd.DataFrame): Сырые данные из Excel

    Returns:
        pd.DataFrame: Очищенный DataFrame с корректными заголовками

    Raises:
        ValueError: Если не найдена строка с маркером 'Код передачи'
    """
    str_df = raw_df.astype(str)
    mask = (str_df == "Код передачи").any(axis=1)

    if not mask.any():
        raise ValueError("Не найдена строка с 'Код передачи'")

    start_row = mask.idxmax()
    headers = raw_df.iloc[start_row].reset_index(drop=True)

    cleaned = raw_df.iloc[start_row + 1:].copy()
    cleaned.columns = headers
    cleaned = cleaned.loc[:, ~cleaned.columns.duplicated()]

    # Удаление только полностью пустых колонок без заголовков
    valid_columns = [
        col for col in cleaned.columns
        if not ((pd.isna(col) or str(col).strip() == "") and cleaned[col].isna().all())
    ]
    cleaned = cleaned[valid_columns].reset_index(drop=True)

    return cleaned


def load_and_clean_documents_excel(filepath: str) -> pd.DataFrame:
    """
    Загрузка и очистка данных из Excel для отчета 'Документы'.

    Args:
        filepath (str): Путь к файлу Excel

    Returns:
        pd.DataFrame: Очищенный DataFrame
    """
    try:
        raw_df = pd.read_excel(filepath, sheet_name='Отчёт', header=None)
    except ValueError:
        raw_df = pd.read_excel(filepath, header=None)
        print("Предупреждение: лист 'Отчёт' не найден, используется первый лист")

    return clean_documents_data(raw_df)