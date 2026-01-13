import os
import inspect
from datetime import date, timedelta
import random

from typing import Dict, List

import pandas as pd

from backend.app.common.config.column_names import COLUMNS, VALUES
from backend.app.common.config.calendar_config import russian_calendar
from backend.app.saving_results.modules.saving_results_settings import (
    save_with_xlsxwriter_formatting,
    generate_filename
)
# 1. Дата, на которую нужны данные
CHECK_DATE: date = date(2025, 12, 26)

# 2. паттерны на виды

DETAILED_PATTERN_KEYS = [
    "START_ROW_RAINBOW",
    "CASE_STATUS",
    "METHOD_OF_PROTECTION",
    "CASE_CODE",
    "CASE_TYPE",
    "REQUEST_TYPE",
    "GOSB",
    "RESPONSIBLE_EXECUTOR",
    "CATEGORY",
    "COURT",
    "CHARACTERISTICS_FINAL_COURT_ACT",
    "ACTUAL_TRANSFER_DATE",
    "ACTUAL_RECEIPT_DATE",
    "LAST_REQUEST_DATE",
    "LAST_REQUEST_DATE_IN_UP",
    "LAWSUIT_FILING_DATE",
    "FIRST_LAWSUIT_FILING_DATE",
    "PREVIOUS_HEARING_DATE",
    "NEXT_HEARING_DATE",
    "COURT_HEARING_DATE",
    "COURT_DECISION_DATE",
    "DECISION_RECEIPT_DATE",
    "CASE_CLOSING_DATE",
    "DECISION_COURT_DATE",
    "CASE_COMMENTS",
    "COURT_DETERMINATION",
    "DETERMINATION_DATE",
    "FINAL_ACT_RECEIPT_DATE",
    "FINAL_ACT_TRANSFER_DATE",
]

DOCUMENTS_PATTERN_KEYS = [
    "START_ROW_SCHEDULER",
    "DOCUMENT_CASE_CODE",
    "DOCUMENT_TYPE",
    "DEPARTMENT_CATEGORY",
    "DOCUMENT_RECEIPT_DATE",
    "DOCUMENT_TRANSFER_DATE",
    "DOCUMENT_REQUEST_DATE",
    "ESSENSE_OF_THE_ANSWER",
    "DOCUMENT_REQUEST_CODE",
    "COURT_NAME",
]

# =========================================================
# 3. Контекст кодов
# =========================================================

class CodeContext:
    def __init__(self):
        self.case = 1
        self.doctr = 1
        self.rqst = 1


class CodeGenerator:
    @staticmethod
    def cp_case(num: int) -> str:
        return f"CP-CASE-{num:07d}"

    @staticmethod
    def cp_doctr(num: int) -> str:
        return f"CP-DOCTR-{num:07d}"

    @staticmethod
    def cp_rqst(num: int) -> str:
        return f"CP-RQST-{num:07d}"


# 4. Строки

def empty_detailed_row() -> Dict:
    row = {COLUMNS[key]: None for key in DETAILED_PATTERN_KEYS}
    row["Статус мониторинга (план)"] = None
    row["Выполнено (план)"] = None
    return row


def empty_documents_row() -> Dict:
    row = {COLUMNS[key]: None for key in DOCUMENTS_PATTERN_KEYS}
    row["Статус мониторинга (план)"] = None
    row["Выполнено (план)"] = None
    return row


def base_detailed_row(row_num: int, case_code: str, production_type: str = None) -> Dict:
    REQUEST_TYPES = [
        "Взыскание дебиторской задолженности по транзакционному бизнесу",
        "Сопровождение уголовного дела в суде",
        "Заявление в ФАС (РНП)",
        "Иск гос. органа",
        "Взыскание задолженности по кредитам с поручительством (ЮЛ)",
        "Обжалование решений/действий/бездействия судебных приставов-исполнителей",
    ]
    row = empty_detailed_row()
    row[COLUMNS["START_ROW_RAINBOW"]] = row_num
    row[COLUMNS["CASE_CODE"]] = case_code
    request_type = random.choice(REQUEST_TYPES)
    row[COLUMNS["REQUEST_TYPE"]] = request_type
    row[COLUMNS["CASE_TYPE"]] = request_type

    if production_type is None:
        raise ValueError("production_type обязателен! Укажите 'lawsuit' или 'order'")

    if production_type == "lawsuit":
        row[COLUMNS["METHOD_OF_PROTECTION"]] = VALUES["CLAIM_PROCEEDINGS"]  # Исковое
    elif production_type == "order":
        row[COLUMNS["METHOD_OF_PROTECTION"]] = VALUES["ORDER_PRODUCTION"]  # Приказное
    else:
        # Если передан неизвестный тип
        row[COLUMNS["METHOD_OF_PROTECTION"]] = "Не указано"

    row[COLUMNS["CASE_TYPE"]] = VALUES["MORTGAGE_DEBT_RECOVERY"]
    row[COLUMNS["GOSB"]] = "Аппарат Банка"
    row[COLUMNS["RESPONSIBLE_EXECUTOR"]] = "Иванов И.И."
    row[COLUMNS["CATEGORY"]] = VALUES["CLAIM_FROM_BANK"]
    row[COLUMNS["COURT"]] = "Арбитражный суд г. Москвы"
    return row


