# backend/app/saving_results/routes/saving.py
"""
Модуль маршрутов FastAPI для сохранения обработанных данных в Excel файлы (v3).

Предоставляет эндпоинты для экспорта различных типов отчетов:
- Исходные данные (детальный отчет, отчет документов)
- Конфигурационные данные (этапы, проверки)
- Результаты проверок (дела, документы)
- Задачи и пользовательские переопределения
"""

import tempfile
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import FileResponse
import pandas as pd

from backend.app.data_management.modules.normalized_data_manager import normalized_manager
from backend.app.saving_results.modules.saving_results_settings import (
    generate_filename,
    save_with_xlsxwriter_formatting,
    DETAILED_AND_DOCUMENTS_RENAME_MAP,
    STAGES_RENAME_MAP,
    CHECKS_RENAME_MAP,
    CHECK_RESULTS_RENAME_MAP,
    TASKS_RENAME_MAP,
    TASKS_EXTRA_RENAME_MAP,
    USER_OVERRIDES_RENAME_MAP,
    format_monitoring_status,
    format_completion_status,
    format_is_completed,
    format_is_active,
    format_stage_code,
    enrich_tasks_for_export,
)
from backend.app.administration_settings.modules.authorization_logic import get_current_user
from backend.app.administration_settings.modules.user_models import UserSession

router = APIRouter(prefix="/api/save", tags=["saving"])


# ==================== СТАТУС ДАННЫХ ====================

@router.get("/available-data")
async def get_available_data_status():
    """
    Получение статуса доступных данных для экспорта.

    Returns:
        dict: Статус загрузки всех типов данных
    """
    try:
        detailed_df = normalized_manager.get_cases_data()
        documents_df = normalized_manager.get_documents_data()
        check_results_df = normalized_manager.get_check_results_data()
        tasks_df = normalized_manager.get_tasks_data()
        overrides_df = normalized_manager.get_user_overrides_data()

        status = {
            "detailed_report": {
                "loaded": not detailed_df.empty,
                "row_count": len(detailed_df) if not detailed_df.empty else 0,
            },
            "documents_report": {
                "loaded": not documents_df.empty,
                "row_count": len(documents_df) if not documents_df.empty else 0,
            },
            "stages": {
                "loaded": True,
                "row_count": len(normalized_manager.get_stages_data()),
            },
            "checks": {
                "loaded": True,
                "row_count": len(normalized_manager.get_checks_data()),
            },
            "check_results": {
                "loaded": not check_results_df.empty,
                "row_count": len(check_results_df) if not check_results_df.empty else 0,
            },
            "tasks": {
                "loaded": not tasks_df.empty,
                "row_count": len(tasks_df) if not tasks_df.empty else 0,
            },
            "user_overrides": {
                "loaded": not overrides_df.empty,
                "row_count": len(overrides_df) if not overrides_df.empty else 0,
            },
        }

        return {"success": True, "status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ИСХОДНЫЕ ДАННЫЕ ====================

@router.get("/detailed-report")
async def save_detailed_report():
    """
    Сохранение детального отчета с переименованием колонок и форматированием.

    Returns:
        FileResponse: Excel файл с детальным отчетом

    Raises:
        HTTPException: 400 если отчет не загружен
        HTTPException: 500 при ошибках сохранения
    """
    try:
        df = normalized_manager.get_cases_data()

        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="Детальный отчет не загружен")

        print(f"💾 Сохраняем детальный отчет: {len(df)} строк, {len(df.columns)} колонок")

        # Замена значений stageCode на stageName (до переименования колонки)
        stages_df = normalized_manager.get_stages_data()
        if "stageCode" in df.columns:
            df["stageCode"] = df["stageCode"].apply(
                lambda x: format_stage_code(x, stages_df)
            )

        # Переименование колонок
        df = df.rename(columns=DETAILED_AND_DOCUMENTS_RENAME_MAP)

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        save_with_xlsxwriter_formatting(df, filepath, 'Детальный отчет')

        download_filename = generate_filename("detailed_report")

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка сохранения детального отчета: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")


@router.get("/documents-report")
async def save_documents_report():
    """
    Сохранение отчета документов с переименованием колонок и форматированием.

    Returns:
        FileResponse: Excel файл с отчетом документов

    Raises:
        HTTPException: 400 если отчет не загружен
        HTTPException: 500 при ошибках сохранения
    """
    try:
        df = normalized_manager.get_documents_data()

        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="Отчет документов не загружен")

        print(f"💾 Сохраняем отчет документов: {len(df)} строк, {len(df.columns)} колонок")

        # Замена значений stageCode на stageName (до переименования колонки)
        stages_df = normalized_manager.get_stages_data()
        if "stageCode" in df.columns:
            df["stageCode"] = df["stageCode"].apply(
                lambda x: format_stage_code(x, stages_df)
            )

        # Переименование колонок
        df = df.rename(columns=DETAILED_AND_DOCUMENTS_RENAME_MAP)

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        save_with_xlsxwriter_formatting(df, filepath, 'Документы')

        download_filename = generate_filename("documents_report")

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка сохранения отчета документов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")


