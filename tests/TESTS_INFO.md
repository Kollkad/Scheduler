
# Система тестирования (pytest)

## Структура

- `tests/auto/` — автоматические тесты
- `tests/conftest.py` — общие хелперы и подготовка данных
- `tests/pytest.ini` — конфигурация
- `tests/data/dev_data/` — полные файлы (.gitignore)
- `tests/data/sample_data/` — сэмплы (в Git)

## Запуск

```bash
# Все тесты
pytest tests/ -v

# Только CI (быстрые)
pytest tests/ -v -m ci

# С выводом логов
pytest tests/auto/test_upload_detailed_report_multisheet.py -v -s
```

## Маркеры

- `ci` — быстрые тесты, запускаются на каждый push
- `slow` — полные тесты с загрузкой файлов
- `unit` — юнит-тесты без данных

## Список тестов

1. test_upload_detailed_report_multisheet — загрузка детального отчета
2. test_normalize_gosb_fill — нормализация ГОСБ
3. test_upload_documents_report — загрузка отчета документов
4. test_auth_existing_user — авторизация пользователя
5. test_auth_guest_user — гостевая авторизация
6. test_rainbow_analyze — Rainbow-анализ
7. test_rainbow_filtered_cases — фильтрация по цвету
8. test_analyze_lawsuit — анализ искового производства
9. test_analyze_order — анализ приказного производства
10. test_analyze_documents — анализ документов
11. test_tasks_calculate — расчёт задач
12. test_tasks_filter_executor — фильтр задач по исполнителю
13. test_task_detail — детали задачи
14. test_task_mark_completed — отметка задачи выполненной
15. test_task_shift_deadline — перенос срока задачи
16. test_stages_with_checks — этапы с проверками
17. test_export_all — экспорт всех данных
18. test_import_all — импорт всех данных
19. test_collect_overrides — сбор оверрайдов
20. test_check_violations — проверка нарушений

## Обмен данными

Тесты независимы. Каждый тест сам готовит данные через `clean_manager`. `conftest.py` предоставляет `project_root`, `detailed_df`, `documents_df`, `compare_dataframes`.

