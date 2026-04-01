# backend/app/saving_results/routes/saving.py
"""
Модуль маршрутов FastAPI для сохранения обработанных данных в Excel файлы.

Предоставляет эндпоинты для экспорта различных типов отчетов:
- Очищенные исходные данные
- Результаты анализа производств
- Цветовую классификацию (радугу)
- Рассчитанные задачи
- Комплексные архивы всех данных
"""
import urllib
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import pandas as pd
import tempfile
import logging

from backend.app.common.config.column_names import COLUMNS
from backend.app.data_management.modules.data_manager import data_manager
from backend.app.saving_results.modules.saving_results_settings import (
    generate_filename,
    save_with_xlsxwriter_formatting,
    rename_columns_to_russian, add_source_columns_to_tasks
)

router = APIRouter(prefix="/api/save", tags=["saving"])

@router.get("/available-data")
async def get_available_data_status():
    """
    Получение статуса доступных данных для экспорта.

    Returns:
        dict: Статус загрузки основных отчетов
    """
    try:
        detailed_data = data_manager.get_detailed_data()
        documents_data = data_manager.get_documents_data()

        status = {
            "detailed_report": {
                "loaded": detailed_data is not None,
                "row_count": len(detailed_data) if detailed_data is not None else 0,
            },
            "documents_report": {
                "loaded": documents_data is not None,
                "row_count": len(documents_data) if documents_data is not None else 0,
            }
        }

        return {
            "success": True,
            "status": status,
            "message": "Статус данных получен"
        }

    except Exception as e:
        print(f"❌ Ошибка получения статуса: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса: {str(e)}")

@router.get("/all-processed-data")
async def get_all_processed_data_status():
    """
    Получение комплексного статуса всех обработанных данных.

    Returns:
        dict: Статус всех типов данных системы
    """
    try:
        detailed_data = data_manager.get_detailed_data()
        documents_data = data_manager.get_documents_data()
        lawsuit_data = data_manager.get_processed_data("lawsuit_staged")
        order_data = data_manager.get_processed_data("order_staged")
        documents_analysis_data = data_manager.get_processed_data("documents_processed")
        tasks_data = data_manager.get_processed_data("tasks")

        # Объединение данных производств для статуса
        terms_productions_data = pd.concat(
            [df for df in [lawsuit_data, order_data] if df is not None and not df.empty],
            ignore_index=True
        ) if (lawsuit_data is not None or order_data is not None) else None

        status = {
            "detailed_report": {
                "loaded": detailed_data is not None,
                "row_count": len(detailed_data) if detailed_data is not None else 0,
            },
            "documents_report": {
                "loaded": documents_data is not None,
                "row_count": len(documents_data) if documents_data is not None else 0,
            },
            "terms_productions": {
                "loaded": terms_productions_data is not None and not terms_productions_data.empty,
                "row_count": len(terms_productions_data) if terms_productions_data is not None else 0,
            },
            "documents_analysis": {
                "loaded": documents_analysis_data is not None,
                "row_count": len(documents_analysis_data) if documents_analysis_data is not None else 0,
            },
            "tasks": {
                "loaded": tasks_data is not None,
                "row_count": len(tasks_data) if tasks_data is not None else 0,
            }
        }

        return {
            "success": True,
            "status": status,
            "message": "Статус всех данных получен"
        }

    except Exception as e:
        print(f"❌ Ошибка получения статуса всех данных: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса: {str(e)}")

@router.get("/detailed-report")
async def save_detailed_report():
    """
    Сохранение очищенного детального отчета с профессиональным форматированием.

    Returns:
        FileResponse: Excel файл с детальным отчетом

    Raises:
        HTTPException: 400 если отчет не загружен
        HTTPException: 500 при ошибках сохранения
    """
    try:
        detailed_data = data_manager.get_detailed_data()

        if detailed_data is None or detailed_data.empty:
            raise HTTPException(status_code=400, detail="Детальный отчет не загружен")

        print(f"💾 Сохраняем детальный отчет: {len(detailed_data)} строк, {len(detailed_data.columns)} колонок")

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        # Сохранение с форматированием через xlsxwriter
        save_with_xlsxwriter_formatting(detailed_data, filepath, 'Детальный отчет')

        download_filename = generate_filename("detailed_report")

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        print(f"❌ Ошибка сохранения детального отчета: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")


