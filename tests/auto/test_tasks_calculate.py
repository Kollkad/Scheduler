# tests/auto/test_tasks_calculate.py

"""
Тест: test_tasks_calculate

Проверяет:
1. GET /api/tasks/calculate — статус 200
2. totalTasks > 0
3. Каждая задача содержит taskCode
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.data_management.modules.normalized_data_manager import normalized_manager
from backend.app.administration_settings.modules.user_models import UserSession, UserRole
from backend.app.administration_settings.modules import authorization_logic
from tests.conftest import _get_data_path

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def clean_manager():
    """Очищает менеджер перед каждым тестом."""
    normalized_manager.clear_data("all")
    yield
    normalized_manager.clear_data("all")

@pytest.mark.ci
def test_tasks_calculate(project_root):
    # подмена get_current_user — возвращает админа (нужен для /calculate)
    async def mock_get_current_user(request=None):
        user = UserSession()
        user.set_user(
            login="test_admin",
            email="test@test.com",
            name="Test Admin",
            role=UserRole.ADMIN
        )
        return user

    app.dependency_overrides[authorization_logic.get_current_user] = mock_get_current_user

    try:
        # Предусловие: загрузка обоих отчётов
        detailed_path = _get_data_path(project_root, "detailed.xlsx")
        documents_path = _get_data_path(project_root, "documents.xlsx")
        assert detailed_path and detailed_path.exists()
        assert documents_path and documents_path.exists()

        with open(detailed_path, "rb") as f:
            resp = client.post(
                "/api/data/upload-file?file_type=current_detailed_report",
                files={"file": f}
            )
        assert resp.status_code == 200
        normalized_manager.load_detailed_report()

        with open(documents_path, "rb") as f:
            resp = client.post(
                "/api/data/upload-file?file_type=documents_report",
                files={"file": f}
            )
        assert resp.status_code == 200
        normalized_manager.load_documents_report()

        # Выполнение трёх анализов
        resp = client.get("/api/terms/v3/lawsuit/analyze_lawsuit")
        assert resp.status_code == 200
        resp = client.get("/api/terms/v3/order/analyze_order")
        assert resp.status_code == 200
        resp = client.get("/api/documents/v3/analyze_documents")
        assert resp.status_code == 200

        # Шаг 1: расчёт задач
        resp = client.get("/api/tasks/calculate")
        assert resp.status_code == 200
        data = resp.json()

        # Шаг 2: totalTasks > 0
        assert data["totalTasks"] > 0, "totalTasks = 0"

        # Шаг 3: каждая задача содержит taskCode
        for task in data["data"]:
            assert "taskCode" in task, f"Задача без taskCode: {task}"
    finally:
        app.dependency_overrides.clear()