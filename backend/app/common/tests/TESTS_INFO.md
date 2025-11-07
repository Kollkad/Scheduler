# Система тестирования

## Общие принципы

### Структура тестов
- **Автотесты** (`app/common/tests/auto/`) - полностью автоматические тесты, запускаются без вмешательства пользователя
- **Интерактивные тесты** (`app/common/tests/interactive/`) - тесты с меню выбора и управлением
- **Общие утилиты** (`app/common/tests/shared/`) - общие модули для тестов

### Автоматическое обнаружение
Система автоматически сканирует папки с тестами. Новые тесты добавляются в общий список без необходимости редактирования конфигурационных файлов.

## Запуск тестов

### Полный тестовый раннер (рекомендуется)
```bash
python backend/app/common/tests/interactive_full_test.py
```

Запускает интерактивное меню с выбором тестов. Поддерживает последовательный запуск всех тестов.

### Прямой запуск автотестов
```bash
# Базовые тесты данных
python backend/app/common/tests/auto/file_loader_test.py
python backend/app/common/tests/auto/test_unique_columns.py

# Тесты функциональности
python backend/app/common/tests/auto/terms_v2_test.py
python backend/app/common/tests/auto/task_manager_test.py
python backend/app/common/tests/auto/saving_test.py
```

### Аргументы командной строки
```bash
# Быстрый запуск всех тестов
python backend/app/common/tests/interactive_full_test.py quick

# Только анализ производств
python backend/app/common/tests/interactive_full_test.py terms

# Только модуль задач  
python backend/app/common/tests/interactive_full_test.py tasks
```

## Рекомендуемая последовательность тестирования

1. **file_loader_test** - базовая загрузка файлов
2. **terms_v2_test** - анализ судебных производств  
3. **task_manager_test** - расчет задач
4. **saving_test** - тестирование эндпоинтов сохранения
5. **test_unique_columns** - анализ уникальности данных

## Добавление новых тестов

### Автотесты
1. Создайте файл в папке `app/common/tests/auto/`
2. Реализуйте функцию `run()` которая возвращает `bool` (успех/неудача)
3. Для консольного режима добавьте `run_console(**kwargs)`
4. Тест автоматически появится в списке доступных

### Требования к автотестам
- Обязательная функция `run() -> bool`
- Использование `TestsConfig` для путей к файлам
- Интеграция с `data_manager` для обмена данными между тестами
- Четкая диагностика и отчетность о результатах

## Конфигурация тестов

Основные настройки в `tests_config.py`:
- `TestsConfig.TEST_FILES` - пути к тестовым файлам
- `TestsConfig.RESULTS_DIR` - директория для результатов (`app/data/auto_test/`)
- `TestsConfig.PROJECT_ROOT` - корневая директория проекта

## Обмен данными между тестами

Тесты используют общий `data_manager` для передачи данных:
- Загруженные отчеты сохраняются в data_manager
- Результаты анализа доступны для последующих тестов
- Задачи и производства кэшируются для повторного использования


