# tests/auto/test_export_all.py

"""
Тест: test_export_all

Проверяет:
1. POST /api/exchange/export/all — статус 200
2. В app_data/ созданы parquet-файлы, размер > 0
"""

import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.data_management.modules.normalized_data_manager import normalized_manager
from backend.app.administration_settings.modules.user_models import UserSession, UserRole
from backend.app.administration_settings.modules import authorization_logic
from backend.app.data_exchange.modules.data_io import get_exchange_folder
from tests.conftest import _get_data_path

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def clean_manager():
    """Очищает менеджер перед каждым тестом."""
    normalized_manager.clear_data("all")
    yield
    normalized_manager.clear_data("all")


def test_export_all(project_root):
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

        # Шаг 1: экспорт всех данных
        resp = client.post("/api/exchange/export/all")
        assert resp.status_code == 200
        data = resp.json()
        exported_files = data["files"]
        assert len(exported_files) > 0, "Нет экспортированных файлов"

        # Шаг 2: проверка parquet-файлов в app_data/
        exchange_dir = get_exchange_folder()
        for filename in exported_files:
            filepath = exchange_dir / filename
            assert filepath.exists(), f"Файл {filename} не создан"
            assert filepath.stat().st_size > 0, f"Файл {filename} пустой"
    finally:
        app.dependency_overrides.clear()


