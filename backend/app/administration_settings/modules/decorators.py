# backend/app/administration_settings/modules/decorators.py
"""
Декораторы для проверки прав доступа.
"""

from functools import wraps
from fastapi import HTTPException, status, Depends

from backend.app.administration_settings.modules.user_models import UserSession, UserRole
from backend.app.administration_settings.modules.authorization_logic import get_current_user


def require_auth(func):
    """
    Декоратор: требует авторизации пользователя (не гость).
    """
    @wraps(func)
    async def wrapper(*args, current_user: UserSession = Depends(get_current_user), **kwargs):
        if not current_user.is_authenticated():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Требуется авторизация"
            )
        return await func(*args, current_user=current_user, **kwargs)
    return wrapper


def require_role(required_role: UserRole):
    """
    Декоратор: требует определенную роль или выше.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: UserSession = Depends(get_current_user), **kwargs):
            if not current_user.has_role(required_role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Недостаточно прав. Требуется роль: {required_role.value}"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


def require_admin(func):
    """Сокращение: требует роль Администратор"""
    return require_role(UserRole.ADMIN)(func)


def require_manager(func):
    """Сокращение: требует роль Руководитель или выше"""
    return require_role(UserRole.MANAGER)(func)

def require_manager_or_admin(func):
    """Требует роль Руководитель или выше."""
    @wraps(func)
    async def wrapper(*args, current_user: UserSession = Depends(get_current_user), **kwargs):
        if not current_user.has_role(UserRole.MANAGER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав. Требуется роль Руководитель или выше"
            )
        return await func(*args, current_user=current_user, **kwargs)
    return wrapper
