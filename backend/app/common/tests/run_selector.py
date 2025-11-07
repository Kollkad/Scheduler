# backend/app/common/tests/run_selector.py
"""
Основной скрипт выбора тестов - показывает список всех тестов
"""

from test_discovery import TestDiscovery


def main():
    print("СИСТЕМА УПРАВЛЕНИЯ ТЕСТАМИ")
    print("=" * 40)

    # Находим все тесты
    discovery = TestDiscovery()
    all_tests = discovery.discover_tests()

    # Показываем список
    print("\n📋 ДОСТУПНЫЕ ТЕСТЫ:")

    test_list = []
    index = 1

    # Автотесты
    print("\n🤖 АВТОТЕСТЫ:")
    for test_name in all_tests['auto'].keys():
        print(f"   {index}. {test_name}")
        test_list.append(all_tests['auto'][test_name])
        index += 1

    # Консольные тесты  
    print("\n🎮 КОНСОЛЬНЫЕ ТЕСТЫ:")
    for test_name in all_tests['console'].keys():
        print(f"   {index}. {test_name}")
        test_list.append(all_tests['console'][test_name])
        index += 1

    # Выбор теста
    if not test_list:
        print("❌ Тесты не найдены!")
        return

    try:
        choice = int(input(f"\n🎯 Выберите тест (1-{len(test_list)}): "))
        if 1 <= choice <= len(test_list):
            selected_test = test_list[choice - 1]
            print(f"\n🚀 Запуск теста: {selected_test['module_path']}")

            # Загружаем и запускаем тест
            test_function = discovery.load_test(selected_test)
            if test_function:
                success = test_function()
                print(f"\n{'✅ ТЕСТ УСПЕШЕН' if success else '❌ ТЕСТ ПРОВАЛЕН'}")
            else:
                print("❌ Не удалось загрузить тест")
        else:
            print("❌ Неверный выбор")
    except ValueError:
        print("❌ Введите число")
    except KeyboardInterrupt:
        print("\n👋 Завершено пользователем")


if __name__ == "__main__":
    main()