def base_documents_row(ctx: CodeContext, production_type: str = "lawsuit") -> Dict:
    row = empty_documents_row()
    row[COLUMNS["START_ROW_SCHEDULER"]] = CodeGenerator.cp_doctr(ctx.doctr)
    row[COLUMNS["DOCUMENT_REQUEST_CODE"]] = CodeGenerator.cp_rqst(ctx.rqst)
    row[COLUMNS["DOCUMENT_CASE_CODE"]] = CodeGenerator.cp_case(ctx.case)
    row[COLUMNS["COURT_NAME"]] = "Арбитражный суд г. Москвы"

    if production_type == "lawsuit":
        row[COLUMNS["METHOD_OF_PROTECTION"]] = VALUES["CLAIM_PROCEEDINGS"]
    elif production_type == "order":
        row[COLUMNS["METHOD_OF_PROTECTION"]] = VALUES["ORDER_PRODUCTION"]
    else:
        row[COLUMNS["METHOD_OF_PROTECTION"]] = "Не указано"

    return row

# =========================================================
# 5.1. td_lawsuit-функции (детальный отчет)
# =========================================================

def td_lawsuit_evaluate_closed_row(today: date, ctx: CodeContext) -> pd.DataFrame:
    rows = []
    scenarios = [
        ("timely", False, +10),     # Дело не закрыто, дедлайн ещё не наступил
        ("overdue", False, -10),    # Дело не закрыто, дедлайн истёк
        ("timely", True, +5),       # Дело закрыто в срок
        ("overdue", True, -5),      # Дело закрыто с опозданием
        ("no_data", False, None),   # Нет даты подачи
    ]

    for idx, (monitoring_status, completed, delta) in enumerate(scenarios, start=1):
        case_code = CodeGenerator.cp_case(ctx.case)
        row = base_detailed_row(idx, case_code, "lawsuit")

        if delta is not None:
            filing_date = today + timedelta(days=delta - 125)
            row[COLUMNS["LAWSUIT_FILING_DATE"]] = filing_date
            row[COLUMNS["FIRST_LAWSUIT_FILING_DATE"]] = filing_date
            row[COLUMNS["LAST_REQUEST_DATE"]] = filing_date

            if completed:
                deadline_date = filing_date + timedelta(days=125)
                row[COLUMNS["CASE_CLOSING_DATE"]] = deadline_date - timedelta(days=1) if monitoring_status == "timely" else deadline_date + timedelta(days=1)
            else:
                row[COLUMNS["CASE_CLOSING_DATE"]] = None
        else:
            # Сценарий no_data
            row[COLUMNS["LAWSUIT_FILING_DATE"]] = None
            row[COLUMNS["FIRST_LAWSUIT_FILING_DATE"]] = None
            row[COLUMNS["CASE_CLOSING_DATE"]] = None

        row[COLUMNS["CASE_STATUS"]] = VALUES["CLOSED"] if completed else VALUES["UNDER_CONSIDERATION"]
        if row[COLUMNS["CASE_STATUS"]] == VALUES["CLOSED"]:
            row[COLUMNS["CHARACTERISTICS_FINAL_COURT_ACT"]] = "Не в пользу Банка"

        row["Статус мониторинга (план)"] = monitoring_status
        row["Выполнено (план)"] = completed

        rows.append(row)
        ctx.case += 1

    return pd.DataFrame(rows)



def td_lawsuit_evaluate_decision_date_row(today: date, ctx: CodeContext) -> pd.DataFrame:
    rows = []

    scenarios = [
        ("timely", True, -30, -10),
        ("overdue", True, -50, -5),
        ("timely", False, -20, None),
        ("overdue", False, -60, None),
        ("no_data", False, None, None),
    ]

    for idx, (status, completed, delta_decision_court, delta_court_decision) in enumerate(scenarios, start=1):
        case_code = CodeGenerator.cp_case(ctx.case)
        row = base_detailed_row(idx, case_code, "lawsuit")

        row[COLUMNS["CASE_STATUS"]] = VALUES["DECISION_MADE"]
        row[COLUMNS["CHARACTERISTICS_FINAL_COURT_ACT"]] = "Нейтрально"

        row[COLUMNS["DECISION_COURT_DATE"]] = today + timedelta(days=delta_decision_court) if delta_decision_court is not None else None
        row[COLUMNS["COURT_DECISION_DATE"]] = today + timedelta(days=delta_court_decision) if delta_court_decision is not None else None

        row["Статус мониторинга (план)"] = status
        row["Выполнено (план)"] = completed

        rows.append(row)
        ctx.case += 1

    return pd.DataFrame(rows)


