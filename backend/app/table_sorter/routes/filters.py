# backend/app/table_sorter/routes/filters.py
"""
Модуль маршрутов FastAPI для управления фильтрацией данных.

Предоставляет API эндпоинты для:
- Получения опций фильтрации по колонкам
- Получения метаинформации о доступных фильтрах
- Применения фильтров к данным с возвратом результатов
"""

from typing import Dict, Any, List
import pandas as pd
from fastapi import APIRouter, HTTPException, Body, Query
from backend.app.table_sorter.modules.filter_manager import filter_settings
from backend.app.data_management.modules.normalized_data_manager import normalized_manager
from backend.app.common.config.column_names import COLUMNS

router = APIRouter(prefix="/api", tags=["filters"])

# Маппинг системных имен фильтров к реальным колонкам
FILTER_COLUMN_MAPPING = {
    "gosb": COLUMNS["GOSB"],
    "responsibleExecutor": COLUMNS["RESPONSIBLE_EXECUTOR"],
    "courtReviewingCase": COLUMNS["COURT"],
    "courtProtectionMethod": COLUMNS["METHOD_OF_PROTECTION"],
    "currentPeriodColor": COLUMNS["CURRENT_PERIOD_COLOR"],
    "caseCode": COLUMNS["CASE_CODE"],
    "caseStatus": COLUMNS["CASE_STATUS"],
}


@router.get("/filter-options")
async def get_filter_options(columns: List[str] = Query(None)):
    """
    Возвращает уникальные значения для указанных колонок.

    Args:
        columns (List[str]): Список системных имен колонок для получения опций

    Returns:
        dict: Результат с опциями фильтрации
    """
    try:
        options = filter_settings.get_filter_options(columns)
        return {
            "success": True,
            "data": options,
            "message": "Filter options retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/filters/metadata")
async def get_filters_metadata():
    """
    Возвращает метаинформацию о доступных фильтрах.

    Returns:
        dict: Метаинформация о фильтрах
    """
    try:
        filters_meta = filter_settings.get_available_filters()
        return {
            "success": True,
            "data": {
                "filters": filters_meta,
                "totalFilters": len(filters_meta)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/filter/apply")
async def apply_filters(filters: Dict[str, Any] = Body(...)):
    """
    Применяет фильтры к данным и возвращает отфильтрованные результаты.

    Args:
        filters (Dict[str, Any]): Словарь фильтров в формате {field_name: filter_value}

    Returns:
        dict: Результат фильтрации
    """
    try:
        df = normalized_manager.get_cases_data()

        if df is None or df.empty:
            return {
                "success": False,
                "data": [],
                "total": 0,
                "message": "Данные не загружены"
            }

        # Последовательное применение фильтров
        filtered_df = df.copy()

        for field_name, filter_value in filters.items():
            if filter_value and isinstance(filter_value, str) and filter_value.strip():
                # Получение реального имени колонки
                column_name = FILTER_COLUMN_MAPPING.get(field_name, field_name)

                if column_name in filtered_df.columns:
                    # Приведение к строке и сравнение
                    mask = filtered_df[column_name].astype(str).str.strip() == filter_value.strip()
                    filtered_df = filtered_df[mask]

        # Очистка от дубликатов колонок
        if filtered_df.columns.duplicated().any():
            filtered_df = filtered_df.loc[:, ~filtered_df.columns.duplicated()]

        # Выбор колонок для ответа (переименование в системные имена)
        columns_to_include = {
            COLUMNS["CASE_CODE"]: "caseCode",
            COLUMNS["RESPONSIBLE_EXECUTOR"]: "responsibleExecutor",
            COLUMNS["GOSB"]: "gosb",
            COLUMNS["METHOD_OF_PROTECTION"]: "courtProtectionMethod",
            COLUMNS["COURT"]: "courtReviewingCase",
            COLUMNS["CASE_STATUS"]: "caseStatus",
            COLUMNS["CURRENT_PERIOD_COLOR"]: "currentPeriodColor",
        }

        existing_columns = {k: v for k, v in columns_to_include.items() if k in filtered_df.columns}
        result_df = filtered_df[list(existing_columns.keys())].rename(columns=existing_columns)

        # Заполнение NaN значений
        for col in result_df.columns:
            if result_df[col].dtype == 'object':
                result_df[col] = result_df[col].fillna("Не указано")
            elif pd.api.types.is_numeric_dtype(result_df[col]):
                result_df[col] = result_df[col].fillna(0)

        result = result_df.to_dict(orient='records')

        return {
            "success": True,
            "data": result,
            "total": len(result),
            "filtersApplied": filters
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка фильтрации: {str(e)}")