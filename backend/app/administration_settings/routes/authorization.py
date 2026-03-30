# backend/app/administration_settings/routes/authorization.py
"""
Роуты для авторизации пользователей.
"""

import logging
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from pydantic import BaseModel
from typing import Optional

from backend.app.administration_settings.modules.user_models import UserSession, UserRole
from backend.app.administration_settings.modules.authorization_logic import get_current_user, get_system_login
from backend.app.administration_settings.modules.session_storage import delete_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


class AuthStatusResponse(BaseModel):
    authenticated: bool
    login: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None


class AuthLoginResponse(BaseModel):
    success: bool
    authenticated: bool
    login: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    message: str


class UserInfoResponse(BaseModel):
    login: str
    email: Optional[str] = None
    name: Optional[str] = None
    role: str


@router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status(current_user: UserSession = Depends(get_current_user)):
    """
    Получение текущего статуса авторизации.
    """
    return AuthStatusResponse(
        authenticated=current_user.is_authenticated(),
        login=current_user.login,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role.value if current_user.role else None
    )


@router.post("/login", response_model=AuthLoginResponse)
async def login(
    request: Request,
    response: Response,
    current_user: UserSession = Depends(get_current_user)
):
    """
    Выполняет авторизацию пользователя. Устанавливает session_id в cookies.
    """
    try:
        # Если в get_current_user был создан новый session_id — устанавливаем cookies
        if hasattr(request.state, 'new_session_id'):
            response.set_cookie(
                key="session_id",
                value=request.state.new_session_id,
                httponly=True,
                secure=False,
                samesite="lax"
            )

        return AuthLoginResponse(
            success=True,
            authenticated=current_user.is_authenticated(),
            login=current_user.login,
            email=current_user.email,
            name=current_user.name,
            role=current_user.role.value if current_user.role else None,
            message="Авторизация выполнена"
        )

    except Exception as e:
        logger.error(f"Ошибка при авторизации: {e}")
        return AuthLoginResponse(
            success=False,
            authenticated=False,
            message=f"Ошибка: {str(e)}"
        )


@router.post("/logout")
async def logout(request: Request, response: Response):
    """
    Выход из системы (очистка сессии и удаление cookies).
    """
    session_id = request.cookies.get('session_id')
    if session_id:
        delete_session(session_id)

    response.delete_cookie("session_id")
    logger.info("Пользователь вышел из системы")
    return {"success": True, "message": "Выход выполнен"}


@router.get("/user-info", response_model=UserInfoResponse)
async def get_user_info(current_user: UserSession = Depends(get_current_user)):
    """
    Получение информации о текущем пользователе.
    """
    if not current_user.login:
        raise HTTPException(status_code=401, detail="Не авторизован")

    return UserInfoResponse(
        login=current_user.login or get_system_login(),
        email=current_user.email,
        name=current_user.name,
        role=current_user.role.value if current_user.role else "Гость"
    )