def td_lawsuit_evaluate_decision_receipt_row(today: date, ctx: CodeContext) -> pd.DataFrame:
    rows = []

    scenarios = [
        ("timely", True, -5, -3),
        ("overdue", True, -10, -5),
        ("timely", False, -2, None),
        ("overdue", False, -7, None),
        ("no_data", False, None, None),
    ]

    for idx, (status, completed, delta_court_decision, delta_receipt) in enumerate(scenarios, start=1):
        case_code = CodeGenerator.cp_case(ctx.case)
        row = base_detailed_row(idx, case_code, "lawsuit")

        row[COLUMNS["CASE_STATUS"]] = VALUES["DECISION_MADE"]
        row[COLUMNS["COURT_DECISION_DATE"]] = today + timedelta(days=delta_court_decision) if delta_court_decision is not None else None
        row[COLUMNS["DECISION_RECEIPT_DATE"]] = today + timedelta(days=delta_receipt) if delta_receipt is not None else None

        row["Статус мониторинга (план)"] = status
        row["Выполнено (план)"] = completed

        rows.append(row)
        ctx.case += 1

    return pd.DataFrame(rows)


def td_lawsuit_evaluate_decision_transfer_row(today: date, ctx: CodeContext) -> pd.DataFrame:
    rows = []

    scenarios = [
        ("timely", True, -2, -1),
        ("overdue", True, -3, +1),
        ("timely", False, -1, None),
        ("overdue", False, -3, None),
        ("no_data", False, None, None),
    ]

    for idx, (status, completed, delta_court_decision, delta_transfer) in enumerate(scenarios, start=1):
        case_code = CodeGenerator.cp_case(ctx.case)
        row = base_detailed_row(idx, case_code, "lawsuit")

        row[COLUMNS["CASE_STATUS"]] = VALUES["DECISION_MADE"]
        row[COLUMNS["COURT_DECISION_DATE"]] = today + timedelta(days=delta_court_decision) if delta_court_decision is not None else None
        row[COLUMNS["ACTUAL_TRANSFER_DATE"]] = today + timedelta(days=delta_transfer) if delta_transfer is not None else None

        row["Статус мониторинга (план)"] = status
        row["Выполнено (план)"] = completed

        rows.append(row)
        ctx.case += 1

    return pd.DataFrame(rows)


def td_lawsuit_evaluate_next_hearing_row(today: date, ctx: CodeContext, calendar=russian_calendar) -> pd.DataFrame:
    rows = []

    scenarios = [
        ("timely", True, -5, -2),
        ("overdue", True, -7, 0),
        ("timely", False, -2, None),
        ("overdue", False, -5, None),
        ("no_data", False, None, None),
    ]

    for idx, (status, completed, delta_determination, delta_hearing) in enumerate(scenarios, start=1):
        case_code = CodeGenerator.cp_case(ctx.case)
        row = base_detailed_row(idx, case_code, "lawsuit")

        row[COLUMNS["CASE_STATUS"]] = VALUES["UNDER_CONSIDERATION"]
        row[COLUMNS["DETERMINATION_DATE"]] = calendar.add_working_days(today, delta_determination) if delta_determination is not None else None
        row[COLUMNS["NEXT_HEARING_DATE"]] = calendar.add_working_days(today, delta_hearing) if delta_hearing is not None else None

        row["Статус мониторинга (план)"] = status
        row["Выполнено (план)"] = completed

        rows.append(row)
        ctx.case += 1

    return pd.DataFrame(rows)


def td_lawsuit_evaluate_prev_to_next_hearing_row(today: date, ctx: CodeContext, calendar=russian_calendar) -> pd.DataFrame:
    rows = []

    scenarios = [
        ("timely", True, -5, -3),
        ("overdue", True, -7, -3),
        ("timely", False, -2, None),
        ("overdue", False, -5, None),
        ("timely", False, None, -2),
        ("overdue", False, None, -5),
        ("overdue", False, None, None),
    ]

    for idx, (status, completed, delta_prev, delta_next) in enumerate(scenarios, start=1):
        case_code = CodeGenerator.cp_case(ctx.case)
        row = base_detailed_row(idx, case_code, "lawsuit")

        row[COLUMNS["CASE_STATUS"]] = VALUES["UNDER_CONSIDERATION"]
        row[COLUMNS["PREVIOUS_HEARING_DATE"]] = calendar.add_working_days(today, delta_prev) if delta_prev is not None else None
        row[COLUMNS["NEXT_HEARING_DATE"]] = calendar.add_working_days(today, delta_next) if delta_next is not None else None

        row["Статус мониторинга (план)"] = status
        row["Выполнено (план)"] = completed

        rows.append(row)
        ctx.case += 1

    return pd.DataFrame(rows)


