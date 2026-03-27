# backend/app/administration_settings/routes/admin.py
from typing import Optional
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from ..modules.administration_analysis import admin_access_manager
from ..modules.assistant_functions import get_working_directory

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["admin"])


class AdminStatusResponse(BaseModel):
    """
    Модель ответа с информацией о правах администратора.

    Attributes:
        isAdmin: Флаг, указывающий наличие прав администратора
        message: Текстовое пояснение к статусу
        cacheValid: Флаг актуальности кэша (опционально)
    """
    isAdmin: bool
    message: str = ""
    cacheValid: Optional[bool] = None


@router.get("/admin-status", response_model=AdminStatusResponse)
async def get_admin_status():
    """
    Эндпоинт для проверки прав администратора текущего пользователя.

    Функция получает рабочую директорию через get_working_directory() и
    делегирует проверку прав в AdminAccessManager.

    Returns:
        AdminStatusResponse: Объект с результатами проверки прав
    """
    try:
        # Получение рабочей директории
        working_dir = get_working_directory()
        if not working_dir:
            logger.error("Не удалось определить рабочую директорию")
            return AdminStatusResponse(
                isAdmin=False,
                message="Не удалось определить рабочую директорию"
            )

        logger.info(f"Проверка прав доступа. Рабочая директория: {working_dir}")

        # Делегирование проверки прав в менеджер
        is_admin = admin_access_manager.check_admin_status()

        # Формирование информационного сообщения
        if is_admin:
            message = "Пользователь имеет права администратора"
        else:
            message = "Пользователь не имеет прав администратора"

        # Получение статуса кэша для отладки (опционально)
        cache_valid = hasattr(admin_access_manager, '_cache_timestamp') and \
                      (time.time() - admin_access_manager._cache_timestamp) < admin_access_manager.CACHE_TTL

        return AdminStatusResponse(
            isAdmin=is_admin,
            message=message,
            cacheValid=cache_valid
        )

    except Exception as e:
        logger.error(f"Ошибка в эндпоинте admin-status: {e}", exc_info=True)
        return AdminStatusResponse(
            isAdmin=False,
            message="Внутренняя ошибка сервера при проверке прав доступа"
        )


@router.post("/admin-status/reset-cache")
async def reset_admin_cache():
    """
    Принудительный сброс кэша прав доступа.

    Эндпоинт предназначен для отладки и административных целей.
    Очищает внутренний кэш менеджера, forcing повторное чтение файла
    при следующем запросе /admin-status.

    Returns:
        Dict: Сообщение о результате операции
    """
    try:
        admin_access_manager._clear_cache()
        logger.info("Кэш прав доступа принудительно сброшен")
        return {"message": "Кэш прав доступа успешно сброшен"}
    except Exception as e:
        logger.error(f"Ошибка при сбросе кэша: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сбросе кэша")

