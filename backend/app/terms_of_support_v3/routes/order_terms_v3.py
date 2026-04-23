# backend/app/terms_of_support_v3/routes/order_terms_v3.py
"""
Модуль маршрутов для анализа сроков приказного производства (v3).

Содержит эндпоинты для:
- Анализа дел приказного производства с определением этапов и статусов мониторинга
- Формирования данных для диаграмм
- Фильтрации дел по этапам и статусам для отображения в таблицах
"""

from fastapi import APIRouter, HTTPException, Query
import pandas as pd

from backend.app.data_management.modules.normalized_data_manager import normalized_manager
from backend.app.common.modules.utils import filter_production_cases
from backend.app.terms_of_support_v3.modules.order_stage_checks_v3 import analyze_order, _assign_order_stages
from backend.app.terms_of_support_v3.modules.terms_analyzer_v3 import prepare_filtered_cases_response
from backend.app.common.config.column_names import COLUMNS, VALUES

router = APIRouter()

class OrderChartAnalyzerV3:
    """
    Анализатор для преобразования данных check_results в формат для диаграмм.

    Анализирует результаты проверок и формирует статистику по каждому checkCode.
    """

    def __init__(self, check_results_df: pd.DataFrame, total_cases: int):
        """
        Инициализация анализатора.

        Args:
            check_results_df (pd.DataFrame): DataFrame с результатами проверок.
            total_cases (int): Общее количество дел приказного производства.
        """
        self.check_results_df = check_results_df
        self.total_cases = total_cases

    def analyze_for_charts(self) -> list:
        """
        Формирует данные для диаграмм на основе check_results.

        Returns:
            list: Список словарей с данными для диаграмм в формате:
                  [{"group_name": str, "values": [int, int, int, int]}, ...]
        """
        if self.check_results_df.empty:
            return []

        results = []

        # Группировка по checkCode
        for check_code, group in self.check_results_df.groupby("checkCode"):
            status_counts = group["monitoringStatus"].value_counts()

            if check_code == "exceptionsO":
                # Для исключений особая обработка
                values = [
                    int(status_counts.get("reopened", 0)),
                    int(status_counts.get("complaint_filed", 0)),
                    int(status_counts.get("error_dublicate", 0)),
                    int(status_counts.get("withdraw_by_the_initiator", 0)),
                ]
            else:
                # Для обычных проверок
                values = [
                    int(status_counts.get("timely", 0)),
                    int(status_counts.get("overdue", 0)),
                    0,  # Резервное значение для совместимости
                    int(status_counts.get("no_data", 0)),
                ]

            results.append({
                "group_name": check_code,
                "values": [int(v) for v in values]
            })

        return results


@router.get("/analyze_order")
async def analyze_order_terms():
    """
    Запускает процесс анализа дел приказного производства.

    Выполняет:
    1. Загрузку детального отчета через NormalizedDataManager
    2. Инициализацию колонки stageCode в исходных данных (если отсутствует)
    3. Присвоение stageCode для приказных дел
    4. Фильтрацию приказных дел
    5. Анализ с выполнением проверок
    6. Сохранение результатов в NormalizedDataManager

    Returns:
        Dict: Результат анализа
    """
    try:
        df = normalized_manager.get_or_load_detailed_report()
        if df.empty:
            return {"success": True, "totalCases": 0, "message": "Детальный отчет пуст"}

        # Инициализация колонки stageCode в исходных данных
        if "stageCode" not in df.columns:
            df["stageCode"] = pd.NA

        # Присвоение stageCode только для приказных дел
        order_mask = df[COLUMNS["METHOD_OF_PROTECTION"]] == VALUES["ORDER_PRODUCTION"]
        df.loc[order_mask, "stageCode"] = _assign_order_stages(df[order_mask])

        # Фильтрация приказных дел для анализа
        df_order = df[order_mask].copy()
        if df_order.empty:
            return {"success": True, "totalCases": 0, "message": "Нет дел приказного производства"}

        # Анализ (stageCode уже есть в df_order, analyze_order не добавляет её повторно)
        check_results_df = analyze_order(df_order)
        normalized_manager.set_check_results_data(check_results_df, analysis_type="order")

        return {
            "success": True,
            "totalCases": len(df_order),
            "message": f"Анализ приказного производства выполнен. Обработано {len(df_order)} дел"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")


@router.get("/analyze_order_charts")
async def analyze_order_charts():
    """
    Предоставляет данные приказного производства в формате для диаграмм.

    Использует предварительно рассчитанные результаты проверок.

    Returns:
        Dict: Результат с данными для диаграмм:
              {
                  "success": bool,
                  "data": List[Dict],
                  "totalCases": int,
                  "message": str
              }
    """
    try:
        check_results_df = normalized_manager.get_check_results_data()
        cases_df = normalized_manager.get_cases_data()

        # Проверка наличия данных
        if check_results_df.empty or cases_df.empty:
            raise HTTPException(
                status_code=404,
                detail="Анализ приказного производства не выполнен. Сначала вызовите /analyze_order"
            )

        check_results_df = check_results_df[
            check_results_df["checkCode"].str.endswith("O", na=False) |
            (check_results_df["checkCode"] == "exceptionsO")
            ]

        # Определение общего количества дел приказного производства
        cases_df = filter_production_cases(cases_df, 'order')
        total_cases = len(cases_df)

        # Анализ данных для диаграмм
        analyzer = OrderChartAnalyzerV3(check_results_df, total_cases)
        chart_data = analyzer.analyze_for_charts()

        return {
            "success": True,
            "data": chart_data,
            "totalCases": total_cases,
            "message": "Данные для диаграмм подготовлены"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка подготовки данных для диаграмм: {str(e)}")


@router.get("/filtered-cases")
async def get_filtered_order_cases(
    stage: str = Query(..., description="Код проверки (например: closedO, courtReactionO)"),
    status: str = Query(..., description="Статус мониторинга (timely, overdue, no_data, reopened, ...)")
):
    """
    Фильтрация дел приказного производства по проверке и статусу мониторинга.

    Args:
        stage (str): Код проверки (checkCode из конфига)
        status (str): Статус мониторинга

    Returns:
        Dict: Результат фильтрации:
              {
                  "success": bool,
                  "stage": str,
                  "status": str,
                  "count": int,
                  "cases": List[Dict]
              }
    """
    try:
        check_results_df = normalized_manager.get_check_results_data()
        cases_df = normalized_manager.get_cases_data()

        # Проверка наличия данных
        if check_results_df.empty or cases_df.empty:
            raise HTTPException(
                status_code=404,
                detail="Анализ приказного производства не выполнен. Сначала вызовите /analyze_order"
            )

        # Фильтрация check_results по checkCode и monitoringStatus
        filtered_results = check_results_df[
            (check_results_df["checkCode"] == stage) &
            (check_results_df["monitoringStatus"] == status)
        ]

        if filtered_results.empty:
            return {
                "success": True,
                "stage": stage,
                "status": status,
                "count": 0,
                "cases": []
            }

        # Фильтрация дел приказного производства
        cases_df = filter_production_cases(cases_df, 'order')

        # Объединение с данными дел
        merged = filtered_results.merge(
            cases_df,
            left_on="targetId",
            right_on=COLUMNS["CASE_CODE"],
            how="inner"
        )

        if merged.empty:
            return {
                "success": True,
                "stage": stage,
                "status": status,
                "count": 0,
                "cases": []
            }

        # Добавление колонки stageCode для совместимости с prepare_filtered_cases_response
        merged["stageCode"] = stage

        # Подготовка ответа
        result_cases = prepare_filtered_cases_response(merged)

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








