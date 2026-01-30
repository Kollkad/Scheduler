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

router = APIRouter(tags=["filters"])

@router.get("/api/filter-options")
async def get_filter_options(columns: List[str] = Query(None)):
    """
    Возвращает уникальные значения для указанных колонок.

    Поддерживает получение опций фильтрации для одного или нескольких полей.
    Пример использования: /api/filter-options?columns=gosb&columns=responsibleExecutor

    Args:
        columns (List[str]): Список системных имен колонок для получения опций

    Returns:
        dict: Результат с опциями фильтрации в формате {
            "success": bool,
            "data": dict,      # Опции фильтров
            "message": str     # Сообщение о результате
        }

    Raises:
        HTTPException: 500 при внутренних ошибках обработки
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

@router.get("/api/filters/metadata")
async def get_filters_metadata():
    """
    Возвращает метаинформацию о доступных фильтрах.

    Provides frontend with information about available filters, their types
    and corresponding database columns for dynamic interface generation.

    Returns:
        dict: Метаинформация о фильтрах в формате {
            "success": bool,
            "data": {
                "filters": list,      # Список фильтров
                "totalFilters": int   # Общее количество фильтров
            }
        }

    Raises:
        HTTPException: 500 при внутренних ошибках
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


@router.post("/api/filter/apply")
async def apply_filters(filters: Dict[str, Any] = Body(...)):
    """
    Применяет фильтры к данным и возвращает отфильтрованные результаты.

    Args:
        filters (Dict[str, Any]): Словарь фильтров в формате {field_name: filter_value}
            где field_name - системные имена (gosb, responsibleExecutor и т.д.)

    Returns:
        dict: Результат фильтрации
    """
    try:
        from backend.app.common.modules.data_manager import data_manager

        # Получение данных с цветовой классификацией
        df = data_manager.get_colored_data("detailed")
        if df is None or df.empty:
            return {
                "success": False,
                "data": [],
                "total": 0,
                "message": "Данные не загружены"
            }

        # Последовательное применение фильтров к данным
        filtered_df = df.copy()
        for field_name, filter_value in filters.items():
            if filter_value and field_name in filtered_df.columns:
                print(f"🔍 Фильтруем {field_name} по значению: {filter_value}")
                filtered_df = filtered_df[filtered_df[field_name] == filter_value]

        print(f"✅ После фильтрации осталось {len(filtered_df)} записей")

        # Очистка DataFrame от дубликатов колонок
        if filtered_df.columns.duplicated().any():
            filtered_df = filtered_df.loc[:, ~filtered_df.columns.duplicated()]

        # Конвертация в список словарей с обработкой NaN
        result = filtered_df.where(pd.notnull(filtered_df), None).to_dict(orient='records')

        return {
            "success": True,
            "data": result,
            "total": len(result),
            "filtersApplied": filters
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка фильтрации: {str(e)}")