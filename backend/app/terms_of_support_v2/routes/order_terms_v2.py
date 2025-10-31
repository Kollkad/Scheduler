# backend/app/terms_of_support_v2/routes/order_terms_v2.py
"""
Модуль маршрутов FastAPI для анализа сроков приказного производства (версия 2).

Содержит эндпоинты для:
- Анализа дел приказного производства с определением этапов и статусов мониторинга
- Формирования данных для диаграмм в формате совместимом с предыдущей версией
- Фильтрации дел по этапам и статусам для отображения в таблицах

Основные компоненты:
- Класс OrderChartAnalyzer: анализ данных для построения диаграмм
- Функция calculate_order_monitoring_status: расчет статусов мониторинга
- Эндпоинты API: /analyze_order_charts, /analyze_order, /filtered-cases
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, date
import pandas as pd

from backend.app.common.modules.data_manager import data_manager
from backend.app.common.routes.common import current_files
from backend.app.common.config.column_names import COLUMNS, VALUES
from backend.app.terms_of_support_v2.modules.terms_analyzer_v2 import prepare_case_data, build_production_table
from backend.app.terms_of_support_v2.modules.order_stage_v2 import assign_order_stages
from backend.app.terms_of_support_v2.modules.order_stage_checks_v2 import (
    check_exceptions_stage,
    check_closed_stage,
    check_execution_document_received_stage,
    check_court_reaction_stage,
    check_first_status_changed_stage,
)
from backend.app.common.config.terms_checks_config import ORDER_CHECKS_MAPPING
from backend.app.common.modules.utils import filter_production_cases

router = APIRouter()


class OrderChartAnalyzer:
    """
    Анализатор для преобразования данных приказного производства v2
    в формат совместимый с диаграммами предыдущей версии.

    Преобразует комбинированные статусы мониторинга в отдельные статистики по каждой проверке
    для построения столбчатых диаграмм на фронтенде.
    """

    def __init__(self, staged_df: pd.DataFrame):
        """
        Инициализация анализатора.

        Args:
            staged_df (pd.DataFrame): Таблица с данными о делах, содержащая колонки
                                     'caseStage' и 'monitoringStatus'
        """
        self.staged_df = staged_df

    def analyze_for_charts(self) -> list:
        """
        Анализ данных для построения диаграмм в формате предыдущей версии.

        Обрабатывает все этапы дел приказного производства, включая исключения.
        Собирает статистику по статусам timely/overdue/no_data для обычных этапов
        и по типам исключений для этапа исключений.

        Returns:
            List[Dict]: Список словарей с данными для диаграмм в формате:
                       [{"group_name": str, "values": [int, int, int, int]}, ...]
        """
        # Инициализация счетчиков статистики для всех проверок из конфигурации
        stats = {}
        for stage, checks in ORDER_CHECKS_MAPPING.items():
            for check in checks:
                # Особая инициализация для исключений
                if check == "exceptionStatus":
                    stats[check] = {
                        "reopened": 0,
                        "complaint_filed": 0,
                        "error_dublicate": 0,
                        "withdraw_by_the_initiator": 0
                    }
                else:
                    # Стандартная инициализация для обычных проверок
                    stats[check] = {"timely": 0, "overdue": 0, "no_data": 0}

        # Обработка каждой строки таблицы для сбора статистики
        for _, row in self.staged_df.iterrows():
            stage = row["caseStage"]
            status_str = row["monitoringStatus"]

            # Особая обработка для этапа исключений
            if stage == "exceptions":
                if status_str in stats.get("exceptionStatus", {}):
                    stats["exceptionStatus"][status_str] += 1
                continue

            # Стандартная обработка для остальных этапов
            if stage in ORDER_CHECKS_MAPPING:
                checks = ORDER_CHECKS_MAPPING[stage]
                statuses = status_str.split(";")

                # Обработка каждого статуса в комбинированной строке
                for i, status in enumerate(statuses):
                    if i < len(checks):
                        check_name = checks[i]
                        if status in stats[check_name]:
                            stats[check_name][status] += 1

        # Формирование результата в формате для фронтенда
        results = []
        for check_name, counts in stats.items():
            # Для проверки исключений используются типы исключений как значения
            if check_name == "exceptionStatus":
                results.append({
                    "group_name": check_name,
                    "values": [
                        counts.get("reopened", 0),
                        counts.get("complaint_filed", 0),
                        counts.get("error_dublicate", 0),
                        counts.get("withdraw_by_the_initiator", 0)
                    ]
                })
            else:
                # Для обычных проверок используется стандартный формат
                results.append({
                    "group_name": check_name,
                    "values": [
                        counts["timely"],
                        counts["overdue"],
                        0,  # Резервное значение для совместимости
                        counts["no_data"]
                    ]
                })

        return results


@router.get("/analyze_order_charts")
async def analyze_order_charts():
    """
    Эндпоинт для получения данных приказного производства в формате для диаграмм.

    Загружает детальный отчет, фильтрует дела приказного производства, создает таблицу v2
    и преобразует данные в формат совместимый с диаграммами предыдущей версии.

    Returns:
        Dict: Результат анализа с данными для диаграмм:
              {
                  "success": bool,
                  "data": List[Dict],  # Данные для диаграмм
                  "total_cases": int,  # Общее количество обработанных дел
                  "message": str       # Сообщение о результате выполнения
              }

    Raises:
        HTTPException: 404 если детальный отчет не загружен
        HTTPException: 500 при ошибках обработки данных
    """
    if not current_files["current_detailed_report"]:
        raise HTTPException(status_code=404, detail="Детальный отчет не загружен")

    try:
        # Проверка наличия кэшированных данных
        staged_df = data_manager.get_processed_data("order_staged")

        if staged_df is None:
            # Загрузка и обработка данных при отсутствии кэша
            df = data_manager.load_detailed_report(current_files["current_detailed_report"])
            df = filter_production_cases(df, 'order')
            staged_df = build_production_table(df, 'order')
            data_manager.set_processed_data("order_staged", staged_df)

        # Анализ данных для построения диаграмм
        analyzer = OrderChartAnalyzer(staged_df)
        chart_data = analyzer.analyze_for_charts()

        return {
            "success": True,
            "data": chart_data,
            "totalCases": len(staged_df),
            "message": "Данные для диаграмм приказного производства подготовлены"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")


@router.get("/analyze_order")
async def analyze_order_terms():
    """
    Эндпоинт для анализа приказного производства (версия 2).

    Выполняет полный анализ дел приказного производства с определением этапов
    и статусов мониторинга. Возвращает данные в формате v2.

    Returns:
        Dict: Результат анализа в формате v2:
              {
                  "success": bool,
                  "total_cases": int,
                  "data": List[Dict],  # Данные дел с этапами и статусами
                  "message": str
              }

    Raises:
        HTTPException: 404 если детальный отчет не загружен
        HTTPException: 500 при ошибках обработки данных
    """
    if not current_files["current_detailed_report"]:
        raise HTTPException(status_code=404, detail="Детальный отчет не загружен")

    try:
        # Проверка наличия кэшированных данных
        staged_df = data_manager.get_processed_data("order_staged")

        if staged_df is None:
            # Загрузка и обработка данных при отсутствии кэша
            df = data_manager.load_detailed_report(current_files["current_detailed_report"])
            df = filter_production_cases(df, 'order')
            staged_df = build_production_table(df, 'order')
            data_manager.set_processed_data("order_staged", staged_df)

        # Формирование основных данных без внутреннего столбца completion_status
        result_data = staged_df[["caseCode", "caseStage", "monitoringStatus"]].to_dict(orient="records")

        return {
            "success": True,
            "totalCases": len(staged_df),
            "data": result_data,
            "message": "Анализ приказного производства (v2) выполнен"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")


@router.get("/filtered-cases")
async def get_filtered_order_cases(stage: str = Query(...), status: str = Query(...)):
    """
    Фильтрация дел приказного производства по этапу и статусу мониторинга.

    Args:
        stage (str): Название проверки (например: first_status_14_days)
        status (str): Статус мониторинга (timely, overdue, no_data)

    Returns:
        Dict: Результат фильтрации с отфильтрованными делами и мета-информацией:
              {
                  "success": bool,
                  "stage": str,
                  "status": str,
                  "count": int,
                  "cases": List[Dict]
              }

    Raises:
        HTTPException: 404 если детальный отчет не загружен
        HTTPException: 400 если указана неизвестная проверка
        HTTPException: 500 при ошибках обработки данных
    """
    if not current_files["current_detailed_report"]:
        raise HTTPException(status_code=404, detail="Детальный отчет не загружен")

    # Получение кэшированных данных
    staged_df = data_manager.get_processed_data("order_staged")

    # Обработка данных при отсутствии кэша
    if staged_df is None:
        df = data_manager.load_detailed_report(current_files["current_detailed_report"])
        df = filter_production_cases(df, 'order')
        staged_df = build_production_table(df, 'order')
        data_manager.set_processed_data("order_staged", staged_df)

    # Определение базового этапа и индекса проверки
    base_stage = None
    check_index = None
    for stage_name, checks in ORDER_CHECKS_MAPPING.items():
        if stage in checks:
            base_stage = stage_name
            check_index = checks.index(stage)
            break

    if base_stage is None:
        raise HTTPException(status_code=400, detail=f"Неизвестная проверка: {stage}")

    # Векторная фильтрация данных по этапу и статусу
    mask = (
            (staged_df["caseStage"] == base_stage) &
            (staged_df["monitoringStatus"].str.split(";").str[check_index] == status)
    )
    filtered = staged_df[mask]

    # Формирование результата с подготовленными данными дел
    result_cases = [prepare_case_data(row, base_stage, status) for _, row in filtered.iterrows()]

    return {
        "success": True,
        "stage": stage,
        "status": status,
        "count": len(result_cases),
        "cases": result_cases
    }