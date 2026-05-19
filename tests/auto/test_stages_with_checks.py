# tests/auto/test_stages_with_checks.py

"""
Тест: test_stages_with_checks

Проверяет:
1. GET /api/case/stages/lawsuit/with-checks — статус 200
2. Этапы содержат вложенные checks
3. Среди этапов есть исключение (exceptions) с проверками
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

@pytest.mark.ci
def test_stages_with_checks(project_root):
    # Предусловие: загрузить детальный отчёт
    file_path = _get_data_path(project_root, "detailed.xlsx")
    assert file_path and file_path.exists()

    with open(file_path, "rb") as f:
        resp = client.post(
            "/api/data/upload-file?file_type=current_detailed_report",
            files={"file": f}
        )
    assert resp.status_code == 200
    normalized_manager.load_detailed_report()

    # Шаг 1: запрос этапов с проверками
    resp = client.get("/api/case/stages/lawsuit/with-checks")
    assert resp.status_code == 200
    data = resp.json()
    stages = data["stages"]
    assert len(stages) > 0, "Нет этапов"

    # Шаг 2: каждый этап содержит checks
    for stage in stages:
        assert "checks" in stage, f"Этап {stage.get('stageCode')} без checks"
        assert isinstance(stage["checks"], list), \
            f"checks у {stage.get('stageCode')} не список"

    # Шаг 3: среди этапов есть исключение с проверками
    exceptions_stage = next((s for s in stages if "exceptions" in s["stageCode"]), None)
    assert exceptions_stage is not None, "Нет этапа exceptions"
    assert len(exceptions_stage["checks"]) > 0, "У исключения нет проверок"


