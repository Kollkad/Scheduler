# tests/auto/test_normalize_gosb_fill.py

"""
Тест: test_normalize_gosb_fill

Проверяет:
1. Выполнение normalize_detailed_report
2. Заполнение столбца ГОСБ для всех строк
3. Заполнение столбца «Категория дела» для всех строк
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.data_management.modules.normalized_data_manager import normalized_manager
from backend.app.common.config.column_names import COLUMNS
from tests.conftest import _get_data_path

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def clean_manager():
    """Очищает менеджер перед каждым тестом."""
    normalized_manager.clear_data("all")
    yield
    normalized_manager.clear_data("all")


def test_normalize_gosb_fill(project_root):
    # Предусловие: файл детального отчета загружен
    file_path = _get_data_path(project_root, "detailed.xlsx")
    assert file_path is not None, "Нет файла detailed.xlsx ни в dev_data, ни в sample_data"
    assert file_path.exists(), f"Файл не найден: {file_path}"

    # Загрузка через эндпоинт
    with open(file_path, "rb") as f:
        response = client.post(
            "/api/data/upload-file?file_type=current_detailed_report",
            files={"file": f}
        )
    assert response.status_code == 200, f"Ошибка загрузки: {response.text}"

    # Шаг 1: вызов load_detailed_report (включает normalize_detailed_report)
    df = normalized_manager.load_detailed_report()
    assert df is not None, "load_detailed_report вернул None"
    assert len(df) > 0, "DataFrame пустой"

    # Шаг 2: проверка столбца ГОСБ
    gosb_col = COLUMNS["GOSB"]
    assert gosb_col in df.columns, f"Колонка '{gosb_col}' отсутствует"
    empty_gosb = df[gosb_col].isna() | (df[gosb_col].astype(str).str.strip() == "")
    assert not empty_gosb.any(), f"Найдено {empty_gosb.sum()} строк с пустым ГОСБ"

    # Шаг 3: проверка столбца «Категория дела»
    category_col = COLUMNS["CASE_TYPE"]
    assert category_col in df.columns, f"Колонка '{category_col}' отсутствует"
    empty_category = df[category_col].isna() | (df[category_col].astype(str).str.strip() == "")
    assert not empty_category.any(), f"Найдено {empty_category.sum()} строк с пустой категорией дела"