# ==================== КОНФИГУРАЦИОННЫЕ ДАННЫЕ ====================

@router.get("/stages")
async def save_stages():
    """
    Сохранение сводки этапов с переименованием колонок и форматированием.

    Returns:
        FileResponse: Excel файл с этапами

    Raises:
        HTTPException: 400 если данные не загружены
        HTTPException: 500 при ошибках сохранения
    """
    try:
        df = normalized_manager.get_stages_data()

        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="Данные этапов не загружены")

        print(f"💾 Сохраняем этапы: {len(df)} строк, {len(df.columns)} колонок")

        # Переименование колонок
        df = df.rename(columns=STAGES_RENAME_MAP)

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        save_with_xlsxwriter_formatting(df, filepath, 'Этапы')

        download_filename = generate_filename("stages")

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка сохранения этапов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")


@router.get("/checks")
async def save_checks():
    """
    Сохранение сводки проверок с переименованием колонок и форматированием.

    Returns:
        FileResponse: Excel файл с проверками

    Raises:
        HTTPException: 400 если данные не загружены
        HTTPException: 500 при ошибках сохранения
    """
    try:
        df = normalized_manager.get_checks_data()

        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="Данные проверок не загружены")

        print(f"💾 Сохраняем проверки: {len(df)} строк, {len(df.columns)} колонок")

        # Переименование колонок и замена isActive
        df = df.rename(columns=CHECKS_RENAME_MAP)
        if "isActive" in df.columns:
            df["isActive"] = df["isActive"].apply(format_is_active)

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        save_with_xlsxwriter_formatting(df, filepath, 'Проверки')

        download_filename = generate_filename("checks")

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка сохранения проверок: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")


# ==================== РЕЗУЛЬТАТЫ ПРОВЕРОК ====================

def _prepare_check_results_for_save(df: pd.DataFrame) -> pd.DataFrame:
    """
    Применяет переименование колонок и замену значений для результатов проверок.
    """
    df = df.rename(columns=CHECK_RESULTS_RENAME_MAP)
    if "monitoringStatus" in df.columns:
        df["monitoringStatus"] = df["monitoringStatus"].apply(format_monitoring_status)
    if "completionStatus" in df.columns:
        df["completionStatus"] = df["completionStatus"].apply(format_completion_status)
    return df


@router.get("/check-results/cases")
async def save_check_results_cases():
    """
    Сохранение результатов проверок для дел (исковое + приказное).

    Returns:
        FileResponse: Excel файл с результатами проверок дел

    Raises:
        HTTPException: 400 если данные не найдены
        HTTPException: 500 при ошибках сохранения
    """
    try:
        df = normalized_manager.get_check_results_data()

        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="Результаты проверок не найдены")

        # Фильтрация по суффиксам L и O
        df = df[
            df["checkCode"].str.endswith("L", na=False) |
            df["checkCode"].str.endswith("O", na=False)
        ]

        if df.empty:
            raise HTTPException(status_code=400, detail="Результаты проверок для дел не найдены")

        print(f"💾 Сохраняем результаты проверок дел: {len(df)} строк")

        # Переименование и форматирование
        df = _prepare_check_results_for_save(df)

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        save_with_xlsxwriter_formatting(df, filepath, 'Проверки дел')

        download_filename = generate_filename("check_results_cases")

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка сохранения результатов проверок дел: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")


@router.get("/check-results/documents")
async def save_check_results_documents():
    """
    Сохранение результатов проверок для документов.

    Returns:
        FileResponse: Excel файл с результатами проверок документов

    Raises:
        HTTPException: 400 если данные не найдены
        HTTPException: 500 при ошибках сохранения
    """
    try:
        df = normalized_manager.get_check_results_data()

        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="Результаты проверок не найдены")

        # Фильтрация по суффиксу D
        df = df[df["checkCode"].str.endswith("D", na=False)]

        if df.empty:
            raise HTTPException(status_code=400, detail="Результаты проверок для документов не найдены")

        print(f"💾 Сохраняем результаты проверок документов: {len(df)} строк")

        # Переименование и форматирование
        df = _prepare_check_results_for_save(df)

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        save_with_xlsxwriter_formatting(df, filepath, 'Проверки документов')

        download_filename = generate_filename("check_results_documents")

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка сохранения результатов проверок документов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")


