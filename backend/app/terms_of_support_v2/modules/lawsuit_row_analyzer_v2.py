# backend/app/terms_of_support_v2/modules/lawsuit_row_analyzer_v2.py
"""
Модуль анализа строк дел для искового производства (версия 2).

Предоставляет функции для оценки соблюдения сроков на различных этапах
искового производства. Каждая функция анализирует конкретный этап дела
и возвращает статус соблюдения срока.

Основные категории проверок:
- Закрытие дела (Closed)
- Получение исполнительного документа (Execution Document Received)
- Вынесение и получение решения (Decision Made)
- Назначение заседаний (Under Consideration)
- Реакция суда (Court Reaction)
- Смена статуса (First Status Changed)
"""

import pandas as pd
from datetime import datetime, date, timedelta
from backend.app.common.config.column_names import COLUMNS, VALUES
from backend.app.common.modules.utils import get_filing_date, safe_get_column


def evaluate_closed_row(row, today: date) -> tuple:
    """
    Оценивает своевременность закрытия дела в исковом производстве.

    Сравнивает дату закрытия дела с дедлайном в 125 календарных дней
    от даты подачи иска. Если дата закрытия отсутствует, проверяет
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
        # Получение даты подачи иска из данных дела
        filing_date = get_filing_date(row)
        if filing_date is None:
            return "no_data", False
        filing_date = filing_date.date()

        # Расчет дедлайна закрытия дела (125 календарных дней от подачи)
        deadline_date = filing_date + timedelta(days=125)

        # Безопасное получение даты закрытия дела
        closing_date_value = safe_get_column(row, COLUMNS["CASE_CLOSING_DATE"])

        if closing_date_value != "no_data" and pd.notna(closing_date_value):
            # Сравнение даты закрытия с дедлайном при наличии данных
            closing_date = pd.to_datetime(closing_date_value).date()

            if closing_date <= deadline_date:
                return "timely", True  # Дело закрыто в установленный срок
            else:
                return "overdue", True  # Дело закрыто с нарушением срока
        else:
            # Проверка текущего статуса при отсутствии даты закрытия
            if today > deadline_date:
                return "overdue", False  # Дедлайн закрытия истек
            else:
                return "timely", False  # Дедлайн закрытия еще не наступил

    except Exception:
        return "no_data", False


def evaluate_execution_document_received_row(row, documents_df: pd.DataFrame) -> tuple:
    """
    Оценивает получение исполнительного документа в исковом производстве.

    Использует данные из таблицы мониторинга документов для поиска
    исполнительного листа по коду дела и подразделению ПСИП.

    Args:
        row (pd.Series): Строка данных дела для оценки
        documents_df (pd.DataFrame): DataFrame с документами (резервный параметр)

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


def evaluate_decision_date_row(row, today: date) -> tuple:
    """
    Оценивает своевременность вынесения решения суда.

    Сравнивает дату вынесения решения с дедлайном в 45 календарных дней
    от даты принятия дела к производству.

    Args:
        row (pd.Series): Строка данных дела для оценки
        today (date): Текущая дата для сравнения с дедлайном

    Returns:
        tuple: Кортеж (status, is_completed) где:
            - status: 'timely', 'overdue' или 'no_data'
            - is_completed: True если решение вынесено, False если нет
    """
    try:
        # Получение даты принятия дела к производству
        decision_court_date_value = safe_get_column(row, COLUMNS["DECISION_COURT_DATE"])
        if decision_court_date_value == "no_data":
            return "no_data", False

        decision_court_date = pd.to_datetime(decision_court_date_value).date()

        # Расчет дедлайна вынесения решения (45 календарных дней)
        deadline_date = decision_court_date + timedelta(days=45)

        # Получение даты вынесения решения
        court_decision_date_value = safe_get_column(row, COLUMNS["COURT_DECISION_DATE"])

        if court_decision_date_value != "no_data" and pd.notna(court_decision_date_value):
            # Сравнение даты решения с дедлайном при наличии данных
            court_decision_date = pd.to_datetime(court_decision_date_value).date()

            if court_decision_date <= deadline_date:
                return "timely", True  # Решение вынесено в срок
            else:
                return "overdue", True  # Решение вынесено с просрочкой
        else:
            # Проверка текущего статуса при отсутствии даты решения
            if today > deadline_date:
                return "overdue", False  # Просрочено вынесение решения
            else:
                return "timely", False  # Время на вынесение решения еще есть

    except Exception:
        return "no_data", False


