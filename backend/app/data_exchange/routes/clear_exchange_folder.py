# backend/app/data_exchange/routes/clear_exchange_folder.py
"""
Маршрут для очистки папки обмена данными.

Предоставляет эндпоинт для удаления всех файлов из app_data.
"""

from fastapi import APIRouter, HTTPException

from backend.app.data_exchange.modules.data_io import clear_exchange_folder

router = APIRouter(prefix="/api/exchange", tags=["data_exchange"])


@router.post("/clear-app-data")
async def clear_app_data():
    """
    Удаляет все файлы из папки обмена (app_data).

    Используется руководителем для очистки старых данных
    перед новой выгрузкой.

    Returns:
        Dict: Результат очистки

    Raises:
        HTTPException: 500 при ошибке удаления файлов
    """
    try:
        clear_exchange_folder()
        return {
            "success": True,
            "message": "Папка обмена очищена. Все файлы удалены."
        }

    except Exception as e:
        print(f"❌ Ошибка очистки папки обмена: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка очистки: {str(e)}")


