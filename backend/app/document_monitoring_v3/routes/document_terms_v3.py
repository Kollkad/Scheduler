# backend/app/document_monitoring_v3/routes/document_terms_v3.py
"""
Маршруты для системы мониторинга документов (v3 - нормализованные данные)

Предоставляет эндпоинты для анализа, фильтрации и получения статистики
по документам с использованием NormalizedDataManager и модельных данных.

Основные эндпоинты:
- /analyze: Запуск анализа документов (установка stageCode, проверки)
- /charts: Получение данных для построения диаграмм
- /filter: Фильтрация документов по статусу и типу
- /statuses: Получение статистики по статусам документов
- /document: Получение детальной информации о документе
"""

from fastapi import APIRouter, HTTPException, Query
import pandas as pd
from datetime import datetime

from backend.app.common.config.column_names import COLUMNS
from backend.app.data_management.modules.normalized_data_manager import normalized_manager
from backend.app.document_monitoring_v3.modules.document_stage_checks_v3 import analyze_documents
from backend.app.document_monitoring_v3.config.special_fields_document_v3 import SPECIAL_FIELDS_DOCUMENT
from backend.app.common.modules.field_grouping import (
    safe_convert_value,
    group_fields_by_category
)

router = APIRouter(prefix="/api/documents/v3", tags=["document_monitoring_v3"])

