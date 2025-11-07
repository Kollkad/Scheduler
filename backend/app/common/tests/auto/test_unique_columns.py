# backend/app/common/tests/auto/unique_columns_test.py
#TODO: переделать тест, ошибка
"""
Тест проверки уникальности колонок в данных документов

Проверяет уникальность значений в ключевых колонках:
- Код передачи, Код запроса, Код дела
Ищет потенциально уникальные идентификаторы среди всех колонок
"""

import os
import sys
from typing import Dict

import pandas as pd

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

from backend.app.common.modules.data_import import load_excel_data
from backend.app.common.modules.data_clean_documents import clean_documents_data
from backend.app.common.tests.tests_config import TestsConfig


def run():
    """
    Тест проверки уникальности колонок в данных документов

    Returns:
        bool: True если тест пройден успешно
    """
    print("\n" + "=" * 60)
    print("🔍 ТЕСТ ПРОВЕРКИ УНИКАЛЬНОСТИ КОЛОНОК")
    print("=" * 60)

    try:
        # 1. Загрузка данных
        print("\n📁 ЗАГРУЗКА ДАННЫХ ДОКУМЕНТОВ...")
        file_path = TestsConfig.TEST_FILES["documents"]

        if not file_path.exists():
            print(f"❌ Файл не найден: {file_path}")
            return False

        # 2. Проверка уникальности основных колонок
        print("\n🔎 ПРОВЕРКА ОСНОВНЫХ КОЛОНОК...")
        uniqueness_results = check_column_uniqueness(str(file_path))

        if "error" in uniqueness_results:
            print(f"❌ Ошибка: {uniqueness_results['error']}")
            return False

        print_uniqueness_results(uniqueness_results)

        # 3. Поиск всех уникальных идентификаторов
        print("\n🎯 ПОИСК УНИКАЛЬНЫХ ИДЕНТИФИКАТОРОВ...")
        identifier_results = find_unique_identifier(str(file_path))

        if "error" in identifier_results:
            print(f"❌ Ошибка: {identifier_results['error']}")
            return False

        print_identifier_results(identifier_results)

        # Тест считается успешным если данные загружены и проанализированы
        success = True
        if success:
            print("\n✅ ТЕСТ ПРОВЕРКИ УНИКАЛЬНОСТИ УСПЕШНО ЗАВЕРШЕН!")
        else:
            print("\n⚠️ ТЕСТ ЗАВЕРШЕН С ПРЕДУПРЕЖДЕНИЯМИ")

        return success

    except Exception as e:
        print(f"❌ Критическая ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_column_uniqueness(filepath: str) -> Dict[str, Dict]:
    """
    Проверяет уникальность значений в колонках 'Код передачи', 'Код запроса', 'Код дела'
    """
    try:
        # Загружаем и очищаем данные
        raw_df = load_excel_data(filepath)
        cleaned_df = clean_documents_data(raw_df)

        # Проверяем наличие нужных колонок
        required_columns = ['Код передачи', 'Код запроса', 'Код дела']
        missing_columns = [col for col in required_columns if col not in cleaned_df.columns]

        if missing_columns:
            return {"error": f"Отсутствуют колонки: {missing_columns}"}

        results = {}

        for column in required_columns:
            # Получаем значения колонки (исключая NaN)
            values = cleaned_df[column].dropna()
            total_values = len(values)
            unique_values = values.nunique()

            # Проверяем уникальность
            is_unique = unique_values == total_values
            duplicate_count = total_values - unique_values

            results[column] = {
                'total_values': total_values,
                'unique_values': unique_values,
                'is_unique': is_unique,
                'duplicate_count': duplicate_count,
                'duplicate_percentage': (duplicate_count / total_values * 100) if total_values > 0 else 0
            }

            # Если есть дубликаты, находим примеры
            if duplicate_count > 0:
                duplicates = values[values.duplicated(keep=False)]
                results[column]['duplicate_examples'] = duplicates.head(3).tolist()

        return results

    except Exception as e:
        return {"error": f"Ошибка при обработке файла: {str(e)}"}


def find_unique_identifier(filepath: str) -> Dict:
    """
    Ищет потенциально уникальный идентификатор среди всех колонок
    """
    try:
        raw_df = load_excel_data(filepath)
        cleaned_df = clean_documents_data(raw_df)

        results = {}
        unique_columns = []

        for column in cleaned_df.columns:
            try:
                values = cleaned_df[column]

                # Безопасное преобразование к Series если нужно
                if hasattr(values, 'tolist'):
                    values_series = values
                else:
                    values_series = pd.Series(values)

                values_clean = values_series.dropna()
                total_values = len(values_clean)

                if total_values == 0:
                    continue

                # Безопасный подсчет уникальных значений
                try:
                    unique_values = values_clean.nunique()
                except:
                    # Альтернативный способ через set
                    unique_values = len(set(values_clean.astype(str)))

                is_unique = (unique_values == total_values)

                results[column] = {
                    'is_unique': is_unique,
                    'total_values': total_values,
                    'unique_values': unique_values,
                    'duplicate_count': total_values - unique_values
                }

                if is_unique:
                    unique_columns.append(column)

            except Exception as col_error:
                print(f"⚠️ Ошибка в колонке {column}: {col_error}")
                continue

        return {
            'all_columns': results,
            'unique_columns': unique_columns,
            'recommendation': f"Рекомендуемые уникальные идентификаторы: {unique_columns}" if unique_columns else "Не найдено полностью уникальных колонок"
        }

    except Exception as e:
        return {"error": f"Ошибка при поиске идентификатора: {str(e)}"}


def print_uniqueness_results(results):
    """
    Выводит результаты проверки уникальности
    """
    print("\n📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ УНИКАЛЬНОСТИ:")
    print("-" * 70)
    print(f"{'Колонка':<15} {'Уникальна':<10} {'Всего':<8} {'Уникальных':<12} {'Дубликатов':<12} {'% Дубликатов':<12}")
    print("-" * 70)

    for column, stats in results.items():
        status = "✅" if stats['is_unique'] else "❌"
        print(f"{column:<15} {status:<10} {stats['total_values']:<8} {stats['unique_values']:<12} "
              f"{stats['duplicate_count']:<12} {stats['duplicate_percentage']:.1f}%")

        # Показываем примеры дубликатов если есть
        if stats['duplicate_count'] > 0 and 'duplicate_examples' in stats:
            examples = ", ".join(map(str, stats['duplicate_examples'][:2]))
            print(f"                 Примеры дубликатов: {examples}...")


def print_identifier_results(results):
    """
    Выводит результаты поиска уникальных идентификаторов
    """
    unique_columns = results['unique_columns']

    print(f"\n🎯 НАЙДЕНО УНИКАЛЬНЫХ КОЛОНОК: {len(unique_columns)}")

    if unique_columns:
        print("✅ Колонки с уникальными значениями:")
        for i, column in enumerate(unique_columns, 1):
            stats = results['all_columns'][column]
            print(f"   {i}. {column} ({stats['total_values']} значений)")
    else:
        print("❌ Не найдено полностью уникальных колонок")

    # Показываем топ-5 колонок с наименьшим процентом дубликатов
    print(f"\n🏆 ТОП-5 КОЛОНОК С НАИМЕНЬШИМ КОЛИЧЕСТВОМ ДУБЛИКАТОВ:")
    all_columns = []
    for column, stats in results['all_columns'].items():
        if stats['total_values'] > 0:
            duplicate_pct = (stats['duplicate_count'] / stats['total_values']) * 100
            all_columns.append((column, duplicate_pct, stats['total_values']))

    # Сортируем по проценту дубликатов
    all_columns.sort(key=lambda x: x[1])

    for i, (column, duplicate_pct, total) in enumerate(all_columns[:5], 1):
        status = "✅" if duplicate_pct == 0 else "⚠️"
        print(f"   {i}. {column}: {duplicate_pct:.1f}% дубликатов ({total} значений) {status}")


# Функция для консольного режима
def run_console(**kwargs):
    """Запуск теста в консольном режиме"""
    return run()


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)