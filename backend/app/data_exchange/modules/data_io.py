# backend/app/data_exchange/modules/data_io.py
"""
Модуль ввода-вывода данных для обмена между экземплярами приложения.

Предоставляет функции для сохранения и загрузки DataFrame в формат Parquet
с поддержкой повторных попыток при сбоях доступа к сетевой папке.
"""

import json
import os
import time
from datetime import datetime, date
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from backend.app.administration_settings.modules.assistant_functions import get_working_directory


def get_exchange_folder() -> Path:
    """
    Возвращает путь к папке обмена данными.

    Папка создается автоматически, если не существует.
    Путь зависит от режима работы:
    - DEV: DESKTOP_ADDRESS/app_data
    - DEPLOY: NETWORK_FOLDER_ADDRESS/app_data

    Returns:
        Path: Путь к папке обмена

    Raises:
        ValueError: Если не удалось определить рабочую директорию
    """
    working_dir = get_working_directory()
    if not working_dir:
        raise ValueError("Не удалось определить рабочую директорию")

    exchange_dir = Path(working_dir) / "app_data"
    exchange_dir.mkdir(parents=True, exist_ok=True)

    return exchange_dir


def get_user_exchange_folder(login: str) -> Path:
    """
    Возвращает путь к папке обмена для конкретного пользователя.

    Args:
        login: Логин пользователя

    Returns:
        Path: Путь к папке {app_data}/{login}/
    """
    user_dir = get_exchange_folder() / login
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def retry_operation(
    operation: Callable,
    max_attempts: int = 5,
    delay: float = 1.0
):
    """
    Выполняет операцию с повторными попытками при неудаче.

    Args:
        operation: Функция без аргументов, которую нужно выполнить
        max_attempts: Максимальное количество попыток
        delay: Задержка между попытками в секундах

    Returns:
        Результат выполнения operation

    Raises:
        IOError: Если все попытки исчерпаны
    """
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            return operation()
        except Exception as e:
            last_error = e
            if attempt == max_attempts:
                raise IOError(
                    f"Не удалось выполнить операцию после {max_attempts} попыток. "
                    f"Причина: {e}"
                )
            print(f"⚠️ Попытка {attempt}/{max_attempts} не удалась: {e}. Повтор через {delay} сек...")
            time.sleep(delay)


# TODO: Заменить сохранение проблемных дат в CSV на модуль репортов
def save_dataframe(df: pd.DataFrame, filename: str, folder: Optional[Path] = None) -> None:
    """
    Сохраняет DataFrame в Parquet-файл.

    Args:
        df: DataFrame для сохранения
        filename: Имя файла (например, "source_detailed_report.parquet")
        folder: Папка для сохранения (по умолчанию get_exchange_folder())
    """
    if folder is None:
        folder = get_exchange_folder()

    filepath = folder / filename

    # Преобразование date/datetime колонок в datetime64 для Parquet
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == 'object':
            sample = df[col].dropna()
            if not sample.empty:
                first = sample.iloc[0]
                if isinstance(first, (pd.Timestamp, datetime, date)):
                    original = df[col].copy()
                    df[col] = pd.to_datetime(df[col], errors='coerce')

                    problem_mask = df[col].isna() & original.notna()
                    if problem_mask.any():
                        # Сохраняем проблемные даты в CSV для будущего репорта
                        csv_path = folder / f"{filepath.stem}_date_problems.csv"
                        problems_df = pd.DataFrame({
                            'index': df.index[problem_mask],
                            'column': col,
                            'invalid_value': original[problem_mask].astype(str)
                        })
                        problems_df.to_csv(csv_path, index=False)
                        print(f"⚠️ {len(problems_df)} проблемных дат сохранены в {csv_path}")

    def write():
        df.to_parquet(filepath, compression="snappy")

    retry_operation(write)
    print(f"✅ Файл сохранен: {filepath}")


def load_dataframe(filename: str, folder: Optional[Path] = None) -> Optional[pd.DataFrame]:
    """
    Загружает DataFrame из Parquet-файла.

    Args:
        filename: Имя файла (например, "source_detailed_report.parquet")
        folder: Папка для загрузки (по умолчанию get_exchange_folder())

    Returns:
        pd.DataFrame или None, если файл не найден
    """
    if folder is None:
        folder = get_exchange_folder()

    filepath = folder / filename

    if not filepath.exists():
        print(f"⚠️ Файл не найден: {filepath}")
        return None

    def read():
        return pd.read_parquet(filepath)

    df = retry_operation(read)
    print(f"✅ Файл загружен: {filepath} ({len(df)} строк)")
    return df


def save_metadata(metadata: dict, filename: str = "metadata.json", folder: Optional[Path] = None) -> None:
    """
    Сохраняет метаданные обмена в JSON-файл.

    Args:
        metadata: Словарь с метаданными
        filename: Имя файла метаданных (по умолчанию "metadata.json")
        folder: Папка для сохранения (по умолчанию get_exchange_folder())
    """
    if folder is None:
        folder = get_exchange_folder()

    filepath = folder / filename

    def write():
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2, default=str)

    retry_operation(write)
    print(f"✅ Метаданные сохранены: {filepath}")


def load_metadata(filename: str = "metadata.json", folder: Optional[Path] = None) -> dict:
    """
    Загружает метаданные обмена из JSON-файла.

    Args:
        filename: Имя файла метаданных (по умолчанию "metadata.json")
        folder: Папка для загрузки (по умолчанию get_exchange_folder())

    Returns:
        dict: Словарь с метаданными или пустой словарь, если файл не найден
    """
    if folder is None:
        folder = get_exchange_folder()

    filepath = folder / filename

    if not filepath.exists():
        print(f"⚠️ Файл метаданных не найден: {filepath}")
        return {}

    def read():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    metadata = retry_operation(read)
    print(f"✅ Метаданные загружены: {filepath}")
    return metadata


def build_metadata(files_info: dict, exported_by: str) -> dict:
    """
    Формирует словарь метаданных для сохранения при экспорте.

    Args:
        files_info: Словарь {имя_файла: {"rows": int, "columns": int}}
        exported_by: Логин пользователя, выполняющего экспорт

    Returns:
        dict: Метаданные с полями exported_at, exported_by, data_version, files
    """
    return {
        "exported_at": datetime.now().isoformat(),
        "exported_by": exported_by,
        "data_version": os.getenv("APP_VERSION", "0.0.0"),
        "files": files_info
    }


def clear_exchange_folder() -> None:
    """
    Удаляет все файлы из папки обмена.
    """
    exchange_dir = get_exchange_folder()

    def clear():
        for file_path in exchange_dir.iterdir():
            if file_path.is_file():
                file_path.unlink()
                print(f"🗑 Удален файл: {file_path}")

    retry_operation(clear)
    print(f"🧹 Папка обмена очищена: {exchange_dir}")



