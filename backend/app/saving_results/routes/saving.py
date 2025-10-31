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

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import pandas as pd
import tempfile

from backend.app.common.modules.data_manager import data_manager
from backend.app.saving_results.modules.saving_results_settings import (
    generate_filename,
    save_with_xlsxwriter_formatting
)

router = APIRouter(prefix="/api/save", tags=["saving"])


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


@router.get("/lawsuit-production")
async def save_lawsuit_production():
    """
    Сохранение результатов анализа искового производства.

    Returns:
        FileResponse: Excel файл с данными искового производства

    Raises:
        HTTPException: 400 если данные не найдены
        HTTPException: 500 при ошибках сохранения
    """
    try:
        lawsuit_data = data_manager.get_processed_data("lawsuit_staged")

        if lawsuit_data is None or lawsuit_data.empty:
            raise HTTPException(status_code=400, detail="Данные искового производства не найдены")

        print(f"💾 Сохраняем исковое производство: {len(lawsuit_data)} строк, {len(lawsuit_data.columns)} колонок")

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        # Сохранение с форматированием через xlsxwriter
        save_with_xlsxwriter_formatting(lawsuit_data, filepath, 'Исковое производство', 'production')

        download_filename = generate_filename("lawsuit_production")

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        print(f"❌ Ошибка сохранения искового производства: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")


@router.get("/order-production")
async def save_order_production():
    """
    Сохранение результатов анализа приказного производства.

    Returns:
        FileResponse: Excel файл с данными приказного производства

    Raises:
        HTTPException: 400 если данные не найдены
        HTTPException: 500 при ошибках сохранения
    """
    try:
        order_data = data_manager.get_processed_data("order_staged")

        if order_data is None or order_data.empty:
            raise HTTPException(status_code=400, detail="Данные приказного производства не найдены")

        print(f"💾 Сохраняем приказное производство: {len(order_data)} строк, {len(order_data.columns)} колонок")

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        # Сохранение с форматированием через xlsxwriter
        save_with_xlsxwriter_formatting(order_data, filepath, 'Приказное производство', 'production')

        download_filename = generate_filename("order_production")

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        print(f"❌ Ошибка сохранения приказного производства: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")


