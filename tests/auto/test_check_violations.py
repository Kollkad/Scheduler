# tests/auto/test_check_violations.py

"""
Тест: test_check_violations

Проверяет:
1. POST /api/exchange/import/user-overrides/check-violations — статус 200
2. Репорт создан
3. violations_count >= 0
"""

import pytest
from datetime import datetime
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


def test_check_violations(project_root):
    try:
        # Предусловие: загрузка отчётов, анализы, расчёт задач
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

        resp = client.get("/api/terms/v3/lawsuit/analyze_lawsuit")
        assert resp.status_code == 200
        resp = client.get("/api/terms/v3/order/analyze_order")
        assert resp.status_code == 200
        resp = client.get("/api/documents/v3/analyze_documents")
        assert resp.status_code == 200
        resp = client.get("/api/tasks/calculate")
        assert resp.status_code == 200

        # Получить taskCode первой задачи
        resp = client.get('/api/tasks/list?filters={}')
        tasks = resp.json()["tasks"]
        task_code = tasks[0]["taskCode"]

        # Создать выполненный оверрайд
        base_time = datetime.now()
        override = {
            "taskCode": task_code,
            "checkResultCode": tasks[0].get("checkResultCode", ""),
            "taskText": tasks[0].get("taskText", ""),
            "reasonText": tasks[0].get("reasonText", ""),
            "createdAt": base_time,
            "isCompleted": True,
            "executionDateTimeFact": base_time,
            "executionDatePlan": tasks[0].get("executionDatePlan"),
            "shiftCode": None,
            "createdBy": "test_user",
            "updatedAt": base_time,
        }
        normalized_manager.add_user_override(override)

        # Мок админа для check-violations
        async def mock_admin(request=None):
            user = UserSession()
            user.set_user(login="admin", email="admin@test.com", name="Admin", role=UserRole.ADMIN)
            return user

        app.dependency_overrides[authorization_logic.get_current_user] = mock_admin

        # Шаг 1: проверка нарушений
        resp = client.post("/api/exchange/import/user-overrides/check-violations")
        assert resp.status_code == 200
        data = resp.json()

        # Шаг 2: violations_count >= 0
        assert data["violations_found"] is True
        assert data["violations_count"] >= 0

        # Шаг 3: репорт создан
        assert "report_path" in data
        assert data["report_path"]
    finally:
        app.dependency_overrides.clear()


