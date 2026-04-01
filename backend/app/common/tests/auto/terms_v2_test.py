# backend/app/common/tests/auto/terms_v2_test.py
"""
Модульный тест анализа судебных производств и документов

Тестирует различные сценарии анализа:
- Исковое производство
- Приказное производство
- Мониторинг документов
- Все анализы вместе
"""

import os
import sys
import pandas as pd

# Добавление пути к проекту для импортов
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

from backend.app.data_management.modules.data_manager import data_manager
from backend.app.common.config.column_names import COLUMNS, VALUES
from backend.app.common.tests.tests_config import TestsConfig

# Импорты для искового производства v2
from backend.app.terms_of_support_v2.modules.lawsuit_stage_v2 import save_stage_table_to_excel

# Импорты для приказного производства v2
from backend.app.terms_of_support_v2.modules.order_stage_v2 import save_order_stage_table_to_excel
from backend.app.terms_of_support_v2.modules.terms_analyzer_v2 import build_production_table

# Импорты для документов v2
from backend.app.document_monitoring_v2.modules.document_stage_checks_v2 import (
    analyze_documents,
    save_document_monitoring_status
)


def run():
    """
    Основной тест анализа судебных производств v2

    Returns:
        bool: True если тест пройден успешно
    """
    print("\n" + "=" * 60)
    print("⚖️ ТЕСТ АНАЛИЗА СУДЕБНЫХ ПРОИЗВОДСТВ V2")
    print("=" * 60)

    try:
        # 1. Загрузка данных - ИСПРАВЛЕННЫЙ ВАРИАНТ
        print("\n📁 ЗАГРУЗКА ДАННЫХ...")
        from backend.app.common.tests.auto.file_loader_test import load_test_files

        # Загружаем файлы используя существующую функцию
        load_result = load_test_files(force_reload=False)

        if not load_result.get("success", False) or not load_result.get("loaded", False):
            print("❌ Не удалось загрузить файлы для тестирования")
            return False

        # Проверяем что данные загружены в data_manager
        if not data_manager.is_loaded("both"):
            print("❌ Данные не загружены в data_manager")
            return False

        # Получаем данные из data_manager
        documents_df = data_manager.get_documents_data()
        detailed_df = data_manager.get_detailed_data()

        print(f"✅ Детальный отчет: {len(detailed_df)} записей")
        print(f"✅ Отчет документов: {len(documents_df)} записей")

        # 2. Запуск всех анализов
        print("\n🔍 ЗАПУСК ВСЕХ АНАЛИЗОВ...")
        results = run_all_analyses(detailed_df, documents_df)

        # 3. Вывод результатов
        print_test_summary(results)

        # Тест считается успешным если все модули отработали без критических ошибок
        success = results['summary']['all_modules_working']

        if success:
            print("\n✅ ТЕСТ АНАЛИЗА ПРОИЗВОДСТВ V2 УСПЕШНО ЗАВЕРШЕН!")
        else:
            print("\n⚠️ ТЕСТ ЗАВЕРШЕН С ПРЕДУПРЕЖДЕНИЯМИ")

        return success

    except Exception as e:
        print(f"❌ Критическая ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_analyses(detailed_df: pd.DataFrame, documents_df: pd.DataFrame) -> dict:
    """
    Запускает все анализы: исковое, приказное и документы

    Returns:
        dict: Результаты всех анализов
    """
    results = {
        'lawsuit': {'success': False, 'data': None, 'file_created': False},
        'order': {'success': False, 'data': None, 'file_created': False},
        'documents': {'success': False, 'data': None, 'file_created': False}
    }

    # Анализ документов
    print("\n📄 АНАЛИЗ ДОКУМЕНТОВ...")
    if documents_df is not None and not documents_df.empty:
        try:
            documents_analysis = analyze_documents(documents_df)
            docs_output_path = save_document_monitoring_status(documents_analysis, str(TestsConfig.RESULTS_DIR))

            results['documents'] = {
                'success': True,
                'data': documents_analysis,
                'file_created': os.path.exists(docs_output_path),
                'records_count': len(documents_analysis),
                'output_path': docs_output_path
            }
            data_manager.set_processed_data("documents_processed", documents_analysis)
            print(f"✅ Документы: {len(documents_analysis)} записей")
        except Exception as e:
            print(f"❌ Ошибка анализа документов: {e}")
    else:
        print("⚠️ Нет данных документов для анализа")

    # Анализ искового производства
    print("\n⚔️ АНАЛИЗ ИСКОВОГО ПРОИЗВОДСТВА...")
    try:
        lawsuit_analysis = run_lawsuit_analysis(detailed_df)
        if lawsuit_analysis is not None and not lawsuit_analysis.empty:
            results['lawsuit'] = {
                'success': True,
                'data': lawsuit_analysis,
                'records_count': len(lawsuit_analysis),
                'stages_distribution': lawsuit_analysis[
                    'caseStage'].value_counts().to_dict() if 'caseStage' in lawsuit_analysis.columns else {}
            }
            print(f"✅ Исковое: {len(lawsuit_analysis)} записей")
        else:
            print("⚠️ Нет данных для искового производства")
    except Exception as e:
        print(f"❌ Ошибка анализа искового: {e}")

    # Анализ приказного производства
    print("\n📝 АНАЛИЗ ПРИКАЗНОГО ПРОИЗВОДСТВА...")
    try:
        order_analysis = run_order_analysis(detailed_df)
        if order_analysis is not None and not order_analysis.empty:
            results['order'] = {
                'success': True,
                'data': order_analysis,
                'records_count': len(order_analysis),
                'stages_distribution': order_analysis[
                    'caseStage'].value_counts().to_dict() if 'caseStage' in order_analysis.columns else {}
            }
            print(f"✅ Приказное: {len(order_analysis)} записей")
        else:
            print("⚠️ Нет данных для приказного производства")
    except Exception as e:
        print(f"❌ Ошибка анализа приказного: {e}")

    # Сводка по всем модулям
    results['summary'] = {
        'all_modules_working': all(
            [results['lawsuit']['success'], results['order']['success'], results['documents']['success']]),
        'any_module_working': any(
            [results['lawsuit']['success'], results['order']['success'], results['documents']['success']]),
        'total_records': sum([results[module]['records_count'] for module in ['lawsuit', 'order', 'documents'] if
                              results[module]['success']])
    }

    return results


def run_lawsuit_analysis(detailed_df: pd.DataFrame) -> pd.DataFrame:
    """Запуск анализа искового производства"""
    # Фильтрация данных для искового производства
    filtered = detailed_df[
        (detailed_df[COLUMNS["CATEGORY"]] == VALUES["CLAIM_FROM_BANK"]) &
        (detailed_df[COLUMNS["METHOD_OF_PROTECTION"]] == VALUES["CLAIM_PROCEEDINGS"])
        ].copy()

    if filtered.empty:
        return pd.DataFrame()

    # Построение таблицы анализа
    analysis_df = build_production_table(filtered, 'lawsuit')

    # Сохранение результатов
    output_path = save_stage_table_to_excel(analysis_df, str(TestsConfig.RESULTS_DIR))

    return analysis_df


def run_order_analysis(detailed_df: pd.DataFrame) -> pd.DataFrame:
    """Запуск анализа приказного производства"""
    # Фильтрация данных для приказного производства
    filtered = detailed_df[
        (detailed_df[COLUMNS["CATEGORY"]] == VALUES["CLAIM_FROM_BANK"]) &
        (detailed_df[COLUMNS["METHOD_OF_PROTECTION"]] == VALUES["ORDER_PRODUCTION"])
        ].copy()

    if filtered.empty:
        return pd.DataFrame()

    # Построение таблицы анализа
    analysis_df = build_production_table(filtered, 'order')

    # Сохранение результатов
    output_path = save_order_stage_table_to_excel(analysis_df, str(TestsConfig.RESULTS_DIR))

    return analysis_df


def print_test_summary(results):
    """
    Выводит детальную сводку результатов теста
    """
    print("\n" + "=" * 60)
    print("📊 ДЕТАЛЬНАЯ СВОДКА РЕЗУЛЬТАТОВ")
    print("=" * 60)

    # Статусы модулей
    print("\n🔧 СТАТУСЫ МОДУЛЕЙ:")
    modules = {
        'Исковое производство': results['lawsuit'],
        'Приказное производство': results['order'],
        'Анализ документов': results['documents']
    }

    for name, result in modules.items():
        status = "✅" if result['success'] else "❌"
        count = result.get('records_count', 0)
        print(f"  {status} {name}: {count} записей")

        # Дополнительная информация для производств
        if name != 'Анализ документов' and result['success']:
            stages = result.get('stages_distribution', {})
            if stages:
                print(f"     Распределение по этапам: {stages}")

    # Общая статистика
    summary = results['summary']
    print(f"\n📈 ОБЩАЯ СТАТИСТИКА:")
    print(f"  Всего записей: {summary['total_records']}")
    print(f"  Работающих модулей: {sum([1 for module in modules.values() if module['success']])}/3")

    # Рекомендации
    print(f"\n💡 РЕКОМЕНДАЦИИ:")
    if summary['all_modules_working']:
        print("  ✅ Все модули работают корректно!")
    else:
        failed_modules = [name for name, result in modules.items() if not result['success']]
        if failed_modules:
            print(f"  ⚠️  Проверить модули: {', '.join(failed_modules)}")

    if summary['total_records'] == 0:
        print("  🚨 Внимание: не обработано ни одной записи!")


# Функция для консольного режима с выбором сценария
def run_console(**kwargs):
    """
    Запуск теста в консольном режиме с выбором сценария
    """
    scenario = kwargs.get('scenario', 'all')

    print(f"\n🎯 ЗАПУСК С ЦЕНОАРИЕМ: {scenario.upper()}")

    # Загрузка данных - ИСПРАВЛЕННЫЙ ВАРИАНТ
    from backend.app.common.tests.auto.file_loader_test import load_test_files

    load_result = load_test_files(force_reload=False)
    if not load_result.get("success", False) or not load_result.get("loaded", False):
        print("❌ Не удалось загрузить файлы для тестирования")
        return False

    documents_df = data_manager.get_documents_data()
    detailed_df = data_manager.get_detailed_data()

    if scenario == 'lawsuit':
        result = run_lawsuit_analysis(detailed_df)
        print(f"✅ Исковое производство: {len(result)} записей")
        return result is not None and not result.empty
    elif scenario == 'order':
        result = run_order_analysis(detailed_df)
        print(f"✅ Приказное производство: {len(result)} записей")
        return result is not None and not result.empty
    elif scenario == 'documents':
        result = analyze_documents(documents_df)
        print(f"✅ Анализ документов: {len(result)} записей")
        return result is not None and not result.empty
    else:
        # Полный тест
        return run()


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)