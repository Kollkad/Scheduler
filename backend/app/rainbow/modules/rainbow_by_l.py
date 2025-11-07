# rainbow_by_l.py
import pandas as pd
from typing import Dict
from datetime import datetime, date
from backend.app.common.config.column_names import COLUMNS, VALUES
from backend.app.common.modules.utils import safe_get_column


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

        # ФИЛЬТРАЦИЯ: только иски от банка с определенными статусами
        filtered_indices = []
        for idx, row in df.iterrows():
            category = safe_get_column(row, COLUMNS["CATEGORY"])
            case_status = safe_get_column(row, COLUMNS["CASE_STATUS"])

            if (category == VALUES["CLAIM_FROM_BANK"] and
                    case_status not in [VALUES["CLOSED"], VALUES["ERROR_DUBLICATE"],
                                        VALUES["WITHDRAWN_BY_THE_INITIATOR"]]):
                filtered_indices.append(idx)

        filtered_df = df.loc[filtered_indices]

        for _, row in filtered_df.iterrows():
            # Безопасное получение значений
            request_type = safe_get_column(row, COLUMNS["REQUEST_TYPE"], "")
            case_status = safe_get_column(row, COLUMNS["CASE_STATUS"], "")
            method_of_protection = safe_get_column(row, COLUMNS["METHOD_OF_PROTECTION"], "")
            actual_transfer_date = safe_get_column(row, COLUMNS["ACTUAL_TRANSFER_DATE"], None)
            court_hearing_date = safe_get_column(row, COLUMNS["COURT_HEARING_DATE"], None)
            last_request_date = safe_get_column(row, COLUMNS["LAST_REQUEST_DATE"], None)

            # 1. ИК - проверка наличия "залог" в Вид запроса
            if "залог" in str(request_type).lower():
                counters["ИК (Ипотечные)"] += 1
                continue

            # 2. Серый - Переоткрыто
            if case_status == VALUES["REOPENED"]:
                counters["Серый (Переоткрыто)"] += 1
                continue

            # 3. Зеленый - Суд.акт + передача (AD38 > X38 и AD38 не пусто)
            if (case_status == VALUES["COURT_ACT_IN_FORCE"] and
                    actual_transfer_date is not None and
                    court_hearing_date is not None):
                try:
                    if pd.notna(actual_transfer_date) and pd.notna(court_hearing_date):
                        if actual_transfer_date > court_hearing_date:
                            counters["Зеленый (Суд.акт + передача)"] += 1
                            continue
                except (TypeError, ValueError):
                    pass

            # 4. Желтый - Условно закрыто + передача (AD38 не пусто)
            if (case_status == VALUES["CONDITIONALLY_CLOSED"] and
                    actual_transfer_date is not None and
                    pd.notna(actual_transfer_date)):
                counters["Желтый (Условно закрыто + передача)"] += 1
                continue

            # 5. Оранжевый - Суд.акт без передачи (AD38 пусто)
            if (case_status == VALUES["COURT_ACT_IN_FORCE"] and
                    (actual_transfer_date is None or pd.isna(actual_transfer_date))):
                counters["Оранжевый (Суд.акт без передачи)"] += 1
                continue

            # 6. Синий - Приказное >90 дней
            if (method_of_protection == VALUES["ORDER_PRODUCTION"] and
                    last_request_date is not None and
                    pd.notna(last_request_date)):
                try:
                    if (today - last_request_date.date()) > pd.Timedelta(days=90):
                        counters["Синий (Приказное >90 дней)"] += 1
                        continue
                except (TypeError, AttributeError):
                    pass

            # 7. Красный - До 2023 года
            if last_request_date is not None and pd.notna(last_request_date):
                try:
                    if last_request_date.date() < date(2023, 1, 1):
                        counters["Красный (До 2023 года)"] += 1
                        continue
                except (TypeError, AttributeError):
                    pass

            # 8. Лиловый - Исковое >120 дней
            if (method_of_protection == VALUES["CLAIM_PROCEEDINGS"] and
                    last_request_date is not None and
                    pd.notna(last_request_date)):
                try:
                    if (today - last_request_date.date()) > pd.Timedelta(days=120):
                        counters["Лиловый (Исковое >120 дней)"] += 1
                        continue
                except (TypeError, AttributeError):
                    pass

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