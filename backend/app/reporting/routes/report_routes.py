# backend/app/reporting/routes/report_routes.py
"""
Маршруты для управления репортами.

Предоставляет API для просмотра списка репортов, получения информации,
скачивания и удаления репортов.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional

from backend.app.reporting.modules.report_builder import (
    list_reports,
    delete_report,
    retry_save_operation,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/")
async def get_reports_list(
    report_type: Optional[str] = Query(None, description="Фильтр по типу репорта")
):
    """
    Возвращает список всех сохранённых репортов.

    Args:
        report_type: Код типа репорта для фильтрации (опционально)

    Returns:
        Dict: Список репортов с метаданными
    """
    try:
        def fetch():
            return list_reports(report_type)

        reports = retry_save_operation(fetch)  # retry для доступа к сетевой папке

        return {
            "success": True,
            "reports": reports,
            "total": len(reports),
            "message": f"Найдено {len(reports)} репортов"
        }

    except Exception as e:
        print(f"❌ Ошибка получения списка репортов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка: {str(e)}")


@router.get("/{report_id}")
async def get_report_info(report_id: str):
    """
    Возвращает информацию о конкретном репорте.

    Args:
        report_id: Идентификатор репорта (имя файла без расширения)

    Returns:
        Dict: Информация о репорте

    Raises:
        HTTPException: 404 если репорт не найден
    """
    try:
        def fetch():
            return list_reports()

        all_reports = retry_save_operation(fetch)

        report = next((r for r in all_reports if r["id"] == report_id), None)

        if not report:
            raise HTTPException(status_code=404, detail=f"Репорт '{report_id}' не найден")

        return {
            "success": True,
            "report": report,
            "message": "Информация о репорте получена"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка получения информации о репорте: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения информации: {str(e)}")


@router.get("/{report_id}/download")
async def download_report(report_id: str):
    """
    Скачивает Excel-файл репорта.

    Args:
        report_id: Идентификатор репорта (имя файла без расширения)

    Returns:
        FileResponse: Excel-файл репорта

    Raises:
        HTTPException: 404 если репорт не найден
    """
    try:
        def fetch():
            return list_reports()

        all_reports = retry_save_operation(fetch)

        report = next((r for r in all_reports if r["id"] == report_id), None)

        if not report:
            raise HTTPException(status_code=404, detail=f"Репорт '{report_id}' не найден")

        filepath = Path(report["filepath"])
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Файл репорта не найден на диске")

        return FileResponse(
            path=str(filepath),
            filename=f"{report_id}.xlsx",
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка скачивания репорта: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка скачивания: {str(e)}")


@router.delete("/{report_id}")
async def delete_report_route(report_id: str):
    """
    Удаляет репорт по его идентификатору.

    Args:
        report_id: Идентификатор репорта (имя файла без расширения)

    Returns:
        Dict: Результат удаления

    Raises:
        HTTPException: 404 если репорт не найден
    """
    try:
        def perform_delete():
            result = delete_report(report_id)
            if not result:
                raise HTTPException(status_code=404, detail=f"Репорт '{report_id}' не найден")
            return result

        retry_save_operation(perform_delete)

        return {
            "success": True,
            "message": f"Репорт '{report_id}' успешно удален"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка удаления репорта: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка удаления: {str(e)}")




