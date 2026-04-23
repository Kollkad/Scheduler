# backend/app/data_management/routes/data_status.py
"""
Модуль маршрутов FastAPI для проверки состояния данных и управления результатами анализа.

Предоставляет API эндпоинты:
- Проверка структуры загруженных данных
- Сброс результатов анализа и очищенных данных
"""

from fastapi import APIRouter, HTTPException
import pandas as pd
import gc
from backend.app.data_management.modules.normalized_data_manager import normalized_manager
from backend.app.common.config.column_names import COLUMNS

router = APIRouter(prefix="/api/data", tags=["data-status"])


@router.get("/test-data")
async def test_data():
    """
    Проверяет наличие и структуру загруженных данных.

    Returns:
        dict:
            {
                "status": str,
                "all_columns": list,
                "target_columns": dict,
                "shape": tuple,
                "sample_data": dict
            }
            или {"status": "no_data"} при отсутствии данных
    """

    df = normalized_manager.get_cases_data()
    # Проверка наличия и корректности данных
    if df is None or df.empty:
        return {"status": "no_data"}

    all_columns = list(df.columns)

    target_columns = {
        "GOSB": COLUMNS["GOSB"],
        "RESPONSIBLE_EXECUTOR": COLUMNS["RESPONSIBLE_EXECUTOR"],
        "COURT": COLUMNS["COURT"],
        "METHOD_OF_PROTECTION": COLUMNS["METHOD_OF_PROTECTION"]
    }

    found_columns = {}
    sample_data = {}

    # Проверка наличия целевых столбцов
    for eng_name, rus_name in target_columns.items():
        found = rus_name in all_columns
        found_columns[eng_name] = found
        if found:
            try:
                # Извлечение уникальных значений для примера
                unique_vals = df[rus_name].fillna('Не указано').astype(str).unique()
                sample_data[eng_name] = unique_vals.tolist()[:10]
            except Exception as e:
                sample_data[eng_name] = f"ERROR: {str(e)}"

    return {
        "status": "data_loaded",
        "all_columns": all_columns,
        "target_columns": found_columns,
        "shape": df.shape,
        "sample_data": sample_data
    }


@router.post("/reset-analysis")
async def reset_analysis():
    """
    Выполняет полный сброс результатов анализа и загруженных данных.

    Returns:
        dict:
            {
                "success": bool,
                "message": str,
                "cleared_data": list,
                "memory_cleaned": bool
            }

    Raises:
        HTTPException: 500 при ошибке сброса
    """

    try:
        # Очистка всех данных в normalized_manager
        normalized_manager.clear_data("all")
        gc.collect()

        return {
            "success": True,
            "message": "Сброс результатов анализа выполнен успешно",
            "cleared_data": [
                "detailed_report",
                "documents_report",
                "check_results",
                "tasks"
            ],
            "memory_cleaned": True
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сброса анализа: {str(e)}")



