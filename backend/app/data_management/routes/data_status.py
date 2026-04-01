# backend/app/data_management/routes/data_status.py
"""
Модуль маршрутов FastAPI для проверки состояния данных и управления результатами анализа.

Предоставляет API эндпоинты:
- Проверка структуры загруженных данных
- Сброс результатов анализа и очищенных данных
"""

from fastapi import APIRouter, HTTPException
import pandas as pd

from backend.app.data_management.modules.data_manager import data_manager

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

    # Получение DataFrame из менеджера данных
    df = data_manager.get_detailed_data()

    # Проверка наличия и корректности данных
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return {"status": "no_data"}

    all_columns = list(df.columns)

    from backend.app.common.config.column_names import COLUMNS

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
        cleared_data = []

        # Очистка обработанных данных анализа
        data_manager.clear_processed_data("all")
        cleared_data.extend([
            "lawsuit_staged",
            "order_staged",
            "documents_processed",
            "tasks"
        ])

        # Очистка загруженных и подготовленных данных
        data_manager.clear_data("all")
        cleared_data.extend([
            "detailed_report",
            "documents_report",
            "raw_data",
            "colored_data"
        ])

        # Принудительная очистка памяти
        import gc
        gc.collect()

        return {
            "success": True,
            "message": "Сброс результатов анализа выполнен успешно",
            "cleared_data": cleared_data,
            "memory_cleaned": True
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка сброса анализа: {str(e)}"
        )



