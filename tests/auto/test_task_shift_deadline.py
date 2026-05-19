# tests/auto/test_task_shift_deadline.py

"""
Тест: test_task_shift_deadline

Проверяет:
1. PATCH /api/tasks/{taskCode} с shiftCode — статус 200
2. executionDatePlan изменён
3. shiftCode записан
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


def test_task_shift_deadline(project_root):
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

        # Получить список задач
        resp = client.get('/api/tasks/list?filters={}')
        assert resp.status_code == 200
        tasks = resp.json()["tasks"]

        # Найти задачу с плановой датой и допустимыми причинами переноса
        task_code = None
        original_date = None
        shift_code = None

        for t in tasks:
            if not t.get("executionDatePlan"):
                continue
            resp = client.get(f"/api/tasks/{t['taskCode']}/shift-reasons")
            if resp.status_code == 200:
                reasons = resp.json()["shiftReasons"]
                if len(reasons) > 0:
                    task_code = t["taskCode"]
                    original_date = t["executionDatePlan"]
                    shift_code = reasons[0]["shiftCode"]
                    break

        assert task_code is not None, "Нет задач с допустимыми причинами переноса"

        # Шаг 1: перенос срока
        resp = client.patch(
            f"/api/tasks/{task_code}",
            json={"shift_code": shift_code}
        )
        assert resp.status_code == 200
        task = resp.json()["task"]

        # Шаг 2: executionDatePlan изменён
        new_date = task.get("executionDatePlan")
        assert new_date is not None, "executionDatePlan отсутствует в ответе"
        assert new_date != original_date, "Дата не изменилась"

        # Шаг 3: shiftCode записан
        assert task.get("shiftCode") == shift_code, \
            f"shiftCode = {task.get('shiftCode')}, ожидался {shift_code}"
    finally:
        app.dependency_overrides.clear()