@router.get("/documents-analysis")
async def save_documents_analysis():
    """
    Сохранение результатов анализа документов.

    Returns:
        FileResponse: Excel файл с анализом документов

    Raises:
        HTTPException: 400 если данные не найдены
        HTTPException: 500 при ошибках сохранения
    """
    try:
        documents_data = data_manager.get_processed_data("documents_processed")

        if documents_data is None or documents_data.empty:
            raise HTTPException(status_code=400, detail="Данные анализа документов не найдены")

        print(f"💾 Сохраняем анализ документов: {len(documents_data)} строк, {len(documents_data.columns)} колонок")

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        # Сохранение с форматированием через xlsxwriter
        save_with_xlsxwriter_formatting(documents_data, filepath, 'Анализ документов')

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

    Returns:
        FileResponse: Excel файл с задачами

    Raises:
        HTTPException: 400 если данные не найдены
        HTTPException: 500 при ошибках сохранения
    """
    try:
        tasks_data = data_manager.get_processed_data("tasks")

        if tasks_data is None or tasks_data.empty:
            raise HTTPException(status_code=400, detail="Данные задач не найдены")

        print(f"💾 Сохраняем задачи: {len(tasks_data)} строк, {len(tasks_data.columns)} колонок")

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        # Сохранение с форматированием через xlsxwriter
        # data_type="tasks" автоматически применит маппинг в save_with_xlsxwriter_formatting
        save_with_xlsxwriter_formatting(tasks_data, filepath, 'Задачи', 'tasks')

        download_filename = generate_filename("tasks")

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        print(f"❌ Ошибка сохранения задач: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")


@router.get("/rainbow-analysis")
async def save_rainbow_analysis():
    """
    Сохранение результатов цветовой классификации (радуги).

    Использует те же данные и фильтры, что и визуализация радуги для обеспечения согласованности.

    Returns:
        FileResponse: Excel файл с цветовой классификацией дел

    Raises:
        HTTPException: 400 если данные не загружены
        HTTPException: 500 при ошибках сохранения
    """
    try:
        # Получение детального отчета
        detailed_data = data_manager.get_detailed_data()

        if detailed_data is None or detailed_data.empty:
            raise HTTPException(status_code=400, detail="Детальный отчет не загружен")

        # Использование той же функции что и для графика радуги
        from backend.app.rainbow.modules.rainbow_classifier import RainbowClassifier

        # Получение данных с цветовой классификацией
        colored_data = RainbowClassifier.add_color_column(detailed_data)

        # Применение тех же фильтров что и в classify_cases()
        from backend.app.common.config.column_names import COLUMNS, VALUES

        rainbow_data = colored_data[
            (colored_data[COLUMNS["CATEGORY"]] == VALUES["CLAIM_FROM_BANK"]) &
            (~colored_data[COLUMNS["CASE_STATUS"]].isin([
                VALUES["CLOSED"],
                VALUES["ERROR_DUBLICATE"],
                VALUES["WITHDRAWN_BY_THE_INITIATOR"]
            ]))
        ]

        if rainbow_data.empty:
            raise HTTPException(status_code=400, detail="Нет данных для анализа радуги")

        print(f"Сохраняем анализ радуги: {len(rainbow_data)} строк")

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        save_with_xlsxwriter_formatting(rainbow_data, filepath, 'Цветовая классификация')

        download_filename = generate_filename("rainbow_analysis")

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        print(f"Ошибка сохранения анализа радуги: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")


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

        status = {
            "detailed_report": {
                "loaded": detailed_data is not None,
                "row_count": len(detailed_data) if detailed_data is not None else 0,
            },
            "documents_report": {
                "loaded": documents_data is not None,
                "row_count": len(documents_data) if documents_data is not None else 0,
            },
            "lawsuit_production": {
                "loaded": lawsuit_data is not None,
                "row_count": len(lawsuit_data) if lawsuit_data is not None else 0,
            },
            "order_production": {
                "loaded": order_data is not None,
                "row_count": len(order_data) if order_data is not None else 0,
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


@router.get("/all-analysis")
async def save_all_analysis():
    """
    Сохранение всех видов анализа в один ZIP-архив.

    Создает комплексный архив содержащий все доступные отчеты и анализы.

    Returns:
        FileResponse: ZIP архив со всеми отчетами

    Raises:
        HTTPException: 400 если нет данных для сохранения
        HTTPException: 500 при ошибках создания архива
    """
    import zipfile
    import os

    try:
        # Создание временного файла для ZIP архива (не директории)
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_zip_file:
            zip_filepath = tmp_zip_file.name

        files_to_zip = []
        temp_files = []  # Для отслеживания временных файлов

        try:
            # Словарь соответствия типов данных и методов получения
            data_sources = {
                "detailed_report": {
                    "data": data_manager.get_detailed_data(),  # ПРАВИЛЬНЫЙ МЕТОД
                    "sheet_name": "Детальный отчет",
                    "data_type": None
                },
                "documents_report": {
                    "data": data_manager.get_documents_data(),  # ПРАВИЛЬНЫЙ МЕТОД
                    "sheet_name": "Отчет документов",
                    "data_type": None
                },
                "lawsuit_production": {
                    "data": data_manager.get_processed_data("lawsuit_staged"),
                    "sheet_name": "Исковое производство",
                    "data_type": "production"
                },
                "order_production": {
                    "data": data_manager.get_processed_data("order_staged"),
                    "sheet_name": "Приказное производство",
                    "data_type": "production"
                },
                "documents_analysis": {
                    "data": data_manager.get_processed_data("documents_processed"),
                    "sheet_name": "Анализ документов",
                    "data_type": None
                },
                "tasks": {
                    "data": data_manager.get_processed_data("tasks"),
                    "sheet_name": "Задачи",
                    "data_type": "tasks"
                }
            }

            # Сохранение всех видов анализа в отдельные временные файлы
            for data_key, config in data_sources.items():
                try:
                    data = config["data"]
                    sheet_name = config["sheet_name"]
                    data_type = config["data_type"]

                    if data is not None and not data.empty:
                        # Создание временного файла для каждого отчета
                        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
                            filepath = tmp_file.name
                            temp_files.append(filepath)  # Запоминаем для очистки

                        # Сохранение с форматированием
                        save_with_xlsxwriter_formatting(data, filepath, sheet_name, data_type)
                        files_to_zip.append((filepath, f"{data_key}.xlsx"))
                        print(f"✅ Добавлен в архив: {sheet_name}")

                    else:
                        print(f"⚠️ Пропущено: {sheet_name} - нет данных")

                except Exception as e:
                    print(f"⚠️ Не удалось добавить {config['sheet_name']}: {e}")

            if not files_to_zip:
                raise HTTPException(status_code=400, detail="Нет данных для сохранения")

            # Создание ZIP-архива
            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path, archive_name in files_to_zip:
                    zipf.write(file_path, archive_name)

            # Генерация имени файла для скачивания
            download_filename = generate_filename("all_analysis") + ".zip"

            # Возврат ZIP-архива клиенту
            return FileResponse(
                path=zip_filepath,
                filename=download_filename,
                media_type='application/zip'
            )

        finally:
            # Очистка временных файлов после создания архива
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
        # Очистка ZIP файла в случае ошибки
        try:
            if os.path.exists(zip_filepath):
                os.unlink(zip_filepath)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Ошибка создания архива: {str(e)}")