# ==================== ЗАДАЧИ ====================

def _prepare_tasks_for_save(tasks_df: pd.DataFrame) -> pd.DataFrame:
    """
    Обогащает задачи дополнительными колонками, переименовывает и форматирует.
    """
    # Обогащение
    tasks_df = enrich_tasks_for_export(
        tasks_df=tasks_df,
        check_results_df=normalized_manager.get_check_results_data(),
        checks_df=normalized_manager.get_checks_data(),
        stages_df=normalized_manager.get_stages_data(),
        cases_df=normalized_manager.get_cases_data(),
    )

    # Переименование основных колонок
    tasks_df = tasks_df.rename(columns=TASKS_RENAME_MAP)

    # Переименование дополнительных колонок
    tasks_df = tasks_df.rename(columns=TASKS_EXTRA_RENAME_MAP)

    # Замена значений
    if "monitoringStatus" in tasks_df.columns:
        tasks_df["monitoringStatus"] = tasks_df["monitoringStatus"].apply(format_monitoring_status)
    if "completionStatus" in tasks_df.columns:
        tasks_df["completionStatus"] = tasks_df["completionStatus"].apply(format_completion_status)
    if "isCompleted" in tasks_df.columns:
        tasks_df["isCompleted"] = tasks_df["isCompleted"].apply(format_is_completed)

    return tasks_df


@router.get("/tasks")
async def save_tasks():
    """
    Сохранение итогового списка задач с обогащением и форматированием.

    Returns:
        FileResponse: Excel файл с задачами

    Raises:
        HTTPException: 400 если данные не найдены
        HTTPException: 500 при ошибках сохранения
    """
    try:
        df = normalized_manager.get_tasks_data()

        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="Задачи не найдены")

        print(f"💾 Сохраняем задачи: {len(df)} строк")

        # Обогащение, переименование, форматирование
        df = _prepare_tasks_for_save(df)

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        save_with_xlsxwriter_formatting(df, filepath, 'Задачи')

        download_filename = generate_filename("tasks")

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка сохранения задач: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")


@router.get("/tasks-by-executor")
async def save_tasks_by_executor(
    executor: str = Query(..., description="Ответственный исполнитель")
):
    """
    Сохранение списка задач для конкретного исполнителя с обогащением и форматированием.

    Args:
        executor: Ответственный исполнитель

    Returns:
        FileResponse: Excel файл с задачами исполнителя

    Raises:
        HTTPException: 400 если данные не найдены
        HTTPException: 500 при ошибках сохранения
    """
    try:
        df = normalized_manager.get_tasks_data()

        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="Задачи не найдены")

        # Обогащение до фильтрации (чтобы получить responsibleExecutor)
        df = _prepare_tasks_for_save(df)

        # Фильтрация по исполнителю
        if "responsibleExecutor" not in df.columns:
            raise HTTPException(status_code=400, detail="Колонка responsibleExecutor не найдена")

        df = df[df["responsibleExecutor"] == executor]

        if df.empty:
            raise HTTPException(status_code=400, detail=f"Задачи для исполнителя '{executor}' не найдены")

        print(f"💾 Сохраняем задачи для {executor}: {len(df)} строк")

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        save_with_xlsxwriter_formatting(df, filepath, f'Задачи {executor}')

        download_filename = generate_filename("tasks_by_executor", executor)

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка сохранения задач для {executor}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")


# ==================== ПОЛЬЗОВАТЕЛЬСКИЕ ПЕРЕОПРЕДЕЛЕНИЯ ====================

@router.get("/user-overrides")
async def save_user_overrides(
    current_user: UserSession = Depends(get_current_user)
):
    """
    Сохранение пользовательских переопределений задач для текущего пользователя.

    Returns:
        FileResponse: Excel файл с переопределениями

    Raises:
        HTTPException: 401 если не авторизован
        HTTPException: 400 если данные не найдены
        HTTPException: 500 при ошибках сохранения
    """
    try:
        if not current_user.login:
            raise HTTPException(status_code=401, detail="Требуется авторизация")

        df = normalized_manager.get_user_overrides_data()

        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="Пользовательские переопределения не найдены")

        print(f"💾 Сохраняем переопределения для {current_user.login}: {len(df)} строк")

        # Обогащение, переименование, форматирование (аналогично задачам)
        df = _prepare_tasks_for_save(df)
        df = df.rename(columns=USER_OVERRIDES_RENAME_MAP)

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        save_with_xlsxwriter_formatting(df, filepath, f'Изменения {current_user.login}')

        download_filename = generate_filename("user_overrides", current_user.login)

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка сохранения переопределений: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")

