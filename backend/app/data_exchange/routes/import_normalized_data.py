# backend/app/data_exchange/routes/import_normalized_data.py
"""
Маршруты для импорта данных в NormalizedDataManager из сетевой папки.

Предоставляет эндпоинты для получения информации о доступных данных
и загрузки всех данных или пользовательских переопределений.
"""
import pandas as pd
from fastapi import APIRouter, HTTPException, Depends

from backend.app.administration_settings.modules.authorization_logic import get_current_user
from backend.app.data_exchange.modules.data_io import get_user_overrides_folder
from backend.app.administration_settings.modules.user_models import UserSession
from backend.app.common.config.column_names import COLUMNS
from backend.app.administration_settings.modules.decorators import require_manager_or_admin
from backend.app.data_exchange.modules.data_io import (
    load_dataframe,
    load_metadata
)
from backend.app.data_management.modules.normalized_data_manager import normalized_manager

router = APIRouter(prefix="/api/exchange", tags=["data_exchange"])


@router.get("/info")
async def get_exchange_info():
    """
    Возвращает информацию о данных, доступных в папке обмена.

    Читает metadata.json и metadata_overrides.json без загрузки самих данных.
    Используется фронтендом для отображения модального окна с информацией
    перед выполнением импорта.

    Returns:
        Dict: Информация о доступных данных
    """
    try:
        metadata = load_metadata("metadata.json")
        overrides_metadata = load_metadata("metadata_overrides.json")

        return {
            "success": True,
            "metadata": metadata,
            "overrides_metadata": overrides_metadata,
            "message": "Информация о данных получена"
        }

    except Exception as e:
        print(f"❌ Ошибка получения информации: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.post("/import/all")
async def import_all_data():
    """
    Загружает все данные из папки обмена в NormalizedDataManager.

    Читает metadata.json, загружает все перечисленные в нем Parquet-файлы
    и сохраняет их в соответствующие хранилища менеджера.

    Stages и checks не заменяются, но сравниваются с текущими —
    при расхождении выводится предупреждение.

    Returns:
        Dict: Результат импорта с информацией о загруженных файлах
    """
    try:
        # Проверка наличия метаданных
        metadata = load_metadata("metadata.json")
        if not metadata:
            raise HTTPException(status_code=400, detail="Нет данных для импорта. Папка обмена пуста.")

        files_info = metadata.get("files", {})
        if not files_info:
            raise HTTPException(status_code=400, detail="Метаданные не содержат информации о файлах.")

        imported_files = []

        # Импорт детального отчета
        filename = "source_detailed_report.parquet"
        if filename in files_info:
            df = load_dataframe(filename)
            if df is not None:
                normalized_manager.set_cases_data(df)
                imported_files.append(filename)

        # Импорт отчета документов
        filename = "source_documents_report.parquet"
        if filename in files_info:
            df = load_dataframe(filename)
            if df is not None:
                normalized_manager.set_documents_data(df)
                imported_files.append(filename)

        # Импорт результатов проверок
        filename = "check_results.parquet"
        if filename in files_info:
            df = load_dataframe(filename)
            if df is not None:
                normalized_manager.set_check_results_data(df)
                imported_files.append(filename)

        # Импорт задач
        filename = "tasks.parquet"
        if filename in files_info:
            df = load_dataframe(filename)
            if df is not None:
                normalized_manager.set_tasks_data(df)
                imported_files.append(filename)

        # Проверка этапов (без замены)
        filename = "stages.parquet"
        if filename in files_info:
            new_stages = load_dataframe(filename)
            if new_stages is not None:
                current_stages = normalized_manager.get_stages_data()
                if not new_stages.equals(current_stages):
                    print("⚠️ Импортированные этапы отличаются от текущих! Возможны ошибки при работе.")
                else:
                    print("✅ Импортированные этапы совпадают с текущими.")

        # Проверка проверок (без замены)
        filename = "checks.parquet"
        if filename in files_info:
            new_checks = load_dataframe(filename)
            if new_checks is not None:
                current_checks = normalized_manager.get_checks_data()
                if not new_checks.equals(current_checks):
                    print("⚠️ Импортированные проверки отличаются от текущих! Возможны ошибки при работе.")
                else:
                    print("✅ Импортированные проверки совпадают с текущими.")

        # Сброс времени загрузки данных
        normalized_manager.reset_data_loaded_at()

        if not imported_files:
            raise HTTPException(status_code=400, detail="Не удалось загрузить ни один файл.")

        return {
            "success": True,
            "imported_files": imported_files,
            "metadata": metadata,
            "message": f"Импорт выполнен успешно. Загружено {len(imported_files)} файлов."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка импорта данных: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка импорта: {str(e)}")


@router.post("/import/user-overrides")
async def import_user_overrides():
    """
    Загружает пользовательские переопределения из папки обмена.

    Читает metadata_overrides.json, загружает user_overrides.parquet
    и сохраняет в _user_overrides.

    Returns:
        Dict: Результат импорта с информацией о загруженных файлах
    """
    try:
        # Проверка наличия метаданных
        metadata = load_metadata("metadata_overrides.json")
        if not metadata:
            raise HTTPException(status_code=400, detail="Нет переопределений для импорта. Папка обмена пуста.")

        files_info = metadata.get("files", {})
        filename = "user_overrides.parquet"

        if filename not in files_info:
            raise HTTPException(status_code=400, detail="Файл переопределений не найден в метаданных.")

        df = load_dataframe(filename)
        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="Файл переопределений пуст.")

        normalized_manager.set_user_overrides_data(df)

        return {
            "success": True,
            "imported_files": [filename],
            "metadata": metadata,
            "message": f"Импорт переопределений выполнен успешно. Загружено {len(df)} записей."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка импорта переопределений: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка импорта: {str(e)}")



@router.post("/import/user-overrides/collect")
@require_manager_or_admin
async def collect_user_overrides(
    current_user: UserSession = Depends(get_current_user)
):
    """
    Собирает пользовательские переопределения задач из индивидуальных файлов
    сотрудников в сводный DataFrame и загружает в менеджер данных.

    Доступно только руководителям и администраторам.

    Логика работы:
    1. Загружает базовый сводный user_overrides.parquet из корня app_data/
       (если существует) как основу.
    2. Сканирует папку app_data/user_overrides/ на наличие файлов
       user_overrides_{login}.parquet.
    3. Для каждого файла: сравнивает записи по taskCode,
       оставляя запись с более поздним updatedAt.
    4. Сохраняет результат в normalized_manager._user_overrides.

    Returns:
        Dict: Результат сбора с информацией о количестве записей и источниках
    """
    try:
        user_overrides_folder = get_user_overrides_folder()
        exchange_folder = user_overrides_folder.parent  # app_data/

        # === Шаг 1: Загружаем базовый сводный файл ===
        base_filename = "user_overrides.parquet"
        base_filepath = exchange_folder / base_filename

        if base_filepath.exists():
            base_df = load_dataframe(base_filename, folder=exchange_folder)
            print(f"✅ Загружен базовый сводный файл: {len(base_df)} записей")
        else:
            # Создаём пустой DataFrame с правильными колонками
            base_df = pd.DataFrame(columns=[
                "taskCode", "checkResultCode", "taskText", "reasonText",
                "createdAt", "isCompleted", "executionDateTimeFact",
                "executionDatePlan", "shiftCode", "createdBy", "updatedAt"
            ])
            print("ℹ️ Базовый сводный файл не найден, начинаем с пустого DataFrame")

        # === Шаг 2: Сканируем папку user_overrides/ ===
        pattern = "user_overrides_*.parquet"
        user_files = sorted(user_overrides_folder.glob(pattern))

        if not user_files:
            # Нет индивидуальных файлов — загружаем только сводный (если он был)
            if base_filepath.exists():
                normalized_manager.set_user_overrides_data(base_df)
                return {
                    "success": True,
                    "total_records": len(base_df),
                    "sources": [],
                    "message": f"Загружен только сводный файл. {len(base_df)} записей."
                }
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Нет данных для сбора. Отсутствует сводный файл и файлы сотрудников."
                )

        # === Шаг 3: Обрабатываем каждый файл сотрудника ===
        sources = []

        for filepath in user_files:
            # Извлекаем логин из имени файла: user_overrides_{login}.parquet
            filename = filepath.name
            login = filename.replace("user_overrides_", "").replace(".parquet", "")
            sources.append(login)

            # Загружаем DataFrame сотрудника
            new_df = load_dataframe(filename, folder=user_overrides_folder)
            if new_df is None or new_df.empty:
                print(f"⚠️ Файл {filename} пуст, пропускаем")
                continue

            # Для каждого taskCode из нового файла — разрешаем конфликт по updatedAt
            has_updated_at = "updatedAt" in base_df.columns and "updatedAt" in new_df.columns

            if has_updated_at:
                # Объединяем базу и новый файл по taskCode
                merged = pd.concat([base_df, new_df], ignore_index=True)

                # Для каждого taskCode оставляем запись с максимальным updatedAt
                merged["updatedAt"] = pd.to_datetime(merged["updatedAt"], errors="coerce")
                idx = merged.groupby("taskCode")["updatedAt"].idxmax()
                base_df = merged.loc[idx].reset_index(drop=True)

                print(f"✅ Обработан файл {filename}: {len(new_df)} записей, конфликты разрешены по updatedAt (login: {login})")
            else:
                # Старое поведение: новый перезаписывает старый
                new_task_codes = set(new_df["taskCode"].tolist())
                base_df = base_df[~base_df["taskCode"].isin(new_task_codes)]
                base_df = pd.concat([base_df, new_df], ignore_index=True)

                print(f"✅ Обработан файл {filename}: {len(new_df)} записей (login: {login})")

        # === Шаг 4: Сохраняем результат в менеджер ===
        normalized_manager.set_user_overrides_data(base_df)

        return {
            "success": True,
            "total_records": len(base_df),
            "sources": sources,
            "message": f"Собрано переопределений от {len(sources)} сотрудников. Всего {len(base_df)} записей."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка сбора переопределений: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сбора переопределений: {str(e)}")

@router.post("/import/user-overrides/check-violations")
@require_manager_or_admin
async def check_override_violations(
    current_user: UserSession = Depends(get_current_user)
):
    """
    Проверяет оверрайды на нарушения и создаёт репорт.

    Находит задачи, которые сотрудники отметили как выполненные,
    но при новом анализе они снова появились в списке задач.
    Для каждой задачи определяет ответственного исполнителя
    из исходных данных (дела или документы).

    Доступно только руководителям и администраторам.

    Returns:
        Dict: Результат проверки с путём к репорту
    """
    try:
        tasks_df = normalized_manager.get_tasks_data()
        overrides_df = normalized_manager.get_user_overrides_data()
        check_results_df = normalized_manager.get_check_results_data()
        cases_df = normalized_manager.get_cases_data()
        documents_df = normalized_manager.get_documents_data()

        if tasks_df.empty:
            raise HTTPException(status_code=400, detail="Нет задач для проверки.")

        if overrides_df.empty:
            return {
                "success": True,
                "violations_found": False,
                "message": "Нет пользовательских переопределений для проверки."
            }

        # Находим выполненные оверрайды
        completed_overrides = overrides_df[overrides_df["isCompleted"] == True].copy()

        if completed_overrides.empty:
            return {
                "success": True,
                "violations_found": False,
                "message": "Нет выполненных задач в переопределениях."
            }

        # Находим задачи, которые снова появились
        violated = tasks_df[tasks_df["taskCode"].isin(completed_overrides["taskCode"])].copy()

        if violated.empty:
            return {
                "success": True,
                "violations_found": False,
                "message": "Нарушений не найдено. Все выполненные задачи отсутствуют в новых."
            }

        # === Шаг 1: Получаем targetId из check_results ===
        if not check_results_df.empty and "checkResultCode" in violated.columns:
            violated = violated.merge(
                check_results_df[["checkResultCode", "targetId"]],
                on="checkResultCode",
                how="left"
            )

        # === Шаг 2: Ищем исполнителя через дела (targetId = caseCode) ===
        if not cases_df.empty and "targetId" in violated.columns:
            case_cols = [COLUMNS["CASE_CODE"], COLUMNS["RESPONSIBLE_EXECUTOR"]]
            available = [c for c in case_cols if c in cases_df.columns]
            if available:
                violated = violated.merge(
                    cases_df[available],
                    left_on="targetId",
                    right_on=COLUMNS["CASE_CODE"],
                    how="left",
                    suffixes=("", "_case")
                )

        # === Шаг 3: Ищем исполнителя через документы (targetId = transferCode) ===
        if not documents_df.empty and "targetId" in violated.columns:
            doc_cols = [COLUMNS["TRANSFER_CODE"], COLUMNS["RESPONSIBLE_EXECUTOR"]]
            available = [c for c in doc_cols if c in documents_df.columns]
            if available:
                violated = violated.merge(
                    documents_df[available],
                    left_on="targetId",
                    right_on=COLUMNS["TRANSFER_CODE"],
                    how="left",
                    suffixes=("", "_doc")
                )

        # === Шаг 4: Берём первого непустого исполнителя ===
        if COLUMNS["RESPONSIBLE_EXECUTOR"] in violated.columns:
            doc_executor_col = f"{COLUMNS['RESPONSIBLE_EXECUTOR']}_doc"
            if doc_executor_col in violated.columns:
                violated["responsibleExecutor"] = (
                    violated[COLUMNS["RESPONSIBLE_EXECUTOR"]]
                    .fillna(violated[doc_executor_col])
                )
            else:
                violated["responsibleExecutor"] = violated[COLUMNS["RESPONSIBLE_EXECUTOR"]]
        else:
            violated["responsibleExecutor"] = None

        violated["responsibleExecutor"] = violated["responsibleExecutor"].fillna("Неизвестно")

        # === Шаг 5: Джойним оверрайды для информации о том, кто и когда отметил выполненным ===
        if not overrides_df.empty and "taskCode" in violated.columns:
            override_info_cols = ["taskCode", "isCompleted", "createdBy", "updatedAt"]
            available_override = [c for c in override_info_cols if c in overrides_df.columns]
            if available_override:
                violated = violated.merge(
                    overrides_df[available_override],
                    on="taskCode",
                    how="left",
                    suffixes=("", "_override")
                )
                # Переименовываем для ясности в репорте
                if "isCompleted_override" in violated.columns:
                    violated["overrideIsCompleted"] = violated["isCompleted_override"]
                    violated = violated.drop(columns=["isCompleted_override"])
                if "createdBy_override" in violated.columns:
                    violated["overrideCreatedBy"] = violated["createdBy_override"]
                    violated = violated.drop(columns=["createdBy_override"])
                if "updatedAt_override" in violated.columns:
                    violated["updatedAt"] = violated["updatedAt_override"]
                    violated = violated.drop(columns=["updatedAt_override"])

        # === Шаг 6: Оставляем только нужные колонки для репорта ===
        report_columns = [
            "taskCode", "taskText", "reasonText", "createdAt", "createdBy",
            "targetId", "monitoringStatus", "responsibleExecutor",
            "updatedAt", "overrideIsCompleted", "overrideCreatedBy"
        ]
        available_report_cols = [c for c in report_columns if c in violated.columns]
        violated = violated[available_report_cols]

        # Создаём репорт
        from backend.app.reporting.modules.report_builder import build_report

        info_metadata = {
            "Всего нарушений": str(len(violated)),
            "Проверил": current_user.login or "unknown",
        }

        report_path = build_report(
            info_metadata=info_metadata,
            data_df=violated,
            report_type="override_violations",
            created_by=current_user.login or "unknown"
        )

        return {
            "success": True,
            "violations_found": True,
            "violations_count": len(violated),
            "report_path": report_path,
            "message": f"Найдено {len(violated)} нарушений. Репорт сохранен."
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка проверки нарушений: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка проверки: {str(e)}")

