# backend/app/administration_settings/routes/admin.py
from typing import Optional
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import logging

from ..modules.administration_analysis import admin_access_manager

# Загрузка переменных окружения из .env файла
load_dotenv()

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

    Функция определяет активный источник данных на основе переменной SOURCE_ADDRESS,
    формирует путь к папке настроек и делегирует проверку прав в AdminAccessManager.

    Возможные значения SOURCE_ADDRESS:
    - DESKTOP_ADDRESS: используется локальный путь из переменной DESKTOP_ADDRESS
    - NETWORK_FOLDER_ADDRESS: используется сетевой путь из NETWORK_FOLDER_ADDRESS
    - Любое другое значение: по умолчанию DESKTOP_ADDRESS

    Returns:
        AdminStatusResponse: Объект с результатами проверки прав
    """
    try:
        # Получение типа источника из переменных окружения
        source_env = os.getenv('SOURCE_ADDRESS', 'DESKTOP_ADDRESS')

        # Определение конкретного пути в зависимости от типа источника
        if source_env == 'NETWORK_FOLDER_ADDRESS':
            source_address = os.getenv('NETWORK_FOLDER_ADDRESS', '')
            source_type = "сетевая папка"
        else:  # DESKTOP_ADDRESS или другое значение
            source_address = os.getenv('DESKTOP_ADDRESS', '')
            source_type = "локальная папка"

        # Проверка наличия настроенного пути
        if not source_address:
            logger.error(f"SOURCE_ADDRESS не настроен в .env для типа {source_env}")
            return AdminStatusResponse(
                isAdmin=False,
                message="SOURCE_ADDRESS не настроен в конфигурации"
            )

        logger.info(f"Проверка прав доступа. Источник: {source_type}, путь: {source_address}")

        # Делегирование проверки прав в менеджер
        is_admin = admin_access_manager.check_admin_status(source_address)

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


@router.get("/admin-status/debug")
async def admin_status_debug():
    """
    Отладочный эндпоинт для проверки конфигурации.

    Возвращает информацию о текущих настройках без проверки прав.
    Используется только для отладки, не должен быть доступен в production.

    Returns:
        Dict: Информация о конфигурации
    """
    # Только для отладки - в production этот эндпоинт должен быть отключен
    source_env = os.getenv('SOURCE_ADDRESS', 'DESKTOP_ADDRESS')
    desktop = os.getenv('DESKTOP_ADDRESS', 'не задан')
    network = os.getenv('NETWORK_FOLDER_ADDRESS', 'не задан')

    current_user = admin_access_manager.get_current_user()

    return {
        "source_env": source_env,
        "desktop_address": desktop,
        "network_address": network,
        "current_user": current_user,
        "cache_ttl_seconds": admin_access_manager.CACHE_TTL,
        "cache_valid": (
                                   time.time() - admin_access_manager._cache_timestamp) < admin_access_manager.CACHE_TTL if admin_access_manager._cache_timestamp else False
    }