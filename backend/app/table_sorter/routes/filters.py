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

    Поддерживает множественную фильтрацию по различным полям данных.
    Обеспечивает безопасное преобразование типов данных для JSON-совместимости.

    Args:
        filters (Dict[str, Any]): Словарь фильтров в формате {field_name: filter_value}

    Returns:
        dict: Результат фильтрации в формате {
            "success": bool,
            "data": list,           # Отфильтрованные данные
            "total": int,           # Количество записей
            "filtersApplied": dict  # Примененные фильтры
        }

    Raises:
        HTTPException: 500 при ошибках применения фильтров
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

        # Проверка наличия колонки с цветовой классификацией
        color_column_name = 'Цвет (текущий период)'
        if color_column_name not in df.columns:
            raise HTTPException(status_code=500, detail="Столбец с цветом не найден в данных")

        # Маппинг системных имен фильтров на названия колонок в данных
        column_mapping = {
            "gosb": "ГОСБ",
            "courtProtectionMethod": "Способ судебной защиты",
            "responsibleExecutor": "Ответственный исполнитель",
            "currentPeriodColor": color_column_name,
            "courtReviewingCase": "Суд, рассматривающий дело"
        }

        # Последовательное применение фильтров к данным
        filtered_df = df.copy()
        for frontend_field, filter_value in filters.items():
            if filter_value and frontend_field in column_mapping:
                db_column = column_mapping[frontend_field]
                if db_column in filtered_df.columns:
                    print(f"🔍 Фильтруем {db_column} по значению: {filter_value}")
                    filtered_df = filtered_df[filtered_df[db_column] == filter_value]

        print(f"✅ После фильтрации осталось {len(filtered_df)} записей")

        # Очистка DataFrame от дубликатов колонок
        if filtered_df.columns.duplicated().any():
            filtered_df = filtered_df.loc[:, ~filtered_df.columns.duplicated()]

        def safe_convert(value):
            """
            Безопасное преобразование значений в JSON-совместимые типы.

            Args:
                value: Исходное значение для преобразования

            Returns:
                Преобразованное значение или None
            """
            if pd.isna(value):
                return None
            elif isinstance(value, (int, float)):
                # Обработка специальных числовых значений
                if value == float('inf') or value == float('-inf'):
                    return None
                try:
                    # Преобразование к целому числу если возможно
                    if value == int(value):
                        return int(value)
                    return float(value)
                except (ValueError, OverflowError):
                    return str(value)
            else:
                return str(value)

        # Конвертация отфильтрованных данных в JSON-совместимый формат
        result = []
        for _, row in filtered_df.iterrows():
            row_dict = {}
            for col in filtered_df.columns:
                try:
                    row_dict[col] = safe_convert(row[col])
                except Exception as e:
                    row_dict[col] = None
            result.append(row_dict)

        return {
            "success": True,
            "data": result,
            "total": len(result),
            "filtersApplied": filters
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка фильтрации: {str(e)}")