# backend/app/administration_settings/modules/session_storage.py
"""
Хранилище сессий пользователей в памяти.
"""

import uuid
from typing import Dict, Optional
from backend.app.administration_settings.modules.user_models import UserSession


# Хранилище сессий: {session_id: UserSession}
_sessions: Dict[str, UserSession] = {}


def create_session(user: UserSession) -> str:
    """
    Создает новую сессию и возвращает session_id.
    """
    session_id = str(uuid.uuid4())
    _sessions[session_id] = user
    return session_id


def get_session(session_id: str) -> Optional[UserSession]:
    """
    Получает сессию по id.
    """
    return _sessions.get(session_id)


def delete_session(session_id: str) -> None:
    """
    Удаляет сессию.
    """
    if session_id in _sessions:
        del _sessions[session_id]