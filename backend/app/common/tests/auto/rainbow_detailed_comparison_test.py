# backend/app/common/tests/auto/rainbow_detailed_comparison_test.py
"""
Детальное сравнение классификаций радуги с красивой статистикой

Сравнивает результаты двух систем классификации и выводит детальный отчет
о расхождениях между актуальной и дополнительной системами.
"""

import os
import sys

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

from backend.app.common.modules.data_import import load_excel_data
from backend.app.common.modules.data_clean_detailed import clean_data
from backend.app.rainbow.modules.rainbow_classifier import RainbowClassifier
from backend.app.rainbow.modules.rainbow_by_l import RainbowByLClassifier
from backend.app.common.tests.tests_config import TestsConfig


def run():
    """
    Детальное сравнение двух систем классификации радуги

    Returns:
        bool: True если тест пройден успешно
    """
    print("\n" + "=" * 80)
    print("🌈 ДЕТАЛЬНОЕ СРАВНЕНИЕ КЛАССИФИКАЦИЙ РАДУГИ")
    print("=" * 80)

    try:
        # 1. Загрузка данных
        print("\n📁 ЗАГРУЗКА ДАННЫХ...")
        file_path = TestsConfig.TEST_FILES["detailed"]

        if not file_path.exists():
            print(f"❌ Файл не найден: {file_path}")
            return False

        raw_data = load_excel_data(str(file_path))
        cleaned_data = clean_data(raw_data)

        print(f"✅ Данные загружены: {len(cleaned_data)} строк")

        # 2. Получаем статистики
        print("\n🔵 АКТУАЛЬНАЯ КЛАССИФИКАЦИЯ...")
        actual_stats = RainbowClassifier.classify_cases(cleaned_data)

        print("🟢 ДОПОЛНИТЕЛЬНАЯ КЛАССИФИКАЦИЯ...")
        additional_stats = RainbowByLClassifier.classify_cases(cleaned_data)

        # 3. Сравниваем статистики
        print("\n📊 ДЕТАЛЬНОЕ СРАВНЕНИЕ:")
        results = compare_rainbow_statistics(actual_stats, additional_stats)

        # 4. Вывод итогов
        print_comparison_summary(results)

        # Тест успешен если обе системы работают и есть разумное сходство
        success = (results['summary']['both_working'] and
                   results['summary']['avg_similarity'] > 80)

        if success:
            print("\n✅ ТЕСТ СРАВНЕНИЯ РАДУГИ УСПЕШНО ЗАВЕРШЕН!")
        else:
            print("\n⚠️ ТЕСТ ЗАВЕРШЕН С ПРЕДУПРЕЖДЕНИЯМИ")

        return success

    except Exception as e:
        print(f"❌ Критическая ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        return False


def compare_rainbow_statistics(actual_stats, additional_stats):
    """
    Сравнивает две статистики радуги и выводит детальный отчет.

    Args:
        actual_stats: Статистика актуальной системы
        additional_stats: Статистика дополнительной системы

    Returns:
        dict: Детализированные результаты сравнения
    """
    # Названия цветовых категорий
    color_names = [
        "ИК (Ипотечные)",
        "Серый (Переоткрыто)",
        "Зеленый (Суд.акт + передача)",
        "Желтый (Условно закрыто + передача)",
        "Оранжевый (Суд.акт без передачи)",
        "Синий (Приказное >90 дней)",
        "Красный (До 2023 года)",
        "Лиловый (Исковое >120 дней)",
        "Иное"
    ]

    # Преобразуем актуальную статистику в список если нужно
    if hasattr(actual_stats, 'items'):
        actual_list = [actual_stats.get(color.split(' ')[0], 0) for color in color_names]
    else:
        actual_list = actual_stats

    # Преобразуем дополнительную статистику в список
    if hasattr(additional_stats, 'items'):
        additional_list = [additional_stats[color] for color in color_names]
    else:
        additional_list = additional_stats

    # Проверка корректности данных
    if len(actual_list) != len(additional_list):
        raise ValueError(f"Разная длина массивов: Актуальная={len(actual_list)}, Дополнительная={len(additional_list)}")

    # Расчет общих сумм
    actual_total = sum(actual_list)
    additional_total = sum(additional_list)

    print("=" * 80)
    print("📊 СРАВНЕНИЕ СТАТИСТИК: Актуальная vs Дополнительная система")
    print("=" * 80)
    print(
        f"Общее количество дел: Актуальная={actual_total}, Дополнительная={additional_total}, Разница={additional_total - actual_total}\n")

    # Таблица 1: Абсолютные значения
    print("ТАБЛИЦА 1: Абсолютные значения")
    print("-" * 70)
    print(f"{'Цвет':<25} {'Актуальная':<12} {'Дополнит.':<12} {'Разница':<12} {'% сходства':<12}")
    print("-" * 70)

    results_absolute = []
    for i, color in enumerate(color_names):
        actual_val = actual_list[i]
        additional_val = additional_list[i]
        diff = actual_val - additional_val
        diff_sign = "+" if diff > 0 else "" if diff == 0 else ""

        # Расчет процента сходства
        max_val = max(actual_val, additional_val)
        similarity_pct = (1 - abs(diff) / max_val) * 100 if max_val > 0 else 100

        # Определение эмодзи для визуализации
        if similarity_pct >= 98:
            emoji = "✅"
        elif similarity_pct >= 90:
            emoji = "⚠️"
        else:
            emoji = "🚨"

        print(f"{color:<25} {actual_val:<12} {additional_val:<12} {diff_sign}{diff:<11} {similarity_pct:.1f}% {emoji}")
        results_absolute.append({
            'color': color,
            'actual': actual_val,
            'additional': additional_val,
            'diff': diff,
            'similarity': similarity_pct,
            'emoji': emoji
        })

    print()

    # Таблица 2: Процентные значения
    print("ТАБЛИЦА 2: Процентные значения (нормализованные)")
    print("-" * 75)
    print(f"{'Цвет':<25} {'Актуальная (%)':<14} {'Дополнит. (%)':<14} {'Разница (%)':<12} {'Статус':<8}")
    print("-" * 75)

    results_percentage = []
    for i, color in enumerate(color_names):
        actual_pct = (actual_list[i] / actual_total) * 100
        additional_pct = (additional_list[i] / additional_total) * 100
        diff_pct = actual_pct - additional_pct
        diff_sign = "+" if diff_pct > 0 else "" if diff_pct == 0 else ""

        # Определение статуса
        abs_diff = abs(diff_pct)
        if abs_diff <= 0.1:
            status = "✅"
        elif abs_diff <= 0.5:
            status = "⚠️"
        else:
            status = "🚨"

        print(
            f"{color:<25} {actual_pct:.2f}%{' ':>8} {additional_pct:.2f}%{' ':>8} {diff_sign}{diff_pct:.2f}%{' ':>8} {status}")
        results_percentage.append({
            'color': color,
            'actual_pct': actual_pct,
            'additional_pct': additional_pct,
            'diff_pct': diff_pct,
            'status': status
        })

    print()

    # Сводная статистика
    print("📈 СВОДНАЯ СТАТИСТИКА:")
    print("-" * 40)

    # Средний процент сходства
    avg_similarity = sum([r['similarity'] for r in results_absolute]) / len(results_absolute)
    print(f"Средний процент сходства: {avg_similarity:.1f}%")

    # Количество проблемных категорий
    problematic = len([r for r in results_absolute if r['similarity'] < 90])
    warning = len([r for r in results_absolute if 90 <= r['similarity'] < 98])
    good = len([r for r in results_absolute if r['similarity'] >= 98])

    print(f"Категории: ✅ {good} отличных, ⚠️ {warning} с предупреждением, 🚨 {problematic} проблемных")

    return {
        'absolute': results_absolute,
        'percentage': results_percentage,
        'summary': {
            'total_actual': actual_total,
            'total_additional': additional_total,
            'avg_similarity': avg_similarity,
            'problematic_categories': problematic,
            'both_working': actual_total > 0 and additional_total > 0
        }
    }


def print_comparison_summary(results):
    """
    Выводит итоговое сравнение
    """
    summary = results['summary']

    print("\n🎯 ИТОГИ СРАВНЕНИЯ:")
    print("-" * 40)
    print(f"Общее сходство: {summary['avg_similarity']:.1f}%")

    if summary['avg_similarity'] >= 95:
        print("✅ Системы показывают высокое сходство")
    elif summary['avg_similarity'] >= 85:
        print("⚠️ Системы показывают умеренное сходство")
    else:
        print("🚨 Системы показывают значительные расхождения")

    if summary['problematic_categories'] == 0:
        print("✅ Все категории классифицируются согласованно")
    else:
        print(f"⚠️ Проблемные категории: {summary['problematic_categories']}")


# Функция для консольного режима
def run_console(**kwargs):
    """Запуск теста в консольном режиме"""
    return run()


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)