# backend/app/common/tests/auto/performance_test.py
"""
Тест производительности полного цикла обработки данных

Измеряет время выполнения всех ключевых операций:
- Загрузка и очистка данных
- Анализ радуги (оба классификатора)
- Анализ производств (исковое/приказное)
- Анализ документов
- Расчет задач
- Сохранение результатов
"""

import os
import sys
import time
import pandas as pd
from datetime import datetime
from typing import Dict, List

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

from backend.app.data_management.modules.data_import import load_excel_data
from backend.app.data_management.modules.data_clean_detailed import clean_data
from backend.app.data_management.modules.data_clean_documents import clean_documents_data
from backend.app.data_management.modules.data_manager import data_manager
from backend.app.rainbow.modules.rainbow_classifier import RainbowClassifier
from backend.app.rainbow.modules.rainbow_by_l import RainbowByLClassifier
from backend.app.terms_of_support_v2.modules.terms_analyzer_v2 import build_production_table
from backend.app.document_monitoring_v2.modules.document_stage_checks_v2 import analyze_documents
from backend.app.task_manager.modules.task_analyzer import task_analyzer
from backend.app.common.config.column_names import COLUMNS, VALUES
from backend.app.common.tests.tests_config import TestsConfig


class PerformanceTimer:
    """Утилита для измерения времени выполнения"""

    def __init__(self):
        self.metrics = {}
        self.current_operation = None
        self.start_time = None

    def start(self, operation_name: str):
        """Начать измерение операции"""
        self.current_operation = operation_name
        self.start_time = time.time()
        print(f"⏱️  Начало: {operation_name}")

    def stop(self) -> float:
        """Завершить измерение и вернуть время"""
        if not self.current_operation or not self.start_time:
            return 0.0

        duration = time.time() - self.start_time
        self.metrics[self.current_operation] = duration
        print(f"⏱️  Завершено: {self.current_operation} - {duration:.2f} сек")

        self.current_operation = None
        self.start_time = None
        return duration

    def get_summary(self) -> Dict:
        """Получить сводку по всем измерениям"""
        total_time = sum(self.metrics.values())
        return {
            'total_time': total_time,
            'metrics': self.metrics.copy(),
            'operations_count': len(self.metrics),
            'average_time': total_time / len(self.metrics) if self.metrics else 0
        }


