# backend/app/terms_of_support_v2/modules/lawsuit_stage_checks_v2.py
"""
Модуль проверок этапов для искового производства (версия 2).

Содержит функции для проверки соблюдения сроков на различных этапах искового производства.
Каждая функция соответствует определенному этапу дела и объединяет результаты проверок
в комбинированную строку статуса мониторинга.

Основные этапы проверок:
- Исключения (exceptions)
- Закрытие дела (closed)
- Получение исполнительного документа (executionDocumentReceived)
- Вынесение решения (decisionMade)
- Рассмотрение дела (underConsideration)
- Реакция суда (courtReaction)
- Смена статуса (firstStatusChanged)
"""

from datetime import date
from typing import List, Tuple
import pandas as pd
from backend.app.common.modules.utils import evaluate_exceptions_row
from .lawsuit_row_analyzer_v2 import (
    # Closed
    evaluate_closed_row,
    # Execution document
    evaluate_execution_document_received_row,
    # Decision made
    evaluate_decision_date_row,
    evaluate_decision_receipt_row,
    evaluate_decision_transfer_row,
    # Under consideration
    evaluate_next_hearing_present_row,
    evaluate_prev_to_next_hearing_row,
    evaluate_under_consideration_60days_row,
    # Court reaction
    evaluate_court_reaction_row,
    # First status changed
    evaluate_first_status_changed_row,
)


def _combine_results(results: List[str]) -> str:
    """
    Объединяет список результатов проверок в единую строку monitoring_status.

    Функция используется для формирования комбинированного статуса, содержащего
    результаты всех проверок текущего этапа в формате "status1;status2;status3".

    Args:
        results (List[str]): Список строковых результатов проверок

    Returns:
        str: Комбинированная строка статусов или "no_data" при пустом списке
    """
    return ";".join(results) if results else "no_data"


def _combine_completion_statuses(completion_statuses: List[bool]) -> str:
    """
    Объединяет список флагов выполнения в строку для completion_status.

    Пример: [True, False, True] → "true;false;true"

    Args:
        completion_statuses (List[bool]): Список флагов выполнения проверок

    Returns:
        str: Комбинированная строка флагов выполнения или "false" при пустом списке
    """
    return ";".join(str(status).lower() for status in completion_statuses) if completion_statuses else "false"


def check_exceptions_stage(row: pd.Series, today: date) -> Tuple[str, str]:
    """
    Проверка этапа исключений для искового производства.

    Анализирует дела с особыми статусами, которые не подлежат стандартной проверке сроков.
    Использует универсальную функцию проверки исключений, общую для искового и приказного производства.

    Args:
        row (pd.Series): Строка данных дела
        today (date): Текущая дата для расчетов (не используется в этой проверке)

    Returns:
        Tuple[str, str]: Кортеж (monitoring_status, completion_status) где:
            - monitoring_status: комбинированный статус проверки исключений
            - completion_status: комбинированный статус выполнения условий
    """
    # Вызов универсальной функции проверки исключений
    result = evaluate_exceptions_row(row)
    # Для exceptions всегда считаем условие выполненным (не требуем действий)
    return _combine_results([result]), _combine_completion_statuses([True])


def check_closed_stage(row: pd.Series, today: date) -> Tuple[str, str]:
    """
    Проверка этапа закрытия дела искового производства.

    Контролирует соблюдение срока закрытия дела (125 календарных дней от даты подачи иска).
    Использует специализированную функцию проверки закрытия для искового производства.

    Args:
        row (pd.Series): Строка данных дела
        today (date): Текущая дата для расчетов сроков

    Returns:
        Tuple[str, str]: Кортеж (monitoring_status, completion_status) где:
            - monitoring_status: комбинированный статус проверки закрытия дела
            - completion_status: комбинированный статус выполнения условий
    """
    # Вызов функции проверки закрытия дела для искового производства
    status, is_completed = evaluate_closed_row(row, today)
    return _combine_results([status]), _combine_completion_statuses([is_completed])


def check_execution_document_received_stage(row: pd.Series, today: date) -> Tuple[str, str]:
    """
    Проверка этапа получения исполнительного документа.

    Временная заглушка для проверки получения исполнительного документа.
    Функциональность будет реализована после интеграции с модулем обработки документов.

    Args:
        row (pd.Series): Строка данных дела
        today (date): Текущая дата для расчетов (не используется в заглушке)

    Returns:
        Tuple[str, str]: Кортеж (monitoring_status, completion_status) где:
            - monitoring_status: комбинированный статус проверки получения документа
            - completion_status: комбинированный статус выполнения условий
    """
    # Вызов временной заглушки для проверки получения исполнительного документа
    status, is_completed = evaluate_execution_document_received_row(row, None)
    return _combine_results([status]), _combine_completion_statuses([is_completed])