def td_lawsuit_evaluate_under_consideration_60days(today: date, ctx: CodeContext) -> pd.DataFrame:
    rows = []
    scenarios = [
        ("timely", -30),
        ("overdue", -70),
        ("no_data", None),
    ]

    for idx, (status, filing_offset) in enumerate(scenarios, start=1):
        case_code = CodeGenerator.cp_case(ctx.case)
        row = base_detailed_row(idx, case_code, "lawsuit")

        row[COLUMNS["CASE_STATUS"]] = VALUES["UNDER_CONSIDERATION"]
        row[COLUMNS["CHARACTERISTICS_FINAL_COURT_ACT"]] = "Полностью в пользу Банка"
        row[COLUMNS["METHOD_OF_PROTECTION"]] = VALUES["CLAIM_PROCEEDINGS"]
        row[COLUMNS["CASE_TYPE"]] = VALUES["MORTGAGE_DEBT_RECOVERY"]

        if filing_offset is not None:
            row[COLUMNS["LAWSUIT_FILING_DATE"]] = today + timedelta(days=filing_offset)
            row[COLUMNS["FIRST_LAWSUIT_FILING_DATE"]] = today + timedelta(days=filing_offset)
        else:
            row[COLUMNS["LAWSUIT_FILING_DATE"]] = None
            row[COLUMNS["FIRST_LAWSUIT_FILING_DATE"]] = None

        row["Статус мониторинга (план)"] = status
        row["Выполнено (план)"] = False

        rows.append(row)
        ctx.case += 1

    return pd.DataFrame(rows)


def td_lawsuit_evaluate_court_reaction_row(today: date, ctx: CodeContext, calendar=russian_calendar) -> pd.DataFrame:
    rows = []

    scenarios = [
        ("timely", -3, True),
        ("timely", +3, False),
        ("overdue", -10, False),
        ("no_data", None, False),
    ]

    for idx, (status, filing_offset, determination_present) in enumerate(scenarios, start=1):
        case_code = CodeGenerator.cp_case(ctx.case)
        row = base_detailed_row(idx, case_code, "lawsuit")

        row[COLUMNS["CASE_STATUS"]] = VALUES["UNDER_CONSIDERATION"]
        row[COLUMNS["METHOD_OF_PROTECTION"]] = VALUES["CLAIM_PROCEEDINGS"]
        row[COLUMNS["CASE_TYPE"]] = VALUES["MORTGAGE_DEBT_RECOVERY"]

        if filing_offset is not None:
            filing_date = calendar.add_working_days(today, filing_offset)
            row[COLUMNS["LAWSUIT_FILING_DATE"]] = filing_date
            row[COLUMNS["FIRST_LAWSUIT_FILING_DATE"]] = filing_date
        else:
            row[COLUMNS["LAWSUIT_FILING_DATE"]] = None
            row[COLUMNS["FIRST_LAWSUIT_FILING_DATE"]] = None

        row[COLUMNS["DETERMINATION_DATE"]] = today if determination_present else None

        row["Статус мониторинга (план)"] = status
        row["Выполнено (план)"] = determination_present

        rows.append(row)
        ctx.case += 1

    return pd.DataFrame(rows)


def td_lawsuit_evaluate_first_status_changed_row(today: date, ctx: CodeContext) -> pd.DataFrame:
    rows = []

    scenarios = [
        ("timely", -5),
        ("overdue", -20),
        ("no_data", None),
    ]

    for idx, (status, filing_offset) in enumerate(scenarios, start=1):
        case_code = CodeGenerator.cp_case(ctx.case)
        row = base_detailed_row(idx, case_code, "lawsuit")

        row[COLUMNS["CASE_STATUS"]] = VALUES["PREPARATION_OF_DOCUMENTS"]
        row[COLUMNS["METHOD_OF_PROTECTION"]] = VALUES["CLAIM_PROCEEDINGS"]
        row[COLUMNS["CASE_TYPE"]] = VALUES["MORTGAGE_DEBT_RECOVERY"]

        if filing_offset is not None:
            row[COLUMNS["LAWSUIT_FILING_DATE"]] = today + timedelta(days=filing_offset)
            row[COLUMNS["FIRST_LAWSUIT_FILING_DATE"]] = today + timedelta(days=filing_offset)
        else:
            row[COLUMNS["LAWSUIT_FILING_DATE"]] = None
            row[COLUMNS["FIRST_LAWSUIT_FILING_DATE"]] = None

        row["Статус мониторинга (план)"] = status
        row["Выполнено (план)"] = False

        rows.append(row)
        ctx.case += 1

    return pd.DataFrame(rows)

# =========================================================
# 5.2. td_order-функции (детальный отчет)
# =========================================================

