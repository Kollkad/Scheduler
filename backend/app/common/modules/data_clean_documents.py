# backend/app/common/modules/data_clean_documents.py
"""
Модуль очистки данных отчета типа 'Документы'.

Выполняет предобработку данных документов:
- Определение структуры таблицы по маркерам
- Загрузка данных с конкретных листов Excel
- Анализ структуры колонок документа
"""

from typing import Dict
import pandas as pd

def clean_documents_data(raw_df):
    """
    Очистка данных для отчета типа 'Документы'.

    Args:
        raw_df (pd.DataFrame): Сырые данные из Excel файла

    Returns:
        pd.DataFrame: Очищенный DataFrame с корректными заголовками

    Raises:
        ValueError: Если не найдена строка с маркером 'Код передачи'
    """
    # Поиск строки с маркером 'Код передачи' для определения начала таблицы
    start_row = None
    for idx, row in raw_df.iterrows():
        for cell_value in row:
            if str(cell_value).strip() == "Код передачи":
                start_row = idx
                break
        if start_row is not None:
            break

    if start_row is None:
        raise ValueError("Не найдена строка с 'Код передачи'")

    # Установка заголовков таблицы из найденной строки
    headers = raw_df.iloc[start_row].copy()
    df_with_headers = raw_df.iloc[start_row:].copy()
    df_with_headers.columns = headers

    # Удаление строки заголовков
    cleaned = df_with_headers.drop([start_row]).copy()

    # Удаление полностью пустых столбцов
    cleaned = cleaned.dropna(axis=1, how='all')

    return cleaned.reset_index(drop=True)


def load_and_clean_documents_excel(filepath):
    """
    Загрузка и очистка данных из Excel для отчета 'Документы'.

    Args:
        filepath (str): Путь к файлу Excel

    Returns:
        pd.DataFrame: Очищенный DataFrame с данными документов
    """
    try:
        # Приоритетная загрузка данных с листа 'Отчёт'
        raw_df = pd.read_excel(filepath, sheet_name='Отчёт', header=None)
    except ValueError:
        # Резервная загрузка с первого листа при отсутствии целевого
        raw_df = pd.read_excel(filepath, header=None)
        print("Предупреждение: Лист 'Отчёт' не найден, используется первый лист")

    return clean_documents_data(raw_df)


def get_documents_columns_info(filepath: str) -> Dict:
    """
    Анализ структуры колонок в отчете 'Документы'.

    Args:
        filepath (str): Путь к файлу Excel

    Returns:
        Dict: Информация о колонках или сообщение об ошибке
    """
    try:
        cleaned_df = load_and_clean_documents_excel(filepath)

        columns_info = {}
        for column in cleaned_df.columns:
            values = cleaned_df[column].dropna()
            columns_info[column] = {
                'total_values': len(values),
                'unique_values': values.nunique(),
                'is_unique': len(values) == values.nunique(),
                'data_type': str(cleaned_df[column].dtype)
            }

        return columns_info

    except Exception as e:
        return {"error": str(e)}