# tests/auto/test_upload_detailed_report_multisheet.py

"""
Тест: test_upload_detailed_report_multisheet

Проверяет:
1. Загрузку файла через эндпоинт /api/data/upload-file
2. Вызов load_detailed_report()
3. Наличие данных в _source_data
4. Наличие обязательных колонок
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.data_management.modules.normalized_data_manager import normalized_manager
from backend.app.common.config.column_names import COLUMNS
from tests.conftest import _get_data_path


# Расширяемый список обязательных колонок
REQUIRED_COLUMNS = [
    COLUMNS["GOSB"],
    COLUMNS["CASE_CODE"],
    COLUMNS["CASE_TYPE"],
    COLUMNS["CASE_NAME"],
]

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def clean_manager():
    """Очищает менеджер перед каждым тестом."""
    normalized_manager.clear_data("all")
    yield
    normalized_manager.clear_data("all")


def test_upload_detailed_report_multisheet(project_root):
    # Шаг 0: проверка наличия файла
    file_path = _get_data_path(project_root, "detailed.xlsx")
    assert file_path is not None, "Нет файла detailed.xlsx ни в dev_data, ни в sample_data"
    assert file_path.exists(), f"Файл не найден: {file_path}"

    # Шаг 1: загрузка файла через эндпоинт
    with open(file_path, "rb") as f:
        response = client.post(
            "/api/data/upload-file?file_type=current_detailed_report",
            files={"file": f}
        )

    assert response.status_code == 200, f"Ошибка загрузки: {response.text}"
    response_data = response.json()
    assert response_data["message"] == "Файл успешно загружен"

    # Шаг 2: вызов load_detailed_report()
    df = normalized_manager.load_detailed_report()
    assert df is not None, "load_detailed_report вернул None"

    # Шаг 3: проверка _source_data
    source_df = normalized_manager._source_data.get("detailed_report")
    assert source_df is not None, "В _source_data нет detailed_report"
    assert len(source_df) > 0, "DataFrame пустой (0 строк)"
    assert len(source_df.columns) > 0, "DataFrame не содержит колонок"

    # Шаг 4: проверка обязательных колонок
    for col in REQUIRED_COLUMNS:
        assert col in source_df.columns, f"Отсутствует обязательная колонка: {col}"