def td_order_evaluate_order_closed_row(today: date, ctx: CodeContext) -> pd.DataFrame:
    rows = []

    # Сценарии: (monitoring_status, completed, delta_days)
    scenarios = [
        ("timely", True, +5),      # Дело закрыто в срок
        ("overdue", True, -5),     # Дело закрыто с опозданием
        ("timely", False, +0),     # Дело не закрыто, дедлайн еще не наступил
        ("overdue", False, -10),   # Дело не закрыто, дедлайн истек
        ("no_data", False, None),  # Нет даты подачи
    ]

    for idx, (status, completed, delta) in enumerate(scenarios, start=1):
        case_code = CodeGenerator.cp_case(ctx.case)
        row = base_detailed_row(idx, case_code, production_type="order")

        if delta is not None:
            filing_date = today + timedelta(days=delta)
            row[COLUMNS["LAWSUIT_FILING_DATE"]] = filing_date
            row[COLUMNS["FIRST_LAWSUIT_FILING_DATE"]] = filing_date
            if completed:
                row[COLUMNS["CASE_CLOSING_DATE"]] = filing_date + timedelta(days=90 if status == "timely" else 91)
            else:
                row[COLUMNS["CASE_CLOSING_DATE"]] = None
        else:
            # Сценарий no_data
            row[COLUMNS["LAWSUIT_FILING_DATE"]] = None
            row[COLUMNS["FIRST_LAWSUIT_FILING_DATE"]] = None
            row[COLUMNS["CASE_CLOSING_DATE"]] = None

        row[COLUMNS["CASE_STATUS"]] = VALUES["CLOSED"] if completed else VALUES["AWAITING_COURT_RESPONSE"]
        row[COLUMNS["CHARACTERISTICS_FINAL_COURT_ACT"]] = "Полностью в пользу Банка"

        row["Статус мониторинга (план)"] = status
        row["Выполнено (план)"] = completed

        rows.append(row)
        ctx.case += 1

    return pd.DataFrame(rows)


def td_order_evaluate_order_court_reaction_row(today: date, ctx: CodeContext) -> pd.DataFrame:
    rows = []
    scenarios = [
        # Все условия выполнены вовремя
        ("Судебный приказ", True, True, "Условно закрыто", 0),
        # Все условия выполнены, но просрочено
        ("Судебный приказ", True, True, "Условно закрыто", -10),
        # Отсутствует определение суда
        (None, True, True, "Условно закрыто", 0),
        # Не заполнена дата получения
        ("Судебный приказ", False, True, "Условно закрыто", 0),
        # Не заполнена дата передачи
        ("Судебный приказ", True, False, "Условно закрыто", 0),
        # Статус не "Условно закрыто"
        ("Судебный приказ", True, True, "Ожидание ответа суда", 0),
        # Все данные отсутствуют
        (None, False, False, None, None),
    ]

    for idx, (court_determination, receipt, transfer, status_case, delta) in enumerate(scenarios, start=1):
        case_code = CodeGenerator.cp_case(ctx.case)
        row = base_detailed_row(idx, case_code, production_type="order")

        if delta is not None:
            filing_date = today + timedelta(days=delta)
            row[COLUMNS["LAWSUIT_FILING_DATE"]] = filing_date
            row[COLUMNS["FIRST_LAWSUIT_FILING_DATE"]] = filing_date
        else:
            row[COLUMNS["LAWSUIT_FILING_DATE"]] = None
            row[COLUMNS["FIRST_LAWSUIT_FILING_DATE"]] = None

        row[COLUMNS["COURT_DETERMINATION"]] = court_determination
        row[COLUMNS["ACTUAL_RECEIPT_DATE"]] = today if receipt else None
        row[COLUMNS["ACTUAL_TRANSFER_DATE"]] = today if transfer else None
        row[COLUMNS["CASE_STATUS"]] = status_case
        row[COLUMNS["CHARACTERISTICS_FINAL_COURT_ACT"]] = "Нейтрально"

        if delta is None:
            monitoring_status = "no_data"
        elif delta < 0 or not (court_determination and receipt and transfer and status_case == "Условно закрыто"):
            monitoring_status = "overdue"
        else:
            monitoring_status = "timely"

        completed = bool(court_determination and receipt and transfer and status_case == "Условно закрыто")

        row["Статус мониторинга (план)"] = monitoring_status
        row["Выполнено (план)"] = completed

        rows.append(row)
        ctx.case += 1

    return pd.DataFrame(rows)

def td_evaluate_order_first_status_row(today: date, ctx: CodeContext) -> pd.DataFrame:
    rows = []
    scenarios = [
        (VALUES["PREPARATION_OF_DOCUMENTS"], +0, "timely"),   # Дело еще в срок, статус не сменился
        (VALUES["PREPARATION_OF_DOCUMENTS"], -20, "overdue"), # Дедлайн прошел, статус не сменился
        (VALUES["AWAITING_COURT_RESPONSE"], -5, "timely"),    # Статус уже сменился на ожидание реакции суда
        (None, None, "no_data"),                               # Нет даты подачи
    ]

    for idx, (current_status, delta, monitoring_status) in enumerate(scenarios, start=1):
        case_code = CodeGenerator.cp_case(ctx.case)
        row = base_detailed_row(idx, case_code, production_type="order")

        # Заполняем дату подачи
        if delta is not None:
            filing_date = today + timedelta(days=delta)
            row[COLUMNS["LAWSUIT_FILING_DATE"]] = filing_date
            row[COLUMNS["FIRST_LAWSUIT_FILING_DATE"]] = filing_date
        else:
            row[COLUMNS["LAWSUIT_FILING_DATE"]] = None
            row[COLUMNS["FIRST_LAWSUIT_FILING_DATE"]] = None

        row[COLUMNS["CASE_STATUS"]] = current_status

        row["Статус мониторинга (план)"] = monitoring_status
        row["Выполнено (план)"] = False  # Всегда False

        rows.append(row)
        ctx.case += 1

    return pd.DataFrame(rows)

