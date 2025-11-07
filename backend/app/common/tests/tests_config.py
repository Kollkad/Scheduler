# tests_config.py
"""
Конфигурация системы тестирования
"""

import os
from pathlib import Path


def _get_test_files():
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
    dev_paths = {
        "detailed": PROJECT_ROOT / "app" / "data" / "dev_data" / "detailed.xlsx",
        "documents": PROJECT_ROOT / "app" / "data" / "dev_data" / "documents.xlsx"
    }
    sample_paths = {
        "detailed": PROJECT_ROOT / "app" / "data" / "sample_test_data" / "detailed_sample.xlsx",
        "documents": PROJECT_ROOT / "app" / "data" / "sample_test_data" / "documents_sample.xlsx"
    }

    if all(p.exists() for p in dev_paths.values()):
        print("✅ Используются dev тестовые данные")
        return dev_paths
    else:
        print("✅ Используются sample тестовые данные")
        return sample_paths


class TestsConfig:
    """Конфигурация тестовой системы"""

    # Базовые пути
    TESTS_DIR = Path(__file__).parent
    PROJECT_ROOT = TESTS_DIR.parent.parent.parent

    # Пути к типам тестов
    AUTO_TESTS_DIR = TESTS_DIR / 'auto'
    CONSOLE_TESTS_DIR = TESTS_DIR / 'console'
    SHARED_DIR = TESTS_DIR / 'shared'

    # Dev данные
    DEV_DATA_DIR = PROJECT_ROOT / 'app' / 'data' / 'dev_data'

    # Примерные данные
    SAMPLE_DATA_DIR = PROJECT_ROOT / 'app' / 'data' / 'sample_test_data'

    TEST_FILES = _get_test_files()

    # Путь для сохранения результатов
    RESULTS_DIR = PROJECT_ROOT / 'app' / 'data' / 'auto_test'

    # Настройки обнаружения тестов
    EXCLUDED_FILES = {'__init__.py', '__pycache__', 'tests_config.py'}

    @classmethod
    def validate_paths(cls):
        required_dirs = [
            cls.AUTO_TESTS_DIR,
            cls.CONSOLE_TESTS_DIR,
            cls.SHARED_DIR,
            cls.RESULTS_DIR,
            cls.DEV_DATA_DIR,
            cls.SAMPLE_DATA_DIR
        ]

        for directory in required_dirs:
            directory.mkdir(parents=True, exist_ok=True)

        return True


# Создание директорий при импорте
TestsConfig.validate_paths()