#backend/app/common/routes/case.py
"""
Модуль для работы с данными судебных дел.

Предоставляет API для получения детальной информации по делам,
включая поиск, преобразование данных и автоматическую категоризацию полей.
Основные функции:
- Поиск дела по различным идентификаторам
- Безопасное преобразование типов данных
- Автоматическая группировка полей по категориям
"""

from datetime import datetime
import re
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import pandas as pd
from backend.app.common.config.column_names import COLUMNS, VALUES

router = APIRouter(prefix="/api/case", tags=["case"])


@router.get("/{case_code}")
async def get_case_details(case_code: str):
    """
    Получение детальной информации по конкретному судебному делу.

    Args:
        case_code (str): Код дела для поиска

    Returns:
        dict: Данные дела в формате {
            "success": bool,
            "caseCode": str,
            "data": dict,
            "fieldGroups": dict,
            "totalFields": int,
            "foundInColumn": str
        }

    Raises:
        HTTPException: 404 если данные не загружены или дело не найдено
        HTTPException: 500 при внутренней ошибке сервера
    """
    try:
        from backend.app.common.modules.data_manager import data_manager

        # Получение оригинальных очищенных данных через data_manager
        df = data_manager.get_detailed_data()
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="Данные не загружены")

        # Список колонок для поиска кода дела
        case_columns_to_check = [COLUMNS["CASE_CODE"], 'Код дела', 'Номер дела', 'Судебный номер дела']

        case_data = None
        found_column = None

        # Поиск дела по различным возможным колонкам
        for column in case_columns_to_check:
            if column in df.columns:
                try:
                    # Безопасное сравнение с защитой от NA/NaN
                    mask = df[column].apply(lambda x: safe_compare(x, case_code))
                    case_row = df[mask]

                    if not case_row.empty:
                        case_data = case_row.iloc[0].to_dict()
                        found_column = column
                        break
                except Exception as e:
                    print(f"Ошибка при поиске в колонке {column}: {e}")
                    continue

        if not case_data:
            raise HTTPException(status_code=404, detail=f"Дело {case_code} не найдено")

        # Безопасное преобразование данных в корректные типы
        safe_case_data = {}
        for key, value in case_data.items():
            safe_case_data[key] = safe_convert_value(value)

        # Группировка полей по категориям для структурированного отображения
        field_groups = group_fields_by_category(safe_case_data)

        return {
            "success": True,
            "caseCode": case_code,
            "data": safe_case_data,
            "fieldGroups": field_groups,
            "totalFields": len(safe_case_data),
            "foundInColumn": found_column
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Критическая ошибка в get_case_details: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных дела: {str(e)}")


def safe_compare(value, target):
    """
    Безопасное сравнение значений с защитой от NA/NaN.

    Args:
        value: Значение для сравнения
        target: Целевое значение

    Returns:
        bool: Результат сравнения
    """
    if pd.isna(value):
        return False
    try:
        return str(value) == str(target)
    except:
        return False


def safe_convert_value(value):
    """
    Безопасное преобразование значения в корректный тип данных.

    Args:
        value: Исходное значение

    Returns:
        Преобразованное значение в корректном типе
    """
    # Проверка NA значений должна быть первой и самой строгой
    if pd.isna(value):
        return None

    # Если значение уже нормальное - возвращаем его
    try:
        # Для дат и временных меток
        if isinstance(value, (pd.Timestamp, datetime.date)):
            return value.isoformat()
        # Для чисел
        elif isinstance(value, (int, float)):
            return float(value)
        # Для булевых
        elif isinstance(value, bool):
            return value
        # Для строк - убираем лишние пробелы
        elif isinstance(value, str):
            cleaned = value.strip()
            return cleaned if cleaned else None
        # Все остальное в строку
        else:
            # Если значение уже имеет нормальный тип, возвращаем как есть
            return value
    except:
        # В случае ошибки возвращаем оригинальное значение
        return value


def group_fields_by_category(data: Dict[str, Any]) -> Dict[str, List[Dict]]:
    """
    Автоматическая группировка полей по категориям на основе названий.

    Args:
        data (Dict[str, Any]): Словарь с данными дела

    Returns:
        Dict[str, List[Dict]]: Сгруппированные поля по категориям
    """
    groups = {
        "general": [],
        "court": [],
        "financial": [],
        "dates": [],
        "other": []
    }

    # Обработка каждого поля в данных с категоризацией по ключевым словам
    for key, value in data.items():
        try:
            field_info = {
                "id": key,
                "label": key,
                "value": value,
                "type": detect_field_type(value)
            }

            # Автоматическая категоризация по названию поля
            key_lower = key.lower()

            if any(word in key_lower for word in ['дата', 'date', 'срок', 'time']):
                groups["dates"].append(field_info)
            elif any(word in key_lower for word in ['суд', 'court', 'заседание', 'инстанция', 'жалоба']):
                groups["court"].append(field_info)
            elif any(word in key_lower for word in ['сумма', 'деньги', 'валюта', 'финанс', 'price', 'cost']):
                groups["financial"].append(field_info)
            elif any(word in key_lower for word in ['код', 'номер', 'статус', 'исполнитель', 'ответствен']):
                groups["general"].append(field_info)
            else:
                groups["other"].append(field_info)

        except Exception as e:
            print(f"Ошибка при обработке поля {key}: {e}")
            continue

    # Удаление пустых групп для чистого результата
    return {k: v for k, v in groups.items() if v}


def detect_field_type(value: Any) -> str:
    """
    Автоматическое определение типа поля на основе значения.

    Args:
        value (Any): Значение для анализа

    Returns:
        str: Тип поля ('text', 'number', 'boolean', 'date', 'currency')
    """
    # Пустые значения
    if value is None or value == "":
        return 'text'

    # Уже безопасно преобразованные значения
    try:
        # Проверка на число
        if isinstance(value, (int, float)):
            return 'number'

        # Проверка на булево значение
        if isinstance(value, bool):
            return 'boolean'

        # Для строк
        if isinstance(value, str):
            value_lower = value.lower().strip()

            if not value_lower:  # Проверка пустой строки
                return 'text'

            # Булевы значения в строке
            if value_lower in ['true', 'false', 'да', 'нет', 'yes', 'no']:
                return 'boolean'

            # Числовые значения в строке
            if re.match(r'^-?\d+\.?\d*$', value_lower):
                return 'number'

            # Даты в строке
            date_patterns = [
                r'\d{2}\.\d{2}\.\d{4}',
                r'\d{4}-\d{2}-\d{2}',
                r'\d{2}/\d{2}/\d{4}'
            ]
            for pattern in date_patterns:
                if re.match(pattern, value_lower):
                    return 'date'

            # Валютные значения
            if any(word in value_lower for word in ['руб', 'usd', 'eur', '₽', '$', '€', 'р.']):
                return 'currency'

        return 'text'

    except Exception:
        return 'text'