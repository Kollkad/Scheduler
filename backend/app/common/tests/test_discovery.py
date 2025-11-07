# backend/app/common/tests/test_discovery.py
"""
Автоматическое обнаружение тестов в папках auto/ и console/
"""

import importlib
import sys
import os
from pathlib import Path

# Добавляем путь для импортов
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from tests_config import TestsConfig


class TestDiscovery:
    """Обнаружение и загрузка тестов"""

    @staticmethod
    def discover_tests():
        """Находит все тесты в папках auto и console"""
        tests = {'auto': {}, 'console': {}}

        for test_type in ['auto', 'console']:
            type_dir = getattr(TestsConfig, f"{test_type.upper()}_TESTS_DIR")

            if type_dir.exists():
                for file_path in type_dir.glob("*.py"):
                    if file_path.name in TestsConfig.EXCLUDED_FILES:
                        continue

                    test_name = file_path.stem
                    # Используем абсолютный путь к модулю
                    module_path = f"backend.app.common.tests.{test_type}.{test_name}"

                    tests[test_type][test_name] = {
                        'module_path': module_path,
                        'file_path': file_path,
                        'type': test_type
                    }

        return tests

    @staticmethod
    def load_test(test_info):
        """Динамически загружает тест"""
        try:
            module = importlib.import_module(test_info['module_path'])
            if hasattr(module, 'run'):
                return getattr(module, 'run')
            else:
                print(f"❌ Тест {test_info['module_path']} не имеет функции run()")
                return None
        except Exception as e:
            print(f"❌ Ошибка загрузки теста {test_info['module_path']}: {e}")
            import traceback
            traceback.print_exc()
            return None