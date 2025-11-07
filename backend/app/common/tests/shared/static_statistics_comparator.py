# backend/app/common/tests/shared/static_statistics_comparator.py
"""
Модуль для сравнения статистик между Python кодом и Excel формулами.

Сравнивает результаты цветовой классификации и выводит детальный отчет
о расхождениях между двумя методами расчета.
"""


def compare_statistics(my_stats, excel_stats, color_names=None):
    """
    Сравнивает две статистики и выводит детальный отчет.

    Args:
        my_stats (list): Статистика из Python кода [ИК, Серый, Зеленый, ...]
        excel_stats (list): Статистика из Excel формул [ИК, Серый, Зеленый, ...]
        color_names (list): Названия цветовых категорий (опционально)

    Returns:
        dict: Детализированные результаты сравнения
    """

    # Стандартные названия цветов
    if color_names is None:
        color_names = [
            "ИК", "Серый", "Зеленый", "Желтый", "Оранжевый",
            "Синий", "Красный", "Лиловый", "Иное"
        ]

    # Проверка корректности входных данных
    if len(my_stats) != len(excel_stats):
        raise ValueError(f"Разная длина массивов: Python={len(my_stats)}, Excel={len(excel_stats)}")

    if len(my_stats) != len(color_names):
        raise ValueError(f"Количество цветов ({len(color_names)}) не совпадает с данными ({len(my_stats)})")

    # Расчет общих сумм
    my_total = sum(my_stats)
    excel_total = sum(excel_stats)

    print("=" * 80)
    print("📊 СРАВНЕНИЕ СТАТИСТИК: Python код vs Excel формулы")
    print("=" * 80)
    print(f"Общее количество дел: Python={my_total}, Excel={excel_total}, Разница={excel_total - my_total}\n")

    # Таблица 1: Абсолютные значения
    print("ТАБЛИЦА 1: Абсолютные значения")
    print("-" * 60)
    print(f"{'Цвет':<12} {'Python':<8} {'Excel':<8} {'Разница':<10} {'% сходства':<12}")
    print("-" * 60)

    results_absolute = []
    for i, color in enumerate(color_names):
        my_val = my_stats[i]
        excel_val = excel_stats[i]
        diff = my_val - excel_val
        diff_sign = "+" if diff > 0 else "" if diff == 0 else ""

        # Расчет процента сходства
        max_val = max(my_val, excel_val)
        similarity_pct = (1 - abs(diff) / max_val) * 100 if max_val > 0 else 100

        # Определение эмодзи для визуализации
        if similarity_pct >= 98:
            emoji = "✅"
        elif similarity_pct >= 90:
            emoji = "⚠️"
        else:
            emoji = "🚨"

        print(f"{color:<12} {my_val:<8} {excel_val:<8} {diff_sign}{diff:<9} {similarity_pct:.1f}% {emoji}")
        results_absolute.append({
            'color': color,
            'python': my_val,
            'excel': excel_val,
            'diff': diff,
            'similarity': similarity_pct,
            'emoji': emoji
        })

    print()

    # Таблица 2: Процентные значения
    print("ТАБЛИЦА 2: Процентные значения (нормализованные)")
    print("-" * 65)
    print(f"{'Цвет':<12} {'Python (%)':<10} {'Excel (%)':<10} {'Разница (%)':<12} {'Статус':<8}")
    print("-" * 65)

    results_percentage = []
    for i, color in enumerate(color_names):
        my_pct = (my_stats[i] / my_total) * 100
        excel_pct = (excel_stats[i] / excel_total) * 100
        diff_pct = my_pct - excel_pct
        diff_sign = "+" if diff_pct > 0 else "" if diff_pct == 0 else ""

        # Определение статуса
        abs_diff = abs(diff_pct)
        if abs_diff <= 0.1:
            status = "✅"
        elif abs_diff <= 0.5:
            status = "⚠️"
        else:
            status = "🚨"

        print(f"{color:<12} {my_pct:.2f}%{' ':>6} {excel_pct:.2f}%{' ':>6} {diff_sign}{diff_pct:.2f}%{' ':>8} {status}")
        results_percentage.append({
            'color': color,
            'python_pct': my_pct,
            'excel_pct': excel_pct,
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
            'total_python': my_total,
            'total_excel': excel_total,
            'avg_similarity': avg_similarity,
            'problematic_categories': problematic
        }
    }


# Пример использования
if __name__ == "__main__":
    # Pethon данные
    my_statistics = [903, 971, 109, 321, 822, 1105, 64, 2475, 6972]

    # Данные из Excel
    excel_statistics = [893, 985, 101, 397, 886, 936, 64, 2329, 7437]

    # Запуск сравнения
    results = compare_statistics(my_statistics, excel_statistics)
