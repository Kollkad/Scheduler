# tests/auto/test_upload_documents_report.py

"""
Тест: test_upload_documents_report

Проверяет:
1. Загрузку файла отчета документов через /api/data/upload-file
2. Вызов load_documents_report()
3. Наличие данных в _source_data["documents_report"]
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


def test_upload_documents_report(project_root):
    # Предусловие: файл отчета документов существует
    file_path = _get_data_path(project_root, "documents.xlsx")
    assert file_path is not None, "Нет файла documents.xlsx ни в dev_data, ни в sample_data"
    assert file_path.exists(), f"Файл не найден: {file_path}"

    # Шаг 1: загрузка файла через эндпоинт
    with open(file_path, "rb") as f:
        response = client.post(
            "/api/data/upload-file?file_type=documents_report",
            files={"file": f}
        )
    assert response.status_code == 200, f"Ошибка загрузки: {response.text}"
    assert response.json()["message"] == "Файл успешно загружен"

    # Шаг 2: вызов load_documents_report()
    df = normalized_manager.load_documents_report()
    assert df is not None, "load_documents_report вернул None"

    # Шаг 3: проверка _source_data
    source_df = normalized_manager._source_data.get("documents_report")
    assert source_df is not None, "В _source_data нет documents_report"
    assert len(source_df) > 0, f"DataFrame пустой (0 строк)"

