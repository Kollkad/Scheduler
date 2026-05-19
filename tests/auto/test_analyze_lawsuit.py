# tests/auto/test_analyze_lawsuit.py

"""
Тест: test_analyze_lawsuit

Проверяет:
1. GET /api/terms/v3/lawsuit/analyze_lawsuit — статус 200
2. check_results пополнены записями с checkCode, заканчивающимся на L
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


def test_analyze_lawsuit(project_root):
    # Предусловие: загрузка и нормализация детального отчёта
    file_path = _get_data_path(project_root, "detailed.xlsx")
    assert file_path and file_path.exists()

    with open(file_path, "rb") as f:
        resp = client.post(
            "/api/data/upload-file?file_type=current_detailed_report",
            files={"file": f}
        )
    assert resp.status_code == 200

    df = normalized_manager.load_detailed_report()
    assert len(df) > 0

    # Шаг 1: вызов анализа искового производства
    resp = client.get("/api/terms/v3/lawsuit/analyze_lawsuit")
    assert resp.status_code == 200

    # Шаг 2: проверка check_results
    check_results = normalized_manager.get_check_results_data()
    assert not check_results.empty, "check_results пуст"

    # Отфильтровать записи с суффиксом L
    lawsuit_results = check_results[check_results["checkCode"].str.endswith("L", na=False)]
    assert not lawsuit_results.empty, "Нет записей с checkCode, заканчивающимся на L"