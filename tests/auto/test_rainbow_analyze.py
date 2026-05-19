# tests/auto/test_rainbow_analyze.py

"""
Тест: test_rainbow_analyze

Проверяет:
1. GET /api/rainbow/analyze — статус 200
2. Наличие color_counts в ответе
3. Сумма значений coloredCases > 0
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.data_management.modules.normalized_data_manager import normalized_manager
from tests.conftest import _get_data_path

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def clean_manager():
    """Очищает менеджер перед каждым тестом."""
    normalized_manager.clear_data("all")
    yield
    normalized_manager.clear_data("all")


def test_rainbow_analyze(project_root):
    # Предусловие: загружаем и нормализуем детальный отчёт
    file_path = _get_data_path(project_root, "detailed.xlsx")
    assert file_path is not None, "Нет файла detailed.xlsx"
    assert file_path.exists(), f"Файл не найден: {file_path}"

    with open(file_path, "rb") as f:
        response = client.post(
            "/api/data/upload-file?file_type=current_detailed_report",
            files={"file": f}
        )
    assert response.status_code == 200, f"Ошибка загрузки: {response.text}"

    df = normalized_manager.load_detailed_report()
    assert df is not None, "load_detailed_report вернул None"
    assert len(df) > 0, "DataFrame пустой"

    # Шаг 1: вызов Rainbow-анализа
    response = client.get("/api/rainbow/analyze")
    assert response.status_code == 200, f"Ошибка Rainbow-анализа: {response.text}"

    data = response.json()

    # Шаг 2: проверка coloredCases
    assert "coloredCases" in data, "В ответе нет coloredCases"

    # Шаг 3: значение > 0
    assert data["coloredCases"] > 0, "coloredCases = 0"