@router.get("/documents-report")
async def save_documents_report():
    """
    Сохранение очищенного отчета документов с профессиональным форматированием.

    Returns:
        FileResponse: Excel файл с отчетом документов

    Raises:
        HTTPException: 400 если отчет не загружен
        HTTPException: 500 при ошибках сохранения
    """
    try:
        documents_data = data_manager.get_documents_data()

        if documents_data is None or documents_data.empty:
            raise HTTPException(status_code=400, detail="Отчет документов не загружен")

        print(f"💾 Сохраняем отчет документов: {len(documents_data)} строк, {len(documents_data.columns)} колонок")

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        # Сохранение с форматированием через xlsxwriter
        save_with_xlsxwriter_formatting(documents_data, filepath, 'Документы')

        download_filename = generate_filename("documents_report")

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        print(f"❌ Ошибка сохранения отчета документов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")


@router.get("/documents-analysis")
async def save_documents_analysis():
    """
    Сохранение результатов анализа документов с форматированием

    Returns:
        FileResponse: Excel файл с анализом документов

    Raises:
        HTTPException: 400 если данные не найдены
        HTTPException: 500 при ошибках сохранения
    """
    try:
        # Получаем обработанные данные документов
        documents_data = data_manager.get_processed_data("documents_processed")

        if documents_data is None or documents_data.empty:
            raise HTTPException(status_code=400, detail="Данные анализа документов не найдены")

        print(f"💾 Сохраняем анализ документов: {len(documents_data)} строк, {len(documents_data.columns)} колонок")

        # Создание временного файла Excel
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        # Сохранение с форматированием через xlsxwriter
        save_with_xlsxwriter_formatting(documents_data, filepath, 'Анализ документов', data_type="documents")

        download_filename = generate_filename("documents_analysis")

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        print(f"❌ Ошибка сохранения анализа документов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")


@router.get("/tasks")
async def save_tasks():
    """
    Сохранение рассчитанных задач по срокам обработки дел.

    Выполняет дополнительное обогащение данных задач информацией из исходных отчетов
    перед сохранением в Excel файл с профессиональным форматированием.

    Returns:
        FileResponse: Excel файл с задачами, обогащенный дополнительными колонками

    Raises:
        HTTPException: 400 если данные задач не найдены
        HTTPException: 500 при ошибках сохранения или обогащения данных

    Note:
        Обогащение включает добавление колонок из исходных отчетов:
        - Для детальных задач: REQUEST_TYPE, COURT, BORROWER, CASE_NAME
        - Для документных задач: REQUEST_TYPE, COURT_NAME, BORROWER, CASE_NAME
        Отсутствие некоторых колонок в исходных данных не вызывает ошибок
    """
    try:
        # Получение рассчитанных задач из менеджера данных
        tasks_data = data_manager.get_processed_data("tasks")

        if tasks_data is None or tasks_data.empty:
            raise HTTPException(status_code=400, detail="Данные задач не найдены")

        print(f"💾 Начинаем сохранение задач: {len(tasks_data)} строк, {len(tasks_data.columns)} колонок")

        # Получение исходных данных для обогащения задач
        detailed_cleaned = data_manager.get_detailed_data()
        documents_cleaned = data_manager.get_documents_data()

        # Обновление колонок задач дополнительными колонками из исходных отчетов
        if detailed_cleaned is not None or documents_cleaned is not None:
            try:
                tasks_data = add_source_columns_to_tasks(
                    tasks_data,
                    detailed_cleaned,
                    documents_cleaned
                )
            except Exception as enrich_error:
                # Продолжаем сохранение даже при ошибке обогащения
                print(f"⚠️ Ошибка обогащения задач: {enrich_error}")
                print("⚠️ Сохранение продолжается без дополнительных колонок")
        else:
            print("ℹ️ Исходные данные отсутствуют, сохранение без обогащения")

        # Переименование колонок и форматирование значений согласно настройкам
        tasks_data = rename_columns_to_russian(tasks_data, data_type="tasks")

        # Создание временного файла для сохранения
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        # Сохранение с форматированием через xlsxwriter
        save_with_xlsxwriter_formatting(tasks_data, filepath, 'Задачи', 'tasks')

        # Генерация имени файла для скачивания
        download_filename = generate_filename("tasks")

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка сохранения задач: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")

