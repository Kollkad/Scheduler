#backend/app/common/modules/field_grouping.py
"""
Модуль для группировки полей карточек (дел, документов и т.д.)

Предоставляет функции для:
- Безопасного преобразования типов данных
- Определения типа поля (date, number, currency, boolean, text)
- Группировки полей по категориям (general, dates, financial, court, other)
"""

from datetime import datetime
import re
from typing import Dict, Any, List
import pandas as pd


def safe_convert_value(value):
    """
    Безопасное преобразование значения в корректный тип данных.
    """
    if pd.isna(value):
        return None

    try:
        if isinstance(value, (pd.Timestamp, datetime, datetime.date)):
            return value
        elif isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, bool):
            return value
        elif isinstance(value, str):
            cleaned = value.strip()
            return cleaned if cleaned else None
        else:
            return value
    except:
        return value


def is_empty_value(value: Any) -> bool:
    """Проверка, является ли значение пустым."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() in ['', '-', 'Не указано', 'Не задано']
    return False


def detect_field_type(value: Any) -> str:
    """
    Автоматическое определение типа поля на основе значения.

    Returns:
        str: 'text', 'number', 'boolean', 'date', 'currency'
    """
    if value is None or value == "":
        return 'text'

    try:
        if isinstance(value, (pd.Timestamp, datetime, datetime.date)):
            return 'date'

        if isinstance(value, (int, float)):
            return 'number'

        if isinstance(value, bool):
            return 'boolean'

        if isinstance(value, str):
            value_lower = value.lower().strip()

            if not value_lower:
                return 'text'

            if value_lower in ['true', 'false', 'да', 'нет', 'yes', 'no']:
                return 'boolean'

            if re.match(r'^-?\d+\.?\d*$', value_lower):
                return 'number'

            # Даты в строке
            date_patterns = [
                r'\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}',
                r'\d{2}\.\d{2}\.\d{4}',
                r'\d{4}-\d{2}-\d{2}',
                r'\d{2}/\d{2}/\d{4}',
                r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
            ]
            for pattern in date_patterns:
                if re.match(pattern, value_lower):
                    return 'date'

            if any(word in value_lower for word in ['руб', 'usd', 'eur', '₽', '$', '€', 'р.']):
                return 'currency'

        return 'text'
    except Exception:
        return 'text'


def group_fields_by_category(data: Dict[str, Any], special_fields: List[str]) -> Dict[str, List[Dict]]:
    """
    Группировка полей по категориям.

    Args:
        data: Словарь с данными
        special_fields: Список полей для категории "general" в фиксированном порядке

    Returns:
        Dict с ключами: 'general', 'dates', 'financial', 'court', 'other'
    """
    groups = {
        "general": [],
        "dates": [],
        "financial": [],
        "court": [],
        "other": []
    }

    # Сначала обрабатываем специальные поля в заданном порядке
    for field_name in special_fields:
        if field_name in data:
            value = data[field_name]
            groups["general"].append({
                "id": field_name,
                "label": field_name,
                "value": value,
                "type": detect_field_type(value),
                "isEmpty": is_empty_value(value)
            })

    # Затем обрабатываем остальные поля
    for key, value in data.items():
        if key in special_fields:
            continue

        if key == "caseStage":
            continue

        field_info = {
            "id": key,
            "label": key,
            "value": value,
            "type": detect_field_type(value),
            "isEmpty": is_empty_value(value)
        }

        key_lower = key.lower()

        if any(word in key_lower for word in ['дата', 'date', 'срок', 'time', 'период', 'год']):
            groups["dates"].append(field_info)
        elif any(word in key_lower for word in ['сумма', 'деньги', 'валют', 'финанс', 'price', 'cost', 'руб', 'usd', 'eur']):
            groups["financial"].append(field_info)
        elif any(word in key_lower for word in ['суд', 'court', 'заседани', 'инстанц', 'жалоб', 'апелляц']):
            groups["court"].append(field_info)
        else:
            groups["other"].append(field_info)

    return {k: v for k, v in groups.items() if v}