# =========================================================
# 5.3. td_rainbow-функции (детальный отчет)
# =========================================================
def td_rainbow_cases(today: date, ctx: CodeContext) -> pd.DataFrame:
    rows = []

    def base_row(idx, color):
        case_code = CodeGenerator.cp_case(ctx.case)
        row = base_detailed_row(idx, case_code, production_type="rainbow")

        row[COLUMNS["CATEGORY"]] = VALUES["CLAIM_FROM_BANK"]
        row["Цвет (план)"] = color

        ctx.case += 1
        return row

    # 1. ИК — ипотека / залог
    row = base_row(1, "ИК")
    row[COLUMNS["REQUEST_TYPE"]] = "Ипотека под залог"
    row[COLUMNS["CASE_STATUS"]] = VALUES["UNDER_CONSIDERATION"]
    rows.append(row)

    # 2. Серый — переоткрытое дело
    row = base_row(2, "Серый")
    row[COLUMNS["CASE_STATUS"]] = VALUES["REOPENED"]
    rows.append(row)

    # 3. Зеленый — судебный акт в силе + есть передача
    row = base_row(3, "Зеленый")
    row[COLUMNS["CASE_STATUS"]] = VALUES["COURT_ACT_IN_FORCE"]
    row[COLUMNS["ACTUAL_TRANSFER_DATE"]] = today - timedelta(days=5)
    rows.append(row)

    # 4. Желтый — условно закрыто + есть передача
    row = base_row(4, "Желтый")
    row[COLUMNS["CASE_STATUS"]] = VALUES["CONDITIONALLY_CLOSED"]
    row[COLUMNS["ACTUAL_TRANSFER_DATE"]] = today - timedelta(days=3)
    rows.append(row)

    # 5. Оранжевый — судебный акт в силе, но без передачи
    row = base_row(5, "Оранжевый")
    row[COLUMNS["CASE_STATUS"]] = VALUES["COURT_ACT_IN_FORCE"]
    row[COLUMNS["ACTUAL_TRANSFER_DATE"]] = None
    rows.append(row)

    # 6. Синий — приказное производство, запрос > 90 дней
    row = base_row(6, "Синий")
    row[COLUMNS["METHOD_OF_PROTECTION"]] = VALUES["ORDER_PRODUCTION"]
    row[COLUMNS["LAST_REQUEST_DATE"]] = today - timedelta(days=100)
    row[COLUMNS["CASE_STATUS"]] = VALUES["UNDER_CONSIDERATION"]
    rows.append(row)

    # 7. Красный — запрос до 31.12.2022
    row = base_row(7, "Красный")
    row[COLUMNS["LAST_REQUEST_DATE"]] = date(2022, 12, 1)
    row[COLUMNS["CASE_STATUS"]] = VALUES["UNDER_CONSIDERATION"]
    rows.append(row)

    # 8. Лиловый — исковое производство, запрос > 120 дней
    row = base_row(8, "Лиловый")
    row[COLUMNS["METHOD_OF_PROTECTION"]] = VALUES["CLAIM_PROCEEDINGS"]
    row[COLUMNS["LAST_REQUEST_DATE"]] = today - timedelta(days=130)
    row[COLUMNS["CASE_STATUS"]] = VALUES["UNDER_CONSIDERATION"]
    rows.append(row)

    # 9. Белый — не попадает ни под одно правило
    row = base_row(9, "Белый")
    row[COLUMNS["CASE_STATUS"]] = VALUES["UNDER_CONSIDERATION"]
    rows.append(row)

    return pd.DataFrame(rows)



# =========================================================
# 6. TD-ФУНКЦИИ — ОТЧЕТ ДОКУМЕНТОВ
# =========================================================

def td_documents_execution_document_received(today: date, ctx: CodeContext, production_type: str = "lawsuit") -> pd.DataFrame:
    rows = []

    scenarios = [
        ("timely", "Передача подтверждена"),
        ("timely", "Передача не подтверждена"),
        ("overdue", "Передача подтверждена"),
        ("no_data", None),
    ]

    for status, essence in scenarios:
        row = base_documents_row(ctx, production_type=production_type)

        row[COLUMNS["DOCUMENT_TYPE"]] = "Исполнительный лист"
        row[COLUMNS["DEPARTMENT_CATEGORY"]] = "ПСИП"

        row[COLUMNS["DOCUMENT_REQUEST_DATE"]] = today - timedelta(days=10)
        row[COLUMNS["DOCUMENT_RECEIPT_DATE"]] = today - timedelta(days=5)
        row[COLUMNS["DOCUMENT_TRANSFER_DATE"]] = today

        row[COLUMNS["ESSENSE_OF_THE_ANSWER"]] = essence

        row["Статус мониторинга (план)"] = status
        row["Выполнено (план)"] = essence == "Передача подтверждена"

        rows.append(row)

        ctx.case += 1
        ctx.doctr += 1
        ctx.rqst += 1

    return pd.DataFrame(rows)

