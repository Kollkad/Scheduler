# backend/app/rainbow/routes/rainbow.py
"""
Модуль маршрутов FastAPI для анализа данных по цветовой классификации (радуга).

Содержит эндпоинты для цветовой классификации дел и фильтрации по цветовым категориям.
Обеспечивает интеграцию с модулем RainbowClassifier для анализа данных и предоставляет
API для получения статистики и детальной информации по делам различных цветовых категорий.

Основные эндпоинты:
- /analyze: Анализ данных и добавление цветовой колонки в источник данных
- /fill-diagram: Получение данных для заполнения диаграммы распределения по цветам
- /cases-by-color: Фильтрация дел по цветовым категориям
- /quick-test: Тестовые данные для разработки
"""

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, List, Optional, Any

router = APIRouter(prefix="/api/rainbow", tags=["rainbow"])

from backend.app.data_management.modules.normalized_data_manager import normalized_manager
from backend.app.rainbow.modules.rainbow_classifier import (
    add_rainbow_color_column,
    get_rainbow_filtered_dataframe
)
from backend.app.common.config.column_names import COLUMNS, VALUES

# Маппинг цветовых категорий для преобразования английских кодов в русские названия
COLOR_MAPPING = {
    "ik": "ИК",
    "gray": "Серый",
    "green": "Зеленый",
    "yellow": "Желтый",
    "orange": "Оранжевый",
    "blue": "Синий",
    "red": "Красный",
    "purple": "Лиловый",
    "white": "Белый"
}


@router.get("/analyze")
async def analyze_rainbow():
    """
    Выполняет расчет и добавление цветовой классификации в данные дел.

    Функция реализует:
    1. Загрузку детального отчета через NormalizedDataManager
    2. Добавление колонки с цветовой категорией
    3. Сохранение обновленного DataFrame обратно в менеджер

    Returns:
        Dict: Результат подготовки данных в формате: {
            "success": bool,
            "message": str,
            "totalCases": int,
            "coloredCases": int
        }

    Raises:
        HTTPException: 404 если детальный отчет не загружен в систему
        HTTPException: 500 при возникновении ошибок обработки данных
    """
    try:
        df = normalized_manager.get_or_load_detailed_report()

        if df is None or df.empty:
            raise HTTPException(
                status_code=404,
                detail="Детальный отчет не загружен или пуст"
            )

        # Добавление цветовой колонки
        df_with_color = add_rainbow_color_column(df)

        # Сохранение обновленного DataFrame
        normalized_manager.set_cases_data(df_with_color)

        # Подсчет количества классифицированных дел (имеющих цвет)
        color_column = COLUMNS["CURRENT_PERIOD_COLOR"]
        colored_count = df_with_color[color_column].notna().sum() if color_column in df_with_color.columns else 0

        return {
            "success": True,
            "message": "Цветовая классификация выполнена успешно",
            "totalCases": len(df_with_color),
            "coloredCases": int(colored_count)
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ОШИБКА ПОДГОТОВКИ ДАННЫХ РАДУГИ: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка подготовки данных: {str(e)}")


@router.get("/fill-diagram")
@router.post("/fill-diagram")
async def fill_diagram(
        filters: Optional[Dict[str, Any]] = Body(None, embed=True)
):
    """
    Возвращает данные для построения диаграммы распределения дел по цветовым категориям.

    Args:
        filters (Optional[Dict[str, Any]]): Фильтры для применения к данным в формате:
            {
                "field_name1": "value1",
                "field_name2": "value2",
                ...
            }
            Поддерживаемые поля: caseCode, responsibleExecutor, gosb,
            courtProtectionMethod, courtReviewingCase, caseStatus

    Returns:
        Dict: Данные для визуализации диаграммы в формате: {
            "success": bool,
            "data": List[int],      # Количества дел по цветам в стандартном порядке
            "totalCases": int,      # Общее количество (отфильтрованных) дел
            "filtered": bool,       # Применены ли фильтры
            "filters": Dict,        # Примененные фильтры (если есть)
            "colorLabels": List[str], # Метки цветов на русском
            "message": str          # Описательное сообщение о результате
        }

    Raises:
        HTTPException: 400 если данные не загружены
        HTTPException: 500 при возникновении ошибок расчета статистики
    """
    try:
        df = normalized_manager.get_cases_data()

        if df is None or df.empty:
            raise HTTPException(
                status_code=400,
                detail="Данные дел не загружены. Сначала загрузите детальный отчет"
            )

        # Проверка наличия цветовой колонки
        color_column = COLUMNS["CURRENT_PERIOD_COLOR"]
        if color_column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail="Цветовая классификация не выполнена. Сначала вызовите /api/rainbow/analyze"
            )

        # Применение фильтрации по правилам радуги
        working_df = get_rainbow_filtered_dataframe(df)

        if working_df.empty:
            color_order = list(COLOR_MAPPING.values())
            return {
                "success": True,
                "data": [0] * len(color_order),
                "totalCases": 0,
                "filtered": False,
                "colorLabels": color_order,
                "message": "Нет дел, удовлетворяющих условиям радуги"
            }

        # Применение пользовательских фильтров
        filtered = False
        if filters and isinstance(filters, dict):
            filtered_df = working_df.copy()
            filters_applied = 0

            # Маппинг полей фильтра к колонкам DataFrame
            field_mapping = {
                "caseCode": COLUMNS["CASE_CODE"],
                "responsibleExecutor": COLUMNS["RESPONSIBLE_EXECUTOR"],
                "gosb": COLUMNS["GOSB"],
                "courtProtectionMethod": COLUMNS["METHOD_OF_PROTECTION"],
                "courtReviewingCase": COLUMNS["COURT"],
                "caseStatus": COLUMNS["CASE_STATUS"],
                "currentPeriodColor": COLUMNS["CURRENT_PERIOD_COLOR"],
            }

            for field_name, filter_value in filters.items():
                if field_name not in field_mapping:
                    continue

                col_name = field_mapping[field_name]
                if col_name not in filtered_df.columns:
                    continue

                if filter_value and isinstance(filter_value, str):
                    try:
                        mask = filtered_df[col_name].astype(str).str.strip() == str(filter_value).strip()
                        filtered_df = filtered_df[mask]
                        filters_applied += 1
                    except Exception as filter_error:
                        print(f"  ⚠️ Ошибка применения фильтра {field_name}: {filter_error}")
                        continue

            if filters_applied > 0:
                working_df = filtered_df
                filtered = True

        # Определение порядка цветов для диаграммы
        color_order = list(COLOR_MAPPING.values())
        chart_data = [0] * len(color_order)

        # Подсчет количества дел по цветовым категориям
        if not working_df.empty and color_column in working_df.columns:
            color_counts = working_df[color_column].value_counts()

            for i, color_name in enumerate(color_order):
                chart_data[i] = int(color_counts.get(color_name, 0))

        total_cases = len(working_df)

        response_data = {
            "success": True,
            "data": chart_data,
            "totalCases": total_cases,
            "filtered": filtered,
            "colorLabels": color_order,
            "message": f"Данные для диаграммы успешно рассчитаны ({total_cases} дел)" +
                       (" с применением фильтров" if filtered else "")
        }

        if filtered and filters:
            response_data["filters"] = filters

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ОШИБКА РАСЧЕТА ДАННЫХ ДЛЯ ДИАГРАММЫ: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка расчета данных диаграммы: {str(e)}")


