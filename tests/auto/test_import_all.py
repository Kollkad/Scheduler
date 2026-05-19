# tests/auto/test_import_all.py

"""
Тест: test_import_all

Проверяет:
1. POST /api/exchange/import/all после очистки — статус 200
2. _source_data восстановлен, не пуст
3. _check_results восстановлен, записи присутствуют
4. _tasks восстановлен, totalTasks > 0
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


def test_import_all(project_root):
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
        # Предусловие: загрузка отчётов, анализы, расчёт задач, экспорт
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

        # Экспорт
        resp = client.post("/api/exchange/export/all")
        assert resp.status_code == 200

        # Очистка менеджера
        normalized_manager.clear_data("all")

        # Проверка, что данные действительно очищены
        assert normalized_manager.get_cases_data().empty
        assert normalized_manager.get_documents_data().empty
        assert normalized_manager.get_check_results_data().empty
        assert normalized_manager.get_tasks_data().empty

        # Шаг 1: импорт всех данных
        resp = client.post("/api/exchange/import/all")
        assert resp.status_code == 200

        # Шаг 2: проверка _source_data
        cases = normalized_manager.get_cases_data()
        documents = normalized_manager.get_documents_data()
        assert not cases.empty, "_source_data detailed_report пуст"
        assert not documents.empty, "_source_data documents_report пуст"

        # Шаг 3: проверка _check_results
        check_results = normalized_manager.get_check_results_data()
        assert not check_results.empty, "_check_results пуст"

        # Шаг 4: проверка _tasks
        tasks = normalized_manager.get_tasks_data()
        assert not tasks.empty, "_tasks пуст"
        assert len(tasks) > 0, "totalTasks = 0"
    finally:
        app.dependency_overrides.clear()