@router.get("/analyze_documents")
async def analyze_documents_v3():
    """
    Запускает процесс анализа документов с использованием новой логики:
    1. Загружает документы через NormalizedDataManager
    2. Устанавливает stageCode
    3. Выполняет проверки для этапа transferredDocumentD
    4. Сохраняет результаты проверок в CheckResult

    Returns:
        dict: Результат анализа
    """
    try:
        # 1. Загрузка документов через новый менеджер
        documents_df = normalized_manager.get_or_load_documents_report()

        if documents_df is None or documents_df.empty:
            return {
                "success": True,
                "count": 0,
                "message": "Отчет документов пуст"
            }

        # 2. Выполнение анализа (модифицирует documents_df, добавляя stageCode)
        #    Возвращает DataFrame в формате CheckResult
        check_results_df = analyze_documents(documents_df)

        # 3. Сохранение результатов проверок в новый менеджер
        normalized_manager.set_check_results_data(check_results_df, analysis_type="documents")

        return {
            "success": True,
            "count": len(check_results_df),
            "message": f"Анализ документов выполнен успешно. Сформировано {len(check_results_df)} результатов проверок"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа документов: {str(e)}")


@router.get("/analyze_document_charts")
async def analyze_document_charts_v3():
    """
    Предоставляет агрегированные данные для построения диаграмм по результатам проверки документов.

    Возвращает статистику количества проверок в разрезе типов документов и статусов мониторинга.
    Статистика формируется путём сопоставления результатов проверок (check_results)
    с исходными данными документов по ключу targetId = transferCode.

    Returns:
        dict: Структура с полями success, data (список словарей с ключами group_name и values),
              totalDocuments (количество учтённых проверок) и message.
    """
    try:
        documents_df = normalized_manager.get_documents_data()
        check_results_df = normalized_manager.get_check_results_data()
        check_results_df = check_results_df[
            check_results_df["checkCode"].str.endswith("D", na=False)
        ]
        if documents_df.empty or check_results_df.empty:
            return {
                "success": True,
                "data": [],
                "totalDocuments": 0,
                "message": "Нет данных для построения диаграмм (анализ не выполнен)"
            }

        # Подготовка данных для объединения: оставляются только значимые колонки,
        docs_subset = documents_df[[COLUMNS["TRANSFER_CODE"], COLUMNS["DOCUMENT_TYPE"]]].copy()
        docs_subset[COLUMNS["TRANSFER_CODE"]] = docs_subset[COLUMNS["TRANSFER_CODE"]].astype(str)

        results_subset = check_results_df[["targetId", "monitoringStatus"]].copy()
        results_subset["targetId"] = results_subset["targetId"].astype(str)

        # Объединение таблиц: для каждой проверки находится соответствующий тип документа
        # Используется левое соединение, чтобы сохранить все проверки, даже если связь отсутствует
        merged = results_subset.merge(
            docs_subset,
            left_on="targetId",
            right_on=COLUMNS["TRANSFER_CODE"],
            how="left"
        )

        # Выявление и логирование проверок, для которых не удалось определить тип документа
        missing_mask = merged[COLUMNS["DOCUMENT_TYPE"]].isna()
        if missing_mask.any():
            missing_ids = merged.loc[missing_mask, "targetId"].unique()
            print(f"⚠️ Обнаружены targetId без соответствующего типа документа: {list(missing_ids)}")
            merged = merged[~missing_mask]

        if merged.empty:
            return {
                "success": True,
                "data": [],
                "totalDocuments": 0,
                "message": "Все результаты проверок не имеют привязки к типу документа"
            }

        # Группировка и подсчёт количества проверок по парам (тип документа, статус)
        grouped = merged.groupby([COLUMNS["DOCUMENT_TYPE"], "monitoringStatus"]).size()

        # Преобразование мультииндексного ряда в таблицу, где строками выступают типы документов,
        # столбцами — возможные статусы мониторинга
        pivot = grouped.unstack(fill_value=0)

        # Обеспечение присутствия в таблице всех трёх ожидаемых статусов,
        # даже если в данных отсутствуют записи для какого-либо статуса
        required_statuses = ["timely", "overdue", "no_data"]
        for status in required_statuses:
            if status not in pivot.columns:
                pivot[status] = 0

        # Фиксация порядка столбцов для предсказуемости выходного формата
        pivot = pivot[required_statuses]

        # Формирование итогового списка для поля data
        results = []
        for doc_type, row in pivot.iterrows():
            results.append({
                "group_name": doc_type,  # Русскоязычное наименование типа документа
                "values": row.tolist()    # Список значений в порядке: timely, overdue, no_data
            })

        total_used = merged.shape[0]

        return {
            "success": True,
            "data": results,
            "totalDocuments": total_used,
            "message": f"Данные для диаграмм подготовлены. Обработано {total_used} результатов проверок"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка подготовки данных для диаграмм: {str(e)}")


@router.get("/filter_documents")
async def filter_documents_v3(
    status: str = Query(..., description="Статус мониторинга: timely, overdue, no_data"),
    documentType: str = Query(None, description="Тип документа (русское название, например 'Исполнительный лист')")
):
    """
    Возвращает список документов, отфильтрованных по статусу мониторинга и (опционально) типу документа.
    Данные формируются путём соединения результатов проверок с исходными документами по ключу targetId = transferCode.
    """
    try:
        documents_df = normalized_manager.get_documents_data()
        check_results_df = normalized_manager.get_check_results_data()

        if documents_df.empty or check_results_df.empty:
            raise HTTPException(
                status_code=404,
                detail="Анализ документов не выполнен. Сначала вызовите /api/documents/v3/analyze"
            )

        # Отбор результатов проверок с указанным статусом мониторинга
        filtered_results = check_results_df[check_results_df["monitoringStatus"] == status].copy()
        if filtered_results.empty:
            return {
                "success": True,
                "count": 0,
                "status": status,
                "documentType": documentType,
                "documents": []
            }

        # Подготовка данных документов: приведение ключа к строке и выбор только значимых полей
        docs_subset = documents_df[[
            COLUMNS["TRANSFER_CODE"],
            COLUMNS["DOCUMENT_TYPE"],
            COLUMNS["DOCUMENT_REQUEST_CODE"],
            COLUMNS["DOCUMENT_CASE_CODE"],
            COLUMNS["RESPONSIBLE_EXECUTOR"],
            COLUMNS["DEPARTMENT_CATEGORY"],
            COLUMNS["ESSENSE_OF_THE_ANSWER"]
        ]].copy()
        docs_subset[COLUMNS["TRANSFER_CODE"]] = docs_subset[COLUMNS["TRANSFER_CODE"]].astype(str)

        # Приведение targetId к строковому типу для корректного соединения
        filtered_results["targetId"] = filtered_results["targetId"].astype(str)

        # Внутреннее соединение: для каждого результата проверки находится соответствующий документ
        merged = filtered_results.merge(
            docs_subset,
            left_on="targetId",
            right_on=COLUMNS["TRANSFER_CODE"],
            how="inner"
        )

        # Фильтрация по типу документа, если параметр передан
        if documentType is not None:
            merged = merged[merged[COLUMNS["DOCUMENT_TYPE"]] == documentType]

        # Если после всех фильтров не осталось строк, возвращается пустой список
        if merged.empty:
            return {
                "success": True,
                "count": 0,
                "status": status,
                "documentType": documentType,
                "documents": []
            }

        # Добавление колонки monitoringStatus (значение одинаково для всех отфильтрованных строк)
        merged["monitoringStatus"] = status

        # Выбор полей для итогового ответа (переименование на ожидаемые клиентом ключи)
        result_columns = {
            COLUMNS["TRANSFER_CODE"]: "transferCode",
            COLUMNS["DOCUMENT_REQUEST_CODE"]: "requestCode",
            COLUMNS["DOCUMENT_CASE_CODE"]: "caseCode",
            COLUMNS["RESPONSIBLE_EXECUTOR"]: "responsibleExecutor",
            COLUMNS["DOCUMENT_TYPE"]: "documentType",
            COLUMNS["DEPARTMENT_CATEGORY"]: "department",
            COLUMNS["ESSENSE_OF_THE_ANSWER"]: "responseEssence",
            "monitoringStatus": "monitoringStatus"
        }
        output_df = merged[list(result_columns.keys())].rename(columns=result_columns)

        # Преобразование в список словарей
        documents_list = output_df.to_dict(orient="records")

        return {
            "success": True,
            "count": len(documents_list),
            "status": status,
            "documentType": documentType,
            "documents": documents_list
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка фильтрации документов: {str(e)}")


@router.get("/document_statuses")
async def get_document_statuses_v3():
    """
    Предоставляет статистику распределения документов по статусам мониторинга и завершенности.
    Использует check_results.

    Returns:
        dict: Статистика документов
    """
    try:
        check_results_df = normalized_manager.get_check_results_data()

        if check_results_df.empty:
            return {
                "success": True,
                "totalDocuments": 0,
                "statusDistribution": {},
                "completionDistribution": {},
                "message": "Анализ документов не выполнен"
            }

        # Подсчёт распределения по статусам мониторинга
        status_counts = check_results_df["monitoringStatus"].value_counts().to_dict()

        # Подсчёт распределения по статусам завершенности
        completion_counts = check_results_df["completionStatus"].value_counts().to_dict()
        completion_counts_str = {str(k): v for k, v in completion_counts.items()}

        return {
            "success": True,
            "totalDocuments": len(check_results_df),
            "statusDistribution": status_counts,
            "completionDistribution": completion_counts_str,
            "message": f"Проанализировано {len(check_results_df)} результатов проверок"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа статусов: {str(e)}")


@router.get("/document")
async def get_document_details_v3(
    transferCode: str = Query(..., description="Код передачи документа")
):
    """
    Получение детальной информации для страницы документа по коду передачи.
    Использует исходные данные документов из NormalizedDataManager.

    Args:
        transferCode: Уникальный код передачи документа

    Returns:
        dict: Детальная информация о документе, включая сгруппированные поля

    Raises:
        HTTPException 404: Документ не найден или данные не загружены
        HTTPException 500: Ошибка сервера или отсутствует колонка с кодом передачи
    """
    try:
        # Получение данных
        documents_df = normalized_manager.get_documents_data()

        if documents_df.empty:
            raise HTTPException(status_code=404, detail="Данные документов не загружены")

        # Поиск документа по transferCode
        transfer_col = COLUMNS["TRANSFER_CODE"]
        if transfer_col not in documents_df.columns:
            raise HTTPException(
                status_code=500,
                detail=f"Колонка '{transfer_col}' не найдена в данных документов"
            )

        mask = documents_df[transfer_col].astype(str).str.strip() == transferCode
        doc = documents_df[mask]

        if doc.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Документ с кодом передачи '{transferCode}' не найден"
            )

        # Преобразование в словарь с безопасными значениями
        doc_dict = doc.iloc[0].to_dict()
        safe_document = {}
        for key, value in doc_dict.items():
            safe_document[key] = safe_convert_value(value)

        # Группировка полей по категориям
        field_groups = group_fields_by_category(safe_document, SPECIAL_FIELDS_DOCUMENT)

        return {
            "success": True,
            "transferCode": transferCode,
            "caseCode": safe_document.get(COLUMNS["DOCUMENT_CASE_CODE"], ""),
            "documentType": safe_document.get(COLUMNS["DOCUMENT_TYPE"], ""),
            "department": safe_document.get(COLUMNS["DEPARTMENT_CATEGORY"], ""),
            "fieldGroups": field_groups,
            "totalFields": len(safe_document),
            "message": "Данные документа получены"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения документа: {str(e)}")