@router.get("/cases-by-color")
async def get_cases_by_color(
        color: str = Query(
            ...,
            description="Цвет категории (ИК, Серый, Зеленый, Желтый, Оранжевый, Красный, Лиловый, Синий, Белый)"
        )
):
    """
    Возвращает таблицу дел по указанной цветовой категории.

    Args:
        color (str): Название цвета на русском или английском коде

    Returns:
        Dict: Результат фильтрации с данными дел

    Raises:
        HTTPException: 400 при неверном параметре цвета или отсутствии данных
        HTTPException: 500 при ошибках обработки данных
    """
    try:
        df = normalized_manager.get_cases_data()

        if df is None or df.empty:
            raise HTTPException(
                status_code=400,
                detail="Данные дел не загружены. Сначала загрузите детальный отчет"
            )

        color_column = COLUMNS["CURRENT_PERIOD_COLOR"]
        if color_column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail="Цветовая классификация не выполнена. Сначала вызовите /api/rainbow/analyze"
            )

        # Преобразование входного цвета в русское название
        russian_color = COLOR_MAPPING.get(color, color)
        valid_russian_colors = list(COLOR_MAPPING.values())
        if russian_color not in valid_russian_colors:
            raise HTTPException(
                status_code=400,
                detail=f"Неверный цвет. Допустимые значения: {', '.join(valid_russian_colors)}"
            )

        # Применение фильтрации по правилам радуги
        working_df = get_rainbow_filtered_dataframe(df)

        # Фильтрация по цвету
        filtered_df = working_df[working_df[color_column] == russian_color]

        # Формирование данных для ответа
        columns_to_include = {
            COLUMNS["CASE_CODE"]: "caseCode",
            COLUMNS["RESPONSIBLE_EXECUTOR"]: "responsibleExecutor",
            COLUMNS["GOSB"]: "gosb",
            COLUMNS["METHOD_OF_PROTECTION"]: "courtProtectionMethod",
            COLUMNS["COURT"]: "courtReviewingCase",
            COLUMNS["CASE_STATUS"]: "caseStatus",
            color_column: "currentPeriodColor",
        }

        # Оставляем только существующие колонки
        existing_columns = {k: v for k, v in columns_to_include.items() if k in filtered_df.columns}

        result_df = filtered_df[list(existing_columns.keys())].rename(columns=existing_columns)

        # Заполнение NaN значений
        for col in result_df.columns:
            if result_df[col].dtype == 'object':
                result_df[col] = result_df[col].fillna("Не указано")
            elif pd.api.types.is_numeric_dtype(result_df[col]):
                result_df[col] = result_df[col].fillna(0)

        cases_data = result_df.to_dict(orient="records")

        return {
            "success": True,
            "color": color,
            "russianColor": russian_color,
            "count": len(cases_data),
            "cases": cases_data,
            "message": f"Найдено {len(cases_data)} дел с цветом '{russian_color}'"
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка обработки данных: {str(e)}")


@router.get("/quick-test")
async def quick_test_analysis():
    """
    Предоставляет мгновенные тестовые данные для разработки фронтенда.

    Возвращает фиксированные тестовые значения цветовой классификации
    для отладки и разработки без необходимости загрузки реальных данных.

    Returns:
        Dict: Тестовые данные цветовой классификации: {
            "success": bool,
            "data": List[int],  # Тестовые количества дел по цветам
            "totalCases": int,  # Общее тестовое количество
            "message": str      # Информационное сообщение
        }
    """
    test_values = [743, 23, 0, 211, 0, 4204, 7131, 0, 6729]

    return {
        "success": True,
        "data": test_values,
        "totalCases": sum(test_values),
        "message": "Тестовые данные для разработки"
    }