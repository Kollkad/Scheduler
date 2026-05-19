# tests/auto/test_rainbow_filtered_cases.py

"""
Тест: test_rainbow_filtered_cases

Проверяет:
1. GET /api/rainbow/cases-by-color?color=Красный — статус 200
2. Все дела имеют currentPeriodColor = "Красный"
3. Количество записей > 0
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


def test_rainbow_filtered_cases(project_root):
    # Предусловие: загрузка, нормализация, Rainbow-анализ
    file_path = _get_data_path(project_root, "detailed.xlsx")
    assert file_path and file_path.exists()

    with open(file_path, "rb") as f:
        resp = client.post("/api/data/upload-file?file_type=current_detailed_report", files={"file": f})
    assert resp.status_code == 200

    normalized_manager.load_detailed_report()
    resp = client.get("/api/rainbow/analyze")
    assert resp.status_code == 200

    # Шаг 1: фильтрация по цвету
    resp = client.get("/api/rainbow/cases-by-color?color=ИК")
    assert resp.status_code == 200
    data = resp.json()

    # Шаг 2: все дела цвета
    cases = data["cases"]
    for case in cases:
        assert case["currentPeriodColor"] == "ИК", f"Найден цвет: {case['currentPeriodColor']}"

    # Шаг 3: список не пуст
    assert len(cases) > 0