# backend/app/reporting/modules/report_builder.py
"""
Модуль построения репортов.

Предоставляет общие функции для создания, сохранения и управления
Excel-репортами с единым оформлением.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

import pandas as pd

from backend.app.administration_settings.modules.assistant_functions import get_working_directory
from backend.app.reporting.config.report_types import REPORT_TYPES, REPORTS_BASE_PATH


def get_reports_folder() -> Path:
    """
    Возвращает путь к папке репортов.

    Returns:
        Path: Путь к {working_dir}/administration/reports/
    """
    working_dir = get_working_directory()
    if not working_dir:
        raise ValueError("Не удалось определить рабочую директорию")

    reports_dir = Path(working_dir) / REPORTS_BASE_PATH
    reports_dir.mkdir(parents=True, exist_ok=True)

    return reports_dir


def get_report_folder(report_type: str) -> Path:
    """
    Возвращает путь к папке конкретного типа репорта.

    Args:
        report_type: Код типа репорта из REPORT_TYPES

    Returns:
        Path: Путь к папке репорта
    """
    folder = REPORT_TYPES.get(report_type, {}).get("folder", "uncategorized")
    report_dir = get_reports_folder() / folder
    report_dir.mkdir(parents=True, exist_ok=True)

    return report_dir


def generate_report_filename(report_type: str) -> str:
    """
    Генерирует уникальное имя файла репорта с временной меткой.

    Args:
        report_type: Код типа репорта

    Returns:
        str: Имя файла с расширением .xlsx
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{report_type}_{timestamp}.xlsx"


def retry_save_operation(operation: Callable, max_attempts: int = 5, delay: float = 1.0):
    """
    Выполняет операцию с повторными попытками.

    Args:
        operation: Функция без аргументов
        max_attempts: Максимальное количество попыток
        delay: Задержка между попытками в секундах

    Returns:
        Результат выполнения operation

    Raises:
        IOError: Если все попытки исчерпаны
    """
    import time

    for attempt in range(1, max_attempts + 1):
        try:
            return operation()
        except Exception as e:
            if attempt == max_attempts:
                raise IOError(
                    f"Не удалось выполнить операцию после {max_attempts} попыток. Причина: {e}"
                )
            print(f"⚠️ Попытка {attempt}/{max_attempts} не удалась: {e}. Повтор через {delay} сек...")
            time.sleep(delay)


