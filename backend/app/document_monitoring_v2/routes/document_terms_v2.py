# backend/app/document_monitoring_v2/routes/document_terms_v2.py
"""
Маршруты для системы мониторинга документов

Предоставляет эндпоинты для анализа, фильтрации и получения статистики
по документам с использованием оптимизированных алгоритмов обработки.

Основные эндпоинты:
- /analyze: Запуск анализа документов
- /analyze_document_charts: Получение данных для построения диаграмм
- /filter_documents: Фильтрация документов по статусу и типу
- /document_statuses: Получение статистики по статусам документов
- /document: Получение детальной информации о документе
"""

from fastapi import APIRouter, HTTPException, Query
import pandas as pd
from datetime import datetime

from backend.app.common.config.column_names import COLUMNS
from backend.app.data_management.modules.data_manager import data_manager
from backend.app.document_monitoring_v2.modules.document_stage_checks_v2 import (
    analyze_documents,
    save_document_monitoring_status,
)
from backend.app.common.modules.field_grouping import (
    safe_convert_value,
    detect_field_type,
    group_fields_by_category,
    is_empty_value
)
from backend.app.document_monitoring_v2.config.special_fields_document import SPECIAL_FIELDS_DOCUMENT

router = APIRouter(prefix="/api/documents", tags=["document_monitoring_v2"])


class DocumentChartAnalyzer:
    """
    Анализатор для преобразования данных документов в формат для визуализации диаграмм.

    Выполняет группировку документов по типам и статусам для построения
    сегментированных диаграмм. Поддерживает основные типы документов:
    - Исполнительный лист
    - Решение суда
    - Судебный приказ
    """

    def __init__(self, documents_df: pd.DataFrame):
        """
        Инициализирует анализатор с данными документов.

        Args:
            documents_df (pd.DataFrame): DataFrame с колонками ['document', 'monitoringStatus']
        """
        self.documents_df = documents_df

    def analyze_for_charts(self):
        """
        Анализирует документы для построения сегментированной диаграммы.

        Группирует документы по типам и подсчитывает количество документов
        каждого статуса (timely, overdue, no_data) для каждого типа.

        Returns:
            List[Dict]: Данные для диаграммы в формате:
                [
                    {
                        "group_name": "executionDocument",
                        "values": [timely_count, overdue_count, 0, no_data_count]
                    },
                    ...
                ]
        """
        # Сопоставление типов документов с русскими названиями
        document_types = {
            "executionDocument": "Исполнительный лист",
            "courtDecision": "Решение суда",
            "courtOrder": "Судебный приказ"
        }

        # Инициализация статистики по типам документов
        stats = {}
        for doc_key, doc_name in document_types.items():
            stats[doc_key] = {"timely": 0, "overdue": 0, "no_data": 0}

        # Подсчет статистики по каждому документу
        for _, row in self.documents_df.iterrows():
            doc_type = row.get("document", "unknown")
            status = row.get("monitoringStatus", "no_data")

            # Определение ключа типа документа по русскому названию
            doc_key = None
            for key, name in document_types.items():
                if name == doc_type:
                    doc_key = key
                    break

            # Учет статистики только для основных типов документов
            if doc_key in stats and status in stats[doc_key]:
                stats[doc_key][status] += 1

        # Формирование результата в формате для фронтенда
        results = []
        for doc_key, counts in stats.items():
            results.append({
                "group_name": doc_key,
                "values": [
                    counts["timely"],
                    counts["overdue"],
                    0,  # Резервное значение для будущего использования
                    counts["no_data"]
                ]
            })

        return results


