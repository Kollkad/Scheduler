# backend/app/common/tests/interactive_full_test.py

"""
Полный тестовый раннер - центральный хаб для запуска всех тестов проекта.

Запускает тесты в правильной последовательности:
1. Загрузка и анализ данных (terms_v2_test)
2. Модуль задач (task_manager_test)
3. Другие тесты (можно добавить позже)
"""

import os
import sys
import importlib

sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))


def run_file_loader_test():
    """Запуск тестирования загрузки файлов."""
    print("\n" + "=" * 60)
    print("0. ТЕСТИРОВАНИЕ ЗАГРУЗКИ ФАЙЛОВ")
    print("=" * 60)

    try:
        from backend.app.common.tests.auto.file_loader_test import run as loader_run
        result = loader_run()
        return result  # возвращает True/False напрямую
    except Exception as e:
        print(f"❌ Ошибка при запуске file_loader_test: {e}")
        return False


def run_terms_v2_test():
    """Запуск тестирования анализа производств и документов."""
    print("\n" + "=" * 60)
    print("1. ТЕСТИРОВАНИЕ АНАЛИЗА ПРОИЗВОДСТВ И ДОКУМЕНТОВ")
    print("=" * 60)

    try:
        from backend.app.common.tests.auto.terms_v2_test import run as terms_run
        return terms_run()  # возвращает True/False
    except Exception as e:
        print(f"❌ Ошибка при запуске terms_v2_test: {e}")
        return False


def run_task_manager_test():
    """Запуск тестирования модуля задач."""
    print("\n" + "=" * 60)
    print("2. ТЕСТИРОВАНИЕ MODULE TASK_MANAGER")
    print("=" * 60)

    try:
        from backend.app.common.tests.auto.task_manager_test import run as tasks_run
        return tasks_run()  # возвращает True/False
    except Exception as e:
        print(f"❌ Ошибка при запуске task_manager_test: {e}")
        return False


def run_other_tests():
    """Запуск других тестов (можно расширять)."""
    print("\n" + "=" * 60)
    print("3. 📊 ДРУГИЕ ТЕСТЫ")
    print("=" * 60)

    # Здесь можно добавить вызовы других тестов
    print("✅ Другие тесты пока не подключены")
    print("   Можно добавить: table_sorter_test, rainbow_test, etc.")

    return True


def interactive_menu():
    """интерактивное меню выбора тестов."""
    while True:
        print("\n" + "=" * 50)
        print("полный тестовый раннер")
        print("=" * 50)
        print("выберите тесты для запуска:")
        print("  0 — только загрузка файлов")
        print("  1 — все тесты по порядку")
        print("  2 — только анализ производств (terms_v2)")
        print("  3 — только модуль задач (task_manager)")
        print("  4 — выборочные тесты")
        print("  5 — выход")

        choice = input("\nвведите 0-5: ").strip()

        if choice == "0":
            run_file_loader_test()

        elif choice == "1":
            print("\n🚀 запуск всех тестов по порядку...")
            if run_file_loader_test():
                run_terms_v2_test()
                run_task_manager_test()
            print("\n✅ все тесты завершены!")

        elif choice == "2":
            if run_file_loader_test():
                run_terms_v2_test()

        elif choice == "3":
            if run_file_loader_test():
                run_task_manager_test()

        elif choice == "4":
            print("\n🔍 выборочное тестирование:")
            run_files = input("  запустить загрузку файлов? (y/n): ").strip().lower() == 'y'
            run_terms = input("  запустить анализ производств? (y/n): ").strip().lower() == 'y'
            run_tasks = input("  запустить модуль задач? (y/n): ").strip().lower() == 'y'

            if run_files:
                files_loaded = run_file_loader_test()
                if files_loaded:
                    if run_terms:
                        run_terms_v2_test()
                    if run_tasks:
                        run_task_manager_test()
            else:
                if run_terms:
                    run_terms_v2_test()
                if run_tasks:
                    run_task_manager_test()

        elif choice == "5":
            print("выход из тестового раннера")
            break

        else:
            print("❌ неверный выбор")

        if choice != "5":
            continue_test = input("\nпродолжить тестирование? (y/n): ").strip().lower()
            if continue_test != 'y':
                print("завершение работы")
                break


def quick_test():
    """Быстрый запуск всех тестов без меню."""
    print("🚀 БЫСТРЫЙ ЗАПУСК ВСЕХ ТЕСТОВ...")
    run_terms_v2_test()
    run_task_manager_test()
    run_other_tests()
    print("\n🎉 Все тесты завершены!")


def main():
    """
    основная функция тестового раннера.
    """
    # проверяем аргументы командной строки
    if len(sys.argv) > 1:
        if sys.argv[1] == "quick":
            if run_file_loader_test():
                run_terms_v2_test()
                run_task_manager_test()
        elif sys.argv[1] == "terms":
            if run_file_loader_test():
                run_terms_v2_test()
        elif sys.argv[1] == "tasks":
            if run_file_loader_test():
                run_task_manager_test()
        else:
            print(f"❌ неизвестный аргумент: {sys.argv[1]}")
            print("доступные аргументы: quick, terms, tasks")
    else:
        # интерактивный режим по умолчанию
        interactive_menu()


if __name__ == "__main__":
    main()