@router.get("/tasks-by-executor")
async def save_tasks_by_executor(responsibleExecutor: str):
    """
    Сохранение рассчитанных задач для конкретного ответственного исполнителя в Excel файл.

    Args:
        responsibleExecutor (str): Имя ответственного исполнителя для фильтрации задач.

    Returns:
        FileResponse: Excel файл с задачами исполнителя, обогащенный дополнительными колонками

    Raises:
        HTTPException: 400 если данные задач отсутствуют
        HTTPException: 500 при ошибках сохранения или обогащения данных
    """
    try:
        if not responsibleExecutor:
            raise HTTPException(status_code=400, detail="Не указан ответственный исполнитель")

        # Получение всех рассчитанных задач
        tasks_data = data_manager.get_processed_data("tasks")
        if tasks_data is None or tasks_data.empty:
            raise HTTPException(status_code=400, detail="Данные задач не найдены")

        # Фильтрация по исполнителю
        tasks_data = tasks_data[tasks_data["responsibleExecutor"] == responsibleExecutor]
        if tasks_data.empty:
            raise HTTPException(
                status_code=400,
                detail=f"Задачи для исполнителя '{responsibleExecutor}' не найдены"
            )

        # Получение исходных данных для обогащения
        detailed_cleaned = data_manager.get_detailed_data()
        documents_cleaned = data_manager.get_documents_data()

        # Обогащение дополнительными колонками
        if detailed_cleaned is not None or documents_cleaned is not None:
            try:
                tasks_data = add_source_columns_to_tasks(
                    tasks_data,
                    detailed_cleaned,
                    documents_cleaned
                )
            except Exception as enrich_error:
                print(f"⚠️ Ошибка обогащения задач: {enrich_error}")
                print("⚠️ Продолжаем сохранение без дополнительных колонок")

        # Переименование колонок и форматирование значений
        tasks_data = rename_columns_to_russian(tasks_data, data_type="tasks")

        # Сохранение во временный файл
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        save_with_xlsxwriter_formatting(tasks_data, filepath, 'Задачи', 'tasks')

        # Генерация имени файла
        download_filename = generate_filename("tasks")

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка сохранения задач для {responsibleExecutor}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")

@router.get("/rainbow-analysis")
async def save_rainbow_analysis():
    """
    Сохранение объединенных данных радуги с профессиональным форматированием.

    Функция реализует объединение очищенных детальных данных с цветовой классификацией
    и сохранение результата в Excel файл с форматированием. Объединение выполняется
    по коду дела с использованием внутренних структур данных менеджера.

    Returns:
        FileResponse: Excel файл с объединенными данными радуги

    Raises:
        HTTPException: 400 если данные не загружены или отсутствуют
        HTTPException: 500 при ошибках обработки или сохранения данных
    """
    try:
        # Получение очищенных детальных данных выполняется
        cleaned_df = data_manager._cleaned_data.get("detailed_report")
        if cleaned_df is None or cleaned_df.empty:
            raise HTTPException(status_code=400, detail="Детальный отчет не загружен")

        # Получение derived данных цветовой классификации
        derived_df = data_manager._derived_data.get("detailed_rainbow")
        if derived_df is None or derived_df.empty:
            raise HTTPException(status_code=400, detail="Данные цветовой классификации не подготовлены")

        # Приведение ключей к строковому типу выполняется для обеспечения корректного объединения
        cleaned_key = COLUMNS["CASE_CODE"]
        derived_key = COLUMNS["CASE_CODE"]

        cleaned_df[cleaned_key] = cleaned_df[cleaned_key].astype(str).str.strip()
        derived_df[derived_key] = derived_df[derived_key].astype(str).str.strip()

        # Объединение данных выполняется по коду дела с использованием левого соединения
        # Левое соединение сохраняет все записи из детального отчета
        merged_df = cleaned_df.merge(
            derived_df[[derived_key, COLUMNS["CURRENT_PERIOD_COLOR"]]],
            how="left",
            left_on=cleaned_key,
            right_on=derived_key,
            suffixes=("", "_rainbow")
        )

        # Создание временного файла выполняется для последующего возврата как FileResponse
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        # Сохранение с форматированием выполняется через специализированную функцию
        save_with_xlsxwriter_formatting(
            merged_df,
            filepath,
            sheet_name="Цветовая классификация",
            data_type="detailed"
        )

        # Генерация имени файла для скачивания выполняется по стандартному шаблону
        download_filename = generate_filename("rainbow_analysis")

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка сохранения анализа радуги: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")

