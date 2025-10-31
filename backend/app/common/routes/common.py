#backend/app/common/routes/common.py
"""
Модуль маршрутов FastAPI для общих операций с данными.

Предоставляет API эндпоинты для управления файлами данных:
- Загрузка файлов отчетов
- Проверка статуса и целостности данных
- Управление состоянием анализа (сброс, удаление)
- Интеграция с модулем фильтров
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
import tempfile
import shutil
import os
import pandas as pd
from typing import Dict, Optional
from backend.app.table_sorter.routes.filters import router as filters_router
from ..modules.data_manager import data_manager

router = APIRouter(tags=["common"])
router.include_router(filters_router)

# Глобальное состояние для хранения путей к загруженным файлам
current_files: Dict[str, Optional[str]] = {
    "current_detailed_report": None,
    "documents_report": None,
    "previous_detailed_report": None
}

@router.post("/upload-file")
async def upload_file(file_type: str, file: UploadFile = File(...)):
    """
    Загрузка Excel файла для дальнейшего анализа.

    Args:
        file_type (str): Тип файла (current_detailed_report, documents_report, previous_detailed_report)
        file (UploadFile): Загружаемый Excel файл

    Returns:
        dict: Результат загрузки в формате {
            "message": str,
            "filename": str,
            "file_type": str,
            "filepath": str
        }

    Raises:
        HTTPException: 400 если неверный тип файла или расширение
        HTTPException: 500 если ошибка обработки файла
    """
    global current_files

    # Проверка расширения файла
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Только Excel файлы разрешены")

    # Проверка допустимого типа файла
    if file_type not in current_files:
        raise HTTPException(status_code=400, detail="Неверный тип файла")

    try:
        # Создание временного файла и сохранение загруженных данных
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            current_files[file_type] = tmp_file.name

        # Логирование успешной загрузки файла
        print(f"✅ Файл загружен: {file.filename} (тип: {file_type})")
        print(f"📁 Временный путь: {current_files[file_type]}")

        return {
            "message": "Файл успешно загружен",
            "filename": file.filename,
            "file_type": file_type,
            "filepath": current_files[file_type]
        }
    except Exception as e:
        # Логирование ошибки обработки файла
        print(f"❌ Ошибка загрузки файла: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка обработки файла: {str(e)}")
    finally:
        # Гарантированное закрытие файлового потока
        file.file.close()


@router.get("/test-data")
async def test_data():
    """
    Тестирование загруженных данных и проверка структуры DataFrame.

    Returns:
        dict: Результат проверки данных в формате {
            "status": str,
            "all_columns": list,
            "target_columns": dict,
            "shape": tuple,
            "sample_data": dict
        }
    """
    # Получение данных через data_manager
    df = data_manager.get_detailed_data()
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return {"status": "no_data"}

    # Получение списка всех столбцов в данных
    all_columns = list(df.columns)

    # Проверка наличия целевых столбцов в данных
    from backend.app.common.config.column_names import COLUMNS
    target_columns = {
        "GOSB": COLUMNS["GOSB"],
        "RESPONSIBLE_EXECUTOR": COLUMNS["RESPONSIBLE_EXECUTOR"],
        "COURT": COLUMNS["COURT"],
        "METHOD_OF_PROTECTION": COLUMNS["METHOD_OF_PROTECTION"]
    }

    found_columns = {}
    sample_data = {}

    # Проверка каждого целевого столбца и извлечение примеров данных
    for eng_name, rus_name in target_columns.items():
        found = rus_name in all_columns
        found_columns[eng_name] = found

        if found:
            try:
                # Получение уникальных значений из столбца
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


@router.get("/files-status")
async def get_files_status():
    """
    Получение статуса загруженных файлов.

    Returns:
        dict: Статус файлов в формате {
            file_type: {
                "loaded": bool,
                "filepath": str,
                "exists": bool
            },
            "ready_for_analysis": bool
        }
    """
    status = {}

    # Проверка статуса каждого файла
    for file_type, filepath in current_files.items():
        status[file_type] = {
            "loaded": filepath is not None,
            "filepath": filepath,
            "exists": filepath is not None and os.path.exists(filepath)
        }

    # Проверка наличия обязательных файлов для анализа
    mandatory_loaded = all([
        current_files["current_detailed_report"] is not None,
        current_files["documents_report"] is not None
    ])

    status["ready_for_analysis"] = mandatory_loaded

    return status


@router.delete("/remove-file")
async def remove_file(file_type: str):
    """
    Удаление загруженного файла из памяти.

    Args:
        file_type (str): Тип файла для удаления

    Returns:
        dict: Результат удаления в формате {
            "message": str,
            "file_type": str,
            "removed": bool
        }

    Raises:
        HTTPException: 400 если неверный тип файла
    """
    global current_files

    if file_type not in current_files:
        raise HTTPException(status_code=400, detail="Неверный тип файла")

    # Очистка ссылки на файл в глобальном состоянии
    current_files[file_type] = None

    # Логирование операции удаления файла
    print(f"🗑️ Файл удален: {file_type}")

    return {
        "message": f"Файл {file_type} удален",
        "file_type": file_type,
        "removed": True
    }


@router.post("/reset-analysis")
async def reset_analysis():
    """
    Сброс всех результатов анализа и данных, без удаления загруженных файлов.

    Returns:
        dict: Результат сброса в формате {
            "success": bool,
            "message": str,
            "cleared_data": list
        }
    """
    global current_files

    try:
        cleared_data = []

        # Очистка ВСЕХ обработанных данных анализа (без удаления исходных файлов)
        data_manager.clear_processed_data("all")
        cleared_data.extend(["lawsuit_staged", "order_staged", "documents_processed", "tasks"])
        print("✅ Очищены результаты анализа")

        # Очистка загруженных и очищенных данных
        data_manager.clear_data("all")
        cleared_data.extend(["detailed_report", "documents_report", "raw_data", "colored_data"])
        print("✅ Очищены загруженные данные")

        # Принудительная сборка мусора для освобождения памяти
        import gc
        gc.collect()
        print("✅ Выполнена сборка мусора")

        return {
            "success": True,
            "message": "Сброс результатов анализа выполнен успешно",
            "cleared_data": cleared_data,
            "memory_cleaned": True
        }

    except Exception as e:
        # Логирование ошибки сброса анализа
        print(f"❌ Ошибка при сбросе анализа: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка сброса анализа: {str(e)}"
        )