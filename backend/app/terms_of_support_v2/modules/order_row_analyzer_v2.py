# backend/app/terms_of_support_v2/modules/order_row_analyzer_v2.py
"""
Модуль анализа строк дел для приказного производства (версия 2).

Предоставляет функции для проверки соблюдения сроков на различных этапах
приказного производства. Каждая функция анализирует конкретный аспект дела
и возвращает статус соблюдения срока.

Основные категории проверок:
- Закрытие дела (Closed)
- Получение исполнительного документа (Execution Document Received)
- Реакция суда (Court Reaction)
- Смена статуса (First Status Changed)
"""

from datetime import date
from backend.app.common.config.column_names import COLUMNS, VALUES
import pandas as pd
from backend.app.common.modules.utils import get_filing_date, safe_get_column


def evaluate_order_closed_row(row: pd.Series, today: date) -> tuple:
    """
    Оценивает своевременность закрытия дела в приказном производстве.

    Сравнивает дату закрытия дела с дедлайном в 90 календарных дней
    от даты подачи заявления. Если дата закрытия отсутствует, проверяет
    не истек ли дедлайн на текущую дату.

    Args:
        row (pd.Series): Строка данных дела для оценки
        today (date): Текущая дата для сравнения с дедлайном

    Returns:
        tuple: Кортеж (status, is_completed) где:
            - status: 'timely' (в срок), 'overdue' (просрочено) или 'no_data' (нет данных)
            - is_completed: True если дело закрыто, False если нет
    """
    try:
        # Получение даты подачи заявления из данных дела
        filing_date = get_filing_date(row)
        if filing_date is None:
            return "no_data", False
        filing_date = filing_date.date()

        # Расчет дедлайна закрытия дела (90 календарных дней от подачи)
        deadline_date = filing_date + pd.Timedelta(days=90)

        # Безопасное получение даты закрытия дела
        closing_date_value = safe_get_column(row, COLUMNS["CASE_CLOSING_DATE"])

        if pd.notna(closing_date_value) and closing_date_value != "no_data":
            # Сравнение даты закрытия с дедлайном при наличии данных
            closing_date = pd.to_datetime(closing_date_value).date()

            if closing_date <= deadline_date:
                return "timely", True  # Дело закрыто в установленный срок
            else:
                return "overdue", True  # Дело закрыто с нарушением срока
        else:
            # Проверка текущего статуса при отсутствии даты закрытия
            if today > deadline_date:
                return "overdue", False  # Дедлайн закрытия дела истек
            else:
                return "timely", False  # Дедлайн закрытия дела еще не наступил

    except Exception:
        return "no_data", False


def evaluate_order_execution_document_row(row: pd.Series, today: date) -> tuple:
    """
    Оценивает получение исполнительного документа в приказном производстве.

    Использует данные из таблицы мониторинга документов для поиска
    исполнительного листа по коду дела и подразделению ПСИП.

    Args:
        row (pd.Series): Строка данных дела для оценки
        today (date): Текущая дата для расчетов (резервный параметр)

    Returns:
        tuple: Кортеж (status, is_completed) где:
            - status: статус из таблицы документов или 'no_data'
            - is_completed: True если подтверждена передача документа
    """
    try:
        case_code = safe_get_column(row, COLUMNS["CASE_CODE"])
        if case_code == "no_data":
            return "no_data", False

        # Получение обработанных данных документов через data_manager
        from backend.app.common.modules.data_manager import data_manager
        current_processed_documents = data_manager.get_processed_data("documents_processed")

        if current_processed_documents is None or current_processed_documents.empty:
            return "no_data", False

        # Поиск соответствующего исполнительного листа
        matching_docs = current_processed_documents[
            (current_processed_documents["caseCode"] == case_code) &
            (current_processed_documents["department"] == "ПСИП") &
            (current_processed_documents["document"] == "Исполнительный лист")
            ]

        if not matching_docs.empty:
            doc = matching_docs.iloc[0]
            doc_status = doc["monitoringStatus"]
            response_essence = doc.get("responseEssence", "")
            is_completed = (response_essence == "Передача подтверждена")
            return doc_status, is_completed
        return "no_data", False

    except Exception:
        return "no_data", False


