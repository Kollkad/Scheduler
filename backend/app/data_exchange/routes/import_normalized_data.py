# backend/app/data_exchange/routes/import_normalized_data.py
"""
Маршруты для импорта данных в NormalizedDataManager из сетевой папки.

Предоставляет эндпоинты для получения информации о доступных данных
и загрузки всех данных или пользовательских переопределений.
"""

from fastapi import APIRouter, HTTPException

from backend.app.data_exchange.modules.data_io import (
    load_dataframe,
    load_metadata
)
from backend.app.data_management.modules.normalized_data_manager import normalized_manager

router = APIRouter(prefix="/api/exchange", tags=["data_exchange"])


@router.get("/info")
async def get_exchange_info():
    """
    Возвращает информацию о данных, доступных в папке обмена.

    Читает metadata.json и metadata_overrides.json без загрузки самих данных.
    Используется фронтендом для отображения модального окна с информацией
    перед выполнением импорта.

    Returns:
        Dict: Информация о доступных данных
    """
    try:
        metadata = load_metadata("metadata.json")
        overrides_metadata = load_metadata("metadata_overrides.json")

        return {
            "success": True,
            "metadata": metadata,
            "overrides_metadata": overrides_metadata,
            "message": "Информация о данных получена"
        }

    except Exception as e:
        print(f"❌ Ошибка получения информации: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.post("/import/all")
async def import_all_data():
    """
    Загружает все данные из папки обмена в NormalizedDataManager.

    Читает metadata.json, загружает все перечисленные в нем Parquet-файлы
    и сохраняет их в соответствующие хранилища менеджера.

    Stages и checks не заменяются, но сравниваются с текущими —
    при расхождении выводится предупреждение.

    Returns:
        Dict: Результат импорта с информацией о загруженных файлах
    """
    try:
        # Проверка наличия метаданных
        metadata = load_metadata("metadata.json")
        if not metadata:
            raise HTTPException(status_code=400, detail="Нет данных для импорта. Папка обмена пуста.")

        files_info = metadata.get("files", {})
        if not files_info:
            raise HTTPException(status_code=400, detail="Метаданные не содержат информации о файлах.")

        imported_files = []

        # Импорт детального отчета
        filename = "source_detailed_report.parquet"
        if filename in files_info:
            df = load_dataframe(filename)
            if df is not None:
                normalized_manager.set_cases_data(df)
                imported_files.append(filename)

        # Импорт отчета документов
        filename = "source_documents_report.parquet"
        if filename in files_info:
            df = load_dataframe(filename)
            if df is not None:
                normalized_manager.set_documents_data(df)
                imported_files.append(filename)

        # Импорт результатов проверок
        filename = "check_results.parquet"
        if filename in files_info:
            df = load_dataframe(filename)
            if df is not None:
                normalized_manager.set_check_results_data(df)
                imported_files.append(filename)

        # Импорт задач
        filename = "tasks.parquet"
        if filename in files_info:
            df = load_dataframe(filename)
            if df is not None:
                normalized_manager.set_tasks_data(df)
                imported_files.append(filename)

        # Проверка этапов (без замены)
        filename = "stages.parquet"
        if filename in files_info:
            new_stages = load_dataframe(filename)
            if new_stages is not None:
                current_stages = normalized_manager.get_stages_data()
                if not new_stages.equals(current_stages):
                    print("⚠️ Импортированные этапы отличаются от текущих! Возможны ошибки при работе.")
                else:
                    print("✅ Импортированные этапы совпадают с текущими.")

        # Проверка проверок (без замены)
        filename = "checks.parquet"
        if filename in files_info:
            new_checks = load_dataframe(filename)
            if new_checks is not None:
                current_checks = normalized_manager.get_checks_data()
                if not new_checks.equals(current_checks):
                    print("⚠️ Импортированные проверки отличаются от текущих! Возможны ошибки при работе.")
                else:
                    print("✅ Импортированные проверки совпадают с текущими.")

        # Сброс времени загрузки данных
        normalized_manager.reset_data_loaded_at()

        if not imported_files:
            raise HTTPException(status_code=400, detail="Не удалось загрузить ни один файл.")

        return {
            "success": True,
            "imported_files": imported_files,
            "metadata": metadata,
            "message": f"Импорт выполнен успешно. Загружено {len(imported_files)} файлов."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка импорта данных: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка импорта: {str(e)}")


@router.post("/import/user-overrides")
async def import_user_overrides():
    """
    Загружает пользовательские переопределения из папки обмена.

    Читает metadata_overrides.json, загружает user_overrides.parquet
    и сохраняет в _user_overrides.

    Returns:
        Dict: Результат импорта с информацией о загруженных файлах
    """
    try:
        # Проверка наличия метаданных
        metadata = load_metadata("metadata_overrides.json")
        if not metadata:
            raise HTTPException(status_code=400, detail="Нет переопределений для импорта. Папка обмена пуста.")

        files_info = metadata.get("files", {})
        filename = "user_overrides.parquet"

        if filename not in files_info:
            raise HTTPException(status_code=400, detail="Файл переопределений не найден в метаданных.")

        df = load_dataframe(filename)
        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="Файл переопределений пуст.")

        normalized_manager.set_user_overrides_data(df)

        return {
            "success": True,
            "imported_files": [filename],
            "metadata": metadata,
            "message": f"Импорт переопределений выполнен успешно. Загружено {len(df)} записей."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка импорта переопределений: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка импорта: {str(e)}")


