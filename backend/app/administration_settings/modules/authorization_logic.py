# backend/app/administration_settings/modules/authorization_logic.py
"""
Модуль для авторизации пользователей на основе системного логина
"""

import os
import socket
import logging
from pathlib import Path
from typing import Optional, Dict

import pandas as pd
from fastapi import Request

from backend.app.administration_settings.modules.assistant_functions import get_working_directory, get_work_mode
from backend.app.administration_settings.modules.session_storage import create_session, get_session
from backend.app.administration_settings.modules.user_models import UserSession, UserRole
from backend.app.common.config.column_names import COLUMNS

logger = logging.getLogger(__name__)


def get_system_login() -> str:
    """
    Получает системный логин текущего пользователя.
    """
    try:
        username = os.environ.get('USERNAME', '')
        if username:
            return username.lower()
    except Exception:
        pass

    try:
        import pwd
        return pwd.getpwuid(os.getuid()).pw_name.lower()
    except Exception:
        pass

    return socket.gethostname().lower()


def get_allowed_users_file_path(working_dir: str) -> Optional[Path]:
    """Формирует путь к файлу allowed_users.xlsx."""
    if not working_dir:
        return None
    return Path(working_dir) / "settings" / "allowed_users.xlsx"


def read_allowed_users(working_dir: str) -> Dict[str, Dict[str, str]]:
    """
    Читает файл allowed_users.xlsx и возвращает словарь пользователей.
    """
    users_dict = {}
    file_path = get_allowed_users_file_path(working_dir)

    if not file_path or not file_path.exists():
        logger.warning(f"Файл пользователей не найден: {file_path}")
        return users_dict

    try:
        df = pd.read_excel(file_path, dtype=str)

        login_col = None
        email_col = None
        name_col = None
        role_col = None

        for col in df.columns:
            if col == COLUMNS.get('USER_LOGIN', 'Логин'):
                login_col = col
            elif col == COLUMNS.get('USER_EMAIL', 'Почта'):
                email_col = col
            elif col == COLUMNS.get('USER_FIO', 'ФИО'):
                name_col = col
            elif col == COLUMNS.get('USER_ROLE', 'Роль'):
                role_col = col

        if not login_col or not email_col or not name_col:
            logger.error(f"Не найдены обязательные колонки. Доступные: {list(df.columns)}")
            return users_dict

        for _, row in df.iterrows():
            login = str(row[login_col]).strip().lower() if pd.notna(row[login_col]) else None
            email = str(row[email_col]).strip() if pd.notna(row[email_col]) else None
            name = str(row[name_col]).strip() if pd.notna(row[name_col]) else None
            role = str(row[role_col]).strip() if role_col and pd.notna(row[role_col]) else 'Сотрудник'

            if login and email and name:
                users_dict[login] = {
                    'email': email,
                    'name': name,
                    'role': role
                }

        logger.info(f"Загружено {len(users_dict)} пользователей")

    except Exception as e:
        logger.error(f"Ошибка чтения файла пользователей: {e}")

    return users_dict


def get_user_by_login(login: str, working_dir: str) -> Optional[Dict[str, str]]:
    """Ищет пользователя по системному логину."""
    if not login:
        return None

    login_lower = login.strip().lower()
    users = read_allowed_users(working_dir)

    if login_lower in users:
        logger.info(f"Пользователь найден: {login_lower}")
        return users[login_lower]

    logger.debug(f"Пользователь не найден: {login_lower}")
    return None


def get_dev_default_user() -> Dict[str, str]:
    """Возвращает тестового пользователя для режима разработки."""
    import os
    return {
        'login': os.getenv('DEV_USER_LOGIN', get_system_login()),
        'email': os.getenv('DEV_USER_EMAIL', 'developer@sbrf.com'),
        'name': os.getenv('DEV_USER_NAME', 'Аккаунт Разработчика'),
        'role': os.getenv('DEV_USER_ROLE', 'Администратор')
    }


def _create_user_session(working_dir: str, is_dev_mode: bool) -> UserSession:
    """
    Создает сессию пользователя на основе системного логина или DEV режима.
    """
    user = UserSession()

    if is_dev_mode:
        dev_user = get_dev_default_user()
        role = None
        for r in UserRole:
            if r.value == dev_user['role']:
                role = r
                break
        user.set_user(
            login=dev_user['login'],
            email=dev_user['email'],
            name=dev_user['name'],
            role=role or UserRole.ADMIN
        )
        logger.info(f"DEV режим: создана сессия для {dev_user['name']}")
        return user

    if not working_dir:
        logger.error("Не удалось определить рабочую директорию")
        user.set_guest()
        return user

    system_login = get_system_login()
    logger.info(f"Системный логин: {system_login}")

    user_data = get_user_by_login(system_login, working_dir)

    if user_data:
        role = UserRole.GUEST
        for r in UserRole:
            if r.value == user_data['role']:
                role = r
                break
        user.set_user(
            login=system_login,
            email=user_data['email'],
            name=user_data['name'],
            role=role
        )
        logger.info(f"Пользователь авторизован: {system_login} ({user_data['name']})")
    else:
        user.set_guest()
        logger.info(f"Пользователь {system_login} не найден, гостевой режим")

    return user


async def get_current_user(request: Request) -> UserSession:
    """
    Dependency для FastAPI. Получает текущего пользователя по session_id из cookies.
    """
    session_id = request.cookies.get('session_id')

    if session_id:
        user = get_session(session_id)
        if user:
            return user

    # Создаем новую сессию
    work_mode = get_work_mode()
    is_dev = work_mode == 'DEV'
    working_dir = get_working_directory()

    user = _create_user_session(working_dir, is_dev)

    # Сохраняем сессию
    new_session_id = create_session(user)

    # Устанавливаем cookies в response (через request.state)
    request.state.new_session_id = new_session_id

    return user