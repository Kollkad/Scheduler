# tests/auto/test_task_detail.py

"""
Тест: test_task_detail

Проверяет:
1. GET /api/tasks/{taskCode} — статус 200
2. task.taskCode совпадает с запрошенным
3. responsibleExecutor не "Неизвестно"
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


def test_task_detail(project_root):
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

        # Расчёт задач
        resp = client.get("/api/tasks/calculate")
        assert resp.status_code == 200

        # Получить любой taskCode из списка
        resp = client.get('/api/tasks/list?filters={}')
        assert resp.status_code == 200
        tasks = resp.json()["tasks"]
        assert len(tasks) > 0, "Нет задач"
        task_code = tasks[0]["taskCode"]

        # Шаг 1: запрос деталей задачи
        resp = client.get(f"/api/tasks/{task_code}")
        assert resp.status_code == 200
        task = resp.json()["task"]

        # Шаг 2: taskCode совпадает
        assert task["taskCode"] == task_code

        # Шаг 3: responsibleExecutor не "Неизвестно"
        assert task["responsibleExecutor"] != "Неизвестно", \
            f"responsibleExecutor = {task['responsibleExecutor']}"
    finally:
        app.dependency_overrides.clear()