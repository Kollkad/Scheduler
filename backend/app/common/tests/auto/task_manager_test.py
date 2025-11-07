# backend/app/common/tests/auto/task_manager_test.py
"""
Автотест менеджера задач - проверка формирования и анализа задач

Тестирует:
- Расчет всех задач
- Фильтрация по исполнителям
- Сохранение в Excel
- Статистика задач
"""

import os
import sys
import pandas as pd

# Добавление пути к проекту для импортов
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

from backend.app.common.modules.data_manager import data_manager
from backend.app.task_manager.modules.task_analyzer import task_analyzer
from backend.app.common.config.column_names import COLUMNS, VALUES
from backend.app.common.tests.tests_config import TestsConfig


def run():
    """
    Основной тест менеджера задач

    Returns:
        bool: True если тест пройден успешно
    """
    print("\n" + "=" * 60)
    print("🔧 ТЕСТ МЕНЕДЖЕРА ЗАДАЧ")
    print("=" * 60)

    try:
        # 1. Проверка и подготовка данных
        print("\n📁 ПОДГОТОВКА ДАННЫХ...")
        if not prepare_test_data():
            print("❌ Не удалось подготовить данные для тестирования")
            return False

        # 2. Проверка статуса данных
        print("\n📊 ПРОВЕРКА СТАТУСА ДАННЫХ...")
        data_status = check_data_status()
        print_data_status(data_status)

        if not data_status['ready_for_tasks']:
            print("❌ Данные не готовы для расчета задач")
            return False

        # 3. Расчет всех задач
        print("\n🔍 РАСЧЕТ ВСЕХ ЗАДАЧ...")
        all_tasks = calculate_all_tasks()

        if not all_tasks:
            print("❌ Не удалось рассчитать задачи")
            return False

        # 4. Анализ результатов
        print("\n📈 АНАЛИЗ РЕЗУЛЬТАТОВ...")
        analysis_results = analyze_tasks_results(all_tasks, data_status)

        # 5. Сохранение результатов
        print("\n💾 СОХРАНЕНИЕ РЕЗУЛЬТАТОВ...")
        save_results(all_tasks, analysis_results)

        # 6. Вывод итогов
        print_test_summary(analysis_results)

        # Тест считается успешным если задачи рассчитаны и есть разумное количество
        success = (analysis_results['total_tasks'] > 0 and
                   analysis_results['tasks_by_source']['detailed'] > 0)

        if success:
            print("\n✅ ТЕСТ МЕНЕДЖЕРА ЗАДАЧ УСПЕШНО ЗАВЕРШЕН!")
        else:
            print("\n⚠️ ТЕСТ ЗАВЕРШЕН С ПРЕДУПРЕЖДЕНИЯМИ")

        return success

    except Exception as e:
        print(f"❌ Критическая ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        return False


def prepare_test_data():
    """
    Подготавливает данные для тестирования задач

    Returns:
        bool: True если данные готовы
    """
    try:
        # Загружаем файлы через file_loader_test - ИСПРАВЛЕННАЯ ВЕРСИЯ
        from backend.app.common.tests.auto.file_loader_test import load_test_files

        # Загружаем файлы
        file_paths = {
            "detailed": str(TestsConfig.TEST_FILES["detailed"]),
            "documents": str(TestsConfig.TEST_FILES["documents"])
        }
        load_result = load_test_files(file_paths=file_paths, force_reload=False)

        if not load_result.get("success", False) or not load_result.get("loaded", False):
            print("❌ Не удалось загрузить файлы для тестирования")
            return False

        # Проверяем что данные загружены в data_manager
        if not data_manager.is_loaded("both"):
            print("❌ Данные не загружены в data_manager")
            return False

        # Получаем данные
        detailed_df = data_manager.get_detailed_data()
        documents_df = data_manager.get_documents_data()

        # Если нет проанализированных данных - запускаем анализ
        lawsuit_staged = data_manager.get_processed_data("lawsuit_staged")
        order_staged = data_manager.get_processed_data("order_staged")
        documents_processed = data_manager.get_processed_data("documents_processed")

        needs_analysis = not all(
            [lawsuit_staged is not None, order_staged is not None, documents_processed is not None])

        if needs_analysis:
            print("🔍 ЗАПУСК АНАЛИЗА ДАННЫХ ДЛЯ ЗАДАЧ...")

            # Анализируем исковое производство
            from backend.app.terms_of_support_v2.modules.terms_analyzer_v2 import build_production_table

            lawsuit_filtered = detailed_df[
                (detailed_df[COLUMNS["CATEGORY"]] == VALUES["CLAIM_FROM_BANK"]) &
                (detailed_df[COLUMNS["METHOD_OF_PROTECTION"]] == VALUES["CLAIM_PROCEEDINGS"])
                ].copy()

            if not lawsuit_filtered.empty:
                lawsuit_result = build_production_table(lawsuit_filtered, 'lawsuit')
                data_manager.set_processed_data("lawsuit_staged", lawsuit_result)
                print(f"✅ Исковое проанализировано: {len(lawsuit_result)} записей")

            # Анализируем приказное производство
            order_filtered = detailed_df[
                (detailed_df[COLUMNS["CATEGORY"]] == VALUES["CLAIM_FROM_BANK"]) &
                (detailed_df[COLUMNS["METHOD_OF_PROTECTION"]] == VALUES["ORDER_PRODUCTION"])
                ].copy()

            if not order_filtered.empty:
                order_result = build_production_table(order_filtered, 'order')
                data_manager.set_processed_data("order_staged", order_result)
                print(f"✅ Приказное проанализировано: {len(order_result)} записей")

            # Анализируем документы
            from backend.app.document_monitoring_v2.modules.document_stage_checks_v2 import analyze_documents

            if documents_df is not None and not documents_df.empty:
                documents_result = analyze_documents(documents_df)
                data_manager.set_processed_data("documents_processed", documents_result)
                print(f"✅ Документы проанализированы: {len(documents_result)} записей")

        return True

    except Exception as e:
        print(f"❌ Ошибка подготовки данных: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_data_status():
    """
    Проверяет статус всех необходимых данных

    Returns:
        dict: Статус данных
    """
    status = {
        'reports_loaded': data_manager.is_loaded("both"),
        'detailed_data': data_manager.get_detailed_data() is not None,
        'documents_data': data_manager.get_documents_data() is not None,
        'lawsuit_staged': data_manager.get_processed_data("lawsuit_staged") is not None,
        'order_staged': data_manager.get_processed_data("order_staged") is not None,
        'documents_processed': data_manager.get_processed_data("documents_processed") is not None,
        'ready_for_tasks': False
    }

    # Проверяем готовность к расчету задач
    status['ready_for_tasks'] = all([
        status['reports_loaded'],
        status['lawsuit_staged'] or status['order_staged'],
        status['documents_processed']
    ])

    # Дополнительная информация
    detailed_df = data_manager.get_detailed_data()
    if detailed_df is not None and COLUMNS["RESPONSIBLE_EXECUTOR"] in detailed_df.columns:
        status['available_executors'] = detailed_df[COLUMNS["RESPONSIBLE_EXECUTOR"]].dropna().unique().tolist()
    else:
        status['available_executors'] = []

    return status


def print_data_status(status):
    """
    Выводит статус данных
    """
    print("\n📊 СТАТУС ДАННЫХ:")
    print(f"  📋 Отчеты загружены: {'✅' if status['reports_loaded'] else '❌'}")
    print(f"  ⚔️  Исковое проанализировано: {'✅' if status['lawsuit_staged'] else '❌'}")
    print(f"  📝 Приказное проанализировано: {'✅' if status['order_staged'] else '❌'}")
    print(f"  📄 Документы проанализированы: {'✅' if status['documents_processed'] else '❌'}")
    print(f"  🎯 Готово к расчету задач: {'✅' if status['ready_for_tasks'] else '❌'}")

    if status['available_executors']:
        print(f"  👤 Доступные исполнители: {len(status['available_executors'])}")


def calculate_all_tasks():
    """
    Рассчитывает все задачи

    Returns:
        list: Список задач или None при ошибке
    """
    try:
        all_tasks = task_analyzer.analyze_all_tasks()

        if not all_tasks:
            print("❌ Не рассчитано ни одной задачи")
            return None

        # Сохраняем задачи в data_manager
        tasks_df = pd.DataFrame(all_tasks)
        data_manager.set_processed_data("tasks", tasks_df)

        print(f"✅ Рассчитано задач: {len(all_tasks)}")
        return all_tasks

    except Exception as e:
        print(f"❌ Ошибка расчета задач: {e}")
        return None


def analyze_tasks_results(tasks, data_status):
    """
    Анализирует результаты расчета задач

    Returns:
        dict: Результаты анализа
    """
    analysis = {
        'total_tasks': len(tasks),
        'tasks_by_source': {'detailed': 0, 'documents': 0, 'unknown': 0},
        'tasks_by_executor': {},
        'tasks_by_stage': {},
        'top_executors': []
    }

    # Анализ по источникам - ИСПРАВЛЕННАЯ ВЕРСИЯ
    for task in tasks:
        source = task.get('sourceType', 'unknown')
        if source == 'detailed':
            analysis['tasks_by_source']['detailed'] += 1
        elif source == 'documents':
            analysis['tasks_by_source']['documents'] += 1
        else:
            analysis['tasks_by_source']['unknown'] += 1

    # Анализ по исполнителям - ИСПРАВЛЕННАЯ ВЕРСИЯ
    for task in tasks:
        executor = task.get('responsibleExecutor', 'unknown')
        analysis['tasks_by_executor'][executor] = analysis['tasks_by_executor'].get(executor, 0) + 1

    # Анализ по этапам - ИСПРАВЛЕННАЯ ВЕРСИЯ
    for task in tasks:
        stage = task.get('caseStage', 'unknown')
        analysis['tasks_by_stage'][stage] = analysis['tasks_by_stage'].get(stage, 0) + 1

    # Топ исполнители (исключаем 'unknown')
    valid_executors = {k: v for k, v in analysis['tasks_by_executor'].items()
                       if k and k != 'unknown' and k != 'Не указано'}
    analysis['top_executors'] = sorted(
        valid_executors.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    return analysis


def save_results(tasks, analysis):
    """
    Сохраняет результаты теста
    """
    try:
        # Сохраняем все задачи
        tasks_df = pd.DataFrame(tasks)
        tasks_path = TestsConfig.RESULTS_DIR / "all_tasks_export.xlsx"
        tasks_df.to_excel(tasks_path, index=False)
        print(f"💾 Все задачи сохранены: {tasks_path}")

        # Сохраняем анализ
        analysis_df = pd.DataFrame([analysis])
        analysis_path = TestsConfig.RESULTS_DIR / "tasks_analysis.xlsx"
        analysis_df.to_excel(analysis_path, index=False)
        print(f"💾 Анализ задач сохранен: {analysis_path}")

        # Сохраняем топ исполнителей
        if analysis['top_executors']:
            top_executors_df = pd.DataFrame(analysis['top_executors'], columns=['executor', 'task_count'])
            top_executors_path = TestsConfig.RESULTS_DIR / "top_executors.xlsx"
            top_executors_df.to_excel(top_executors_path, index=False)
            print(f"💾 Топ исполнителей сохранен: {top_executors_path}")

    except Exception as e:
        print(f"⚠️ Не удалось сохранить некоторые результаты: {e}")


def print_test_summary(analysis):
    """
    Выводит итоговую сводку теста
    """
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ТЕСТА МЕНЕДЖЕРА ЗАДАЧ")
    print("=" * 60)

    print(f"\n📈 ОСНОВНАЯ СТАТИСТИКА:")
    print(f"  Всего задач: {analysis['total_tasks']}")
    print(f"  Задач из детального отчета: {analysis['tasks_by_source']['detailed']}")
    print(f"  Задач из документов: {analysis['tasks_by_source']['documents']}")
    print(f"  Задач неизвестного источника: {analysis['tasks_by_source']['unknown']}")

    print(f"\n👤 ТОП ИСПОЛНИТЕЛИ:")
    if analysis['top_executors']:
        for i, (executor, count) in enumerate(analysis['top_executors'], 1):
            print(f"  {i}. {executor}: {count} задач")
    else:
        print("  Нет данных об исполнителях")

    print(f"\n📊 РАСПРЕДЕЛЕНИЕ ПО ЭТАПАМ:")
    top_stages = sorted(analysis['tasks_by_stage'].items(), key=lambda x: x[1], reverse=True)[:10]
    for stage, count in top_stages:
        print(f"  {stage}: {count}")

    # Оценка результатов - ИСПРАВЛЕННАЯ ВЕРСИЯ
    if analysis['total_tasks'] == 0:
        print("\n🚨 ВНИМАНИЕ: Не рассчитано ни одной задачи!")
    elif analysis['tasks_by_source']['detailed'] == 0:
        print("\n⚠️  ПРЕДУПРЕЖДЕНИЕ: Нет задач из детального отчета")
    elif analysis['tasks_by_source']['documents'] == 0:
        print("\n⚠️  ПРЕДУПРЕЖДЕНИЕ: Нет задач из документов")
    else:
        print("\n✅ РЕЗУЛЬТАТЫ: Задачи успешно рассчитаны из всех источников!")


# Функция для консольного режима
def run_console(**kwargs):
    """Запуск теста в консольном режиме"""
    return run()


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)