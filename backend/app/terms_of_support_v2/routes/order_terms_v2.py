# backend/app/terms_of_support_v2/routes/order_terms_v2.py
"""
Модуль маршрутов для анализа сроков приказного производства.

Содержит эндпоинты для:
- Анализа дел приказного производства с определением этапов и статусов мониторинга
- Формирования данных для диаграмм в формате совместимом с предыдущей версией
- Фильтрации дел по этапам и статусам для отображения в таблицах

Основные компоненты:
- Класс OrderChartAnalyzer: анализ данных для построения диаграмм
- Функция calculate_order_monitoring_status: расчет статусов мониторинга
- Эндпоинты API: /analyze_order, /analyze_order_charts, /filtered-cases
"""

from fastapi import APIRouter, HTTPException, Query
import pandas as pd

from backend.app.data_management.modules.data_manager import data_manager
from backend.app.terms_of_support_v2.modules.terms_analyzer_v2 import prepare_case_data, build_production_table
from backend.app.common.config.terms_checks_config import ORDER_CHECKS_MAPPING
from backend.app.common.modules.utils import filter_production_cases

router = APIRouter()


class OrderChartAnalyzer:
    """
    Анализатор для преобразования данных приказного производства
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
        Анализ данных для построения диаграмм.

        Обрабатывает все этапы дел приказного производства, включая исключения.
        Собирает статистику по статусам timely/overdue/no_data для обычных этапов
        и по типам исключений для этапа исключений.

        Returns:
            List[Dict]: Список словачей с данными для диаграмм в формате:
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


@router.get("/analyze_order")
async def analyze_order_terms():
    """
    Эндпоинт для анализа приказного производства.
    Только этот эндпоинт имеет право загружать данные и выполнять анализ.

    Выполняет полный анализ дел приказного производства с определением этапов
    и статусов мониторинга.

    Returns:
        Dict: Результат анализа в формате v2:
              {
                  "success": bool,
                  "total_cases": int,
                  "data": List[Dict],
                  "message": str
              }

    Raises:
        HTTPException: 404 если детальный отчет не загружен
        HTTPException: 500 при ошибках обработки данных
    """
    try:
        # Проверка наличия загруженного отчета
        try:
            df = data_manager.load_detailed_report()
        except ValueError:
            raise HTTPException(status_code=404, detail="Детальный отчет не загружен")

        # Фильтрация и анализ данных
        df = filter_production_cases(df, 'order')
        staged_df = build_production_table(df, 'order')

        # Сохранение результатов в кэш
        data_manager.set_processed_data("order_staged", staged_df)

        # Формирование основных данных без внутреннего столбца completion_status
        result_data = staged_df[["caseCode", "caseStage", "monitoringStatus"]].to_dict(orient="records")

        return {
            "success": True,
            "totalCases": len(staged_df),
            "data": result_data,
            "message": "Анализ приказного производства выполнен"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")


@router.get("/analyze_order_charts")
async def analyze_order_charts():
    """
    Эндпоинт для получения данных приказного производства в формате для диаграмм.
    Использует только предварительно рассчитанные данные.

    Returns:
        Dict: Результат анализа с данными для диаграмм:
              {
                  "success": bool,
                  "data": List[Dict],  # Данные для диаграмм
                  "total_cases": int,  # Общее количество обработанных дел
                  "message": str       # Сообщение о результате выполнения
              }

    Raises:
        HTTPException: 404 если анализ не выполнен
        HTTPException: 500 при ошибках обработки данных
    """
    try:
        # Получение предварительно рассчитанных данных
        staged_df = data_manager.get_processed_data("order_staged")

        if staged_df is None:
            raise HTTPException(
                status_code=404,
                detail="Анализ приказного производства не выполнен. Сначала вызовите /analyze_order"
            )

        # Анализ данных для построения диаграмм
        analyzer = OrderChartAnalyzer(staged_df)
        chart_data = analyzer.analyze_for_charts()

        return {
            "success": True,
            "data": chart_data,
            "totalCases": len(staged_df),
            "message": "Данные для диаграмм приказного производства подготовлены"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")


@router.get("/filtered-cases")
async def get_filtered_order_cases(stage: str = Query(...), status: str = Query(...)):
    """
    Фильтрация дел приказного производства по этапу и статусу мониторинга.
    Использует только предварительно рассчитанные данные.

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
        HTTPException: 404 если анализ не выполнен
        HTTPException: 400 если указана неизвестная проверка
        HTTPException: 500 при ошибках обработки данных
    """
    try:
        # Получение предварительно рассчитанных данных
        staged_df = data_manager.get_processed_data("order_staged")

        if staged_df is None:
            raise HTTPException(
                status_code=404,
                detail="Анализ приказного производства не выполнен. Сначала вызовите /analyze_order"
            )

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

        # Фильтрация данных по этапу и статусу
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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка фильтрации: {str(e)}")