def td_documents_deadline_expired_variants(
    today: date,
    ctx: CodeContext,
    production_type: str = "lawsuit"
) -> pd.DataFrame:
    rows = []
    scenarios = [
        ("timely", -5, "Передача не подтверждена"),   # дедлайн не истёк
        ("timely", -20, "Передача подтверждена"),     # дедлайн истёк, но ок
        ("overdue", -20, "Передача не подтверждена"), # дедлайн истёк, не подтверждено
        ("no_data", None, None),                      # нет даты запроса
    ]

    for status, delta, essence in scenarios:
        row = base_documents_row(ctx, production_type=production_type)

        row[COLUMNS["DOCUMENT_TYPE"]] = "Запрос документа"
        row[COLUMNS["DEPARTMENT_CATEGORY"]] = "ПСИП"

        if delta is not None:
            row[COLUMNS["DOCUMENT_REQUEST_DATE"]] = today + timedelta(days=delta)
        else:
            row[COLUMNS["DOCUMENT_REQUEST_DATE"]] = None

        row[COLUMNS["ESSENSE_OF_THE_ANSWER"]] = essence

        row["Статус мониторинга (план)"] = status
        row["Выполнено (план)"] = essence == "Передача подтверждена"

        rows.append(row)

        ctx.case += 1
        ctx.doctr += 1
        ctx.rqst += 1

    return pd.DataFrame(rows)


def td_documents_grouping_latest_by_transfer(
    today: date,
    ctx: CodeContext,
    production_type: str = "lawsuit"
) -> pd.DataFrame:
    rows = []
    case_code = CodeGenerator.cp_case(ctx.case)

    for i, transfer_delta in enumerate([-10, -2], start=1):
        row = base_documents_row(ctx, production_type=production_type)

        row[COLUMNS["DOCUMENT_CASE_CODE"]] = case_code
        row[COLUMNS["DOCUMENT_TYPE"]] = "Справка"
        row[COLUMNS["DEPARTMENT_CATEGORY"]] = "ЮО"

        row[COLUMNS["DOCUMENT_REQUEST_DATE"]] = today - timedelta(days=30)
        row[COLUMNS["DOCUMENT_TRANSFER_DATE"]] = today + timedelta(days=transfer_delta)
        row[COLUMNS["ESSENSE_OF_THE_ANSWER"]] = (
            "Передача подтверждена" if transfer_delta == -2 else "Передача не подтверждена"
        )

        rows.append(row)

        ctx.doctr += 1
        ctx.rqst += 1

    # ожидается, что будет взята запись с transfer = -2
    rows[-1]["Статус мониторинга (план)"] = "timely"
    rows[-1]["Выполнено (план)"] = True

    ctx.case += 1

    return pd.DataFrame(rows)

def td_documents_grouping_latest_by_receipt(
    today: date,
    ctx: CodeContext,
    production_type: str = "lawsuit"
) -> pd.DataFrame:
    rows = []

    case_code = CodeGenerator.cp_case(ctx.case)

    for receipt_delta in [-15, -3]:
        row = base_documents_row(ctx, production_type=production_type)

        row[COLUMNS["DOCUMENT_CASE_CODE"]] = case_code
        row[COLUMNS["DOCUMENT_TYPE"]] = "Уведомление"
        row[COLUMNS["DEPARTMENT_CATEGORY"]] = "ЮО"

        row[COLUMNS["DOCUMENT_REQUEST_DATE"]] = today - timedelta(days=40)
        row[COLUMNS["DOCUMENT_RECEIPT_DATE"]] = today + timedelta(days=receipt_delta)
        row[COLUMNS["DOCUMENT_TRANSFER_DATE"]] = None
        row[COLUMNS["ESSENSE_OF_THE_ANSWER"]] = "Передача не подтверждена"

        rows.append(row)

        ctx.doctr += 1
        ctx.rqst += 1

    rows[-1]["Статус мониторинга (план)"] = "overdue"
    rows[-1]["Выполнено (план)"] = False

    ctx.case += 1

    return pd.DataFrame(rows)

# =========================================================
# 7. СБОР TD-ФУНКЦИЙ
# =========================================================

def collect_td_functions(prefix: str) -> List:
    return [
        func for _, func in inspect.getmembers(
            inspect.getmodule(collect_td_functions),
            inspect.isfunction
        )
        if func.__name__.startswith(prefix)
    ]


def generate_dataset(td_functions: List, today: date) -> pd.DataFrame:
    ctx = CodeContext()
    dfs = []

    for func in td_functions:
        params = inspect.signature(func).parameters
        if "calendar" in params:
            from backend.app.common.config.calendar_config import russian_calendar
            df = func(today, ctx, russian_calendar)
        else:
            df = func(today, ctx)

        if not df.empty:
            dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    combined_df = pd.concat(dfs, ignore_index=True)

    # "Итого"
    total_row = pd.DataFrame(
        {combined_df.columns[0]: ["Итого"]},
        index=[0]
    )
    combined_df = pd.concat([combined_df, total_row], ignore_index=True)

    return combined_df

