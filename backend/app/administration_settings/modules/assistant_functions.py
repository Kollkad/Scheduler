# backend/app/administration_settings/modules/assistant_functions.py
"""
Модуль содержит вспомогательные функции для администрирования приложения.
Обеспечивает утилитарные функции для работы с конфигурациями, файловой системой
и другими административными задачами.

Основные функции:
    get_working_directory() - определение рабочей директории на основе режима работы
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


def get_working_directory() -> Optional[str]:
    """
    Определяет рабочую директорию для хранения важных файлов на основе режима работы.

    Функция загружает переменные окружения из файла .env и анализирует параметр WORK_MODE.
    В зависимости от его значения возвращает соответствующий путь к директории:
    - для режима DEV используется DESKTOP_ADDRESS
    - для режима DEPLOY используется NETWORK_FOLDER_ADDRESS

    Если переменная WORK_MODE отсутствует или имеет пустое значение,
    функция по умолчанию использует режим DEPLOY.

    Args:
        Нет параметров

    Returns:
        Optional[str]: Строка с путем к рабочей директории или None, если:
            - не удалось загрузить переменные окружения
            - WORK_MODE имеет недопустимое значение
            - требуемая переменная окружения отсутствует
    """

    # Определение пути
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent
    env_path = project_root / '.env'
    
    # Загрузка переменных окружения из файла .env
    load_dotenv(dotenv_path=env_path, override=True)
    # Получение режима работы из переменных окружения
    work_mode = os.getenv('WORK_MODE')

    # Если переменная WORK_MODE отсутствует или пустая, используется режим DEPLOY по умолчанию
    if not work_mode:
        work_mode = 'DEPLOY'

    # Определение рабочей директории в зависимости от режима работы
    if work_mode == 'DEV':
        # Режим разработки - используется локальная директория на рабочем столе
        directory_path = os.getenv('DESKTOP_ADDRESS')
        if not directory_path:
            return None
    elif work_mode == 'DEPLOY':
        # Режим развертывания - используется сетевая папка
        directory_path = os.getenv('NETWORK_FOLDER_ADDRESS')
        if not directory_path:
            return None
    else:
        raise ValueError(f"Недопустимое значение WORK_MODE: {work_mode}. Допустимые значения: DEV, DEPLOY")
    path_object = Path(directory_path)

    # Создание директории, если она не существует
    if not path_object.exists():
        try:
            path_object.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return None

    return str(path_object.resolve())


def get_work_mode() -> str:
    """
    Возвращает режим работы приложения.

    Returns:
        str: 'DEV' или 'DEPLOY'
    """
    from dotenv import load_dotenv
    from pathlib import Path

    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent
    env_path = project_root / 'backend' / '.env'

    load_dotenv(dotenv_path=env_path, override=True)

    work_mode = os.getenv('WORK_MODE', 'DEPLOY')
    return work_mode if work_mode in ['DEV', 'DEPLOY'] else 'DEPLOY'

