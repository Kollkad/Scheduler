# tests/conftest.py
import pytest
import pandas as pd
from pathlib import Path


@pytest.fixture(scope="session")
def project_root():
    """Корень проекта"""
    return Path(__file__).parent.parent


def _get_data_path(project_root, filename):
    """
    Возвращает путь к файлу.
    Сначала проверяет dev_data (полные файлы).
    Если их нет — берёт sample_data (урезанные сэмплы).
    """
    dev_path = project_root / "tests" / "data" / "dev_data" / filename
    sample_path = project_root / "tests" / "data" / "sample_data" / filename

    if dev_path.exists():
        return dev_path
    elif sample_path.exists():
        return sample_path
    else:
        return None


@pytest.fixture(scope="session")
def detailed_df(project_root):
    """Загружает детальный отчет. Сначала ищет в dev_data, потом в sample_data."""
    file_path = _get_data_path(project_root, "detailed.xlsx")

    if file_path is None:
        pytest.skip("Нет файла detailed.xlsx ни в dev_data, ни в sample_data")

    return pd.read_excel(file_path)


@pytest.fixture(scope="session")
def documents_df(project_root):
    """Загружает отчет документов. Сначала ищет в dev_data, потом в sample_data."""
    file_path = _get_data_path(project_root, "documents.xlsx")

    if file_path is None:
        pytest.skip("Нет файла documents.xlsx ни в dev_data, ни в sample_data")

    return pd.read_excel(file_path)


@pytest.fixture
def compare_dataframes():
    """Сравнивает два DataFrame с допуском"""

    def _compare(df1, df2, tolerance=0.01):
        if df1.shape != df2.shape:
            return False
        diff = (df1.fillna(0) - df2.fillna(0)).abs().max().max()
        return diff <= tolerance

    return _compare
