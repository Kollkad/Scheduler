# backend/app/common/tests/console/test_unique_columns.py
"""
Консольный тест проверки уникальности колонок в данных документов

Запуск:
    pytest backend/app/common/tests/console/test_unique_columns.py -v -s
"""
import sys

import pytest
import pandas as pd
from pathlib import Path

from backend.app.data_management.modules.data_import import load_excel_data
from backend.app.data_management.modules.data_clean_documents import clean_documents_data


@pytest.fixture(scope="module")
def documents_df() -> pd.DataFrame:
    """
    Фикстура запрашивает путь у пользователя и загружает данные
    """
    print("\n" + "=" * 60)
    print("КОНСОЛЬНЫЙ ТЕСТ: ПРОВЕРКА УНИКАЛЬНОСТИ КОЛОНОК")
    print("=" * 60)

    # Запрашиваем путь у пользователя
    user_input = input("\n📁 Введите путь к Excel файлу документов: ").strip()

    if not user_input:
        pytest.skip("Путь к файлу не указан")

    filepath = Path(user_input)
    if not filepath.exists():
        pytest.fail(f"Файл не найден: {filepath}")

    print(f"\n📥 Загрузка файла: {filepath}")

    raw_df = load_excel_data(str(filepath))
    cleaned_df = clean_documents_data(raw_df)

    print(f"✅ Загружено {len(cleaned_df)} строк, {len(cleaned_df.columns)} колонок")

    return cleaned_df


class TestDocumentColumnsUniqueness:
    """Тесты уникальности колонок в документах"""

    TARGET_COLUMNS = ['Код передачи', 'Код запроса', 'Код дела']

    def test_required_columns_exist(self, documents_df: pd.DataFrame):
        """Проверка наличия необходимых колонок"""
        missing = [col for col in self.TARGET_COLUMNS if col not in documents_df.columns]

        if missing:
            print(f"\n❌ Отсутствуют колонки: {missing}")
            print(f"   Доступные колонки: {list(documents_df.columns)}")

        assert not missing, f"Отсутствуют колонки: {missing}"

    @pytest.mark.parametrize("column_name", TARGET_COLUMNS)
    def test_column_uniqueness(self, documents_df: pd.DataFrame, column_name: str):
        """Проверка уникальности значений в колонке"""
        if column_name not in documents_df.columns:
            pytest.skip(f"Колонка '{column_name}' отсутствует")

        values = documents_df[column_name].dropna()

        if len(values) == 0:
            pytest.skip(f"Колонка '{column_name}' не содержит значений")

        total = len(values)
        unique = values.nunique()
        duplicates = total - unique
        duplicate_pct = (duplicates / total) * 100 if total > 0 else 0

        print(f"\n📊 Колонка: {column_name}")
        print(f"   Всего значений: {total}")
        print(f"   Уникальных: {unique}")
        print(f"   Дубликатов: {duplicates} ({duplicate_pct:.1f}%)")

        if duplicates > 0:
            dup_values = values[values.duplicated()].unique()[:5]
            print(f"   Примеры дубликатов: {list(dup_values)}")

        assert duplicates == 0, f"Колонка '{column_name}' содержит {duplicates} дубликатов"

    def test_transfer_code_vs_case_code_relationship(self, documents_df: pd.DataFrame):
        """Проверка: Код передачи и Код дела - разные значения"""
        required = ['Код передачи', 'Код дела']
        missing = [col for col in required if col not in documents_df.columns]

        if missing:
            pytest.skip(f"Необходимые колонки отсутствуют: {missing}")

        temp_df = documents_df[required].dropna()
        matches = temp_df[temp_df['Код передачи'] == temp_df['Код дела']]

        if len(matches) > 0:
            print(f"\n⚠️ Найдено {len(matches)} строк где Код передачи == Код дела")
            print(f"   Примеры: {matches.head(3).to_dict('records')}")

        assert len(matches) == 0, f"Найдено {len(matches)} совпадений Код передачи == Код дела"

    def test_all_unique_columns_report(self, documents_df: pd.DataFrame):
        """Отчет обо всех колонках с уникальными значениями"""
        print("\n" + "=" * 70)
        print("🔍 ПОИСК ВСЕХ УНИКАЛЬНЫХ КОЛОНОК")
        print("=" * 70)

        unique_columns = []
        results = []

        for column in documents_df.columns:
            values = documents_df[column].dropna()
            if len(values) == 0:
                continue

            total = len(values)
            unique = values.nunique()
            is_unique = (unique == total)
            duplicate_pct = ((total - unique) / total) * 100 if total > 0 else 0

            results.append({
                'column': column,
                'total': total,
                'unique': unique,
                'duplicate_pct': duplicate_pct,
                'is_unique': is_unique
            })

            if is_unique:
                unique_columns.append(column)

        results.sort(key=lambda x: x['duplicate_pct'])

        print(f"\n📊 НАЙДЕНО ПОЛНОСТЬЮ УНИКАЛЬНЫХ КОЛОНОК: {len(unique_columns)}")
        if unique_columns:
            print(f"   ✅ {', '.join(unique_columns)}")

        print(f"\n🏆 ТОП-10 КОЛОНОК С НАИМЕНЬШИМ ПРОЦЕНТОМ ДУБЛИКАТОВ:")
        print("-" * 70)
        print(f"{'Колонка':<35} {'Всего':<10} {'Уникальных':<12} {'% дубликатов':<15}")
        print("-" * 70)

        for r in results[:10]:
            status = "✅" if r['is_unique'] else "  "
            print(f"{status} {r['column'][:34]:<35} {r['total']:<10} {r['unique']:<12} {r['duplicate_pct']:.1f}%")

        if 'Код передачи' in unique_columns:
            print("\n💡 Рекомендуемый первичный ключ: Код передачи")
        elif unique_columns:
            print(f"\n💡 Потенциальные первичные ключи: {', '.join(unique_columns[:3])}")
        else:
            print("\n⚠️ Не найдено полностью уникальных колонок. Возможно нужен составной ключ.")

        assert True


def run_console(**kwargs):
    """Запуск теста в консольном режиме"""
    import sys
    exit_code = pytest.main([
        __file__,
        "-v",
        "-s",
        "--tb=short"
    ])
    return exit_code == 0


if __name__ == "__main__":
    success = run_console()
    sys.exit(0 if success else 1)