def build_report(
    info_metadata: dict,
    data_df: Optional[pd.DataFrame],
    report_type: str,
    created_by: str
) -> str:
    """
    Создает Excel-репорт с единым оформлением.

    Лист 1 «Справочная информация»:
        - Автор, дата создания, тип репорта
        - Дополнительные поля из info_metadata
    Лист 2 «Данные» (если data_df передан):
        - Таблица с данными

    Args:
        info_metadata: Словарь с дополнительной информацией о репорте
        data_df: DataFrame с данными (опционально)
        report_type: Код типа репорта из REPORT_TYPES
        created_by: Логин пользователя, создавшего репорт

    Returns:
        str: Полный путь к сохраненному файлу

    Raises:
        ValueError: Если report_type не найден в конфиге
    """
    if report_type not in REPORT_TYPES:
        raise ValueError(f"Неизвестный тип репорта: {report_type}")

    report_config = REPORT_TYPES[report_type]
    report_name = report_config["name"]
    report_dir = get_report_folder(report_type)
    filename = generate_report_filename(report_type)
    filepath = report_dir / filename

    def save():
        with pd.ExcelWriter(str(filepath), engine='xlsxwriter') as writer:
            workbook = writer.book

            # ===== Лист 1: Справочная информация =====
            info_sheet = workbook.add_worksheet("Справочная информация")

            # Форматы
            title_format = workbook.add_format({
                'bold': True,
                'font_size': 14,
                'font_color': '#439639',
            })
            header_format = workbook.add_format({
                'bold': True,
                'font_size': 11,
                'bg_color': '#439639',
                'font_color': 'white',
                'border': 1,
                'border_color': '#D0D0D0',
            })
            cell_format = workbook.add_format({
                'font_size': 11,
                'border': 1,
                'border_color': '#D0D0D0',
            })

            # Заголовок
            info_sheet.merge_range('A1:B1', 'Справочная информация', title_format)
            info_sheet.set_column('A:A', 30)
            info_sheet.set_column('B:B', 60)

            # Базовые поля
            base_info = {
                "Автор репорта": created_by,
                "Дата создания": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                "Тип репорта": report_name,
            }

            row = 2
            for label, value in base_info.items():
                info_sheet.write(row, 0, label, header_format)
                info_sheet.write(row, 1, str(value), cell_format)
                row += 1

            # Дополнительные поля из info_metadata
            if info_metadata:
                for label, value in info_metadata.items():
                    info_sheet.write(row, 0, str(label), header_format)
                    info_sheet.write(row, 1, str(value), cell_format)
                    row += 1

            # ===== Лист 2: Данные (опционально) =====
            if data_df is not None and not data_df.empty:
                data_df.to_excel(writer, sheet_name="Данные", index=False)

                data_sheet = writer.sheets["Данные"]

                # Форматы для данных
                data_header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#439639',
                    'font_color': 'white',
                    'text_wrap': True,
                    'valign': 'vcenter',
                    'align': 'center',
                    'border': 1,
                    'border_color': '#D0D0D0',
                })
                even_format = workbook.add_format({
                    'bg_color': 'white',
                    'text_wrap': True,
                    'valign': 'vcenter',
                    'align': 'center',
                    'border': 1,
                    'border_color': '#D0D0D0',
                })
                odd_format = workbook.add_format({
                    'bg_color': '#F8FBFC',
                    'text_wrap': True,
                    'valign': 'vcenter',
                    'align': 'center',
                    'border': 1,
                    'border_color': '#D0D0D0',
                })

                # Форматирование заголовков данных
                for col_num, col_name in enumerate(data_df.columns):
                    data_sheet.write(0, col_num, str(col_name), data_header_format)
                    # Автоширина
                    max_len = max(len(str(col_name)), data_df[col_name].astype(str).str.len().max())
                    data_sheet.set_column(col_num, col_num, min(max_len + 2, 50))

                # Форматирование строк данных
                for row_num in range(len(data_df)):
                    fmt = even_format if row_num % 2 == 0 else odd_format
                    data_sheet.set_row(row_num + 1, None, fmt)

    retry_save_operation(save)
    print(f"✅ Репорт сохранен: {filepath}")
    return str(filepath)


def list_reports(report_type: Optional[str] = None) -> List[dict]:
    """
    Возвращает список всех сохраненных репортов.

    Args:
        report_type: Код типа репорта для фильтрации (опционально)

    Returns:
        List[dict]: Список репортов с полями id, type, name, filepath, created_at
    """
    reports = []
    reports_dir = get_reports_folder()

    for folder in reports_dir.iterdir():
        if not folder.is_dir():
            continue

        for file in folder.iterdir():
            if not file.is_file() or not file.suffix == '.xlsx':
                continue

            # Определение типа репорта из имени файла
            parts = file.stem.rsplit('_', 2)
            file_report_type = parts[0] if len(parts) == 3 else None

            if report_type and file_report_type != report_type:
                continue

            report_config = REPORT_TYPES.get(file_report_type, {})

            reports.append({
                "id": file.stem,
                "type": file_report_type,
                "name": report_config.get("name", file_report_type),
                "filepath": str(file),
                "folder": folder.name,
                "created_at": datetime.fromtimestamp(
                    file.stat().st_mtime
                ).strftime("%d.%m.%Y %H:%M:%S"),
            })

    # Сортировка по дате создания (новые сверху)
    reports.sort(key=lambda x: x["created_at"], reverse=True)
    return reports


def delete_report(report_id: str) -> bool:
    """
    Удаляет репорт по его идентификатору (имени файла без расширения).

    Args:
        report_id: Идентификатор репорта (имя файла без .xlsx)

    Returns:
        bool: True если репорт удален, False если не найден
    """
    reports_dir = get_reports_folder()
    filename = f"{report_id}.xlsx"

    for folder in reports_dir.iterdir():
        if not folder.is_dir():
            continue

        filepath = folder / filename
        if filepath.exists():
            filepath.unlink()
            print(f"🗑 Репорт удален: {filepath}")
            return True

    print(f"⚠️ Репорт не найден: {report_id}")
    return False