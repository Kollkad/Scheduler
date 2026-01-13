#backend/app.common.modules.utils.py
"""
Модуль утилитарных функций для обработки данных судебных дел.

Содержит вспомогательные функции для:
- Управления памятью
- Расчетов для визуализации данных
- Безопасного извлечения и преобразования данных
- Фильтрации дел по типам производства
- Оценки исключительных статусов дел
"""

import gc
import math
from typing import Any
import pandas as pd
from backend.app.common.config.column_names import COLUMNS, VALUES

def clear_memory(*objects):
    """
    Очистка памяти от указанных объектов.

    Args:
        *objects: Произвольное количество объектов для удаления
    """
    for obj in objects:
        del obj
    gc.collect()


def calculate_x_axis_max_value(counts: list) -> int:
    """
    Рассчитывает максимальное значение для оси X графика.

    Выполняет округление максимального количества дел в большую сторону до тысяч.

    Args:
        counts: Список значений количества дел для каждого столбца графика

    Returns:
        int: Максимальное значение для оси X, округленное до тысяч
    """
    if not counts:
        return 1000  # Значение по умолчанию при отсутствии данных

    max_count = max(counts)

    # Округление вверх до ближайшей тысячи
    if max_count <= 0:
        return 1000

    rounded_max = math.ceil(max_count / 1000) * 1000
    return rounded_max

def extract_value(value) -> str:
    """
    Безопасно извлекает значение из различных типов данных.

    Args:
        value: Любое значение или объект pandas (Series, DataFrame)

    Returns:
        str: Строковое представление значения или "Не указано"
    """
    if isinstance(value, (pd.Series, pd.DataFrame)):
        if len(value) > 0:
            first_val = value.iloc[0] if hasattr(value, "iloc") else value.values[0]
            return str(first_val) if pd.notna(first_val) else "Не указано"
        return "Не указано"

    return str(value) if pd.notna(value) else "Не указано"

def get_filing_date(row, use_all_fields: bool = True) -> pd.Timestamp | None:
    """
    Извлекает дату подачи документа из данных дела.

    Args:
        row: Строка данных дела
        use_all_fields (bool): Если True - проверяет все доступные поля дат,
                              если False - только основные поля подачи иска

    Returns:
        pd.Timestamp | None: Дата подачи или None при отсутствии данных
    """
    try:
        # Получение даты подачи из основных полей
        first_filing_date = row.get(COLUMNS["FIRST_LAWSUIT_FILING_DATE"])
        if pd.notna(first_filing_date):
            return pd.to_datetime(first_filing_date)

        filing_date = row.get(COLUMNS["LAWSUIT_FILING_DATE"])
        if pd.notna(filing_date):
            return pd.to_datetime(filing_date)

        # Проверка альтернативных полей только если разрешено
        if use_all_fields:
            alt_date = row.get(COLUMNS["LAST_REQUEST_DATE_IN_UP"])
            if pd.notna(alt_date):
                return pd.to_datetime(alt_date)

        # Возврат None при отсутствии данных во всех полях
        return None
    except Exception:
        # Возврат None при ошибках преобразования дат
        return None


def safe_get_column(row, column_name, default="no_data"):
    """
    Безопасно получает значение из колонки DataFrame.

    Выполняет проверку существования колонки и наличие значения.

    Args:
        row: Строка DataFrame
        column_name (str): Название колонки
        default: Значение по умолчанию если колонки нет или значение NaN

    Returns:
        Значение колонки или значение по умолчанию
    """
    try:
        # Проверка существования колонки в индексе строки
        if column_name not in row.index:
            return default

        # Получение значения из колонки
        value = row[column_name]

        # БОЛЕЕ АККУРАТНАЯ проверка на "пустоту"
        if value is None:
            return default

        if isinstance(value, (float, int)) and pd.isna(value):
            return default

        if isinstance(value, str) and value.strip() == "":
            return default

        # Для datetime специальная проверка
        if hasattr(value, 'strftime'):  # это datetime-like объект
            if pd.isna(value):
                return default

        return value
    except Exception as e:
        print(f"Ошибка в safe_get_column для колонки {column_name}: {e}")
        return default

def evaluate_exceptions_row(row) -> str:
    """
    Универсальная проверка на исключения по статусу дела.

    Определяет специальные статусы дел, которые требуют особой обработки
    и не подлежат стандартной проверке сроков. Используется как в исковом,
    так и в приказном производстве.

    Args:
        row: Строка данных дела

    Returns:
        str: Строковый идентификатор исключения или 'no_data'
    """
    try:
        # Получение текущего статуса дела
        current_status = row.get(COLUMNS["CASE_STATUS"])

        # Проверка различных типов исключительных статусов
        if current_status == VALUES["REOPENED"]:
            return "reopened"  # Дело возобновлено
        elif current_status == VALUES["COMPLAINT_FILED"]:
            return "complaint_filed"  # Подана жалоба
        elif current_status == VALUES["ERROR_DUBLICATE"]:
            return "error_dublicate"  # Дубликат или ошибка
        elif current_status == VALUES["WITHDRAWN_BY_THE_INITIATOR"]:
            return "withdraw_by_the_initiator"  # Отозвано инициатором

        # Возврат стандартного значения при отсутствии исключительного статуса
        return "no_data"
    except Exception:
        # Возврат стандартного значения при ошибках получения данных
        return "no_data"


def filter_production_cases(df: pd.DataFrame, production_type: str) -> pd.DataFrame:
    """
    Фильтрация дел по типу производства.

    Args:
        df: DataFrame с детальным отчетом
        production_type: 'lawsuit' для искового производства или 'order' для приказного

    Returns:
        pd.DataFrame: Отфильтрованный DataFrame

    Raises:
        ValueError: При указании неизвестного типа производства
    """
    if production_type == 'lawsuit':
        # Инициализация фильтров нейтральными значениями
        category_filter = True
        method_filter = True

        # Применение фильтров только если соответствующие колонки существуют
        if COLUMNS["CATEGORY"] in df.columns:
            category_filter = (df[COLUMNS["CATEGORY"]] == VALUES["CLAIM_FROM_BANK"])
        if COLUMNS["METHOD_OF_PROTECTION"] in df.columns:
            method_filter = (df[COLUMNS["METHOD_OF_PROTECTION"]] == VALUES["CLAIM_PROCEEDINGS"])

        return df[category_filter & method_filter].copy()

    elif production_type == 'order':
        # Инициализация фильтров нейтральными значениями
        category_filter = True
        method_filter = True

        # Применение фильтров только если соответствующие колонки существуют
        if COLUMNS["CATEGORY"] in df.columns:
            category_filter = (df[COLUMNS["CATEGORY"]] == VALUES["CLAIM_FROM_BANK"])
        if COLUMNS["METHOD_OF_PROTECTION"] in df.columns:
            method_filter = (df[COLUMNS["METHOD_OF_PROTECTION"]] == VALUES["ORDER_PRODUCTION"])

        return df[category_filter & method_filter].copy()

    else:
        raise ValueError(f"Неизвестный тип производства: {production_type}")