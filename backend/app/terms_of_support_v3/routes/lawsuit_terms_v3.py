# backend/app/terms_of_support_v3/routes/lawsuit_terms_v3.py
"""
Модуль маршрутов для анализа сроков искового производства (v3).

Содержит эндпоинты для:
- Анализа дел искового производства с определением этапов и статусов мониторинга
- Формирования данных для диаграмм
- Фильтрации дел по этапам и статусам для отображения в таблицах
"""

from fastapi import APIRouter, HTTPException, Query
import pandas as pd

from backend.app.data_management.modules.normalized_data_manager import normalized_manager
from backend.app.common.modules.utils import filter_production_cases
from backend.app.terms_of_support_v3.modules.lawsuit_stage_checks_v3 import analyze_lawsuit, _assign_lawsuit_stages
from backend.app.terms_of_support_v3.modules.terms_analyzer_v3 import prepare_filtered_cases_response
from backend.app.common.config.column_names import COLUMNS, VALUES

router = APIRouter()


class LawsuitChartAnalyzerV3:
    """
    Анализатор для преобразования данных check_results в формат для диаграмм.

    Анализирует результаты проверок и формирует статистику по каждому checkCode.
    """

    def __init__(self, check_results_df: pd.DataFrame, total_cases: int):
        """
        Инициализация анализатора.

        Args:
            check_results_df (pd.DataFrame): DataFrame с результатами проверок.
            total_cases (int): Общее количество дел искового производства.
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

            if check_code == "exceptionsL":
                # Для исключений особая обработка
                values = [
                    status_counts.get("reopened", 0),
                    status_counts.get("complaint_filed", 0),
                    status_counts.get("error_dublicate", 0),
                    status_counts.get("withdraw_by_the_initiator", 0),
                ]
            else:
                # Для обычных проверок
                values = [
                    status_counts.get("timely", 0),
                    status_counts.get("overdue", 0),
                    0,  # Резервное значение для совместимости
                    status_counts.get("no_data", 0),
                ]

            results.append({
                "group_name": check_code,
                "values": [int(v) for v in values]
            })

        return results


@router.get("/analyze_lawsuit")
async def analyze_lawsuit_terms():
    """
    Запускает процесс анализа дел искового производства.

    Выполняет:
    1. Загрузку детального отчета через NormalizedDataManager
    2. Инициализацию колонки stageCode в исходных данных (если отсутствует)
    3. Присвоение stageCode для исковых дел (дополняет已有的 приказные)
    4. Фильтрацию исковых дел
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

        # Присвоение stageCode только для исковых дел (не затрагивает приказные)
        lawsuit_mask = df[COLUMNS["METHOD_OF_PROTECTION"]] == VALUES["CLAIM_PROCEEDINGS"]
        df.loc[lawsuit_mask, "stageCode"] = _assign_lawsuit_stages(df[lawsuit_mask])

        # Фильтрация исковых дел для анализа
        df_lawsuit = df[lawsuit_mask].copy()
        if df_lawsuit.empty:
            return {"success": True, "totalCases": 0, "message": "Нет дел искового производства"}

        # Анализ (stageCode уже есть в df_lawsuit, analyze_lawsuit не добавляет её повторно)
        check_results_df = analyze_lawsuit(df_lawsuit)
        normalized_manager.set_check_results_data(check_results_df, analysis_type="lawsuit")

        return {
            "success": True,
            "totalCases": len(df_lawsuit),
            "message": f"Анализ искового производства выполнен. Обработано {len(df_lawsuit)} дел"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")


@router.get("/analyze_lawsuit_charts")
async def analyze_lawsuit_charts():
    """
    Предоставляет данные искового производства в формате для диаграмм.

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
                detail="Анализ искового производства не выполнен. Сначала вызовите /analyze_lawsuit"
            )

        check_results_df = check_results_df[
            check_results_df["checkCode"].str.endswith("L", na=False) |
            (check_results_df["checkCode"] == "exceptionsL")
            ]

        # Определение общего количества дел искового производства
        cases_df = filter_production_cases(cases_df, 'lawsuit')
        total_cases = len(cases_df)

        # Анализ данных для диаграмм
        analyzer = LawsuitChartAnalyzerV3(check_results_df, total_cases)
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
async def get_filtered_cases(
    stage: str = Query(..., description="Код проверки (например: closedL, decisionDateL)"),
    status: str = Query(..., description="Статус мониторинга (timely, overdue, no_data, reopened, ...)")
):
    """
    Фильтрация дел искового производства по проверке и статусу мониторинга.

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

        if check_results_df.empty or cases_df.empty:
            raise HTTPException(
                status_code=404,
                detail="Анализ искового производства не выполнен. Сначала вызовите /analyze_lawsuit"
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

        # Фильтрация дел искового производства
        cases_df = filter_production_cases(cases_df, 'lawsuit')

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

        merged["stageCode"] = stage
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