def evaluate_decision_receipt_row(row, today: date) -> tuple:
    """
    Оценивает своевременность получения решения суда.

    Сравнивает дату получения решения с дедлайном в 3 календарных дня
    от даты вынесения решения.

    Args:
        row (pd.Series): Строка данных дела для оценки
        today (date): Текущая дата для сравнения с дедлайном

    Returns:
        tuple: Кортеж (status, is_completed) где:
            - status: 'timely', 'overdue' или 'no_data'
            - is_completed: True если решение получено, False если нет
    """
    try:
        # Получение даты вынесения решения
        court_decision_date_value = safe_get_column(row, COLUMNS["COURT_DECISION_DATE"])
        if court_decision_date_value == "no_data":
            return "no_data", False

        court_decision_date = pd.to_datetime(court_decision_date_value).date()

        # Расчет дедлайна получения решения (3 календарных дня)
        deadline_date = court_decision_date + timedelta(days=3)

        # Получение даты получения решения
        decision_receipt_date_value = safe_get_column(row, COLUMNS["DECISION_RECEIPT_DATE"])

        if decision_receipt_date_value != "no_data" and pd.notna(decision_receipt_date_value):
            # Сравнение даты получения с дедлайном при наличии данных
            decision_receipt_date = pd.to_datetime(decision_receipt_date_value).date()

            if decision_receipt_date <= deadline_date:
                return "timely", True  # Решение получено в срок
            else:
                return "overdue", True  # Решение получено с просрочкой
        else:
            # Проверка текущего статуса при отсутствии даты получения
            if today > deadline_date:
                return "overdue", False  # Просрочено получение решения
            else:
                return "timely", False  # Время на получение решения еще есть

    except Exception:
        return "no_data", False


def evaluate_decision_transfer_row(row, today: date) -> tuple:
    """
    Оценивает своевременность передачи решения суда.

    Сравнивает дату передачи решения с дедлайном в 1 календарный день
    от даты вынесения решения.

    Args:
        row (pd.Series): Строка данных дела для оценки
        today (date): Текущая дата для сравнения с дедлайном

    Returns:
        tuple: Кортеж (status, is_completed) где:
            - status: 'timely', 'overdue' или 'no_data'
            - is_completed: True если решение передано, False если нет
    """
    try:
        # Получение даты вынесения решения
        court_decision_date_value = safe_get_column(row, COLUMNS["COURT_DECISION_DATE"])
        if court_decision_date_value == "no_data":
            return "no_data", False

        court_decision_date = pd.to_datetime(court_decision_date_value).date()

        # Расчет дедлайна передачи решения (1 календарный день)
        deadline_date = court_decision_date + timedelta(days=1)

        # Получение даты передачи решения
        actual_transfer_date_value = safe_get_column(row, COLUMNS["ACTUAL_TRANSFER_DATE"])

        if actual_transfer_date_value != "no_data" and pd.notna(actual_transfer_date_value):
            # Сравнение даты передачи с дедлайном при наличии данных
            actual_transfer_date = pd.to_datetime(actual_transfer_date_value).date()

            if actual_transfer_date <= deadline_date:
                return "timely", True  # Решение передано в срок
            else:
                return "overdue", True  # Решение передано с просрочкой
        else:
            # Проверка текущего статуса при отсутствии даты передачи
            if today > deadline_date:
                return "overdue", False  # Просрочена передача решения
            else:
                return "timely", False  # Время на передачу решения еще есть

    except Exception:
        return "no_data", False