def check_decision_made_stage(row: pd.Series, today: date) -> Tuple[str, str]:
    """
    Проверка этапа вынесения решения суда.

    Контролирует соблюдение сроков на этапе вынесения и обработки судебного решения:
    1. Срок между датой решения суда и датой получения решения (<= 45 дней)
    2. Срок между датой получения решения и датой передачи решения (<= 3 дня)
    3. Срок между датой получения решения и датой фактической передачи (<= 1 день)

    Args:
        row (pd.Series): Строка данных дела
        today (date): Текущая дата для расчетов сроков

    Returns:
        Tuple[str, str]: Кортеж (monitoring_status, completion_status) где:
            - monitoring_status: комбинированный статус трех проверок сроков
            - completion_status: комбинированный статус выполнения условий
    """
    # Проверка срока между датой решения и получением решения
    status1, completed1 = evaluate_decision_date_row(row, today)
    # Проверка срока между получением и передачей решения
    status2, completed2 = evaluate_decision_receipt_row(row, today)
    # Проверка срока между получением и фактической передачей решения
    status3, completed3 = evaluate_decision_transfer_row(row, today)

    statuses = [status1, status2, status3]
    completions = [completed1, completed2, completed3]

    return _combine_results(statuses), _combine_completion_statuses(completions)


def check_under_consideration_stage(row: pd.Series, today: date, calendar) -> Tuple[str, str]:
    """
    Проверка этапа рассмотрения дела в суде.

    Контролирует соблюдение процессуальных сроков на этапе судебного рассмотрения:
    1. Назначение следующего заседания в течение 3 рабочих дней после определения
    2. Интервал между предыдущим и следующим заседанием (<= 2 рабочих дня)
    3. Общий срок рассмотрения дела от даты подачи иска (<= 60 календарных дней)

    Args:
        row (pd.Series): Строка данных дела
        today (date): Текущая дата для расчетов сроков
        calendar: Объект календаря для расчета рабочих дней

    Returns:
        Tuple[str, str]: Кортеж (monitoring_status, completion_status) где:
            - monitoring_status: комбинированный статус трех проверок сроков
            - completion_status: комбинированный статус выполнения условий
    """
    # Проверка назначения следующего заседания
    status1, completed1 = evaluate_next_hearing_present_row(row, today, calendar)
    # Проверка интервала между заседаниями
    status2, completed2 = evaluate_prev_to_next_hearing_row(row, calendar)
    # Проверка общего срока рассмотрения дела
    status3, completed3 = evaluate_under_consideration_60days_row(row, today)

    statuses = [status1, status2, status3]
    completions = [completed1, completed2, completed3]

    return _combine_results(statuses), _combine_completion_statuses(completions)


def check_court_reaction_stage(row: pd.Series, today: date, calendar) -> Tuple[str, str]:
    """
    Проверка этапа реакции суда на поданные документы.

    Контролирует получение реакции суда в течение 7 рабочих дней от даты подачи иска.
    Проверяет наличие определения суда по делу в установленные сроки.

    Args:
        row (pd.Series): Строка данных дела
        today (date): Текущая дата для расчетов сроков
        calendar: Объект календаря для расчета рабочих дней

    Returns:
        Tuple[str, str]: Кортеж (monitoring_status, completion_status) где:
            - monitoring_status: комбинированный статус проверки реакции суда
            - completion_status: комбинированный статус выполнения условий
    """
    # Вызов функции проверки реакции суда для искового производства
    status, is_completed = evaluate_court_reaction_row(row, today, calendar)
    return _combine_results([status]), _combine_completion_statuses([is_completed])


def check_first_status_changed_stage(row: pd.Series, today: date) -> Tuple[str, str]:
    """
    Проверка этапа смены первоначального статуса дела.

    Контролирует смену статуса с "Подготовка документов" на следующий этап
    в течение 14 календарных дней от даты подачи иска.

    Args:
        row (pd.Series): Строка данных дела
        today (date): Текущая дата для расчетов сроков

    Returns:
        Tuple[str, str]: Кортеж (monitoring_status, completion_status) где:
            - monitoring_status: комбинированный статус проверки смены статуса
            - completion_status: комбинированный статус выполнения условий
    """
    # Вызов функции проверки смены статуса для искового производства
    status, is_completed = evaluate_first_status_changed_row(row, today)
    return _combine_results([status]), _combine_completion_statuses([is_completed])