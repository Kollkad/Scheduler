# backend/app/common/modules/gosb_normalization.py
"""
Модуль нормализации ГОСБ для детальных отчетов.

Реализует замену значений ГОСБ на основе справочных данных из конфигурационного файла.
Поддерживает два уровня нормализации:
1. По судам (лист "Суды")
2. По ответственным исполнителям (лист "Сотрудники")
3. Добавление категорий ГОСБ (лист "Категории ГОСБ")
"""

import pandas as pd
import os
from datetime import datetime
from typing import Optional, Tuple, Dict, List
from pathlib import Path

from backend.app.common.config.column_names import COLUMNS
from backend.app.administration_settings.modules.assistant_functions import get_working_directory


class GOSBNormalizer:
    """
    Класс, реализующий логику нормализации значений ГОСБ.
    Содержит методы загрузки конфигурации, создания маппингов и обработки DataFrame.
    """

    def __init__(self, config_path: str = None):
        """
        Инициализация нормализатора с указанием пути к файлу конфигурации.

        Args:
            config_path (str, optional): Путь к файлу конфигурации нормализации.
                                        Если не указан, используется путь по умолчанию.
        """
        if config_path is None:
            # Формирование пути к файлу конфигурации на основе режима работы
            working_dir = get_working_directory()
            if working_dir:
                self.config_path = os.path.join(working_dir, "settings", "normalization_conf.xlsx")
            else:
                self.config_path = None
        else:
            self.config_path = config_path

        self._config_data = {}  # Кэш для загруженных данных конфигурации
        self._warnings = []  # Сбор предупреждений в процессе работы

    def load_config(self) -> Dict[str, pd.DataFrame]:
        """
        Безопасная загрузка конфигурационных данных из Excel-файла.
        При отсутствии файла или листов возвращает пустые DataFrame.

        Returns:
            Dict[str, pd.DataFrame]: Словарь с DataFrames для каждого листа:
                                    courts, employees, categories
        """
        config_data = {
            "courts": pd.DataFrame(),
            "employees": pd.DataFrame(),
            "categories": pd.DataFrame()
        }

        # Проверка существования файла конфигурации
        if not self.config_path or not os.path.exists(self.config_path):
            self._warnings.append(f"Файл конфигурации не найден: {self.config_path}")
            return config_data

        # Загрузка информации о доступных листах
        try:
            xl = pd.ExcelFile(self.config_path)
            available_sheets = xl.sheet_names
        except Exception as e:
            self._warnings.append(f"Ошибка при открытии файла конфигурации: {str(e)}")
            return config_data

        # Загрузка каждого листа по отдельности (если существует)
        sheet_mapping = {
            "courts": "Суды",
            "employees": "Сотрудники",
            "categories": "Категории ГОСБ"
        }

        for key, sheet_name in sheet_mapping.items():
            if sheet_name in available_sheets:
                try:
                    config_data[key] = pd.read_excel(self.config_path, sheet_name=sheet_name)
                except Exception as e:
                    self._warnings.append(f"Ошибка загрузки листа '{sheet_name}': {str(e)}")
            else:
                self._warnings.append(f"Лист '{sheet_name}' отсутствует в файле")

        self._config_data = config_data
        return config_data

    def _create_mapping(self, config_df: pd.DataFrame, key_col: str) -> Dict:
        """
        Создание словаря для маппинга значений из DataFrame конфигурации.
        Выполняет проверку наличия колонок и фильтрацию пустых значений.

        Args:
            config_df (pd.DataFrame): DataFrame с конфигурационными данными
            key_col (str): Название колонки с ключевыми значениями (суд или исполнитель)

        Returns:
            Dict: Словарь {значение_ключа: значение_ГОСБ}
        """
        if config_df.empty:
            return {}

        gosb_col = COLUMNS.get("GOSB", "ГОСБ")

        # Проверка наличия необходимых колонок
        if key_col not in config_df.columns or gosb_col not in config_df.columns:
            return {}

        # Формирование маппинга с приведением ключей к нижнему регистру
        mapping = {}
        for _, row in config_df.iterrows():
            if pd.notna(row[key_col]) and pd.notna(row[gosb_col]):
                try:
                    key_value = str(row[key_col]).strip().lower()
                    gosb_value = str(row[gosb_col]).strip()
                    if key_value and gosb_value:
                        mapping[key_value] = gosb_value
                except Exception:
                    continue

        return mapping

    def _create_category_mapping(self) -> Dict[str, str]:
        """
        Создание словаря для маппинга ГОСБ -> категория.
        Использует данные из листа "Категории ГОСБ".

        Returns:
            Dict[str, str]: Словарь {значение_ГОСБ: категория}
        """
        if "categories" not in self._config_data or self._config_data["categories"].empty:
            return {}

        gosb_col = COLUMNS.get("GOSB", "ГОСБ")
        category_col = COLUMNS.get("GOSB_CATEGORY", "Категория ГОСБ")
        categories_df = self._config_data["categories"]

        # Проверка наличия колонок
        if gosb_col not in categories_df.columns or category_col not in categories_df.columns:
            return {}

        # Формирование маппинга категорий
        mapping = {}
        for _, row in categories_df.iterrows():
            if pd.notna(row[gosb_col]) and pd.notna(row[category_col]):
                try:
                    gosb_value = str(row[gosb_col]).strip()
                    category_value = str(row[category_col]).strip()
                    if gosb_value and category_value:
                        mapping[gosb_value] = category_value
                except Exception:
                    continue

        return mapping

    def _save_unmatched_records(self, unmatched_df: pd.DataFrame) -> Optional[str]:
        """
        Сохранение необработанных записей в отдельный Excel-файл.
        Файл создается в директории data/reports с временной меткой в имени.

        Args:
            unmatched_df (pd.DataFrame): DataFrame с необработанными записями

        Returns:
            Optional[str]: Путь к сохраненному файлу или None при ошибке
        """
        if unmatched_df.empty:
            return None

        try:
            # Формирование пути к директории для отчетов
            working_dir = get_working_directory()
            if working_dir:
                reports_dir = os.path.join(working_dir, "reports")
            else:
                reports_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "data/reports"
                )

            Path(reports_dir).mkdir(parents=True, exist_ok=True)

            # Генерация имени файла с текущей датой и временем
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"unmatched_gosb_{timestamp}.xlsx"
            filepath = os.path.join(reports_dir, filename)

            # Сохранение в Excel
            unmatched_df.to_excel(filepath, index=False)
            print(f"Необработанные записи сохранены в: {filepath}")
            return filepath
        except Exception as e:
            self._warnings.append(f"Ошибка при сохранении отчета: {str(e)}")
            return None

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Основной метод, выполняющий нормализацию значений ГОСБ и добавление категорий.
        Реализует двухуровневый поиск: по суду, затем по исполнителю.
        При отсутствии конфигурации возвращает исходный DataFrame.

        Args:
            df (pd.DataFrame): Исходный DataFrame детального отчета

        Returns:
            pd.DataFrame: DataFrame с нормализованными значениями ГОСБ и категориями
        """
        self._warnings = []
        print("Начало нормализации ГОСБ...")

        # Получение названий колонок из централизованного конфига
        court_col = COLUMNS.get("COURT", "Суд")
        gosb_col = COLUMNS.get("GOSB", "ГОСБ")
        executor_col = COLUMNS.get("RESPONSIBLE_EXECUTOR", "Ответственный исполнитель")
        case_code_col = COLUMNS.get("CASE_CODE", "Код дела")
        category_col = COLUMNS.get("GOSB_CATEGORY", "Категория ГОСБ")

        # Проверка наличия обязательных колонок в исходном DataFrame
        required_cols = [court_col, gosb_col, executor_col, case_code_col]
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            print(f"Нормализация пропущена: отсутствуют колонки {missing_cols}")
            if category_col not in df.columns:
                df[category_col] = None
            return df

        # Создание копии для избежания изменений исходного DataFrame
        normalized_df = df.copy()

        # Добавление колонки для категорий (если отсутствует)
        if category_col not in normalized_df.columns:
            normalized_df[category_col] = None

        # Загрузка конфигурационных данных
        config_data = self.load_config()

        # Создание маппингов для поиска
        court_mapping = self._create_mapping(config_data["courts"], court_col)
        employee_mapping = self._create_mapping(config_data["employees"], executor_col)
        category_mapping = self._create_category_mapping()

        # Если нет данных для нормализации - выход
        if not court_mapping and not employee_mapping and not category_mapping:
            print("Нормализация пропущена: нет данных в конфигурации")
            for warning in self._warnings:
                print(warning)
            return normalized_df

        # Сбор статистики и необработанных записей
        unmatched_records = []
        modified_count = 0
        categorized_count = 0

        # Построчная обработка DataFrame
        for idx, row in normalized_df.iterrows():
            # Подготовка значений для поиска (приведение к нижнему регистру)
            court_value = str(row[court_col]).strip().lower() if pd.notna(row[court_col]) else ""
            executor_value = str(row[executor_col]).strip().lower() if pd.notna(row[executor_col]) else ""
            original_gosb = str(row[gosb_col]).strip() if pd.notna(row[gosb_col]) else ""

            new_gosb = None

            # Первый уровень: поиск ГОСБ по названию суда
            if court_mapping and court_value in court_mapping:
                new_gosb = court_mapping[court_value]
                normalized_df.at[idx, gosb_col] = new_gosb
                modified_count += 1

            # Второй уровень: поиск по исполнителю (если не нашли по суду)
            elif employee_mapping and executor_value in employee_mapping:
                new_gosb = employee_mapping[executor_value]
                normalized_df.at[idx, gosb_col] = new_gosb
                modified_count += 1

            # Запись необработанных случаев для последующего анализа
            elif court_mapping or employee_mapping:
                unmatched_records.append({
                    case_code_col: row[case_code_col],
                    gosb_col: original_gosb,
                    court_col: row[court_col],
                    executor_col: row[executor_col]
                })
                new_gosb = original_gosb

            # Добавление категории по ГОСБ (приоритет у нового значения)
            if category_mapping:
                gosb_for_category = new_gosb or original_gosb
                if gosb_for_category and gosb_for_category in category_mapping:
                    normalized_df.at[idx, category_col] = category_mapping[gosb_for_category]
                    categorized_count += 1

        # Вывод статистики выполнения
        print(f"Статистика нормализации:")
        print(f"  - Изменено ГОСБ: {modified_count} записей")
        print(f"  - Добавлено категорий: {categorized_count} записей")
        print(f"  - Не найдено в справочниках: {len(unmatched_records)} записей")

        # Вывод предупреждений, возникших в процессе
        for warning in self._warnings:
            print(warning)

        # Сохранение необработанных записей в отдельный файл
        if unmatched_records:
            unmatched_df = pd.DataFrame(unmatched_records)
            self._save_unmatched_records(unmatched_df)

        return normalized_df


# Внешнее API для вызова из других модулей
def normalize_detailed_report(df: pd.DataFrame, config_path: str = None) -> pd.DataFrame:
    """
    Функция-обертка для безопасной нормализации детального отчета.
    При возникновении любых ошибок возвращает исходный DataFrame.

    Args:
        df (pd.DataFrame): Исходный DataFrame детального отчета
        config_path (str, optional): Путь к файлу конфигурации

    Returns:
        pd.DataFrame: Нормализованный DataFrame или исходный при ошибках
    """
    try:
        normalizer = GOSBNormalizer(config_path)
        return normalizer.normalize(df)
    except Exception as e:
        print(f"Критическая ошибка в нормализаторе: {str(e)}")
        # Гарантированное добавление колонки категории
        category_col = COLUMNS.get("GOSB_CATEGORY", "Категория ГОСБ")
        if category_col not in df.columns:
            df[category_col] = None
        return df