def evaluate_next_hearing_present_row(row, today: date, calendar) -> tuple:
    """
    Оценивает своевременность назначения следующего заседания.

    Сравнивает дату следующего заседания с дедлайном в 3 рабочих дня
    от даты определения суда.

    Args:
        row (pd.Series): Строка данных дела для оценки
        today (date): Текущая дата для сравнения с дедлайном
        calendar: Объект календаря для расчета рабочих дней

    Returns:
        tuple: Кортеж (status, is_completed) где:
            - status: 'timely', 'overdue' или 'no_data'
            - is_completed: True если заседание назначено, False если нет
    """
    try:
        # Получение даты определения суда
        determination_date_value = safe_get_column(row, COLUMNS["DETERMINATION_DATE"])
        if determination_date_value == "no_data":
            return "no_data", False

        determination_date = pd.to_datetime(determination_date_value).date()

        # Расчет дедлайна назначения заседания (3 рабочих дня)
        deadline_date = calendar.add_working_days(determination_date, 3)

        # Получение даты следующего заседания
        next_hearing_date_value = safe_get_column(row, COLUMNS["NEXT_HEARING_DATE"])

        if next_hearing_date_value != "no_data" and pd.notna(next_hearing_date_value):
            # Сравнение даты заседания с дедлайном при наличии данных
            next_hearing_date = pd.to_datetime(next_hearing_date_value).date()

            if next_hearing_date <= deadline_date:
                return "timely", True  # Заседание назначено в срок
            else:
                return "overdue", True  # Заседание назначено с просрочкой
        else:
            # Проверка текущего статуса при отсутствии даты заседания
            if today > deadline_date:
                return "overdue", False  # Просрочено назначение заседания
            else:
                return "timely", False  # Время на назначение заседания еще есть

    except Exception:
        return "no_data", False


def evaluate_prev_to_next_hearing_row(row, calendar) -> tuple:
    """
    Оценивает соблюдение интервала между заседаниями.

    Проверяет что интервал между предыдущим и следующим заседанием
    не превышает 2 рабочих дня.

    Args:
        row (pd.Series): Строка данных дела для оценки
        calendar: Объект календаря для расчета рабочих дней

    Returns:
        tuple: Кортеж (status, is_completed) где:
            - status: 'timely', 'overdue' или 'no_data'
            - is_completed: True если обе даты заседаний заполнены
    """
    try:
        # Безопасное получение дат заседаний
        prev_hearing_value = safe_get_column(row, COLUMNS["PREVIOUS_HEARING_DATE"])
        next_hearing_value = safe_get_column(row, COLUMNS["NEXT_HEARING_DATE"])

        # Определение завершенности условия (обе даты заполнены)
        is_completed = (prev_hearing_value != "no_data" and next_hearing_value != "no_data")

        # Случай 1: Отсутствие данных о заседаниях
        if prev_hearing_value == "no_data" and next_hearing_value == "no_data":
            return "overdue", is_completed

        # Случай 2: Отсутствие даты предыдущего заседания
        if prev_hearing_value == "no_data" and next_hearing_value != "no_data":
            next_hearing_date = pd.to_datetime(next_hearing_value).date()
            today = date.today()

            deadline_date = calendar.add_working_days(next_hearing_date, 2)
            return "overdue" if today > deadline_date else "timely", is_completed

        # Случай 3 и 4: Наличие даты предыдущего заседания
        if prev_hearing_value != "no_data":
            prev_hearing_date = pd.to_datetime(prev_hearing_value).date()
            today = date.today()

            # Случай 3: Отсутствие даты следующего заседания
            if next_hearing_value == "no_data":
                deadline_date = calendar.add_working_days(prev_hearing_date, 2)
                return "overdue" if today > deadline_date else "timely", is_completed

            next_hearing_date = pd.to_datetime(next_hearing_value).date()

            # Проверка корректности дат (следующее заседание не может быть раньше предыдущего)
            if next_hearing_date < prev_hearing_date:
                deadline_date = calendar.add_working_days(prev_hearing_date, 2)
                return "overdue" if today > deadline_date else "timely", is_completed

            # Случай 4: Обе даты присутствуют и корректны
            working_days_between = calendar.get_working_days_between(prev_hearing_date, next_hearing_date)

            if working_days_between <= 2:
                return "timely", is_completed  # Интервал между заседаниями соблюден
            else:
                return "overdue", is_completed  # Интервал между заседаниями превышен

        return "no_data", is_completed

    except Exception:
        return "no_data", False


