# backend/app/common/tests/auto/saving_test.py
"""
Автотест модуля сохранения результатов - проверка эндпоинтов сохранения

Тестирует все эндпоинты сохранения через TestClient:
- Детальный отчет и документы
- Анализ производств (объединенный)
- Анализ документов и задач
- Анализ радуги
"""

import os
import sys
import pandas as pd
from pathlib import Path

# Добавление пути к проекту для импортов
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

from backend.app.common.modules.data_manager import data_manager
from backend.app.saving_results.modules.saving_results_settings import generate_filename
from backend.app.common.config.column_names import COLUMNS, VALUES
from backend.app.common.tests.tests_config import TestsConfig


def run():
    """
    Основной тест модуля сохранения результатов

    Returns:
        bool: True если тест пройден успешно
    """
    print("\n" + "=" * 60)
    print("💾 ТЕСТ МОДУЛЯ СОХРАНЕНИЯ РЕЗУЛЬТАТОВ")
    print("=" * 60)

    try:
        # 1. Подготовка данных
        print("\n📁 ПОДГОТОВКА ДАННЫХ...")
        if not prepare_test_data():
            print("❌ Не удалось подготовить данные для тестирования")
            return False

        # 2. Тестирование эндпоинтов
        print("\n🔍 ТЕСТИРОВАНИЕ ЭНДПОИНТОВ...")
        endpoints_results = test_all_saving_endpoints()

        # 3. Анализ результатов
        print("\n📊 АНАЛИЗ РЕЗУЛЬТАТОВ...")
        analysis_results = analyze_saving_results(endpoints_results)

        # 4. Вывод итогов
        print_test_summary(analysis_results)

        # Тест считается успешным если основные эндпоинты работают
        success = analysis_results['critical_endpoints_working']

        if success:
            print("\n✅ ТЕСТ МОДУЛЯ СОХРАНЕНИЯ УСПЕШНО ЗАВЕРШЕН!")
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
    Подготавливает данные для тестирования эндпоинтов сохранения

    Returns:
        bool: True если данные готовы
    """
    try:
        # Загружаем файлы используя существующую функцию
        from backend.app.common.tests.auto.file_loader_test import load_test_files

        # Проверяем, не загружены ли файлы уже
        if data_manager.is_loaded("both"):
            print("✅ Файлы уже загружены в data_manager")
        else:
            print("📁 Загрузка тестовых файлов...")
            load_result = load_test_files(force_reload=False)

            if not load_result.get("success", False) or not load_result.get("loaded", False):
                print(f"❌ Ошибка загрузки файлов: {load_result.get('message', 'Unknown error')}")
                return False
            print("✅ Файлы успешно загружены")

        # Получаем загруженные данные
        detailed_df = data_manager.get_detailed_data()
        documents_df = data_manager.get_documents_data()

        if detailed_df is None or documents_df is None:
            print("❌ Данные не загружены в data_manager")
            return False

        print(f"📊 Загружено: детальный отчет - {len(detailed_df)} строк, документы - {len(documents_df)} строк")

        # Анализируем исковое производство
        from backend.app.terms_of_support_v2.modules.terms_analyzer_v2 import build_production_table

        lawsuit_filtered = detailed_df[
            (detailed_df[COLUMNS["CATEGORY"]] == VALUES["CLAIM_FROM_BANK"]) &
            (detailed_df[COLUMNS["METHOD_OF_PROTECTION"]] == VALUES["CLAIM_PROCEEDINGS"])
            ].copy()

        if not lawsuit_filtered.empty:
            lawsuit_result = build_production_table(lawsuit_filtered, 'lawsuit')
            data_manager.set_processed_data("lawsuit_staged", lawsuit_result)
            print(f"✅ Исковое производство подготовлено: {len(lawsuit_result)} записей")
        else:
            print("⚠️ Нет данных для искового производства")

        # Анализируем приказное производство
        order_filtered = detailed_df[
            (detailed_df[COLUMNS["CATEGORY"]] == VALUES["CLAIM_FROM_BANK"]) &
            (detailed_df[COLUMNS["METHOD_OF_PROTECTION"]] == VALUES["ORDER_PRODUCTION"])
            ].copy()

        if not order_filtered.empty:
            order_result = build_production_table(order_filtered, 'order')
            data_manager.set_processed_data("order_staged", order_result)
            print(f"✅ Приказное производство подготовлено: {len(order_result)} записей")
        else:
            print("⚠️ Нет данных для приказного производства")

        # Анализируем документы
        from backend.app.document_monitoring_v2.modules.document_stage_checks_v2 import analyze_documents

        if documents_df is not None and not documents_df.empty:
            documents_result = analyze_documents(documents_df)
            data_manager.set_processed_data("documents_processed", documents_result)
            print(f"✅ Документы подготовлены: {len(documents_result)} записей")
        else:
            print("⚠️ Нет данных документов для анализа")

        # Рассчитываем задачи
        from backend.app.task_manager.modules.task_analyzer import task_analyzer

        all_tasks = task_analyzer.analyze_all_tasks()
        if all_tasks:
            tasks_df = pd.DataFrame(all_tasks)
            data_manager.set_processed_data("tasks", tasks_df)
            print(f"✅ Задачи подготовлены: {len(all_tasks)} задач")
        else:
            print("⚠️ Нет задач для анализа")

        # Подготовка данных радуги
        from backend.app.rainbow.modules.rainbow_classifier import RainbowClassifier

        if detailed_df is not None and not detailed_df.empty:
            derived_df = RainbowClassifier.create_derived_rainbow(detailed_df)
            data_manager._derived_data["detailed_rainbow"] = derived_df
            print(f"✅ Данные радуги подготовлены: {len(derived_df)} записей")
        else:
            print("⚠️ Нет данных для подготовки радуги")

        # Проверяем что хотя бы некоторые данные подготовлены
        prepared_data_types = []
        if data_manager.get_processed_data("lawsuit_staged") is not None:
            prepared_data_types.append("исковое производство")
        if data_manager.get_processed_data("order_staged") is not None:
            prepared_data_types.append("приказное производство")
        if data_manager.get_processed_data("documents_processed") is not None:
            prepared_data_types.append("документы")
        if data_manager.get_processed_data("tasks") is not None:
            prepared_data_types.append("задачи")
        if data_manager._derived_data.get("detailed_rainbow") is not None:
            prepared_data_types.append("данные радуги")

        if prepared_data_types:
            print(f"✅ Подготовлены данные: {', '.join(prepared_data_types)}")
            return True
        else:
            print("❌ Не удалось подготовить ни один тип данных для тестирования")
            return False

    except Exception as e:
        print(f"❌ Ошибка подготовки данных: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_saving_endpoints():
    """
    Тестирует все эндпоинты сохранения через TestClient

    Returns:
        dict: Результаты тестирования каждого эндпоинта
    """
    endpoints = {
        'detailed_report': {'path': '/api/save/detailed-report', 'critical': True},
        'documents_report': {'path': '/api/save/documents-report', 'critical': True},
        'terms_productions': {'path': '/api/save/terms-productions', 'critical': True},
        'documents_analysis': {'path': '/api/save/documents-analysis', 'critical': False},
        'tasks': {'path': '/api/save/tasks', 'critical': False},
        'rainbow_analysis': {'path': '/api/save/rainbow-analysis', 'critical': False},
        'all_analysis': {'path': '/api/save/all-analysis', 'critical': False}
    }

    results = {}

    try:
        from fastapi.testclient import TestClient
        from backend.app.main import app

        client = TestClient(app)

        for endpoint_name, endpoint_info in endpoints.items():
            print(f"\n🔍 Тестируется {endpoint_name}...")

            try:
                response = client.get(endpoint_info['path'])

                if response.status_code == 200:
                    # Сохраняем файл для проверки
                    filename = generate_filename(endpoint_name)
                    filepath = Path(TestsConfig.RESULTS_DIR) / filename

                    with open(filepath, 'wb') as f:
                        f.write(response.content)

                    # Проверяем содержимое файла
                    file_info = validate_saved_file(filepath, endpoint_name)

                    results[endpoint_name] = {
                        'success': True,
                        'status_code': response.status_code,
                        'file_created': True,
                        'file_size': file_info['file_size'],
                        'records_count': file_info['records_count'],
                        'file_path': str(filepath),
                        'critical': endpoint_info['critical']
                    }

                    print(f"✅ {endpoint_name}: {file_info['records_count']} записей, {file_info['file_size']} байт")

                else:
                    results[endpoint_name] = {
                        'success': False,
                        'status_code': response.status_code,
                        'error': f"HTTP {response.status_code}",
                        'critical': endpoint_info['critical']
                    }
                    print(f"❌ {endpoint_name}: HTTP {response.status_code}")

            except Exception as e:
                results[endpoint_name] = {
                    'success': False,
                    'error': str(e),
                    'critical': endpoint_info['critical']
                }
                print(f"❌ {endpoint_name}: {e}")

        return results

    except Exception as e:
        print(f"❌ Ошибка тестирования эндпоинтов: {e}")
        return {}


def validate_saved_file(filepath, endpoint_name):
    """
    Проверяет сохраненный файл на корректность

    Returns:
        dict: Информация о файле
    """
    try:
        filepath_str = str(filepath)
        file_size = os.path.getsize(filepath_str)

        # Читаем файл и проверяем данные
        if filepath_str.endswith('.xlsx'):
            df = pd.read_excel(filepath_str)
            records_count = len(df)
        elif filepath_str.endswith('.zip'):
            records_count = 0  # ZIP архивы не проверяются внутри
        else:
            records_count = 0

        return {
            'file_size': file_size,
            'records_count': records_count,
            'is_valid': records_count > 0 or file_size > 0
        }

    except Exception as e:
        print(f"⚠️ Ошибка проверки файла {filepath}: {e}")
        return {
            'file_size': os.path.getsize(filepath) if os.path.exists(filepath) else 0,
            'records_count': 0,
            'is_valid': False
        }


def analyze_saving_results(endpoints_results):
    """
    Анализирует результаты тестирования эндпоинтов

    Returns:
        dict: Анализ результатов
    """
    analysis = {
        'total_endpoints': len(endpoints_results),
        'successful_endpoints': 0,
        'failed_endpoints': 0,
        'critical_endpoints_working': False,
        'total_files_created': 0,
        'total_records_saved': 0,
        'endpoint_details': {}
    }

    for endpoint_name, result in endpoints_results.items():
        analysis['endpoint_details'][endpoint_name] = result

        if result.get('success', False):
            analysis['successful_endpoints'] += 1
            if result.get('file_created', False):
                analysis['total_files_created'] += 1
                analysis['total_records_saved'] += result.get('records_count', 0)
        else:
            analysis['failed_endpoints'] += 1

    # Проверка работы критических эндпоинтов
    critical_endpoints = [name for name, result in endpoints_results.items()
                          if result.get('critical', False)]
    working_critical = all(endpoints_results.get(name, {}).get('success', False)
                           for name in critical_endpoints)

    analysis['critical_endpoints_working'] = working_critical

    return analysis


def print_test_summary(analysis):
    """
    Вывод итоговой сводку теста
    """
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ТЕСТА СОХРАНЕНИЯ")
    print("=" * 60)

    print(f"\n🎯 ОБЩАЯ СТАТИСТИКА:")
    print(f"  Протестировано эндпоинтов: {analysis['total_endpoints']}")
    print(f"  Успешных: {analysis['successful_endpoints']}")
    print(f"  Неудачных: {analysis['failed_endpoints']}")
    print(f"  Создано файлов: {analysis['total_files_created']}")
    print(f"  Всего записей сохранено: {analysis['total_records_saved']}")

    print(f"\n🔧 СТАТУС ЭНДПОИНТОВ:")
    for endpoint_name, result in analysis['endpoint_details'].items():
        status = "✅" if result.get('success') else "❌"
        critical = "🔴" if result.get('critical') else "⚪"
        records = result.get('records_count', 'N/A')
        print(f"  {status} {critical} {endpoint_name}: {records} записей")

    print(f"\n💡 РЕКОМЕНДАЦИИ:")
    if analysis['critical_endpoints_working']:
        print("  ✅ Все критические эндпоинты работают корректно!")
    else:
        failed_critical = [name for name, result in analysis['endpoint_details'].items()
                           if result.get('critical') and not result.get('success')]
        if failed_critical:
            print(f"  🚨 Критические эндпоинты с ошибками: {', '.join(failed_critical)}")

    if analysis['total_records_saved'] == 0:
        print("  ⚠️  Внимание: не сохранено ни одной записи!")
    elif analysis['failed_endpoints'] > 0:
        print(f"  ⚠️  Некоторые эндпоинты требуют внимания: {analysis['failed_endpoints']} штук")


# Функция для консольного режима
def run_console(**kwargs):
    """Запуск теста в консольном режиме"""
    return run()


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)