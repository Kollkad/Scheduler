# backend/app/common/tests/auto/document_coverage_test.py
"""
Тест покрытия документов - проверка соответствия дел из детального отчета и отчета документов.

Анализирует сколько дел из детального отчета имеют соответствующие записи в отчете документов
для проверки интеграции между модулями.
"""

import os
import sys
import pandas as pd

# Добавление пути к проекту для импортов
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

from backend.app.common.modules.data_manager import data_manager
from backend.app.common.config.column_names import COLUMNS, VALUES
from backend.app.common.tests.tests_config import TestsConfig


def run():
    """
    Тест анализа покрытия документов

    Returns:
        bool: True если тест пройден успешно
    """
    print("\n" + "=" * 60)
    print("📊 ТЕСТ ПОКРЫТИЯ ДОКУМЕНТОВ")
    print("=" * 60)

    try:
        # Анализ покрытия
        results = analyze_document_coverage()

        if not results:
            print("❌ Тест провален: не удалось проанализировать покрытие")
            return False

        # Вывод итогов
        print_summary(results)

        # Сохранение результатов
        save_results(results)

        # Тест считается успешным если данные загружены и проанализированы
        success = results['total_detailed_cases'] > 0 and results['total_document_cases'] > 0

        if success:
            print("\n✅ ТЕСТ ПОКРЫТИЯ ДОКУМЕНТОВ УСПЕШНО ЗАВЕРШЕН!")
        else:
            print("\n⚠️ ТЕСТ ЗАВЕРШЕН С ПРЕДУПРЕЖДЕНИЯМИ")

        return success

    except Exception as e:
        print(f"❌ Критическая ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        return False


def analyze_document_coverage():
    """
    Анализ покрытия документов - проверка соответствия дел между отчетами.

    Returns:
        dict: Результаты анализа покрытия
    """
    print("📥 ЗАГРУЗКА ОТЧЕТОВ...")

    # Используем пути из конфига
    detailed_path = TestsConfig.TEST_FILES["detailed"]
    documents_path = TestsConfig.TEST_FILES["documents"]

    # Проверка существования файлов
    if not detailed_path.exists():
        print(f"❌ Детальный файл не найден: {detailed_path}")
        return None

    if not documents_path.exists():
        print(f"❌ Файл документов не найден: {documents_path}")
        return None

    # Загрузка данных
    detailed_df = data_manager.load_detailed_report(str(detailed_path))
    documents_df = data_manager.load_documents_report(str(documents_path))

    print(f"✅ Детальный отчет: {len(detailed_df)} записей")
    print(f"✅ Отчет документов: {len(documents_df)} записей")

    # Получение уникальных кодов дел из детального отчета
    detailed_case_codes = set()
    if COLUMNS["CASE_CODE"] in detailed_df.columns:
        detailed_case_codes = set(detailed_df[COLUMNS["CASE_CODE"]].dropna().unique())
    else:
        # Поиск колонки с кодом дела по ключевым словам
        for col in detailed_df.columns:
            if any(keyword in col.lower() for keyword in ["код дела", "case", "код"]):
                detailed_case_codes = set(detailed_df[col].dropna().unique())
                break

    # Получение уникальных кодов дел из отчета документов
    documents_case_codes = set()
    if COLUMNS["DOCUMENT_CASE_CODE"] in documents_df.columns:
        documents_case_codes = set(documents_df[COLUMNS["DOCUMENT_CASE_CODE"]].dropna().unique())
    else:
        # Поиск колонки с кодом дела по ключевым словам
        for col in documents_df.columns:
            if any(keyword in col.lower() for keyword in ["код дела", "case", "код"]):
                documents_case_codes = set(documents_df[col].dropna().unique())
                break

    print(f"📋 Уникальных дел в детальном отчете: {len(detailed_case_codes)}")
    print(f"📋 Уникальных дел в отчете документов: {len(documents_case_codes)}")

    # Анализ пересечения
    common_cases = detailed_case_codes.intersection(documents_case_codes)
    only_in_detailed = detailed_case_codes - documents_case_codes
    only_in_documents = documents_case_codes - detailed_case_codes

    # Расчет процентов
    coverage_percent = (len(common_cases) / len(detailed_case_codes)) * 100 if detailed_case_codes else 0

    print("\n📈 РЕЗУЛЬТАТЫ ПОКРЫТИЯ:")
    print(f"• Общих дел: {len(common_cases)}")
    print(f"• Только в детальном отчете: {len(only_in_detailed)}")
    print(f"• Только в отчете документов: {len(only_in_documents)}")
    print(f"• Покрытие: {coverage_percent:.1f}%")

    # Анализ по типам производств
    print("\n🔍 АНАЛИЗ ПО ТИПАМ ПРОИЗВОДСТВ:")

    # Исковое производство
    lawsuit_cases = set()
    if all(col in detailed_df.columns for col in [COLUMNS["CATEGORY"], COLUMNS["METHOD_OF_PROTECTION"]]):
        lawsuit_df = detailed_df[
            (detailed_df[COLUMNS["CATEGORY"]] == VALUES["CLAIM_FROM_BANK"]) &
            (detailed_df[COLUMNS["METHOD_OF_PROTECTION"]] == VALUES["CLAIM_PROCEEDINGS"])
            ]
        if COLUMNS["CASE_CODE"] in lawsuit_df.columns:
            lawsuit_cases = set(lawsuit_df[COLUMNS["CASE_CODE"]].dropna().unique())

    lawsuit_coverage = len(lawsuit_cases.intersection(documents_case_codes))
    lawsuit_percent = (lawsuit_coverage / len(lawsuit_cases)) * 100 if lawsuit_cases else 0

    print(f"• Исковое производство: {lawsuit_coverage}/{len(lawsuit_cases)} ({lawsuit_percent:.1f}%)")

    # Приказное производство
    order_cases = set()
    if all(col in detailed_df.columns for col in [COLUMNS["CATEGORY"], COLUMNS["METHOD_OF_PROTECTION"]]):
        order_df = detailed_df[
            (detailed_df[COLUMNS["CATEGORY"]] == VALUES["CLAIM_FROM_BANK"]) &
            (detailed_df[COLUMNS["METHOD_OF_PROTECTION"]] == VALUES["ORDER_PRODUCTION"])
            ]
        if COLUMNS["CASE_CODE"] in order_df.columns:
            order_cases = set(order_df[COLUMNS["CASE_CODE"]].dropna().unique())

    order_coverage = len(order_cases.intersection(documents_case_codes))
    order_percent = (order_coverage / len(order_cases)) * 100 if order_cases else 0

    print(f"• Приказное производство: {order_coverage}/{len(order_cases)} ({order_percent:.1f}%)")

    # Примеры кодов для отладки
    print("\n🔎 ПРИМЕРЫ ДЛЯ ОТЛАДКИ:")
    if common_cases:
        print(f"• Пример общего дела: {list(common_cases)[:3]}")
    if only_in_detailed:
        print(f"• Пример дела только в детальном: {list(only_in_detailed)[:3]}")
    if only_in_documents:
        print(f"• Пример дела только в документах: {list(only_in_documents)[:3]}")

    # Возвращаем результаты для возможного дальнейшего использования
    return {
        "total_detailed_cases": len(detailed_case_codes),
        "total_document_cases": len(documents_case_codes),
        "common_cases": len(common_cases),
        "only_in_detailed": len(only_in_detailed),
        "only_in_documents": len(only_in_documents),
        "coverage_percent": coverage_percent,
        "lawsuit_coverage": lawsuit_coverage,
        "lawsuit_total": len(lawsuit_cases),
        "order_coverage": order_coverage,
        "order_total": len(order_cases)
    }


def print_summary(results):
    """
    Выводит итоговую сводку теста
    """
    print("\n🎯 ИТОГИ ТЕСТА ПОКРЫТИЯ:")
    print("-" * 40)

    coverage = results['coverage_percent']
    if coverage >= 80:
        status = "✅ ВЫСОКОЕ"
    elif coverage >= 50:
        status = "⚠️ СРЕДНЕЕ"
    else:
        status = "❌ НИЗКОЕ"

    print(f"Общее покрытие: {coverage:.1f}% - {status}")
    print(f"Дел с документами: {results['common_cases']} из {results['total_detailed_cases']}")


def save_results(results):
    """
    Сохраняет результаты анализа в файл
    """
    try:
        results_df = pd.DataFrame([results])
        output_path = TestsConfig.RESULTS_DIR / "document_coverage_analysis.xlsx"
        results_df.to_excel(output_path, index=False)
        print(f"💾 Результаты сохранены: {output_path}")
    except Exception as e:
        print(f"⚠️ Не удалось сохранить результаты: {e}")


# Функция для консольного режима
def run_console(**kwargs):
    """Запуск теста в консольном режиме"""
    return run()


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)