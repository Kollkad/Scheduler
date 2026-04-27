# backend/app/data_exchange/routes/export_normalized_data.py
"""
Маршруты для экспорта данных NormalizedDataManager в сетевую папку.

Предоставляет эндпоинты для выгрузки всех данных или только
пользовательских переопределений в формат Parquet.
"""

from fastapi import APIRouter, HTTPException, Depends

from backend.app.data_exchange.modules.data_io import (
    save_dataframe,
    save_metadata,
    build_metadata, get_user_overrides_folder
)
from backend.app.data_management.modules.normalized_data_manager import normalized_manager
from backend.app.administration_settings.modules.authorization_logic import get_current_user
from backend.app.administration_settings.modules.user_models import UserSession
from backend.app.reporting.modules.report_types.incorrect_dates_in_data_exchange import should_save_date_problems

router = APIRouter(prefix="/api/exchange", tags=["data_exchange"])


@router.post("/export/all")
async def export_all_data(
    current_user: UserSession = Depends(get_current_user)
):
    """
    Выгружает все данные из NormalizedDataManager в папку обмена (app_data).

    Сохраняет в формате Parquet:
    - Детальный отчет и отчет документов (source_data)
    - Результаты проверок, задачи, этапы, проверки
    - Метаданные экспорта в metadata.json
    """
    try:
        # Получение всех данных из менеджера
        data_sources = {
            "source_detailed_report.parquet": normalized_manager.get_cases_data(),
            "source_documents_report.parquet": normalized_manager.get_documents_data(),
            "check_results.parquet": normalized_manager.get_check_results_data(),
            "tasks.parquet": normalized_manager.get_tasks_data(),
            "stages.parquet": normalized_manager.get_stages_data(),
            "checks.parquet": normalized_manager.get_checks_data(),
        }

        # Проверка наличия хотя бы одного непустого DataFrame
        has_data = any(df is not None and not df.empty for df in data_sources.values())
        if not has_data:
            raise HTTPException(status_code=400, detail="Нет данных для экспорта.")

        # Сохранение DataFrame и сбор информации о файлах
        files_info = {}
        exported_files = []

        for filename, df in data_sources.items():
            if df is not None and not df.empty:
                save_problems = should_save_date_problems(current_user.role)
                save_dataframe(df, filename, save_problems=save_problems)
                files_info[filename] = {"rows": len(df), "columns": len(df.columns)}
                exported_files.append(filename)

        # Сохранение метаданных в metadata.json
        exported_by = current_user.login or "unknown"
        metadata = build_metadata(files_info, exported_by)
        save_metadata(metadata, filename="metadata.json")

        return {
            "success": True,
            "files": exported_files,
            "metadata": metadata,
            "message": f"Экспорт выполнен успешно. Сохранено {len(exported_files)} файлов."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка экспорта данных: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")


@router.post("/export/user-overrides")
async def export_user_overrides(
    current_user: UserSession = Depends(get_current_user)
):
    """
    Выгружает пользовательские переопределения задач в папку обмена (app_data).

    Сохраняет в формате Parquet:
    - _user_overrides (все записи)
    - Метаданные экспорта в metadata_overrides.json
    """
    try:
        df = normalized_manager.get_user_overrides_data()

        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="Нет пользовательских переопределений для экспорта.")

        filename = "user_overrides.parquet"
        save_problems = should_save_date_problems(current_user.role)
        save_dataframe(df, filename, save_problems=save_problems)

        # Сохранение метаданных в metadata_overrides.json
        files_info = {filename: {"rows": len(df), "columns": len(df.columns)}}
        exported_by = current_user.login or "unknown"
        metadata = build_metadata(files_info, exported_by)
        save_metadata(metadata, filename="metadata_overrides.json")

        return {
            "success": True,
            "files": [filename],
            "metadata": metadata,
            "message": f"Экспорт переопределений выполнен успешно. Сохранено {len(df)} записей."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка экспорта переопределений: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")


@router.post("/export/my-overrides")
async def export_my_overrides(
    current_user: UserSession = Depends(get_current_user)
):
    """
    Выгружает пользовательские переопределения текущего сотрудника.

    Сохраняет в app_data/user_overrides/:
    - user_overrides_{login}.parquet — только оверрайды этого пользователя
    - metadata_{login}.json — метаданные экспорта

    Returns:
        Dict: Результат экспорта
    """
    try:
        df = normalized_manager.get_user_overrides_data()

        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="Нет пользовательских переопределений.")

        # Фильтрация по createdBy
        login = current_user.login or "unknown"
        df = df[df["createdBy"] == login]

        if df.empty:
            raise HTTPException(status_code=400, detail=f"Нет переопределений для пользователя {login}.")

        # Сохранение в app_data/user_overrides/
        user_folder = get_user_overrides_folder()
        filename = f"user_overrides_{login}.parquet"
        save_problems = should_save_date_problems(current_user.role)
        save_dataframe(df, filename, save_problems=save_problems, folder=user_folder)

        # Сохранение метаданных
        files_info = {filename: {"rows": len(df), "columns": len(df.columns)}}
        metadata = build_metadata(files_info, login)
        metadata_filename = f"metadata_{login}.json"
        save_metadata(metadata, filename=metadata_filename, folder=user_folder)

        return {
            "success": True,
            "files": [filename],
            "metadata": metadata,
            "message": f"Экспорт переопределений для {login} выполнен. Сохранено {len(df)} записей."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка экспорта переопределений: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")