def evaluate_order_court_reaction_row(row: pd.Series, today: date) -> tuple:
    """
    Оценивает полноту реакции суда в приказном производстве.

    Проверяет выполнение всех условий реакции суда в течение 60 календарных дней
    от даты подачи заявления. Условия включают: вынесение судебного приказа,
    заполнение дат получения/передачи ИД, установление статуса "Условно закрыто".

    Args:
        row (pd.Series): Строка данных дела для оценки
        today (date): Текущая дата для сравнения с дедлайном

    Returns:
        tuple: Кортеж (status, is_completed) где:
            - status: 'timely', 'overdue' или 'no_data'
            - is_completed: True если все условия реакции суда выполнены
    """
    try:
        # Получение даты подачи заявления из данных дела
        filing_date = get_filing_date(row)
        if filing_date is None:
            return "no_data", False
        filing_date = filing_date.date()

        # Расчет дедлайна реакции суда (60 календарных дней от подачи)
        deadline_date = filing_date + pd.Timedelta(days=60)

        # Проверка выполнения всех условий реакции суда
        # Условие 1: Определение суда должно быть "Судебный приказ"
        court_determination = safe_get_column(row, COLUMNS["COURT_DETERMINATION"])
        has_court_order = (court_determination == VALUES["COURT_ORDER"])

        # Условие 2: Даты получения и передачи ИД должны быть заполнены
        has_receipt_date = (pd.notna(safe_get_column(row, COLUMNS["ACTUAL_RECEIPT_DATE"]))
                            and safe_get_column(row, COLUMNS["ACTUAL_RECEIPT_DATE"]) != "no_data")

        has_transfer_date = (pd.notna(safe_get_column(row, COLUMNS["ACTUAL_TRANSFER_DATE"]))
                             and safe_get_column(row, COLUMNS["ACTUAL_TRANSFER_DATE"]) != "no_data")

        # Условие 3: Статус дела должен быть "Условно закрыто"
        current_status = safe_get_column(row, COLUMNS["CASE_STATUS"])
        has_correct_status = (current_status == VALUES["CONDITIONALLY_CLOSED"])

        # Проверка выполнения всех условий одновременно
        all_conditions_met = (has_court_order and has_receipt_date and
                              has_transfer_date and has_correct_status)

        # Определение статуса выполнения условия
        is_completed = all_conditions_met

        # Логика определения статуса на основе дедлайна и выполнения условий
        if today > deadline_date:
            # После истечения дедлайна - проверка выполнения всех условий
            return "timely" if all_conditions_met else "overdue", is_completed
        else:
            # До истечения дедлайна - считается своевременным
            return "timely", is_completed

    except Exception:
        return "no_data", False


def evaluate_order_first_status_row(row: pd.Series, today: date) -> tuple:
    """
    Оценивает своевременность смены первоначального статуса дела.

    Контролирует смену статуса с "Подготовка документов" на "Ожидание реакции суда"
    в течение 14 календарных дней от даты подачи заявления.

    Args:
        row (pd.Series): Строка данных дела для оценки
        today (date): Текущая дата для сравнения с дедлайном

    Returns:
        tuple: Кортеж (status, is_completed) где:
            - status: 'timely', 'overdue' или 'no_data'
            - is_completed: False (действие не выполнено, раз дело на этом этапе)
    """
    try:
        # Получение даты подачи заявления из данных дела
        filing_date = get_filing_date(row)
        if filing_date is None:
            return "no_data", False
        filing_date = filing_date.date()

        # Расчет дедлайна смены статуса (14 календарных дней от подачи)
        deadline_date = filing_date + pd.Timedelta(days=14)

        # Получение текущего статуса дела
        current_status = safe_get_column(row, COLUMNS["CASE_STATUS"])

        # Если статус уже сменился на ожидание реакции суда - своевременно
        if current_status == VALUES["AWAITING_COURT_RESPONSE"]:
            return "timely", False  # Статус сменился, но дело все равно на этом этапе

        # Если дедлайн истек и статус все еще подготовка документов - просрочено
        if today > deadline_date and current_status == VALUES["PREPARATION_OF_DOCUMENTS"]:
            return "overdue", False  # Просрочена смена статуса

        # Во всех остальных случаях (время есть или статус уже другой) - своевременно
        return "timely", False

    except Exception:
        return "no_data", False