def evaluate_under_consideration_60days_row(row, today: date) -> tuple:
    """
    Оценивает продолжительность нахождения дела в рассмотрении.

    Проверяет что дело не находится в статусе 'UNDER_CONSIDERATION'
    дольше 60 календарных дней от даты подачи иска.

    Args:
        row (pd.Series): Строка данных дела для оценки
        today (date): Текущая дата для сравнения с дедлайном

    Returns:
        tuple: Кортеж (status, is_completed) где:
            - status: 'timely', 'overdue' или 'no_data'
            - is_completed: False (условие не может быть выполнено на этом этапе)
    """
    try:
        # Получение даты подачи иска
        filing_date = get_filing_date(row)
        if filing_date is None:
            return "no_data", False
        filing_date = filing_date.date()

        # Расчет максимального срока рассмотрения (60 календарных дней)
        deadline_date = filing_date + timedelta(days=60)

        # Сравнение текущей даты с максимальным сроком
        if today > deadline_date:
            return "overdue", False  # Превышен максимальный срок рассмотрения
        else:
            return "timely", False  # Срок рассмотрения в пределах нормы

    except Exception:
        return "no_data", False


def evaluate_court_reaction_row(row, today: date, calendar) -> tuple:
    """
    Оценивает своевременность получения реакции суда.

    Проверяет получение определения суда в течение 7 рабочих дней
    от даты подачи иска.

    Args:
        row (pd.Series): Строка данных дела для оценки
        today (date): Текущая дата для сравнения с дедлайном
        calendar: Объект календаря для расчета рабочих дней

    Returns:
        tuple: Кортеж (status, is_completed) где:
            - status: 'timely', 'overdue' или 'no_data'
            - is_completed: True если определение получено, False если нет
    """
    try:
        # Проверка наличия даты определения суда
        determination_date_value = safe_get_column(row, COLUMNS["DETERMINATION_DATE"])
        if determination_date_value != "no_data" and pd.notna(determination_date_value):
            return "timely", True  # Реакция суда уже получена

        # Получение даты подачи иска для расчета дедлайна
        filing_date = get_filing_date(row)
        if filing_date is None:
            return "no_data", False
        filing_date = filing_date.date()

        # Расчет дедлайна получения реакции суда (7 рабочих дней)
        deadline_date = calendar.add_working_days(filing_date, 7)

        # Проверка текущего статуса при отсутствии определения
        if today > deadline_date:
            return "overdue", False  # Просрочено получение реакции суда
        else:
            return "timely", False  # Время на получение реакции еще есть

    except Exception:
        return "no_data", False


def evaluate_first_status_changed_row(row, today: date) -> tuple:
    """
    Оценивает своевременность смены первоначального статуса дела.

    Проверяет смену статуса с 'PREPARING_DOCUMENTS' в течение
    14 календарных дней от даты подачи иска.

    Args:
        row (pd.Series): Строка данных дела для оценки
        today (date): Текущая дата для сравнения с дедлайном

    Returns:
        tuple: Кортеж (status, is_completed) где:
            - status: 'timely', 'overdue' или 'no_data'
            - is_completed: False (условие не может быть выполнено на этом этапе)
    """
    try:
        # Получение даты подачи иска
        filing_date = get_filing_date(row)
        if filing_date is None:
            return "no_data", False
        filing_date = filing_date.date()

        # Расчет дедлайна смены статуса (14 календарных дней)
        deadline_date = filing_date + timedelta(days=14)

        # Сравнение текущей даты с дедлайном смены статуса
        if today > deadline_date:
            return "overdue", False  # Просрочена смена статуса
        else:
            return "timely", False  # Время на смену статуса еще есть

    except Exception:
        return "no_data", False