@router.get("/analyze_documents")
async def analyze_documents_terms():
    """
    Запускает процесс анализа документов и сохраняет результаты.
    Только этот эндпоинт имеет право загружать данные и выполнять анализ.

    Returns:
        dict: Результат анализа в формате:
            {
                "success": bool,
                "count": int,
                "message": str
            }

    Raises:
        HTTPException: 404 если отчет документов не загружен
        HTTPException: 500 при ошибке обработки данных
    """
    try:
        # Проверка наличия загруженного отчета документов
        try:
            documents_df = data_manager.load_documents_report()
        except ValueError:
            raise HTTPException(status_code=404, detail="Отчет документов не загружен")

        # Проверка наличия данных в загруженном отчете
        if documents_df is None or documents_df.empty:
            return {
                "success": True,
                "count": 0,
                "message": "Отчет документов пуст"
            }

        # Выполнение анализа документов
        analyzed_df = analyze_documents(documents_df)

        # Сохранение результатов анализа в кэш
        data_manager.set_processed_data("documents_processed", analyzed_df)

        return {
            "success": True,
            "count": len(analyzed_df),
            "message": f"Анализ документов выполнен успешно. Обработано {len(analyzed_df)} записей"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа документов: {str(e)}")


@router.get("/analyze_document_charts")
async def analyze_document_charts():
    """
    Предоставляет данные документов в формате для построения диаграмм.
    Использует только предварительно рассчитанные данные.

    Returns:
        Dict: Результат анализа с данными для визуализации:
            {
                "success": bool,
                "data": List[Dict],
                "totalDocuments": int,
                "message": str
            }

    Raises:
        HTTPException: 404 если анализ документов не выполнен
        HTTPException: 500 при ошибке обработки данных
    """
    try:
        # Получение предварительно рассчитанных данных
        processed_df = data_manager.get_processed_data("documents_processed")

        if processed_df is None:
            raise HTTPException(
                status_code=404,
                detail="Анализ документов не выполнен. Сначала вызовите /api/documents/analyze"
            )

        # Анализ данных для построения диаграмм
        analyzer = DocumentChartAnalyzer(processed_df)
        chart_data = analyzer.analyze_for_charts()

        return {
            "success": True,
            "data": chart_data,
            "totalDocuments": len(processed_df),
            "message": f"Данные для диаграмм документов подготовлены. Обработано {len(processed_df)} документов"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа документов для диаграмм: {str(e)}")


@router.get("/filter_documents")
async def filter_documents(
        status: str = Query(..., description="Статус мониторинга для фильтрации (timely/overdue/no_data)"),
        documentType: str = Query(None, description="Тип документа (executionDocument, courtDecision, courtOrder)")
):
    """
    Фильтрует документы по статусу мониторинга и типу документа.
    Использует только предварительно рассчитанные данные.

    Args:
        status (str): Статус для фильтрации (timely/overdue/no_data)
        documentType (str, optional): Тип документа для фильтрации

    Returns:
        dict: Результат фильтрации в формате:
            {
                "success": bool,
                "count": int,
                "status": str,
                "documentType": str,
                "documents": list
            }

    Raises:
        HTTPException: 404 если анализ документов не выполнен
        HTTPException: 500 при ошибке фильтрации данных
    """
    try:
        # Получение предварительно рассчитанных данных
        processed_df = data_manager.get_processed_data("documents_processed")

        if processed_df is None:
            raise HTTPException(
                status_code=404,
                detail="Анализ документов не выполнен. Сначала вызовите /api/documents/analyze"
            )

        # Фильтрация по статусу мониторинга
        filtered = processed_df[processed_df["monitoringStatus"] == status]

        # Дополнительная фильтрация по типу документа при указании
        if documentType:
            document_types_map = {
                "executionDocument": "Исполнительный лист",
                "courtDecision": "Решение суда",
                "courtOrder": "Судебный приказ"
            }
            target_doc_name = document_types_map.get(documentType, documentType)
            filtered = filtered[filtered["document"] == target_doc_name]

        # Подготовка данных для JSON-сериализации
        filtered = filtered.fillna("").replace([float('inf'), -float('inf')], 0)

        # Выбор релевантных колонок для возврата
        columns_to_return = ["requestCode", "caseCode", "document", "department", "responseEssence", "monitoringStatus"]
        filtered = filtered[columns_to_return]

        return {
            "success": True,
            "count": len(filtered),
            "status": status,
            "documentType": documentType,
            "documents": filtered.to_dict(orient="records")
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка фильтрации документов: {str(e)}")


@router.get("/document_statuses")
async def get_document_statuses():
    """
    Предоставляет статистику распределения документов по статусам мониторинга.
    Использует только предварительно рассчитанные данные.

    Returns:
        dict: Статистика документов в формате:
            {
                "success": bool,
                "total_documents": int,
                "status_distribution": dict,
                "message": str
            }

    Raises:
        HTTPException: 404 если анализ документов не выполнен
        HTTPException: 500 при ошибке анализа статистики
    """
    try:
        # Получение предварительно рассчитанных данных
        processed_df = data_manager.get_processed_data("documents_processed")

        if processed_df is None:
            raise HTTPException(
                status_code=404,
                detail="Анализ документов не выполнен. Сначала вызовите /api/documents/analyze"
            )

        # Подсчет распределения документов по статусам
        status_counts = processed_df["monitoringStatus"].value_counts().to_dict()

        return {
            "success": True,
            "totalDocuments": len(processed_df),
            "statusDistribution": status_counts,
            "message": f"Проанализировано {len(processed_df)} документов"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа статусов: {str(e)}")


@router.get("/document")
async def get_document_details(
        case_code: str = Query(..., description="Код дела документа"),
        document_type: str = Query(..., description="Тип документа"),
        department: str = Query(..., description="Категория подразделения")
):
    """
    Получение детальной информации для страницы документа с группировкой полей.

    Args:
        case_code (str): Код дела для поиска документа
        document_type (str): Тип документа (Исполнительный лист, Решение суда, Судебный приказ)
        department (str): Категория подразделения

    Returns:
        dict: Детальная информация о документе в формате:
            {
                "success": bool,
                "documentCode": str,                    # Составной идентификатор
                "caseCode": str,                        # Код дела
                "documentType": str,                    # Тип документа
                "department": str,                      # Категория подразделения
                "data": dict,                           # Все поля документа
                "fieldGroups": {                        # Сгруппированные поля
                    "general": list,                    # Общая информация
                    "dates": list,                      # Даты и сроки
                    "financial": list,                  # Финансовые данные
                    "court": list,                      # Судебные данные
                    "other": list                       # Прочее
                },
                "totalFields": int,                     # Общее количество полей
                "message": str
            }

    Raises:
        HTTPException: 404 если документ не найден или анализ не выполнен
        HTTPException: 500 при ошибке получения данных
    """
    try:
        processed_docs = data_manager.get_processed_data("documents_processed")
        original_docs = data_manager.get_documents_data()

        if processed_docs is None or processed_docs.empty:
            raise HTTPException(
                status_code=404,
                detail="Анализ документов не выполнен. Сначала вызовите /api/documents/analyze"
            )

        if original_docs is None or original_docs.empty:
            raise HTTPException(status_code=404, detail="Данные документов не загружены")

        # Поиск в обработанных данных
        processed_mask = (
                (processed_docs["caseCode"] == case_code) &
                (processed_docs["document"] == document_type) &
                (processed_docs["department"] == department)
        )
        processed_doc = processed_docs[processed_mask]

        if processed_doc.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Документ не найден: дело={case_code}, тип={document_type}, подразделение={department}"
            )

        # Поиск в исходных данных
        original_mask = (
                (original_docs[COLUMNS["DOCUMENT_CASE_CODE"]] == case_code) &
                (original_docs[COLUMNS["DOCUMENT_TYPE"]] == document_type) &
                (original_docs[COLUMNS["DEPARTMENT_CATEGORY"]] == department)
        )
        original_doc = original_docs[original_mask]

        # Объединение данных
        processed_dict = processed_doc.iloc[0].to_dict()
        original_dict = original_doc.iloc[0].to_dict() if not original_doc.empty else {}
        merged_document = {**original_dict, **processed_dict}

        # Безопасное преобразование значений
        safe_document = {}
        for key, value in merged_document.items():
            safe_document[key] = safe_convert_value(value)

        # Группировка полей по категориям
        field_groups = group_fields_by_category(safe_document, SPECIAL_FIELDS_DOCUMENT)

        # Составной идентификатор документа
        document_code = f"{case_code}_{document_type}_{department}"

        return {
            "success": True,
            "documentCode": document_code,
            "caseCode": case_code,
            "documentType": document_type,
            "department": department,
            "data": safe_document,
            "fieldGroups": field_groups,
            "totalFields": len(safe_document),
            "message": "Данные документа получены"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка получения документа: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения документа: {str(e)}")
