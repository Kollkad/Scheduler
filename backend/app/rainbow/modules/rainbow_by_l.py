# rainbow_by_l.py
import pandas as pd
from typing import Dict
from datetime import datetime, date
from backend.app.common.config.column_names import COLUMNS, VALUES


class RainbowByLClassifier:
    @staticmethod
    def classify_cases(df: pd.DataFrame) -> Dict[str, int]:
        """Классифицирует дела по rainbow (точная копия Excel формулы)"""
        today = date.today()

        # Инициализация счетчиков
        counters = {
            "ИК (Ипотечные)": 0,
            "Серый (Переоткрыто)": 0,
            "Зеленый (Суд.акт + передача)": 0,
            "Желтый (Условно закрыто + передача)": 0,
            "Оранжевый (Суд.акт без передачи)": 0,
            "Синий (Приказное >90 дней)": 0,
            "Красный (До 2023 года)": 0,
            "Лиловый (Исковое >120 дней)": 0,
            "Иное": 0
        }

        for _, row in df.iterrows():
            # 1. ИК - проверка наличия "залог" в Вид запроса
            request_type = str(row[COLUMNS["REQUEST_TYPE"]]) if pd.notna(row[COLUMNS["REQUEST_TYPE"]]) else ""
            if "залог" in request_type.lower():
                counters["ИК (Ипотечные)"] += 1
                continue

            # 2. Серый - Переоткрыто
            case_status = str(row[COLUMNS["CASE_STATUS"]]) if pd.notna(row[COLUMNS["CASE_STATUS"]]) else ""
            if case_status == VALUES["REOPENED"]:
                counters["Серый (Переоткрыто)"] += 1
                continue

            # 3. Зеленый - Суд.акт + передача (AD38 > X38 и AD38 не пусто)
            actual_transfer_date = row[COLUMNS["ACTUAL_TRANSFER_DATE"]]
            court_hearing_date = row[COLUMNS["COURT_HEARING_DATE"]]

            if (case_status == VALUES["COURT_ACT_IN_FORCE"] and
                    pd.notna(actual_transfer_date) and
                    pd.notna(court_hearing_date) and
                    actual_transfer_date > court_hearing_date):
                counters["Зеленый (Суд.акт + передача)"] += 1
                continue

            # 4. Желтый - Условно закрыто + передача (AD38 не пусто)
            if (case_status == VALUES["CONDITIONALLY_CLOSED"] and
                    pd.notna(actual_transfer_date)):
                counters["Желтый (Условно закрыто + передача)"] += 1
                continue

            # 5. Оранжевый - Суд.акт без передачи (AD38 пусто)
            if (case_status == VALUES["COURT_ACT_IN_FORCE"] and
                    pd.isna(actual_transfer_date)):
                counters["Оранжевый (Суд.акт без передачи)"] += 1
                continue

            # 6. Синий - Приказное >90 дней
            method_of_protection = str(row[COLUMNS["METHOD_OF_PROTECTION"]]) if pd.notna(
                row[COLUMNS["METHOD_OF_PROTECTION"]]) else ""
            last_request_date = row[COLUMNS["LAST_REQUEST_DATE"]]

            if (method_of_protection == VALUES["ORDER_PRODUCTION"] and
                    pd.notna(last_request_date)):
                if (today - last_request_date.date()) > pd.Timedelta(days=90):
                    counters["Синий (Приказное >90 дней)"] += 1
                    continue

            # 7. Красный - До 2023 года
            if pd.notna(last_request_date):
                if last_request_date.date() < date(2023, 1, 1):
                    counters["Красный (До 2023 года)"] += 1
                    continue

            # 8. Лиловый - Исковое >120 дней
            if (method_of_protection == VALUES["CLAIM_PROCEEDINGS"] and
                    pd.notna(last_request_date)):
                if (today - last_request_date.date()) > pd.Timedelta(days=120):
                    counters["Лиловый (Исковое >120 дней)"] += 1
                    continue

            # 9. Иное
            counters["Иное"] += 1

        return counters

    @staticmethod
    def print_rainbow_stats(counters: Dict[str, int]):
        """Выводит статистику по rainbow в консоль"""
        print("\nСтатистика по делам (формула L):")
        print("-------------------")
        total = 0
        for rainbow, count in counters.items():
            print(f"{rainbow}: {count}")
            total += count
        print("-------------------")
        print(f"Всего: {total}\n")