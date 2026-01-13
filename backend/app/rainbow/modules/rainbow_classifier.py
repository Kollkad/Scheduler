# backend/app/rainbow/modules/rainbow_classifier.py
"""
Модуль классификатора для цветовой категоризации дел (радуга).

Содержит класс RainbowClassifier для классификации дел по цветовым категориям
на основе статусов, дат и других атрибутов. Используется для построения
визуализации "радуги" - диаграммы распределения дел по цветовым категориям.

Основные функции:
- classify_cases: Классификация дел и подсчет статистики по цветам
- print_rainbow_stats: Вывод статистики в консоль
- add_color_column: Добавление цветовой колонки в DataFrame
- _determine_case_color: Определение цвета для конкретного дела
"""

import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
from backend.app.common.config.column_names import COLUMNS, VALUES
from backend.app.common.modules.utils import safe_get_column


class RainbowClassifier:
    """
    Классификатор для цветовой категоризации дел судебного производства.

    Определяет цветовые категории для дел на основе их статусов, дат
    и других характеристик для построения визуализации "радуги".
    """

    @staticmethod
    def classify_cases(df: pd.DataFrame) -> List[int]:
        """
        Классифицирует дела по цветовым категориям и возвращает статистику.

        Анализирует DataFrame с делами и распределяет их по 9 цветовым категориям
        на основе статусов, типов дел и временных характеристик.

        Args:
            df (pd.DataFrame): DataFrame с данными дел для классификации

        Returns:
            List[int]: Список счетчиков дел по цветам в порядке:
                     [ИК, Серый, Зеленый, Желтый, Оранжевый, Синий, Красный, Лиловый, Белый]
        """
        today = datetime.now().date()
        counters = [0, 0, 0, 0, 0, 0, 0, 0, 0]

        # Фильтрация данных с использованием safe_get_column
        filtered_indices = []
        for idx, row in df.iterrows():
            category = safe_get_column(row, COLUMNS["CATEGORY"])
            case_status = safe_get_column(row, COLUMNS["CASE_STATUS"])

            if (category == VALUES["CLAIM_FROM_BANK"] and
                    case_status not in [VALUES["CLOSED"], VALUES["ERROR_DUBLICATE"],
                                        VALUES["WITHDRAWN_BY_THE_INITIATOR"]]):
                filtered_indices.append(idx)

        filtered_df = df.loc[filtered_indices]

        # Использование единой функции определения цвета
        for _, row in filtered_df.iterrows():
            color = RainbowClassifier._determine_case_color(row, today)

            if color == "ИК":
                counters[0] += 1
            elif color == "Серый":
                counters[1] += 1
            elif color == "Зеленый":
                counters[2] += 1
            elif color == "Желтый":
                counters[3] += 1
            elif color == "Оранжевый":
                counters[4] += 1
            elif color == "Синий":
                counters[5] += 1
            elif color == "Красный":
                counters[6] += 1
            elif color == "Лиловый":
                counters[7] += 1
            elif color == "Белый":
                counters[8] += 1

        return counters

    @staticmethod
    def print_rainbow_stats(counters: List[int]):
        """
        Выводит статистику цветовой классификации в консоль.

        Форматирует и отображает количество дел по каждой цветовой категории
        с понятными названиями и итоговой суммой.

        Args:
            counters (List[int]): Список счетчиков дел по цветам
        """
        # Названия цветовых категорий для отображения
        names = [
            "ИК (Ипотечные)",
            "Серый (Переоткрыто)",
            "Зеленый (Суд.акт + передача)",
            "Желтый (Условно закрыто + передача)",
            "Оранжевый (Суд.акт без передачи)",
            "Синий (Приказное >90 дней)",
            "Красный (До 2023 года)",
            "Лиловый (Исковое >120 дней)",
            "Иное"
        ]

        print("\nСтатистика по делам (только иск от банка + исковое производство):")
        print("-------------------")
        total = 0
        # Вывод статистики по каждой категории
        for i, count in enumerate(counters):
            print(f"{names[i]}: {count}")
            total += count
        print("-------------------")
        print(f"Всего: {total}\n")

    @staticmethod
    def add_color_column(df: pd.DataFrame) -> pd.DataFrame:
        """
        Добавляет столбец с цветовой категорией в DataFrame.

        Создает копию входного DataFrame и добавляет колонку с цветом
        для каждого дела на основе классификации.

        Args:
            df (pd.DataFrame): Исходный DataFrame с данными дел

        Returns:
            pd.DataFrame: DataFrame с добавленной колонкой 'Цвет (текущий период)'
        """
        # Создание копии DataFrame для модификации
        df_with_color = df.copy()
        today = datetime.now().date()

        color_column = []
        # Определение цвета для каждого дела в DataFrame
        for _, row in df_with_color.iterrows():
            color = RainbowClassifier._determine_case_color(row, today)
            color_column.append(color)

        # Добавление колонки с цветами в DataFrame
        df_with_color[COLUMNS["CURRENT_PERIOD_COLOR"]] = color_column
        return df_with_color

    @staticmethod
    def _determine_case_color(row, today) -> str:
        """
       Определяет цветовую категорию для конкретного дела.

       Применяет иерархию правил для определения цвета дела на основе
       его атрибутов и временных характеристик. Порядок правил важен.

       Args:
           row: Строка данных дела
           today (date): Текущая дата для временных расчетов

       Returns:
           str: Русское название цветовой категории
        """
        # Безопасное получение значений с fallback
        request_type = safe_get_column(row, COLUMNS["REQUEST_TYPE"])
        case_status = safe_get_column(row, COLUMNS["CASE_STATUS"], None)
        method_of_protection = safe_get_column(row, COLUMNS["METHOD_OF_PROTECTION"], None)
        actual_transfer_date = safe_get_column(row, COLUMNS["ACTUAL_TRANSFER_DATE"], None)
        last_request_date = safe_get_column(row, COLUMNS["LAST_REQUEST_DATE"], None)
        next_hearing_date = safe_get_column(row, COLUMNS["NEXT_HEARING_DATE"])

        # Правило 1: Ипотечные кредиты - категория ИК
        if request_type and "залог" in str(request_type).lower():
            return "ИК"

        # Правило 2: Переоткрытые дела - категория Серый
        if case_status == VALUES["REOPENED"]:
            return "Серый"

        # Правило 3: Судебный акт в силе с передачей - категория Зеленый
        if (case_status == VALUES["COURT_ACT_IN_FORCE"] and
                actual_transfer_date is not None):
            try:
                transfer_date = pd.to_datetime(actual_transfer_date).date()

                # Если есть дата заседания, проверяем AD15>X15
                if next_hearing_date is not None:
                    hearing_date = pd.to_datetime(next_hearing_date).date()
                    if transfer_date > hearing_date:
                        return "Зеленый"
                else:
                    # Если даты заседания нет, достаточно наличия даты передачи (AD15<>"")
                    return "Зеленый"
            except:
                # Если преобразование не удалось, но дата передачи есть
                if actual_transfer_date is not None:
                    return "Зеленый"

        # Правило 4: Условно закрытые дела с передачей - категория Желтый
        if (case_status == VALUES["CONDITIONALLY_CLOSED"] and
                actual_transfer_date not in [None, "no_data"] and
                not pd.isna(actual_transfer_date)):
            return "Желтый"

        # Правило 5: Судебный акт в силе без передачи - категория Оранжевый
        if (case_status == VALUES["COURT_ACT_IN_FORCE"] and
                (actual_transfer_date in [None, "no_data"] or pd.isna(actual_transfer_date))):
            return "Оранжевый"

        # Правило 6: Приказное производство старше 90 дней - категория Синий
        if (method_of_protection == VALUES["ORDER_PRODUCTION"] and
                last_request_date not in [None, "no_data"] and
                not pd.isna(last_request_date)):
            try:
                request_date = pd.to_datetime(last_request_date).date()
                if (today - request_date) > timedelta(days=90):
                    return "Синий"
            except:
                pass

        # Правило 7: Дела с запросами до 2023 года - категория Красный
        if last_request_date is not None:
            try:
                request_date = pd.to_datetime(last_request_date).date()
                if request_date < datetime(2022, 12, 31).date():
                    return "Красный"
            except:
                pass

        # Правило 8: Исковое производство старше 120 дней - категория Лиловый
        if (method_of_protection == VALUES["CLAIM_PROCEEDINGS"] and
                last_request_date not in [None, "no_data"] and
                not pd.isna(last_request_date)):
            try:
                request_date = pd.to_datetime(last_request_date).date()
                if (today - request_date) > timedelta(days=120):
                    return "Лиловый"
            except:
                pass

        # Правило 9: Все остальные дела - категория Белый
        return "Белый"