def run():
    """
    Тест производительности полного цикла обработки

    Returns:
        bool: True если тест пройден успешно
    """
    print("\n" + "=" * 80)
    print("⚡ ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ ПОЛНОГО ЦИКЛА")
    print("=" * 80)

    timer = PerformanceTimer()
    results = {}

    try:
        # 1. Загрузка данных
        print("\n📁 ЭТАП 1: ЗАГРУЗКА ДАННЫХ")
        timer.start("Загрузка детального отчета")
        detailed_data = load_and_clean_detailed()
        timer.stop()

        timer.start("Загрузка отчета документов")
        documents_data = load_and_clean_documents()
        timer.stop()

        if detailed_data is None or documents_data is None:
            print("❌ Не удалось загрузить данные для тестирования")
            return False

        results['data_loaded'] = True
        results['detailed_rows'] = len(detailed_data)
        results['documents_rows'] = len(documents_data)

        # 2. Анализ радуги
        print("\n🌈 ЭТАП 2: АНАЛИЗ РАДУГИ")
        timer.start("Классификация RainbowClassifier")
        rainbow_actual = RainbowClassifier.classify_cases(detailed_data)
        timer.stop()

        timer.start("Классификация RainbowByLClassifier")
        rainbow_additional = RainbowByLClassifier.classify_cases(detailed_data)
        timer.stop()

        results['rainbow_actual_count'] = sum(rainbow_actual) if hasattr(rainbow_actual, '__iter__') else 0
        results['rainbow_additional_count'] = sum(rainbow_additional.values()) if hasattr(rainbow_additional,
                                                                                          'values') else 0

        # 3. Анализ производств
        print("\n⚖️ ЭТАП 3: АНАЛИЗ ПРОИЗВОДСТВ")
        timer.start("Анализ искового производства")
        lawsuit_analysis = analyze_lawsuit_production(detailed_data)
        timer.stop()

        timer.start("Анализ приказного производства")
        order_analysis = analyze_order_production(detailed_data)
        timer.stop()

        results['lawsuit_records'] = len(lawsuit_analysis) if lawsuit_analysis is not None else 0
        results['order_records'] = len(order_analysis) if order_analysis is not None else 0

        # 4. Анализ документов
        print("\n📄 ЭТАП 4: АНАЛИЗ ДОКУМЕНТОВ")
        timer.start("Анализ документов")
        documents_analysis = analyze_documents(documents_data)
        timer.stop()

        results['documents_analyzed'] = len(documents_analysis) if documents_analysis is not None else 0

        # 5. Расчет задач
        print("\n🔧 ЭТАП 5: РАСЧЕТ ЗАДАЧ")
        # Сохраняем данные в data_manager для task_analyzer
        data_manager.set_processed_data("lawsuit_staged", lawsuit_analysis)
        data_manager.set_processed_data("order_staged", order_analysis)
        data_manager.set_processed_data("documents_processed", documents_analysis)

        timer.start("Расчет всех задач")
        all_tasks = task_analyzer.analyze_all_tasks()
        timer.stop()

        results['tasks_calculated'] = len(all_tasks) if all_tasks else 0

        # 6. Сохранение результатов (симуляция)
        print("\n💾 ЭТАП 6: СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
        timer.start("Сохранение результатов анализа")
        save_results_simulation(results)
        timer.stop()

        # 7. Формирование отчета
        print("\n📊 ЭТАП 7: ФОРМИРОВАНИЕ ОТЧЕТА")
        performance_summary = timer.get_summary()
        results['performance'] = performance_summary

        # Вывод итогового отчета
        print_performance_report(results)

        # Сохранение детального отчета
        save_detailed_report(results)

        # Тест считается успешным если все основные этапы выполнены
        success = (results['data_loaded'] and
                   results['rainbow_actual_count'] > 0 and
                   results['tasks_calculated'] > 0)

        if success:
            print("\n✅ ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ УСПЕШНО ЗАВЕРШЕН!")
        else:
            print("\n⚠️ ТЕСТ ЗАВЕРШЕН С ПРЕДУПРЕЖДЕНИЯМИ")

        return success

    except Exception as e:
        print(f"❌ Критическая ошибка в тесте производительности: {e}")
        import traceback
        traceback.print_exc()
        return False


def load_and_clean_detailed():
    """Загрузка и очистка детального отчета"""
    file_path = TestsConfig.TEST_FILES["detailed"]
    if not file_path.exists():
        print(f"❌ Файл не найден: {file_path}")
        return None

    raw_data = load_excel_data(str(file_path))
    return clean_data(raw_data)


def load_and_clean_documents():
    """Загрузка и очистка отчета документов"""
    file_path = TestsConfig.TEST_FILES["documents"]
    if not file_path.exists():
        print(f"❌ Файл не найден: {file_path}")
        return None

    raw_data = load_excel_data(str(file_path))
    return clean_documents_data(raw_data)


def analyze_lawsuit_production(detailed_df: pd.DataFrame) -> pd.DataFrame:
    """Анализ искового производства"""
    filtered = detailed_df[
        (detailed_df[COLUMNS["CATEGORY"]] == VALUES["CLAIM_FROM_BANK"]) &
        (detailed_df[COLUMNS["METHOD_OF_PROTECTION"]] == VALUES["CLAIM_PROCEEDINGS"])
        ].copy()

    if filtered.empty:
        return pd.DataFrame()

    return build_production_table(filtered, 'lawsuit')


def analyze_order_production(detailed_df: pd.DataFrame) -> pd.DataFrame:
    """Анализ приказного производства"""
    filtered = detailed_df[
        (detailed_df[COLUMNS["CATEGORY"]] == VALUES["CLAIM_FROM_BANK"]) &
        (detailed_df[COLUMNS["METHOD_OF_PROTECTION"]] == VALUES["ORDER_PRODUCTION"])
        ].copy()

    if filtered.empty:
        return pd.DataFrame()

    return build_production_table(filtered, 'order')


def save_results_simulation(results: Dict):
    """Симуляция сохранения результатов (без реального создания файлов)"""
    # В реальном тесте здесь были бы вызовы эндпоинтов сохранения
    time.sleep(0.5)  # Имитация времени сохранения
    print("💾 Результаты сохранены (симуляция)")


def print_performance_report(results: Dict):
    """Вывод отчета о производительности"""
    performance = results['performance']

    print("\n" + "=" * 80)
    print("📊 ОТЧЕТ О ПРОИЗВОДИТЕЛЬНОСТИ")
    print("=" * 80)

    print(f"\n🎯 ОБЩАЯ СТАТИСТИКА:")
    print(f"  Общее время выполнения: {performance['total_time']:.2f} сек")
    print(f"  Количество операций: {performance['operations_count']}")
    print(f"  Среднее время на операцию: {performance['average_time']:.2f} сек")

    print(f"\n📈 ДАННЫЕ:")
    print(f"  Строк в детальном отчете: {results['detailed_rows']}")
    print(f"  Строк в документах: {results['documents_rows']}")
    print(f"  Дел в радуге (актуальная): {results['rainbow_actual_count']}")
    print(f"  Дел в радуге (дополнительная): {results['rainbow_additional_count']}")
    print(f"  Записей искового производства: {results['lawsuit_records']}")
    print(f"  Записей приказного производства: {results['order_records']}")
    print(f"  Записей анализа документов: {results['documents_analyzed']}")
    print(f"  Рассчитано задач: {results['tasks_calculated']}")

    print(f"\n⏱️  ДЕТАЛЬНЫЕ ЗАМЕРЫ:")
    print("-" * 60)
    print(f"{'ОПЕРАЦИЯ':<40} {'ВРЕМЯ (сек)':<12} {'% ОТ ОБЩЕГО':<12}")
    print("-" * 60)

    for operation, duration in performance['metrics'].items():
        percentage = (duration / performance['total_time']) * 100
        print(f"{operation:<40} {duration:<12.2f} {percentage:<12.1f}")

    # Определение самых медленных операций
    slow_operations = sorted(performance['metrics'].items(),
                             key=lambda x: x[1], reverse=True)[:3]

    print(f"\n🐌 САМЫЕ МЕДЛЕННЫЕ ОПЕРАЦИИ:")
    for i, (operation, duration) in enumerate(slow_operations, 1):
        print(f"  {i}. {operation}: {duration:.2f} сек")


def save_detailed_report(results: Dict):
    """Сохранение детального отчета о производительности"""
    try:
        # Сохраняем метрики производительности
        metrics_df = pd.DataFrame([
            {'operation': op, 'duration_seconds': duration}
            for op, duration in results['performance']['metrics'].items()
        ])

        # Сохраняем общую статистику
        stats_df = pd.DataFrame([{
            'total_time_seconds': results['performance']['total_time'],
            'operations_count': results['performance']['operations_count'],
            'detailed_rows': results['detailed_rows'],
            'documents_rows': results['documents_rows'],
            'tasks_calculated': results['tasks_calculated'],
            'timestamp': datetime.now().isoformat()
        }])

        # Сохраняем в файл
        report_path = TestsConfig.RESULTS_DIR / "performance_report.xlsx"
        with pd.ExcelWriter(report_path) as writer:
            metrics_df.to_excel(writer, sheet_name='Метрики', index=False)
            stats_df.to_excel(writer, sheet_name='Статистика', index=False)

        print(f"💾 Детальный отчет сохранен: {report_path}")

    except Exception as e:
        print(f"⚠️ Не удалось сохранить детальный отчет: {e}")


# Функция для консольного режима
def run_console(**kwargs):
    """Запуск теста в консольном режиме"""
    return run()


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)