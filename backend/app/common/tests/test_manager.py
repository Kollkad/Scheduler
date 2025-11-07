class TestManager:
    """Управление и запуск тестов"""

    def __init__(self):
        self.tests_registry = {
            'auto': {},
            'console': {}
        }

    def register_test(self, test_type, test_name, test_function):
        """Регистрация теста в системе"""
        self.tests_registry[test_type][test_name] = test_function

    def list_tests(self, test_type=None):
        """Показать доступные тесты"""
        # ... простая логика показа тестов

    def run_auto_test(self, test_name):
        """Запуск автотеста"""
        # ... запуск без параметров

    def run_console_test(self, test_name, **kwargs):
        """Запуск консольного теста с параметрами"""
        # ... запуск с переданными параметрами