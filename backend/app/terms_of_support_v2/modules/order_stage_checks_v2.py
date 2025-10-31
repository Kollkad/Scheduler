# backend/app/terms_of_support_v2/modules/order_stage_checks_v2.py
"""
Модуль проверок этапов для приказного производства (версия 2).

Содержит функции для проверки соблюдения сроков на различных этапах приказного производства.
Каждая функция соответствует определенному этапу дела и объединяет результаты проверок
в комбинированную строку статуса мониторинга.

Основные этапы проверок:
- Исключения (exceptions)
- Закрытие дела (closed)
- Получение исполнительного документа (executionDocumentReceived)
- Реакция суда (courtReaction)
- Смена статуса (firstStatusChanged)
"""

from datetime import date
from typing import List, Tuple
import pandas as pd
from backend.app.common.modules.utils import evaluate_exceptions_row
from backend.app.terms_of_support_v2.modules.order_row_analyzer_v2 import (
    evaluate_order_closed_row,
    evaluate_order_execution_document_row,
    evaluate_order_court_reaction_row,
    evaluate_order_first_status_row,
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
    Проверка этапа исключений для приказного производства.

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
    Проверка этапа закрытия дела приказного производства.

    Контролирует соблюдение срока закрытия дела (90 календарных дней от даты подачи заявления).
    Использует специализированную функцию проверки закрытия для приказного производства.

    Args:
        row (pd.Series): Строка данных дела
        today (date): Текущая дата для расчетов сроков

    Returns:
        Tuple[str, str]: Кортеж (monitoring_status, completion_status) где:
            - monitoring_status: комбинированный статус проверки закрытия дела
            - completion_status: комбинированный статус выполнения условий
    """
    # Вызов функции проверки закрытия дела для приказного производства
    status, is_completed = evaluate_order_closed_row(row, today)
    return _combine_results([status]), _combine_completion_statuses([is_completed])


def check_execution_document_received_stage(row: pd.Series, today: date) -> Tuple[str, str]:
    """
    Проверка этапа получения исполнительного документа.

    Функция для проверки получения исполнительного документа.
    Функциональность будет реализована после интеграции с модулем обработки документов.

    Args:
        row (pd.Series): Строка данных дела
        today (date): Текущая дата для расчетов (не используется в заглушке)

    Returns:
        Tuple[str, str]: Кортеж (monitoring_status, completion_status) где:
            - monitoring_status: комбинированный статус проверки получения документа
            - completion_status: комбинированный статус выполнения условий
    """
    # Вызов функции для проверки получения исполнительного документа
    status, is_completed = evaluate_order_execution_document_row(row, today)
    return _combine_results([status]), _combine_completion_statuses([is_completed])


def check_court_reaction_stage(row: pd.Series, today: date) -> Tuple[str, str]:
    """
    Проверка этапа реакции суда в приказном производстве.

    Контролирует получение реакции суда в течение 60 календарных дней от даты подачи заявления.
    Проверяет выполнение всех условий: вынесение судебного приказа, заполнение дат получения/передачи ИД,
    установление статуса "Условно закрыто".

    Args:
        row (pd.Series): Строка данных дела
        today (date): Текущая дата для расчетов сроков

    Returns:
        Tuple[str, str]: Кортеж (monitoring_status, completion_status) где:
            - monitoring_status: комбинированный статус проверки реакции суда
            - completion_status: комбинированный статус выполнения условий
    """
    # Вызов функции проверки реакции суда для приказного производства
    status, is_completed = evaluate_order_court_reaction_row(row, today)
    return _combine_results([status]), _combine_completion_statuses([is_completed])


def check_first_status_changed_stage(row: pd.Series, today: date) -> Tuple[str, str]:
    """
    Проверка этапа смены первоначального статуса дела.

    Контролирует смену статуса с "Подготовка документов" на "Ожидание реакции суда"
    в течение 14 календарных дней от даты подачи заявления.

    Args:
        row (pd.Series): Строка данных дела
        today (date): Текущая дата для расчетов сроков

    Returns:
        Tuple[str, str]: Кортеж (monitoring_status, completion_status) где:
            - monitoring_status: комбинированный статус проверки смены статуса
            - completion_status: комбинированный статус выполнения условий
    """
    # Вызов функции проверки смены статуса для приказного производства
    status, is_completed = evaluate_order_first_status_row(row, today)
    return _combine_results([status]), _combine_completion_statuses([is_completed])