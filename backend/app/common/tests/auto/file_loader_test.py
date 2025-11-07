# backend/app/common/tests/auto/file_loader_test.py
"""
Тест загрузки файлов - проверяет доступность и загружает тестовые данные

Это автотест - запускается полностью автоматически
"""

import os
import sys
import pandas as pd

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

from backend.app.common.modules.data_manager import data_manager
from backend.app.common.tests.tests_config import TestsConfig


def run():
    """
    Основная функция теста - должна возвращать bool (успех/неудача)

    Returns:
        bool: True если тест пройден успешно
    """
    print("\n" + "=" * 50)
    print("🔄 ТЕСТ ЗАГРУЗКИ ФАЙЛОВ")
    print("=" * 50)

    try:
        # Проверяем существование файлов
        print("\n📁 ПРОВЕРКА ФАЙЛОВ:")
        file_status = check_files_exist()
        missing_files = [ft for ft, status in file_status.items() if not status["exists"]]

        if missing_files:
            print(f"❌ Тест провален: отсутствуют файлы {missing_files}")
            return False

        # Загружаем файлы
        print("\n📥 ЗАГРУЗКА ФАЙЛОВ...")
        result = load_test_files()

        if not result["success"] or not result["loaded"]:
            print(f"❌ Тест провален: {result.get('message', 'Ошибка загрузки')}")
            return False

        # Показываем статус
        print_data_status()

        print("\n✅ ТЕСТ ЗАГРУЗКИ ФАЙЛОВ УСПЕШНО ЗАВЕРШЕН!")
        return True

    except Exception as e:
        print(f"❌ Критическая ошибка в тесте: {e}")
        return False


def check_files_exist(file_paths: dict = None) -> dict:
    """Проверяет существование тестовых файлов"""
    if file_paths is None:
        file_paths = {k: str(v) for k, v in TestsConfig.TEST_FILES.items()}

    status = {}
    for file_type, path in file_paths.items():
        exists = os.path.exists(path)
        status[file_type] = {
            "exists": exists,
            "path": path,
            "size": os.path.getsize(path) if exists else 0
        }
        print(f"   {file_type}: {'✅' if exists else '❌'} {path}")

    return status


def load_test_files(file_paths: dict = None, force_reload: bool = False) -> dict:
    """Загружает тестовые файлы в data_manager"""
    if file_paths is None:
        file_paths = {k: str(v) for k, v in TestsConfig.TEST_FILES.items()}

    try:
        # Очищаем данные если принудительная перезагрузка
        if force_reload:
            data_manager.clear_data("all")

        results = {}

        # Загружаем документы
        if "documents" in file_paths:
            print("📄 Загружаю отчет документов...")
            documents_df = data_manager.load_documents_report(file_paths["documents"])
            results["documents"] = {
                "success": documents_df is not None,
                "rows": len(documents_df) if documents_df is not None else 0
            }
            print(f"   ✅ Документы: {results['documents']['rows']} строк")

        # Загружаем детальный отчет
        if "detailed" in file_paths:
            print("📋 Загружаю детальный отчет...")
            detailed_df = data_manager.load_detailed_report(file_paths["detailed"])
            results["detailed"] = {
                "success": detailed_df is not None,
                "rows": len(detailed_df) if detailed_df is not None else 0
            }
            print(f"   ✅ Детальный: {results['detailed']['rows']} строк")

        # Проверяем что оба файла загружены
        both_loaded = data_manager.is_loaded("both")

        return {
            "success": True,
            "loaded": both_loaded,
            "results": results,
            "message": "Файлы успешно загружены" if both_loaded else "Ошибка загрузки файлов"
        }

    except Exception as e:
        print(f"❌ Ошибка загрузки файлов: {e}")
        return {
            "success": False,
            "loaded": False,
            "error": str(e)
        }


def print_data_status():
    """Выводит статус загруженных данных"""
    status = get_loaded_data_status()

    print("\n📊 СТАТУС ДАННЫХ:")
    print(f"   📋 Отчеты загружены: {'✅' if status['reports_loaded'] else '❌'}")

    if status['detailed_data']['loaded']:
        print(f"   📄 Детальный отчет: {status['detailed_data']['rows']} строк")
    else:
        print("   📄 Детальный отчет: ❌ не загружен")

    if status['documents_data']['loaded']:
        print(f"   📑 Отчет документов: {status['documents_data']['rows']} строк")
    else:
        print("   📑 Отчет документов: ❌ не загружен")


def get_loaded_data_status() -> dict:
    """Получает статус загруженных данных"""
    detailed_df = data_manager.get_detailed_data()
    documents_df = data_manager.get_documents_data()

    return {
        "reports_loaded": data_manager.is_loaded("both"),
        "detailed_data": {
            "loaded": detailed_df is not None,
            "rows": len(detailed_df) if detailed_df is not None else 0
        },
        "documents_data": {
            "loaded": documents_df is not None,
            "rows": len(documents_df) if documents_df is not None else 0
        }
    }


# Функция для консольного режима (если понадобится)
def run_console(**kwargs):
    """Запуск теста в консольном режиме с параметрами"""
    force_reload = kwargs.get('force_reload', False)
    file_paths = kwargs.get('file_paths', None)

    if file_paths:
        print("🎯 Используются пользовательские пути к файлам")

    result = load_test_files(file_paths, force_reload)
    print_data_status()

    return result["success"]


if __name__ == "__main__":
    # При прямом запуске файла
    success = run()
    sys.exit(0 if success else 1)