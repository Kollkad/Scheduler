# tests/auto/test_analyze_documents.py

"""
Тест: test_analyze_documents

Проверяет:
1. GET /api/documents/v3/analyze_documents — статус 200
2. check_results пополнены записями с checkCode, заканчивающимся на D
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


def test_analyze_documents(project_root):
    # Предусловие: загрузка отчёта документов
    file_path = _get_data_path(project_root, "documents.xlsx")
    assert file_path and file_path.exists()

    with open(file_path, "rb") as f:
        resp = client.post(
            "/api/data/upload-file?file_type=documents_report",
            files={"file": f}
        )
    assert resp.status_code == 200

    df = normalized_manager.load_documents_report()
    assert df is not None
    assert len(df) > 0

    # Шаг 1: вызов анализа документов
    resp = client.get("/api/documents/v3/analyze_documents")
    assert resp.status_code == 200

    # Шаг 2: проверка check_results
    check_results = normalized_manager.get_check_results_data()
    assert not check_results.empty, "check_results пуст"

    # Отфильтровать записи с суффиксом D
    doc_results = check_results[check_results["checkCode"].str.endswith("D", na=False)]
    assert not doc_results.empty, "Нет записей с checkCode, заканчивающимся на D"