# backend/app/rainbow/routes/rainbow.py
"""
Модуль маршрутов FastAPI для анализа данных по цветовой классификации (радуга).

Содержит эндпоинты для цветовой классификации дел и фильтрации по цветовым категориям.
Обеспечивает интеграцию с модулем RainbowClassifier для анализа данных и предоставляет
API для получения статистики и детальной информации по делам различных цветовых категорий.

Основные эндпоинты:
- /analyze: Анализ данных и получение цветовой статистики
- /cases-by-color: Фильтрация дел по цветовым категориям
- /quick-test: Тестовые данные для разработки
"""
import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, List, Optional, Any

router = APIRouter(prefix="/api/rainbow", tags=["rainbow"])

# Импорт модулей анализа данных
try:
    from backend.app.common.modules.data_manager import data_manager
    from backend.app.rainbow.modules.rainbow_classifier import RainbowClassifier
    from backend.app.common.routes.common import current_files
    from backend.app.common.config.column_names import COLUMNS
    from backend.app.common.modules.utils import extract_value
except ImportError as e:
    raise RuntimeError("Ошибка инициализации rainbow routes") from e

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
    Выполняет полную подготовку данных для визуализации радуги.

    Функция реализует трехэтапный процесс обработки данных:
    1. Загрузка и очистка исходных данных (cleaned)
    2. Создание производных данных цветовой классификации (derived)
    3. Формирование кэшированных данных для быстрой фильтрации (cached)

    Returns:
        Dict: Результат подготовки данных в формате: {
            "success": bool,
            "message": str,
            "derivedCount": int,  # Количество записей в derived данных
            "cachedCount": int    # Количество записей в cached данных
        }

    Raises:
        HTTPException: 404 если детальный отчет не загружен в систему
        HTTPException: 500 при возникновении ошибок обработки данных
    """
    # Проверка наличия загруженного отчета выполняется первым делом
    if not current_files["current_detailed_report"]:
        raise HTTPException(status_code=404, detail="Текущий детальный отчет не загружен")

    try:
        print("\n🌈 ЗАПУСК ПОЛНОЙ ПОДГОТОВКИ ДАННЫХ РАДУГИ")
        print("=" * 45)

        # Этап 1: Загрузка и очистка данных выполняется через менеджер данных
        detailed_df = data_manager.load_detailed_report(
            current_files["current_detailed_report"]
        )
        print(f"✅ cleaned_data загружен: {len(detailed_df)} строк")

        # Этап 2: Создание derived данных цветовой классификации
        derived_df = RainbowClassifier.create_derived_rainbow(detailed_df)

        # Валидация derived данных выполняется для обеспечения целостности
        if derived_df is None or derived_df.empty:
            print("❌ ОШИБКА: derived_rainbow не создан или пуст")
            raise HTTPException(
                status_code=500,
                detail="Не удалось создать производные данные для радуги"
            )

        # Сохранение derived данных в менеджер обеспечивает их доступность
        data_manager._derived_data["detailed_rainbow"] = derived_df
        print(f"✅ derived_rainbow создан и сохранен: {len(derived_df)} строк")

        # Этап 3: Создание cached данных для быстрой фильтрации по цветам
        cached_df = RainbowClassifier.build_colored_cache(detailed_df, derived_df)

        # Валидация cached данных гарантирует корректность работы фильтрации
        if cached_df is None or cached_df.empty:
            print("❌ ОШИБКА: colored_cache не создан или пуст")
            raise HTTPException(
                status_code=500,
                detail="Не удалось создать кэшированные данные для фильтрации"
            )

        # Сохранение cached данных в менеджер обеспечивает работу эндпоинтов фильтрации
        data_manager._cached_data["detailed_colored"] = cached_df
        print(f"✅ colored_cache создан и сохранен: {len(cached_df)} строк")

        # Завершающее сообщение фиксирует успешное выполнение всех этапов
        print("✅ ВСЕ ДАННЫЕ РАДУГИ ПОДГОТОВЛЕНЫ И СОХРАНЕНЫ")

        return {
            "success": True,
            "message": "Полная подготовка данных радуги выполнена успешно",
            "derivedCount": len(derived_df),
            "cachedCount": len(cached_df)
        }

    except HTTPException:
        # Передача HTTPException без изменений обеспечивает корректную работу FastAPI
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

    Использует get_colored_data для доступа к полным данным с цветовой информацией,
    что позволяет корректно применять фильтры формы настроек.

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
        HTTPException: 400 если данные радуги не были предварительно подготовлены
        HTTPException: 500 при возникновении ошибок расчета статистики
    """
    try:
        print("\n📊 ЗАПРОС ДАННЫХ ДЛЯ ПОСТРОЕНИЯ ДИАГРАММЫ (с colored_cache)")
        print("=" * 50)

        # Логирование полученных фильтров выполняется для отладки
        if filters:
            print(f"🔍 ПОЛУЧЕНЫ ФИЛЬТРЫ ({len(filters)}):")
            for key, value in filters.items():
                print(f"   {key}: {value}")
        else:
            print("📋 ФИЛЬТРЫ НЕ ПЕРЕДАНЫ - возвращаем общую статистику")

        # Получение данных с цветовой классификацией из кэша
        working_df = data_manager.get_colored_data("detailed")

        if working_df is None or working_df.empty:
            print("❌ ОШИБКА: colored_cache отсутствует или пуст")
            raise HTTPException(
                status_code=400,
                detail="Данные радуги не подготовлены. Сначала вызовите /api/rainbow/analyze"
            )

        print(f"✅ Исходные данные из colored_cache: {len(working_df)} строк, {len(working_df.columns)} колонок")

        # Применение фильтров к данным
        if filters and isinstance(filters, dict):
            filtered_df = working_df.copy()
            filters_applied = 0

            # Маппинг названий полей формы на имена колонок DataFrame
            column_mapping = {
                "responsibleExecutor": "responsibleExecutor",
                "gosb": "gosb",
                "courtReviewingCase": "courtReviewingCase",
                "courtProtectionMethod": "courtProtectionMethod",
                "caseStatus": "caseStatus",
                "currentPeriodColor": "currentPeriodColor",
                "previousPeriodColor": "previousPeriodColor",
                "caseCode": "caseCode"
            }

            # Последовательное применение фильтров к DataFrame
            for field_name, filter_value in filters.items():
                column_name = column_mapping.get(field_name, field_name)

                if (filter_value and isinstance(filter_value, str) and
                        column_name in filtered_df.columns):

                    print(f"  → Применяем фильтр: {column_name} = '{filter_value}'")

                    try:
                        # Фильтрация выполняется путем сравнения строковых значений
                        mask = filtered_df[column_name].astype(str).str.strip() == str(filter_value).strip()
                        filtered_df = filtered_df[mask]
                        filters_applied += 1

                        print(f"     Осталось строк: {len(filtered_df)}")
                    except Exception as filter_error:
                        print(f"  ⚠️ Ошибка применения фильтра {column_name}: {filter_error}")
                        continue

            if filters_applied > 0:
                print(f"✅ После фильтрации: {len(filtered_df)} из {len(working_df)} дел")
                working_df = filtered_df
                filtered = True
            else:
                print("ℹ️ Фильтры переданы, но не применены (неверные поля/значения)")
                filtered = False
        else:
            filtered = False
            print(f"✅ Без фильтров: {len(working_df)} дел")

        # Определение порядка цветов для диаграммы
        color_order = list(COLOR_MAPPING.values())
        chart_data = [0] * len(color_order)

        # Подсчет количества дел по цветовым категориям
        color_stats = {}
        unknown_colors = set()

        for _, row in working_df.iterrows():
            color_value = row.get("currentPeriodColor")

            if pd.isna(color_value):
                continue

            color_str = str(color_value).strip()

            # Определение русского названия цвета выполняется по иерархии правил
            russian_color = None

            # Правило 1: Цвет уже в русском формате
            if color_str in color_order:
                russian_color = color_str
            # Правило 2: Цвет в английском коде
            elif color_str in COLOR_MAPPING:
                russian_color = COLOR_MAPPING[color_str]
            # Правило 3: Поиск по частичному совпадению
            else:
                for eng, rus in COLOR_MAPPING.items():
                    if color_str.lower() == eng.lower() or color_str.lower() == rus.lower():
                        russian_color = rus
                        break

                if not russian_color:
                    unknown_colors.add(color_str)
                    continue

            # Увеличение счетчика для найденного цвета
            if russian_color in color_stats:
                color_stats[russian_color] += 1
            else:
                color_stats[russian_color] = 1

        # Заполнение массива данных диаграммы в стандартном порядке
        for i, color_name in enumerate(color_order):
            chart_data[i] = color_stats.get(color_name, 0)

        # Логирование неизвестных цветов выполняется для отладки
        if unknown_colors:
            print(f"⚠️ Найдены неизвестные значения цветов: {list(unknown_colors)[:5]}")

        # Формирование ответа с результатами расчета
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

        print(f"📈 РАСЧЕТ ЗАВЕРШЕН: {total_cases} дел, {sum(chart_data)} классифицировано")
        print("=" * 50)

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
        HTTPException: 400 при неверном параметре цвета
        HTTPException: 404 если детальный отчет не загружен
        HTTPException: 500 при ошибках обработки данных
    """
    try:
        # Получаем готовый кэш через публичный метод DataManager
        detailed_colored_df = data_manager.get_colored_data("detailed")
        if detailed_colored_df is None or detailed_colored_df.empty:
            raise HTTPException(status_code=404, detail="Текущий детальный отчет не загружен")

        # Преобразуем входной цвет в русское название
        russian_color = COLOR_MAPPING.get(color, color)
        valid_russian_colors = list(COLOR_MAPPING.values())
        if russian_color not in valid_russian_colors:
            raise HTTPException(
                status_code=400,
                detail=f"Неверный цвет. Допустимые значения: {', '.join(valid_russian_colors)}"
            )

        # Фильтруем DataFrame по цвету
        filtered_df = detailed_colored_df[detailed_colored_df["currentPeriodColor"] == russian_color]

        # Преобразуем в список словарей для API
        cases_data = filtered_df.to_dict(orient="records")

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
    # Фиксированные тестовые значения для разработки
    test_values = [743, 23, 0, 211, 0, 4204, 7131, 0, 6729]

    return {
        "success": True,
        "data": test_values,
        "totalCases": sum(test_values),
        "message": "Тестовые данные для разработки"
    }