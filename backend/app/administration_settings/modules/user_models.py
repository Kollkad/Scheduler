#backend/app/administration_settings/modules/user_models.py
"""
Модели пользователя и ролей для авторизации.
"""

from enum import Enum
from typing import Optional


class UserRole(str, Enum):
    """Роли пользователей"""
    ADMIN = "Администратор"
    MANAGER = "Руководитель"
    EMPLOYEE = "Сотрудник"
    GUEST = "Гость"


class UserSession:
    """
    Хранит данные пользователя в памяти.
    """

    def __init__(self):
        self.login: Optional[str] = None
        self.email: Optional[str] = None
        self.name: Optional[str] = None
        self.role: Optional[UserRole] = None

    def is_authenticated(self) -> bool:
        """Проверяет, авторизован ли пользователь (не гость)"""
        return self.role is not None and self.role != UserRole.GUEST

    def has_role(self, required_role: UserRole) -> bool:
        """
        Проверяет, имеет ли пользователь требуемую роль или выше.
        Иерархия: Администратор > Руководитель > Сотрудник > Гость
        """
        role_hierarchy = {
            UserRole.ADMIN: 4,
            UserRole.MANAGER: 3,
            UserRole.EMPLOYEE: 2,
            UserRole.GUEST: 1,
            None: 0
        }

        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        return user_level >= required_level

    def set_user(self, login: str, email: str, name: str, role: UserRole):
        """Устанавливает данные пользователя"""
        self.login = login
        self.email = email
        self.name = name
        self.role = role

    def set_guest(self):
        """Устанавливает гостевой режим"""
        self.login = None
        self.email = None
        self.name = None
        self.role = UserRole.GUEST

    def clear(self):
        """Очищает сессию"""
        self.__init__()