@router.get("/terms-productions")
async def save_terms_productions():
    """
    Сохранение рассчитанных сроков производств (иск. и приказное) в один файл Excel.

    Объединяет данные искового и приказного производства в один лист.
    Автоматически применяется переименование колонок и форматирование значений

    Returns:
        FileResponse: Excel файл с объединенными данными производств

    Raises:
        HTTPException: 400 если данные не найдены
        HTTPException: 500 при ошибках сохранения
    """
    try:
        # Получение данных обоих типов производств
        lawsuit_data = data_manager.get_processed_data("lawsuit_staged")
        order_data = data_manager.get_processed_data("order_staged")

        # Проверка наличия данных
        if (lawsuit_data is None or lawsuit_data.empty) and (order_data is None or order_data.empty):
            raise HTTPException(status_code=400, detail="Нет данных для сохранения производств")

        # Объединение данных в один DataFrame
        combined_data = pd.concat(
            [df for df in [lawsuit_data, order_data] if df is not None and not df.empty],
            ignore_index=True
        )

        print(f"💾 Сохраняем рассчитанные сроки производств: {len(combined_data)} строк, {len(combined_data.columns)} колонок")

        # Создание временного файла Excel
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        # Сохранение с форматированием
        save_with_xlsxwriter_formatting(combined_data, filepath, 'Сроки производств', 'production')
        download_filename = generate_filename("terms_productions")

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка сохранения производств: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")

@router.get("/all-analysis")
async def save_all_analysis():
    """
    Сохранение всех видов анализа в один ZIP-архив.

    Создает комплексный архив, содержащий все анализы.
    Исковое и приказное производство объединяются в один лист 'Производства'.

    Returns:
        FileResponse: ZIP архив со всеми отчетами

    Raises:
        HTTPException: 400 если нет данных для сохранения
        HTTPException: 500 при ошибках создания архива
    """
    import zipfile
    import os

    try:
        # Создание временного файла для ZIP архива
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_zip_file:
            zip_filepath = tmp_zip_file.name

        files_to_zip = []
        temp_files = []

        try:
            # Получаем готовые данные
            terms_productions_data = pd.concat(
                [df for df in [
                    data_manager.get_processed_data("lawsuit_staged"),
                    data_manager.get_processed_data("order_staged")
                ] if df is not None and not df.empty],
                ignore_index=True
            ) if (data_manager.get_processed_data("lawsuit_staged") is not None or
                  data_manager.get_processed_data("order_staged") is not None) else None

            documents_analysis_data = data_manager.get_processed_data("documents_processed")
            tasks_data = data_manager.get_processed_data("tasks")
            rainbow_data = data_manager.get_colored_data("detailed")

            # Словарь для всех данных
            data_sources = {
                "terms_productions": {
                    "data": terms_productions_data,
                    "sheet_name": "Обработанные производства",
                    "data_type": "production"
                },
                "documents_analysis": {
                    "data": documents_analysis_data,
                    "sheet_name": "Анализ документов",
                    "data_type": "documents"
                },
                "tasks": {
                    "data": tasks_data,
                    "sheet_name": "Задачи",
                    "data_type": "tasks"
                },
                "rainbow_analysis": {
                    "data": rainbow_data,
                    "sheet_name": "Радуга",
                    "data_type": "detailed"
                }
            }

            # Сохраняем все данные во временные файлы
            for key, cfg in data_sources.items():
                data = cfg["data"]
                sheet_name = cfg["sheet_name"]
                data_type = cfg["data_type"]

                if data is not None and not data.empty:
                    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
                        filepath = tmp_file.name
                        temp_files.append(filepath)

                    save_with_xlsxwriter_formatting(data, filepath, sheet_name, data_type)
                    files_to_zip.append((filepath, f"{key}.xlsx"))
                    print(f"✅ Добавлен в архив: {sheet_name}")
                else:
                    print(f"⚠️ Пропущено: {sheet_name} - нет данных")

            if not files_to_zip:
                raise HTTPException(status_code=400, detail="Нет данных для сохранения")

            # Создаем ZIP архив
            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path, archive_name in files_to_zip:
                    zipf.write(file_path, archive_name)

            download_filename = generate_filename("all_analysis") + ".zip"

            return FileResponse(
                path=zip_filepath,
                filename=download_filename,
                media_type='application/zip'
            )

        finally:
            # Удаляем временные файлы
            for file_path in temp_files:
                try:
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"⚠️ Ошибка удаления временного файла {file_path}: {e}")

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка создания архива всех анализов: {e}")
        try:
            if os.path.exists(zip_filepath):
                os.unlink(zip_filepath)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Ошибка создания архива: {str(e)}")