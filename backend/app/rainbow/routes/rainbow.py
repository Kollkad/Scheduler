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

from fastapi import APIRouter, HTTPException, Query
import pandas as pd
from typing import Dict, List

router = APIRouter(prefix="/api/rainbow", tags=["rainbow"])

# Импорт модулей анализа данных
try:
    from backend.app.common.modules.data_manager import data_manager
    from backend.app.rainbow.modules.rainbow_classifier import RainbowClassifier
    from backend.app.common.routes.common import current_files
    from backend.app.common.config.column_names import COLUMNS
except ImportError as e:
    print(f"❌ Ошибка импорта rainbow модулей: {e}")

    # Заглушки для случаев ошибок импорта
    def load_excel_data(*args):
        """Заглушка функции загрузки данных."""
        return pd.DataFrame()


    def clean_data(*args):
        """Заглушка функции очистки данных."""
        return pd.DataFrame()


    class RainbowClassifier:
        """Заглушка классификатора радуги для тестирования."""

        @staticmethod
        def classify_cases(*args):
            """Возвращает тестовые данные цветовой классификации."""
            return [743, 23, 0, 211, 0, 0, 3989, 6702, 7373]


    def clear_memory(*args):
        """Заглушка функции очистки памяти."""
        pass

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
    Анализ данных для построения цветовой диаграммы (радуги).

    Загружает детальный отчет и выполняет цветовую классификацию дел
    с использованием модуля RainbowClassifier.

    Returns:
        Dict: Результат анализа с цветовой статистикой: {
            "success": bool,
            "data": List[int],  # Количества дел по цветам
            "totalCases": int,  # Общее количество дел
            "message": str      # Сообщение о результате
        }

    Raises:
        HTTPException: 404 если детальный отчет не загружен
        HTTPException: 500 при ошибках анализа данных
    """
    if not current_files["current_detailed_report"]:
        raise HTTPException(status_code=404, detail="Текущий детальный отчет не загружен")

    try:
        print("\n🌈 АНАЛИЗ РАДУГИ")
        print("=" * 30)

        # Загрузка детального отчета из менеджера данных
        detailed_df = data_manager.load_detailed_report(current_files["current_detailed_report"])
        print(f"✅ Получено записей: {len(detailed_df)}")

        # Выполнение цветовой классификации дел
        chart_data = RainbowClassifier.classify_cases(detailed_df)
        print("✅ Классификация по rainbow завершена:")

        # Вывод статистики классификации в консоль
        if hasattr(RainbowClassifier, 'print_rainbow_stats'):
            RainbowClassifier.print_rainbow_stats(chart_data)

        return {
            "success": True,
            "data": chart_data,
            "totalCases": sum(chart_data),
            "message": "Анализ радуги выполнен успешно"
        }

    except Exception as e:
        print(f"❌ ОШИБКА АНАЛИЗА РАДУГИ: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")


@router.get("/cases-by-color")
async def get_cases_by_color(
        color: str = Query(
            ...,
            description="Цвет категории (ИК, Серый, Зеленый, Желтый, Оранжевый, Красный, Лиловый, Синий, Белый)"
        )
):
    """
    Возвращает таблицу дел по указанной цветовой категории.

    Поддерживает как русские названия цветов, так и английские коды.
    Фильтрует дела по цветовой категории и возвращает структурированные данные.

    Args:
        color (str): Название цвета на русском или английском коде

    Returns:
        Dict: Результат фильтрации с данными дел: {
            "success": bool,
            "color": str,           # Исходный параметр цвета
            "russianColor": str,    # Русское название цвета
            "count": int,           # Количество найденных дел
            "cases": List[Dict],    # Данные отфильтрованных дел
            "message": str          # Информационное сообщение
        }

    Raises:
        HTTPException: 404 если отчет не загружен или данные не найдены
        HTTPException: 400 при неверном параметре цвета
        HTTPException: 500 при ошибках обработки данных
    """
    if not current_files["current_detailed_report"]:
        raise HTTPException(status_code=404, detail="Текущий детальный отчет не загружен")

    try:
        # Получение данных с цветовой классификацией
        detailed_df = data_manager.get_colored_data("detailed")
        if detailed_df is None:
            raise HTTPException(status_code=404, detail="Данные с цветом не найдены")

        # Преобразование входного параметра в русское название цвета
        russian_color = color

        # Преобразование английского кода в русское название
        if color in COLOR_MAPPING:
            russian_color = COLOR_MAPPING[color]

        # Валидация русского названия цвета
        valid_russian_colors = list(COLOR_MAPPING.values())
        if russian_color not in valid_russian_colors and russian_color != "ИК":
            raise HTTPException(
                status_code=400,
                detail=f"Неверный цвет. Допустимые значения: {', '.join(valid_russian_colors + ['ИК'])}"
            )

        print(f"🔍 Поиск дел с цветом: '{russian_color}' (исходный параметр: '{color}')")

        # Определение имени столбца с цветовой классификацией
        color_column_name = 'Цвет (текущий период)'
        if color_column_name not in detailed_df.columns:
            raise HTTPException(status_code=500, detail="Столбец с цветом не найден в данных")

        # Фильтрация данных по указанному цвету
        filtered_df = detailed_df[detailed_df[color_column_name] == russian_color]

        print(f"✅ Найдено {len(filtered_df)} дел с цветом '{russian_color}'")

        # Формирование структурированных данных дел
        cases_data = []
        for _, row in filtered_df.iterrows():

            def extract_value(value):
                """
                Безопасное извлечение значения из различных типов данных.

                Args:
                    value: Значение для извлечения

                Returns:
                    str: Строковое представление значения или "Не указано"
                """
                # Обработка pandas структур
                if isinstance(value, (pd.Series, pd.DataFrame)):
                    if len(value) > 0:
                        first_val = value.iloc[0] if hasattr(value, 'iloc') else value.values[0]
                        return str(first_val) if pd.notna(first_val) else "Не указано"
                    else:
                        return "Не указано"
                else:
                    # Обработка обычных значений
                    return str(value) if pd.notna(value) else "Не указано"

            # Формирование структуры данных дела
            case_data = {
                "caseCode": extract_value(row.get(COLUMNS.get("CASE_CODE", "Код дела"), "Не указано")),
                "responsibleExecutor": extract_value(
                    row.get(COLUMNS.get("RESPONSIBLE_EXECUTOR", "Ответственный исполнитель"), "Не указано")),
                "gosb": extract_value(row.get(COLUMNS.get("GOSB", "ГОСБ"), "Не указано")),
                "currentPeriodColor": extract_value(row.get(color_column_name, "Не указано")),
                "courtProtectionMethod": extract_value(
                    row.get(COLUMNS.get("METHOD_OF_PROTECTION", "Способ судебной защиты"), "Не указано")),
                "courtReviewingCase": extract_value(
                    row.get(COLUMNS.get("COURT", "Суд, рассматривающий дело"), "Не указано")),
                "caseStatus": extract_value(row.get(COLUMNS.get("CASE_STATUS", "Статус дела"), "Не указано")),
                "previousPeriodColor": "Не доступно"  # Заглушка для предыдущего периода
            }
            cases_data.append(case_data)

        return {
            "success": True,
            "color": color,
            "russianColor": russian_color,
            "count": len(cases_data),
            "cases": cases_data,
            "message": f"Найдено {len(cases_data)} дел с цветом '{russian_color}'"
        }

    except HTTPException:
        # Перевыброс HTTP исключений без изменений
        raise
    except Exception as e:
        print(f"❌ ОШИБКА получения дел по цвету '{color}': {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка получения дел: {str(e)}")


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