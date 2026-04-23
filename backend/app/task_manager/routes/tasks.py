# backend/app/task_manager/routes/tasks.py
"""
Маршруты FastAPI для управления задачами.

Предоставляет API endpoints для расчета, получения, сохранения
и управления задачами различных типов производств.
"""
import json

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
import pandas as pd
import math

from backend.app.data_management.modules.normalized_data_manager import normalized_manager
from backend.app.task_manager.modules.task_analyzer import task_analyzer
from backend.app.common.config.column_names import COLUMNS
from backend.app.administration_settings.modules.authorization_logic import get_current_user
from backend.app.administration_settings.modules.user_models import UserSession

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/calculate")
async def calculate_tasks(
    executor: Optional[str] = Query(None, description="Фильтр по ответственному исполнителю"),
    current_user: UserSession = Depends(get_current_user)
):
    """
    Расчет всех задач на основе загруженных данных.

    Выполняет анализ данных и формирование задач для всех доступных
    типов производств с возможностью фильтрации по исполнителю.
    Для расчета необходимы предварительно выполненные анализы:
    - исковое производство (/api/terms/v3/lawsuit/analyze_lawsuit)
    - приказное производство (/api/terms/v3/order/analyze_order)
    - анализ документов (/api/documents/v3/analyze_documents)

    Args:
        executor (str, optional): Ответственный исполнитель для фильтрации задач

    Returns:
        dict: Результат расчета задач с статистикой в формате:
              {
                  "success": bool,
                  "totalTasks": int,
                  "filteredTasks": int,
                  "executor": str or None,
                  "data": List[Dict],
                  "message": str
              }

    Raises:
        HTTPException: 400 если нет результатов проверок для расчета
        HTTPException: 500 при ошибках расчета задач
    """
    try:
        if not current_user.login:
            raise HTTPException(status_code=401, detail="Требуется авторизация")
        created_by = current_user.login
        check_results_df = normalized_manager.get_check_results_data()
        cases_df = normalized_manager.get_cases_data()
        documents_df = normalized_manager.get_documents_data()

        if check_results_df.empty:
            raise HTTPException(
                status_code=400,
                detail="Нет результатов проверок для расчета задач. Сначала выполните анализы."
            )

        print("🔄 Начинается расчет задач...")

        all_tasks = task_analyzer.analyze_all_tasks(created_by=created_by)
        print(f"✅ Рассчитано новых задач: {len(all_tasks)}")

        if executor:
            tasks_df = pd.DataFrame(all_tasks)
            tasks_df = _merge_with_check_results(tasks_df, check_results_df)
            tasks_df = _merge_with_cases(tasks_df, cases_df)
            filtered_tasks = tasks_df[tasks_df["responsibleExecutor"] == executor].to_dict('records')
            print(f"✅ Отфильтровано задач для {executor}: {len(filtered_tasks)} из {len(all_tasks)}")
            return {
                "success": True,
                "totalTasks": len(all_tasks),
                "filteredTasks": len(filtered_tasks),
                "executor": executor,
                "data": filtered_tasks,
                "message": f"Рассчитано {len(filtered_tasks)} задач для {executor}"
            }

        return {
            "success": True,
            "totalTasks": len(all_tasks),
            "filteredTasks": len(all_tasks),
            "executor": None,
            "data": all_tasks,
            "message": f"Рассчитано {len(all_tasks)} задач"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка расчета задач: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка расчета задач: {str(e)}")


@router.get("/list")
async def get_tasks_list(
    filters: str = Query(..., description="JSON строка с фильтрами, например: {\"responsibleExecutor\": \"ФИО1\"}")
):
    """
    Получение списка задач с фильтрацией по одному или нескольким столбцам.

    Задачи обогащаются данными из check_results и исходных отчетов
    для обеспечения полной информации о контексте задачи.

    Args:
        filters (str): JSON строка с фильтрами, где ключ - название столбца,
                      значение - значение для фильтрации

    Returns:
        dict: Список задач с метаданными в формате:
              {
                  "success": bool,
                  "totalTasks": int,
                  "filteredCount": int,
                  "filters": Dict,
                  "tasks": List[Dict],
                  "message": str
              }

    Raises:
        HTTPException: 400 при некорректном JSON в параметре filters
        HTTPException: 400 если указанный столбец не найден в данных
        HTTPException: 500 при ошибках получения данных
    """
    try:
        try:
            filters_dict = json.loads(filters)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Некорректный JSON в параметре filters: {str(e)}"
            )

        if not isinstance(filters_dict, dict):
            raise HTTPException(
                status_code=400,
                detail="Параметр filters должен содержать JSON объект"
            )

        tasks_df = normalized_manager.get_tasks_data()
        check_results_df = normalized_manager.get_check_results_data()
        cases_df = normalized_manager.get_cases_data()
        documents_df = normalized_manager.get_documents_data()

        if tasks_df.empty:
            return {
                "success": True,
                "tasks": [],
                "totalTasks": 0,
                "filteredCount": 0,
                "filters": filters_dict,
                "message": "Нет рассчитанных задач. Выполните /calculate сначала."
            }

        tasks_df = _merge_with_check_results(tasks_df, check_results_df)
        tasks_df = _merge_with_cases(tasks_df, cases_df)
        tasks_df = _merge_with_documents(tasks_df, documents_df)
        tasks_df = _merge_with_overrides(tasks_df)

        all_tasks = tasks_df.to_dict('records')

        filtered_tasks = all_tasks
        for column, value in filters_dict.items():
            filtered_tasks = [
                task for task in filtered_tasks
                if str(task.get(column, "")).strip() == str(value).strip()
            ]

        def clean_json_value(value):
            """Очищает NaN и Inf значения для корректной JSON сериализации."""
            if isinstance(value, float):
                if math.isnan(value) or math.isinf(value):
                    return None
            return value

        filtered_tasks = [{k: clean_json_value(v) for k, v in task.items()} for task in filtered_tasks]

        return {
            "success": True,
            "totalTasks": len(all_tasks),
            "filteredCount": len(filtered_tasks),
            "filters": filters_dict,
            "tasks": filtered_tasks,
            "message": f"Найдено {len(filtered_tasks)} задач по фильтрам: {filters_dict}"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка получения задач: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения задач: {str(e)}")


@router.get("/save-all")
async def save_all_tasks():
    """
    Сохранение всех рассчитанных задач в Excel файл.

    Создает файл с временной меткой в директории backend/app/data.

    Returns:
        dict: Результат сохранения с информацией о файле в формате:
              {
                  "success": bool,
                  "filename": str,
                  "filepath": str,
                  "taskCount": int,
                  "message": str
              }

    Raises:
        HTTPException: 400 если нет задач для сохранения
        HTTPException: 500 при ошибках сохранения файла
    """
    try:
        tasks_df = normalized_manager.get_tasks_data()

        if tasks_df.empty:
            raise HTTPException(
                status_code=400,
                detail="Нет задач для сохранения. Выполните /calculate сначала."
            )

        from datetime import datetime
        import os

        os.makedirs("backend/app/data", exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tasks_export_{timestamp}.xlsx"
        filepath = os.path.join("backend/app/data", filename)

        tasks_df.to_excel(filepath, index=False)

        return {
            "success": True,
            "filename": filename,
            "filepath": filepath,
            "taskCount": len(tasks_df),
            "message": f"Задачи сохранены в {filename}"
        }

    except Exception as e:
        print(f"❌ Ошибка сохранения задач: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")


@router.get("/status")
async def get_tasks_status():
    """
    Получение статуса данных для расчета задач.

    Проверяет наличие загруженных отчетов, результатов проверок и рассчитанных задач.

    Returns:
        dict: Статус всех необходимых данных для формирования задач в формате:
              {
                  "success": bool,
                  "status": {
                      "reportsLoaded": {
                          "detailed_report": bool,
                          "documents_report": bool
                      },
                      "processedData": {
                          "checkResults": bool,
                          "tasks": bool
                      },
                      "taskCount": int
                  },
                  "message": str
              }

    Raises:
        HTTPException: 500 при ошибках получения статуса
    """
    try:
        cases_df = normalized_manager.get_cases_data()
        documents_df = normalized_manager.get_documents_data()
        check_results_df = normalized_manager.get_check_results_data()
        tasks_df = normalized_manager.get_tasks_data()

        status = {
            "reportsLoaded": {
                "detailed_report": not cases_df.empty,
                "documents_report": not documents_df.empty
            },
            "processedData": {
                "checkResults": not check_results_df.empty,
                "tasks": not tasks_df.empty
            },
            "taskCount": len(tasks_df) if not tasks_df.empty else 0
        }

        return {
            "success": True,
            "status": status,
            "message": "Статус данных для задач получен"
        }

    except Exception as e:
        print(f"❌ Ошибка получения статуса: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса: {str(e)}")


@router.get("/{task_code}")
async def get_task_details(task_code: str):
    """
    Получение детальной информации по задаче по уникальному taskCode.

    Args:
        task_code (str): Уникальный код задачи (например: TASK_000001)

    Returns:
        dict: Детальная информация о задаче в формате:
              {
                  "success": bool,
                  "task": Dict or None,
                  "message": str
              }

    Raises:
        HTTPException: 404 если задачи не рассчитаны
        HTTPException: 500 при ошибках получения данных
    """
    try:
        tasks_df = normalized_manager.get_tasks_data()
        check_results_df = normalized_manager.get_check_results_data()
        checks_df = normalized_manager.get_checks_data()
        cases_df = normalized_manager.get_cases_data()
        documents_df = normalized_manager.get_documents_data()

        if tasks_df.empty:
            raise HTTPException(status_code=404, detail="Нет рассчитанных задач")

        task_match = tasks_df[tasks_df["taskCode"] == task_code]
        if task_match.empty:
            return {"success": True, "task": None, "message": f"Задача '{task_code}' не найдена"}

        task_df = task_match.copy()

        # 1. Присоединяем check_results
        if not check_results_df.empty:
            task_df = task_df.merge(
                check_results_df[["checkResultCode", "targetId", "checkCode", "monitoringStatus", "executionDatePlan"]],
                on="checkResultCode",
                how="left"
            )

        # 2. Присоединяем checks_df для checkName и stageCode
        if not checks_df.empty and "checkCode" in task_df.columns:
            task_df = task_df.merge(
                checks_df[["checkCode", "checkName", "stageCode"]],
                on="checkCode",
                how="left"
            )
            task_df["failedCheck"] = task_df["checkName"].fillna("")
            task_df["caseStage"] = task_df["stageCode"].fillna("Не указан")

        # 3. Присоединяем cases_df
        if not cases_df.empty and "targetId" in task_df.columns:
            task_df = task_df.merge(
                cases_df[[COLUMNS["CASE_CODE"], COLUMNS["RESPONSIBLE_EXECUTOR"]]],
                left_on="targetId",
                right_on=COLUMNS["CASE_CODE"],
                how="left"
            )
            task_df["caseCode"] = task_df[COLUMNS["CASE_CODE"]].fillna("")
            task_df["responsibleExecutor"] = task_df[COLUMNS["RESPONSIBLE_EXECUTOR"]].fillna("")
            task_df["sourceType"] = "detailed"

        # 4. Присоединяем documents_df (если не нашли в cases_df)
        if not documents_df.empty and "targetId" in task_df.columns:
            doc_cols = [COLUMNS["TRANSFER_CODE"], COLUMNS["DOCUMENT_CASE_CODE"],
                        COLUMNS["DOCUMENT_TYPE"], COLUMNS["DEPARTMENT_CATEGORY"],
                        COLUMNS["DOCUMENT_REQUEST_CODE"]]
            available = [c for c in doc_cols if c in documents_df.columns]
            if available:
                task_df = task_df.merge(
                    documents_df[available],
                    left_on="targetId",
                    right_on=COLUMNS["TRANSFER_CODE"],
                    how="left",
                    suffixes=("", "_doc")
                )
                if task_df["caseCode"].isna().all():
                    task_df["caseCode"] = task_df[COLUMNS["DOCUMENT_CASE_CODE"]].fillna("")
                task_df["documentType"] = task_df.get(COLUMNS["DOCUMENT_TYPE"], "")
                task_df["department"] = task_df.get(COLUMNS["DEPARTMENT_CATEGORY"], "")
                task_df["requestCode"] = task_df.get(COLUMNS["DOCUMENT_REQUEST_CODE"], "")
                task_df["sourceType"] = task_df["sourceType"].fillna("documents")

        # Заполнение пропусков + пользовательские правки
        task_df = _merge_with_overrides(task_df)
        task_data = task_df.iloc[0].to_dict()
        task_data["caseCode"] = task_data.get("caseCode", "")
        task_data["responsibleExecutor"] = task_data.get("responsibleExecutor", "")
        task_data["sourceType"] = task_data.get("sourceType", "")
        task_data["createdDate"] = task_data.get("createdAt", "")

        # Очистка NaN
        for k, v in task_data.items():
            if pd.isna(v):
                task_data[k] = ""

        return {"success": True, "task": task_data, "message": "Задача найдена"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


# ===================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====================

def _merge_with_check_results(tasks_df: pd.DataFrame, check_results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Присоединяет к задачам данные из результатов проверок.

    Добавляет колонки: targetId, checkCode, monitoringStatus, stageCode.

    Args:
        tasks_df (pd.DataFrame): DataFrame с задачами (содержит checkResultCode)
        check_results_df (pd.DataFrame): DataFrame с результатами проверок

    Returns:
        pd.DataFrame: DataFrame задач с добавленными колонками из check_results
    """
    if check_results_df.empty:
        tasks_df["targetId"] = None
        tasks_df["checkCode"] = None
        tasks_df["monitoringStatus"] = None
        tasks_df["stageCode"] = None
        tasks_df["checkName"] = None
        return tasks_df

    columns = ["checkResultCode", "targetId", "checkCode", "monitoringStatus", "executionDatePlan"]
    available = [col for col in columns if col in check_results_df.columns]

    tasks_df = tasks_df.merge(
        check_results_df[available],
        on="checkResultCode",
        how="left"
    )

    # Добавление stageCode и checkName из checks_df
    checks_df = normalized_manager.get_checks_data()
    if not checks_df.empty:
        tasks_df = tasks_df.merge(
            checks_df[["checkCode", "stageCode", "checkName"]],
            on="checkCode",
            how="left",
            suffixes=("", "_checks")
        )
        if "stageCode_checks" in tasks_df.columns:
            tasks_df["stageCode"] = tasks_df["stageCode_checks"].fillna(tasks_df.get("stageCode"))
            tasks_df = tasks_df.drop(columns=["stageCode_checks"])
        if "checkName_checks" in tasks_df.columns:
            tasks_df["checkName"] = tasks_df["checkName_checks"].fillna("")
            tasks_df = tasks_df.drop(columns=["checkName_checks"])
    else:
        tasks_df["stageCode"] = None
        tasks_df["checkName"] = None

    return tasks_df


def _merge_with_cases(tasks_df: pd.DataFrame, cases_df: pd.DataFrame) -> pd.DataFrame:
    """
    Присоединяет к задачам данные дел из детального отчета.

    Добавляет колонки: responsibleExecutor, caseCode.
    Соединение выполняется по targetId = COLUMNS["CASE_CODE"].

    Args:
        tasks_df (pd.DataFrame): DataFrame с задачами (содержит targetId)
        cases_df (pd.DataFrame): DataFrame с данными дел

    Returns:
        pd.DataFrame: DataFrame задач с добавленными колонками из дел
    """
    if cases_df.empty or "targetId" not in tasks_df.columns:
        if "responsibleExecutor" not in tasks_df.columns:
            tasks_df["responsibleExecutor"] = "unknown"
        if "caseCode" not in tasks_df.columns:
            tasks_df["caseCode"] = "unknown"
        return tasks_df

    case_columns = [COLUMNS["CASE_CODE"], COLUMNS["RESPONSIBLE_EXECUTOR"]]
    available = [col for col in case_columns if col in cases_df.columns]

    merged = tasks_df.merge(
        cases_df[available],
        left_on="targetId",
        right_on=COLUMNS["CASE_CODE"],
        how="left"
    )

    if COLUMNS["RESPONSIBLE_EXECUTOR"] in merged.columns:
        merged["responsibleExecutor"] = merged[COLUMNS["RESPONSIBLE_EXECUTOR"]].fillna("unknown")
    else:
        merged["responsibleExecutor"] = "unknown"

    if COLUMNS["CASE_CODE"] in merged.columns:
        merged["caseCode"] = merged[COLUMNS["CASE_CODE"]].fillna("unknown")
    else:
        merged["caseCode"] = "unknown"

    return merged


def _merge_with_documents(tasks_df: pd.DataFrame, documents_df: pd.DataFrame) -> pd.DataFrame:
    """
    Присоединяет к задачам данные документов из отчета документов.

    Добавляет колонки: documentType, department, transferCode, requestCode.
    Соединение выполняется по targetId = COLUMNS["TRANSFER_CODE"].

    Args:
        tasks_df (pd.DataFrame): DataFrame с задачами (содержит targetId)
        documents_df (pd.DataFrame): DataFrame с данными документов

    Returns:
        pd.DataFrame: DataFrame задач с добавленными колонками из документов
    """
    if documents_df.empty or "targetId" not in tasks_df.columns:
        return tasks_df

    doc_columns = [
        COLUMNS["TRANSFER_CODE"],
        COLUMNS["DOCUMENT_TYPE"],
        COLUMNS["DEPARTMENT_CATEGORY"],
        COLUMNS["DOCUMENT_REQUEST_CODE"]
    ]
    available = [col for col in doc_columns if col in documents_df.columns]

    if not available:
        return tasks_df

    merged = tasks_df.merge(
        documents_df[available],
        left_on="targetId",
        right_on=COLUMNS["TRANSFER_CODE"],
        how="left"
    )

    if COLUMNS["DOCUMENT_TYPE"] in merged.columns:
        merged["documentType"] = merged[COLUMNS["DOCUMENT_TYPE"]]
    if COLUMNS["DEPARTMENT_CATEGORY"] in merged.columns:
        merged["department"] = merged[COLUMNS["DEPARTMENT_CATEGORY"]]
    if COLUMNS["TRANSFER_CODE"] in merged.columns:
        merged["transferCode"] = merged[COLUMNS["TRANSFER_CODE"]]
    if COLUMNS["DOCUMENT_REQUEST_CODE"] in merged.columns:
        merged["requestCode"] = merged[COLUMNS["DOCUMENT_REQUEST_CODE"]]

    return merged

def _merge_with_overrides(tasks_df: pd.DataFrame) -> pd.DataFrame:
    """
    Присоединяет к задачам пользовательские переопределения.

    Если для задачи есть оверрайд, поля isCompleted, executionDatePlan, executionDateTimeFact
    берутся из оверрайда. Также добавляются поля hasOverride, shiftCode,
    shiftName, daysToAdd, originalPlannedDate.

    Args:
        tasks_df (pd.DataFrame): DataFrame с задачами (содержит taskCode, executionDatePlan)

    Returns:
        pd.DataFrame: DataFrame задач с добавленными полями из оверрайдов
    """
    overrides_df = normalized_manager.get_user_overrides_data()

    # Инициализация полей по умолчанию
    tasks_df["hasOverride"] = False
    tasks_df["shiftCode"] = None
    tasks_df["shiftName"] = None
    tasks_df["daysToAdd"] = None
    tasks_df["originalPlannedDate"] = tasks_df["executionDatePlan"].copy() if "executionDatePlan" in tasks_df.columns else None

    if overrides_df.empty:
        return tasks_df

    # Сохраняем оригинальную executionDatePlan до мержа
    if "executionDatePlan" in tasks_df.columns:
        original_planned = tasks_df["executionDatePlan"].copy()
    else:
        original_planned = pd.Series([pd.NaT] * len(tasks_df), index=tasks_df.index)

    # Мерж с оверрайдами
    override_cols = ["taskCode", "isCompleted", "executionDatePlan", "executionDateTimeFact", "shiftCode"]
    available = [col for col in override_cols if col in overrides_df.columns]

    tasks_df = tasks_df.merge(
        overrides_df[available],
        on="taskCode",
        how="left",
        suffixes=("", "_override")
    )

    # Применяем оверрайд: если поле из оверрайда не NaN, берем его
    if "isCompleted_override" in tasks_df.columns:
        # Используем where вместо fillna для избежания downcasting
        tasks_df["isCompleted"] = tasks_df["isCompleted_override"].where(
            tasks_df["isCompleted_override"].notna(),
            tasks_df["isCompleted"]
        )
        tasks_df = tasks_df.drop(columns=["isCompleted_override"])

    if "executionDatePlan_override" in tasks_df.columns:
        tasks_df["executionDatePlan"] = tasks_df["executionDatePlan_override"].where(
            tasks_df["executionDatePlan_override"].notna(),
            tasks_df["executionDatePlan"]
        )
        tasks_df = tasks_df.drop(columns=["executionDatePlan_override"])

    if "executionDateTimeFact_override" in tasks_df.columns:
        tasks_df["executionDateTimeFact"] = tasks_df["executionDateTimeFact_override"].where(
            tasks_df["executionDateTimeFact_override"].notna(),
            tasks_df["executionDateTimeFact"] if "executionDateTimeFact" in tasks_df.columns else None
        )
        tasks_df = tasks_df.drop(columns=["executionDateTimeFact_override"])

    if "shiftCode_override" in tasks_df.columns:
        tasks_df["shiftCode"] = tasks_df["shiftCode_override"]
        tasks_df = tasks_df.drop(columns=["shiftCode_override"])

    # Устанавливаем флаг hasOverride
    tasks_df["hasOverride"] = tasks_df["shiftCode"].notna() | (
        tasks_df["isCompleted"] != tasks_df["isCompleted"].where(tasks_df["shiftCode"].isna())
    )

    # Восстанавливаем originalPlannedDate
    tasks_df["originalPlannedDate"] = original_planned

    # Добавляем shiftName и daysToAdd из конфига
    from backend.app.task_manager.config.shift_reasons_config import SHIFT_REASONS_BY_CODE

    def get_shift_name(code):
        if pd.isna(code):
            return None
        return SHIFT_REASONS_BY_CODE.get(code, {}).get("shiftName")

    def get_days_to_add(code):
        if pd.isna(code):
            return None
        return SHIFT_REASONS_BY_CODE.get(code, {}).get("daysToAdd")

    tasks_df["shiftName"] = tasks_df["shiftCode"].apply(get_shift_name)
    tasks_df["daysToAdd"] = tasks_df["shiftCode"].apply(get_days_to_add)

    return tasks_df
