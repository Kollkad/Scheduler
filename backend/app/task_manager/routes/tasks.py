# backend/app/task_manager/routes/tasks.py
"""
Маршруты FastAPI для управления задачами.

Предоставляет API endpoints для расчета, получения, сохранения
и управления задачами различных типов производств.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
import pandas as pd

from backend.app.data_management.modules.data_manager import data_manager
from backend.app.task_manager.modules.task_analyzer import task_analyzer

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/calculate")
async def calculate_tasks(executor: Optional[str] = Query(None,
                                                          description="Фильтр по ответственному исполнителю")):
    """
    Расчет всех задач на основе загруженных данных.

    Выполняет анализ данных и формирование задач для всех доступных
    типов производств с возможностью фильтрации по исполнителю.
    Для расчета необходимы предварительно выполненные анализы:
    - исковое производство (analyze_lawsuit)
    - приказное производство (analyze_order)
    - анализ документов (analyze_documents)

    Args:
        executor (str, optional): Ответственный исполнитель для фильтрации

    Returns:
        dict: Результат расчета задач с статистикой

    Raises:
        HTTPException: 400 если нет данных для расчета, 500 при ошибках
    """
    try:
        # Проверка наличия данных для расчета задач
        has_lawsuit = data_manager.get_processed_data("lawsuit_staged") is not None
        has_order = data_manager.get_processed_data("order_staged") is not None
        has_documents = data_manager.get_processed_data("documents_processed") is not None

        if not (has_lawsuit or has_order or has_documents):
            raise HTTPException(
                status_code=400,
                detail="Нет данных для расчета задач. Сначала выполните анализы: /analyze_lawsuit, /analyze_order, /analyze_documents"
            )

        print("🔄 Начинается расчет задач...")

        # Проверка наличия кэшированных задач
        existing_tasks = data_manager.get_processed_data("tasks")
        if existing_tasks is not None and not existing_tasks.empty:
            print("✅ Используем кэшированные задачи")
            all_tasks = existing_tasks.to_dict('records')
        else:
            # Выполнение расчета новых задач
            all_tasks = task_analyzer.analyze_all_tasks()
            print(f"✅ Рассчитано новых задач: {len(all_tasks)}")

        # Применение фильтра по исполнителю
        if executor:
            filtered_tasks = [task for task in all_tasks if task.get("responsibleExecutor") == executor]
            print(f"✅ Отфильтровано задач для {executor}: {len(filtered_tasks)} из {len(all_tasks)}")
        else:
            filtered_tasks = all_tasks

        return {
            "success": True,
            "totalTasks": len(all_tasks),
            "filteredTasks": len(filtered_tasks),
            "executor": executor,
            "data": filtered_tasks,
            "message": f"Рассчитано {len(filtered_tasks)} задач" + (f" для {executor}" if executor else "")
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка расчета задач: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка расчета задач: {str(e)}")


@router.get("/list")
async def get_tasks_list(
        responsibleExecutor: Optional[str] = Query(None,
                                                   description="Ответственный исполнитель")
):
    """
    Получение списка задач с фильтрами.

    Args:
        responsibleExecutor (str, optional): Фильтр по ответственному исполнителю

    Returns:
        dict: Список задач с метаданными

    Raises:
        HTTPException: Возникает при ошибках получения данных
    """
    try:
        # Получение кэшированных данных задач
        tasks_df = data_manager.get_processed_data("tasks")

        if tasks_df is None or tasks_df.empty:
            return {
                "success": True,
                "tasks": [],
                "totalTasks": 0,
                "filteredCount": 0,
                "message": "Нет рассчитанных задач. Выполните /calculate сначала."
            }

        all_tasks = tasks_df.to_dict('records')
        filtered_tasks = all_tasks

        # Применение фильтра по исполнителю
        if responsibleExecutor:
            filtered_tasks = [task for task in filtered_tasks if
                              str(task.get("responsibleExecutor", "")).strip() == responsibleExecutor]

        def clean_json_value(value):
            import math
            if isinstance(value, float):
                if math.isnan(value) or math.isinf(value):
                    return None
            return value

        # ДОБАВЬ ЭТУ СТРОКУ - очистка значений перед возвратом
        filtered_tasks = [{k: clean_json_value(v) for k, v in task.items()} for task in filtered_tasks]

        return {
            "success": True,
            "totalTasks": len(all_tasks),
            "filteredCount": len(filtered_tasks),
            "tasks": filtered_tasks,
            "message": f"Найдено {len(filtered_tasks)} задач" +
                       (f" для исполнителя {responsibleExecutor}" if responsibleExecutor else "")
        }

    except Exception as e:
        print(f"❌ Ошибка получения задач: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения задач: {str(e)}")


@router.get("/save-all")
async def save_all_tasks():
    """
    Сохранение всех рассчитанных задач в Excel файл.

    Returns:
        dict: Результат сохранения с информацией о файле

    Raises:
        HTTPException: Возникает при отсутствии задач или ошибках сохранения
    """
    try:
        tasks_df = data_manager.get_processed_data("tasks")

        if tasks_df is None or tasks_df.empty:
            raise HTTPException(
                status_code=400,
                detail="Нет задач для сохранения. Выполните /calculate сначала."
            )

        from datetime import datetime
        import os

        # Создание директории для сохранения файлов
        os.makedirs("backend/app/data", exist_ok=True)

        # Генерация имени файла с временной меткой
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tasks_export_{timestamp}.xlsx"
        filepath = os.path.join("backend/app/data", filename)

        # Сохранение задач в Excel файл
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

    Returns:
        dict: Статус всех необходимых данных для формирования задач

    Raises:
        HTTPException: Возникает при ошибках получения статуса
    """
    try:
        # Формирование статуса всех компонентов системы
        status = {
            "reportsLoaded": data_manager.is_loaded("both"),
            "processedData": {
                "lawsuitStaged": data_manager.get_processed_data("lawsuit_staged") is not None,
                "orderStaged": data_manager.get_processed_data("order_staged") is not None,
                "documentsProcessed": data_manager.get_processed_data("documents_processed") is not None,
                "tasks": data_manager.get_processed_data("tasks") is not None
            },
            "taskCount": 0
        }

        # Подсчет количества задач
        tasks_df = data_manager.get_processed_data("tasks")
        if tasks_df is not None:
            status["taskCount"] = len(tasks_df)

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
        dict: Детальная информация о задаче

    Raises:
        HTTPException: Возникает при ошибках поиска задачи
    """
    try:
        tasks_df = data_manager.get_processed_data("tasks")

        if tasks_df is None or tasks_df.empty:
            raise HTTPException(
                status_code=404,
                detail="Нет рассчитанных задач. Выполните /calculate сначала."
            )

        # Поиск задачи по уникальному коду
        task_match = tasks_df[tasks_df["taskCode"] == task_code]

        if task_match.empty:
            return {
                "success": True,
                "task": None,
                "message": f"Задача '{task_code}' не найдена"
            }

        # Преобразование данных задачи и обработка NaN значений
        task_data = task_match.iloc[0].to_dict()
        task_data = {k: ("" if pd.isna(v) else v) for k, v in task_data.items()}

        return {
            "success": True,
            "task": task_data,
            "message": "Задача найдена"
        }

    except Exception as e:
        print(f"❌ Ошибка получения деталей задачи: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения деталей задачи: {str(e)}"
        )