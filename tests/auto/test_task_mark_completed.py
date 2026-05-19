# tests/auto/test_task_mark_completed.py

"""
Тест: test_task_mark_completed

Проверяет:
1. PATCH /api/tasks/{taskCode} с isCompleted=true — статус 200
2. task.isCompleted = true в ответе
3. В _user_overrides появилась запись с данным taskCode
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


def test_task_mark_completed(project_root):
    # Подменяем get_current_user — возвращает админа
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

        # Получить taskCode невыполненной задачи
        resp = client.get('/api/tasks/list?filters={}')
        assert resp.status_code == 200
        tasks = resp.json()["tasks"]
        task_code = tasks[0]["taskCode"]

        # Шаг 1: отметить задачу выполненной
        resp = client.patch(
            f"/api/tasks/{task_code}",
            json={"is_completed": True}
        )
        assert resp.status_code == 200
        task = resp.json()["task"]

        # Шаг 2: проверить isCompleted
        assert task["isCompleted"] is True

        # Шаг 3: проверить _user_overrides
        overrides = normalized_manager.get_user_overrides_data()
        assert not overrides.empty, "_user_overrides пуст"
        assert task_code in overrides["taskCode"].values, \
            f"taskCode {task_code} не найден в _user_overrides"
    finally:
        app.dependency_overrides.clear()