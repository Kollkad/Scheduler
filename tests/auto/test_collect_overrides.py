# tests/auto/test_collect_overrides.py

"""
Тест: test_collect_overrides

Проверяет:
1. POST /api/exchange/import/user-overrides/collect — статус 200
2. total_records > 0
3. sources содержит логины пользователей
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.data_management.modules.normalized_data_manager import normalized_manager
from backend.app.administration_settings.modules.user_models import UserSession, UserRole
from backend.app.administration_settings.modules import authorization_logic
from backend.app.data_exchange.modules.data_io import get_user_overrides_folder
from tests.conftest import _get_data_path

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def clean_manager():
    """Очищает менеджер перед каждым тестом."""
    normalized_manager.clear_data("all")
    yield
    normalized_manager.clear_data("all")


def test_collect_overrides(project_root, monkeypatch):
    try:
        # Предусловие: загрузка отчётов, анализы, расчёт задач
        detailed_path = _get_data_path(project_root, "detailed.xlsx")
        documents_path = _get_data_path(project_root, "documents.xlsx")
        assert detailed_path and detailed_path.exists()
        assert documents_path and documents_path.exists()

        # Мок для загрузки (не требует авторизации)
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

        # Создать оверрайды от двух разных пользователей
        base_time = datetime.now()

        # Пользователь 1: старый оверрайд
        override1 = {
            "taskCode": task_code,
            "checkResultCode": tasks[0].get("checkResultCode", ""),
            "taskText": tasks[0].get("taskText", ""),
            "reasonText": tasks[0].get("reasonText", ""),
            "createdAt": base_time,
            "isCompleted": True,
            "executionDateTimeFact": base_time,
            "executionDatePlan": tasks[0].get("executionDatePlan"),
            "shiftCode": None,
            "createdBy": "user1",
            "updatedAt": base_time,
        }
        normalized_manager.add_user_override(override1)

        # Пользователь 2: более новый оверрайд той же задачи
        override2 = {
            "taskCode": task_code,
            "checkResultCode": tasks[0].get("checkResultCode", ""),
            "taskText": tasks[0].get("taskText", ""),
            "reasonText": tasks[0].get("reasonText", ""),
            "createdAt": base_time,
            "isCompleted": True,
            "executionDateTimeFact": base_time + timedelta(hours=1),
            "executionDatePlan": tasks[0].get("executionDatePlan"),
            "shiftCode": None,
            "createdBy": "user2",
            "updatedAt": base_time + timedelta(hours=1),
        }
        normalized_manager.add_user_override(override2)

        # Второй оверрайд для другого пользователя (другая задача)
        task_code2 = tasks[1]["taskCode"]
        override3 = {
            "taskCode": task_code2,
            "checkResultCode": tasks[1].get("checkResultCode", ""),
            "taskText": tasks[1].get("taskText", ""),
            "reasonText": tasks[1].get("reasonText", ""),
            "createdAt": base_time,
            "isCompleted": False,
            "executionDateTimeFact": None,
            "executionDatePlan": tasks[1].get("executionDatePlan"),
            "shiftCode": None,
            "createdBy": "user1",
            "updatedAt": base_time,
        }
        normalized_manager.add_user_override(override3)

        # Экспортировать оверрайды каждого пользователя
        async def mock_user1(request=None):
            user = UserSession()
            user.set_user(login="user1", email="user1@test.com", name="User 1", role=UserRole.EMPLOYEE)
            return user

        async def mock_user2(request=None):
            user = UserSession()
            user.set_user(login="user2", email="user2@test.com", name="User 2", role=UserRole.EMPLOYEE)
            return user

        app.dependency_overrides[authorization_logic.get_current_user] = mock_user1
        resp = client.post("/api/exchange/export/my-overrides")
        assert resp.status_code == 200

        app.dependency_overrides[authorization_logic.get_current_user] = mock_user2
        resp = client.post("/api/exchange/export/my-overrides")
        assert resp.status_code == 200

        # Мок для collect (требует manager/admin)
        async def mock_admin(request=None):
            user = UserSession()
            user.set_user(login="admin", email="admin@test.com", name="Admin", role=UserRole.ADMIN)
            return user

        app.dependency_overrides[authorization_logic.get_current_user] = mock_admin

        # Шаг 1: сбор оверрайдов
        resp = client.post("/api/exchange/import/user-overrides/collect")
        assert resp.status_code == 200
        data = resp.json()

        # Шаг 2: total_records > 0
        assert data["total_records"] > 0

        # Шаг 3: sources содержит логины
        assert len(data["sources"]) > 0
        assert "user1" in data["sources"] or "user2" in data["sources"]
    finally:
        app.dependency_overrides.clear()



