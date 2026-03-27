# backend/app/administration_settings/modules/administration_analysis.py

import os
import socket
import time
from pathlib import Path
from typing import Optional, Set, Tuple
import logging

from backend.app.administration_settings.modules.assistant_functions import get_working_directory

logger = logging.getLogger(__name__)


class AdminAccessManager:
    """Менеджер для проверки прав администратора с кэшированием по времени"""

    # Время жизни кэша в секундах (5 минут)
    CACHE_TTL = 300

    def __init__(self):
        # Инициализация кэша: None означает отсутствие данных
        self._cached_admins: Optional[Set[str]] = None
        self._cached_user: Optional[str] = None
        self._cache_timestamp: float = 0

    def get_current_user(self) -> str:
        """
        Получает имя текущего системного пользователя.

        Функция пытается получить имя пользователя из переменных окружения
        операционной системы. Для Windows используется USERNAME, для Unix-подобных
        систем используется модуль pwd. В случае неудачи возвращает имя хоста.

        Returns:
            str: Имя пользователя в нижнем регистре
        """
        try:
            # Для Windows получение имени из переменных окружения
            username = os.environ.get('USERNAME', '')
            if username:
                return username.lower()
        except Exception as e:
            logger.debug(f"Не удалось получить USERNAME: {e}")

        try:
            # Для Unix-подобных систем (Linux, macOS)
            import pwd
            return pwd.getpwuid(os.getuid()).pw_name.lower()
        except Exception as e:
            logger.debug(f"Не удалось получить имя через pwd: {e}")

        # Финальное резервное значение - имя хоста
        return socket.gethostname().lower()

    def get_settings_path(self, working_dir: str) -> Path:
        """
        Формирует путь к папке с настройками на основе рабочей директории.

        Args:
            working_dir: Базовая рабочая директория из get_working_directory()

        Returns:
            Path: Путь к папке settings
        """
        base_path = Path(working_dir)
        return base_path / "settings"

    def read_access_rights_file(self, settings_path: Path) -> Set[str]:
        """
        Читает файл с правами доступа из указанной директории.

        Файл access_rights.txt должен содержать список имен пользователей,
        каждое с новой строки. Строки, начинающиеся с '#', считаются комментариями
        и игнорируются. Пустые строки также пропускаются.

        Args:
            settings_path: Путь к папке settings

        Returns:
            Set[str]: Множество имен пользователей с правами администратора
        """
        access_file = settings_path / "access_rights.txt"

        # Проверка существования файла
        if not access_file.exists():
            logger.warning(f"Файл доступа не найден: {access_file}")
            return set()

        try:
            with open(access_file, 'r', encoding='utf-8') as f:
                # Чтение всех строк, удаление пробельных символов,
                # пропуск пустых строк и комментариев
                admins = set()
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        admins.add(line.lower())

            logger.info(f"Загружено {len(admins)} администраторов из файла")
            return admins

        except Exception as e:
            logger.error(f"Ошибка чтения файла доступа: {e}")
            return set()

    def _is_cache_valid(self) -> bool:
        """
        Проверяет актуальность кэша на основе времени.

        Кэш считается валидным, если с момента последнего обновления
        прошло меньше CACHE_TTL секунд.

        Returns:
            bool: True если кэш актуален, False если требуется обновление
        """
        return (time.time() - self._cache_timestamp) < self.CACHE_TTL

    def _update_cache(self, admins: Set[str], current_user: str) -> None:
        """
        Обновляет кэш с данными администраторов.

        Args:
            admins: Множество имен администраторов
            current_user: Имя текущего пользователя
        """
        self._cached_admins = admins
        self._cached_user = current_user
        self._cache_timestamp = time.time()
        logger.debug("Кэш прав доступа обновлен")

    def _clear_cache(self) -> None:
        """Принудительно очищает кэш."""
        self._cached_admins = None
        self._cached_user = None
        self._cache_timestamp = 0
        logger.debug("Кэш прав доступа очищен")

    def check_admin_status(self) -> bool:
        """
        Проверяет, является ли текущий пользователь администратором.

        Функция реализует кэширование результатов с временем жизни CACHE_TTL.
        При первом вызове или истечении TTL выполняется чтение файла из рабочей директории.
        Последующие вызовы в пределах TTL используют кэшированные данные.

        Алгоритм работы:
        1. Получение рабочей директории через get_working_directory()
        2. Получение имени текущего системного пользователя
        3. Проверка актуальности кэша
        4. Если кэш неактуален - чтение файла access_rights.txt
        5. Обновление кэша
        6. Проверка наличия пользователя в списке администраторов

        Returns:
            bool: True если пользователь в списке администраторов, иначе False
        """
        try:
            # Получение рабочей директории
            working_dir = get_working_directory()
            if not working_dir:
                logger.error("Не удалось определить рабочую директорию")
                return False

            # Получение имени текущего пользователя
            current_user = self.get_current_user()

            # Проверка актуальности кэша
            if self._is_cache_valid() and self._cached_admins is not None:
                logger.debug("Использование кэшированных данных прав доступа")
                return current_user in self._cached_admins

            logger.info("Кэш устарел или отсутствует, выполняется чтение файла")

            # Получение пути к папке настроек
            settings_path = self.get_settings_path(working_dir)
            logger.info(f"Путь к настройкам: {settings_path}")

            # Чтение файла с правами доступа
            admins = self.read_access_rights_file(settings_path)

            # Обновление кэша
            self._update_cache(admins, current_user)

            # Проверка наличия пользователя в списке
            is_admin = current_user in admins
            logger.info(f"Статус администратора для {current_user}: {is_admin}")

            return is_admin

        except Exception as e:
            logger.error(f"Ошибка проверки прав администратора: {e}")
            return False


# Создание глобального экземпляра менеджера для использования во всем приложении
admin_access_manager = AdminAccessManager()