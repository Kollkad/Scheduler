# backend/app/task_manager/routes/task_overrides.py
"""
Маршруты для управления пользовательскими переопределениями задач.

Предоставляет API для:
- Отметки задачи выполненной
- Переноса плановой даты
- Удаления переопределений
- Получения допустимых причин переноса
"""

from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Optional, Dict, Any

from backend.app.task_manager.modules.task_override_manager import task_override_manager
from backend.app.administration_settings.modules.authorization_logic import get_current_user
from backend.app.administration_settings.modules.user_models import UserSession

router = APIRouter(prefix="/api/tasks", tags=["task_overrides"])


@router.patch("/{task_code}")
async def update_task_override(
    task_code: str,
    current_user: UserSession = Depends(get_current_user),
    is_completed: Optional[bool] = Body(None),
    shift_code: Optional[str] = Body(None)
):
    """
    Создает или обновляет пользовательское переопределение задачи.

    Может использоваться для:
    - Отметки задачи выполненной (isCompleted = true)
    - Переноса плановой даты (shiftCode = "judges_vacation")
    - Одновременного выполнения и переноса

    Args:
        task_code: Код задачи
        is_completed: Новый статус выполнения (опционально)
        shift_code: Код причины переноса срока (опционально)

    Returns:
        Dict: Обновленная задача

    Raises:
        HTTPException: 400 если не переданы параметры
        HTTPException: 400 если задача не найдена или причина недопустима
        HTTPException: 500 при ошибках обработки
    """
    try:
        if is_completed is None and shift_code is None:
            raise HTTPException(
                status_code=400,
                detail="Необходимо указать хотя бы один параметр: isCompleted или shiftCode"
            )

        if not current_user.login:
            raise HTTPException(status_code=401, detail="Требуется авторизация")

        updated_task = task_override_manager.apply_override(
            task_code=task_code,
            created_by=current_user.login,
            is_completed=is_completed,
            shift_code=shift_code
        )

        return {
            "success": True,
            "task": updated_task,
            "message": "Изменения сохранены"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка обновления задачи: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обновления: {str(e)}")


@router.delete("/{task_code}/override")
async def delete_task_override(task_code: str):
    """
    Удаляет пользовательское переопределение задачи.

    Возвращает задачу к исходному состоянию (из _tasks).

    Args:
        task_code: Код задачи

    Returns:
        Dict: Результат удаления
    """
    try:
        deleted = task_override_manager.delete_override(task_code)

        if deleted:
            return {
                "success": True,
                "message": f"Переопределение для задачи {task_code} удалено"
            }
        else:
            return {
                "success": True,
                "message": f"Переопределение для задачи {task_code} не найдено"
            }

    except Exception as e:
        print(f"❌ Ошибка удаления переопределения: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка удаления: {str(e)}")


@router.get("/{task_code}/shift-reasons")
async def get_shift_reasons(task_code: str):
    """
    Возвращает список причин переноса срока, допустимых для задачи.

    Args:
        task_code: Код задачи

    Returns:
        Dict: Список допустимых причин
    """
    try:
        reasons = task_override_manager.get_shift_reasons_for_task(task_code)

        return {
            "success": True,
            "taskCode": task_code,
            "shiftReasons": reasons,
            "message": f"Найдено {len(reasons)} допустимых причин"
        }

    except Exception as e:
        print(f"❌ Ошибка получения причин переноса: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения причин: {str(e)}")



