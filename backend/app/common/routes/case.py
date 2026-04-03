# backend/app/common/routes/case.py

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
from backend.app.common.modules.field_grouping import (
    safe_convert_value,
    detect_field_type,
    group_fields_by_category,
    is_empty_value
)
from backend.app.common.config.special_fields_case import SPECIAL_FIELDS
from backend.app.data_management.modules.data_manager import data_manager

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
            "foundInColumn": str,
            "caseStage": str,
            "rainbowColor": str
        }
    """
    try:
        # 1. Получение данных дела из cleaned_data
        df = data_manager.get_detailed_data()
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="Данные не загружены")

        # Список колонок для поиска кода дела
        case_columns_to_check = [COLUMNS["CASE_CODE"], 'Код дела']

        case_data = None
        found_column = None

        # Поиск дела по различным возможным колонкам
        for column in case_columns_to_check:
            if column in df.columns:
                try:
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

        # Безопасное преобразование данных
        safe_case_data = {}
        for key, value in case_data.items():
            safe_case_data[key] = safe_convert_value(value)

        # 2. Определение цвета в радуге из detailed_colored
        rainbow_color = get_rainbow_color(case_code)

        # 3. Определение caseStage
        case_stage = get_case_stage(case_code, safe_case_data)

        # Добавление caseStage в данные дела
        safe_case_data["caseStage"] = case_stage

        # 4. Группировка полей по категориям
        field_groups = group_fields_by_category(safe_case_data, SPECIAL_FIELDS)

        return {
            "success": True,
            "caseCode": case_code,
            "data": safe_case_data,
            "fieldGroups": field_groups,
            "totalFields": len(safe_case_data),
            "foundInColumn": found_column,
            "caseStage": case_stage,
            "rainbowColor": rainbow_color
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


def get_rainbow_color(case_code: str) -> str:
    try:
        derived_df = data_manager.get_derived_data("detailed")
        if derived_df is None or derived_df.empty:
            return None

        case_col = COLUMNS["CASE_CODE"]
        if case_col not in derived_df.columns:
            return None

        mask = derived_df[case_col] == case_code
        if not mask.any():
            return None

        color_col = None
        if 'currentPeriodColor' in derived_df.columns:
            color_col = 'currentPeriodColor'
        elif 'Цвет (текущий период)' in derived_df.columns:
            color_col = 'Цвет (текущий период)'
        else:
            return None

        color_value = derived_df.loc[mask, color_col].iloc[0]
        return color_value if pd.notna(color_value) else None
    except Exception as e:
        print(f"Ошибка получения цвета радуги: {e}")
        return None


def get_case_stage(case_code: str, case_data: Dict[str, Any]) -> str:
    """
    Определение этапа дела на основе способа защиты.

    Args:
        case_code (str): Код дела
        case_data (dict): Данные дела

    Returns:
        str: Название этапа или None
    """
    method_of_protection = case_data.get(COLUMNS["METHOD_OF_PROTECTION"])

    if not method_of_protection:
        return None

    # Исковое производство
    if method_of_protection == VALUES["CLAIM_PROCEEDINGS"]:
        lawsuit_df = data_manager.get_processed_data("lawsuit_staged")
        if lawsuit_df is not None and not lawsuit_df.empty:
            mask = lawsuit_df["caseCode"] == case_code
            if mask.any():
                return lawsuit_df.loc[mask, "caseStage"].iloc[0]

    # Приказное производство
    elif method_of_protection == VALUES["ORDER_PRODUCTION"]:
        order_df = data_manager.get_processed_data("order_staged")
        if order_df is not None and not order_df.empty:
            mask = order_df["caseCode"] == case_code
            if mask.any():
                return order_df.loc[mask, "caseStage"].iloc[0]

    return None