def fill_missing_dates(df: pd.DataFrame, check_date: date) -> pd.DataFrame:
    """
    Заполняет недостающие даты по правилам:
      - Для дел со статусом PREPARATION_OF_DOCUMENTS:
          Не трогать LAWSUIT_FILING_DATE
          Если отсутствует LAST_REQUEST_DATE — ставится realistic date в пределах последних 0-13 дней
      - Для всех остальных дел:
          Если отсутствует LAWSUIT_FILING_DATE — ставится realistic date в пределах последних 0-130 дней
          Если отсутствует LAST_REQUEST_DATE — ставится его равным LAWSUIT_FILING_DATE
    НЕ ПЕРЕЗАПИСЫВАЕТ уже установленные (ручные) даты.
    """
    filing_col = COLUMNS["LAWSUIT_FILING_DATE"]
    first_filing_col = COLUMNS["FIRST_LAWSUIT_FILING_DATE"]
    last_req_col = COLUMNS["LAST_REQUEST_DATE"]
    status_col = COLUMNS["CASE_STATUS"]
    total_marker = COLUMNS["END_ROW_RAINBOW"]  # "Итого"
    prep_status = VALUES["PREPARATION_OF_DOCUMENTS"]

    # Если DataFrame пустой — вернуть как есть
    if df is None or df.empty:
        return df

    df = df.copy()  # не менять исходный DF по ссылке

    total_mask = (df.iloc[:, 0] == total_marker)
    for idx in df.index:
        try:
            if total_mask.any() and total_mask.loc[idx]:
                continue
        except Exception:
            # если total_mask не содержит индекс - игнор проверки
            pass

        status = df.at[idx, status_col] if status_col in df.columns else None
        filing_val = df.at[idx, filing_col] if filing_col in df.columns else None
        last_req_val = df.at[idx, last_req_col] if last_req_col in df.columns else None

        # --- случай: "Подготовка документов" ---
        if status == prep_status:
            # Не заполняем LAWSUIT_FILING_DATE
            # Заполняется LAST_REQUEST_DATE, если пусто
            if (last_req_val is None) or pd.isna(last_req_val):
                days_ago = random.randint(0, 13)  # realistic: within last two weeks
                df.at[idx, last_req_col] = check_date - timedelta(days=days_ago)
            continue

        # --- все остальные случаи ---
        # 1) Заполнить LAWSUIT_FILING_DATE, если отсутствует
        if (filing_val is None) or pd.isna(filing_val):
            days_ago_filing = random.randint(0, 130)  # realistic window: last ~4 months
            filing_date = check_date - timedelta(days=days_ago_filing)
            df.at[idx, filing_col] = filing_date
            # также заполнить FIRST_LAWSUIT_FILING_DATE, если он пуст
            if first_filing_col in df.columns:
                first_val = df.at[idx, first_filing_col]
                if (first_val is None) or pd.isna(first_val):
                    df.at[idx, first_filing_col] = filing_date

        # 2) Если LAST_REQUEST_DATE пуст — сделать его равным LAWSUIT_FILING_DATE (но не перезаписываем существующее)
        last_req_val_after = df.at[idx, last_req_col] if last_req_col in df.columns else None
        if (last_req_val_after is None) or pd.isna(last_req_val_after):
            df.at[idx, last_req_col] = df.at[idx, filing_col]

    return df


# =========================================================
# 8. СОХРАНЕНИЕ EXCEL
# =========================================================

def save_to_excel(df: pd.DataFrame, report_type: str, sheet_name: str = "Отчет"):
    filename = generate_filename(report_type)
    base_dir = os.path.join(os.path.dirname(__file__), "dev_data")
    path = os.path.join(base_dir, filename)

    save_with_xlsxwriter_formatting(df, path, sheet_name, data_type="production")

# =========================================================
# 9. ENTRYPOINT
# =========================================================
def main():
    # Детальный отчет (иск и приказное)
    detailed_df = generate_dataset(
        collect_td_functions("td_lawsuit_") + collect_td_functions("td_order_")+ collect_td_functions("td_rainbow_"),
        CHECK_DATE
    )
    detailed_df = fill_missing_dates(detailed_df, CHECK_DATE)

    # ОД для искового
    documents_lawsuit_df = td_documents_execution_document_received(CHECK_DATE, CodeContext(), production_type="lawsuit")
    # ОД для приказного
    documents_order_df = td_documents_execution_document_received(CHECK_DATE, CodeContext(), production_type="order")
    # В один DataFrame
    documents_df = pd.concat([documents_lawsuit_df, documents_order_df], ignore_index=True)

    save_to_excel(detailed_df, report_type="detailed_report", sheet_name="Детальный отчет")
    save_to_excel(documents_df, report_type="documents_report", sheet_name="Отчет документов")

if __name__ == "__main__":
    main()

