#backend/app/additional_processing/routes/anonymization.py
"""
FastAPI роутер для эндпоинтов обезличивания отчетов.
Обрабатывает загрузку файлов, применение правил анонимизации и скачивание результатов.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from typing import List, Optional, Dict
import tempfile
import os
import json

router = APIRouter(prefix="/api/additional_processing", tags=["additional_processing"])

# Импорт модулей выполняется внутри блока try/except для обработки ошибок зависимостей
try:
    from backend.app.common.modules.data_manager import data_manager
    from backend.app.additional_processing.modules.data_anonymizer import DataAnonymizer
    from backend.app.saving_results.modules.saving_results_settings import (
        generate_filename,
        save_with_xlsxwriter_formatting
    )
except ImportError as e:
    raise RuntimeError(f"Ошибка импорта модулей: {e}")

# Временное хранилище для загруженных файлов в памяти процесса
# Ключи соответствуют типам отчетов или содержат префикс 'anonymized_'
_temp_files = {}


@router.post("/load_report")
async def load_report(
        file: UploadFile = File(...),
        report_type: str = Form("detailed_report")
):
    """
    Загружает и предварительно обрабатывает отчет для последующего обезличивания.

    Выбор метода загрузки и предобработки зависит от указанного типа отчета.
    Функция data_manager предоставляет специализированные методы для разных форматов.

    Args:
        file: Загружаемый файл отчета (обычно в формате Excel).
        report_type: Тип отчета, определяющий логику предобработки.
                    Допустимые значения: 'detailed_report', 'documents_report'.

    Returns:
        dict: Информация о загруженном отчете, включая метаданные,
              список колонок и применимые правила анонимизации.

    Raises:
        HTTPException: 400 - при некорректном типе отчета,
                      500 - при ошибках чтения файла или обработки данных.
    """
    try:
        # Сохранение файла во временную директорию
        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        content = await file.read()
        temp_path.write(content)
        temp_path.close()

        # Выбор метода загрузки осуществляется в зависимости от типа отчета
        if report_type == "detailed_report":
            # Загрузка детального отчета со специальной предобработкой
            cleaned_data = data_manager.load_detailed_report(temp_path.name)
        elif report_type == "documents_report":
            # Загрузка отчета по документам со специфичной логикой
            cleaned_data = data_manager.load_documents_report(temp_path.name)
        else:
            raise HTTPException(status_code=400, detail="Неверный тип отчета")

        # Сохранение информации о загруженном файле во временном хранилище
        _temp_files[report_type] = {
            'filepath': temp_path.name,
            'filename': file.filename,
            'data': cleaned_data,
            'report_type': report_type  # Тип сохраняется для последующей обработки
        }

        # Создание экземпляра анонимайзера (правила применяются одинаково для всех типов отчетов)
        anonymizer = DataAnonymizer()
        columns_info = anonymizer.get_available_columns(cleaned_data)

        # Получение всех правил из конфигурации
        all_rules = anonymizer.all_rules

        # Фильтрация правил выполняется по наличию соответствующих колонок в DataFrame
        applicable_rules = []
        for rule in all_rules:
            if rule['column_name'] in cleaned_data.columns:
                applicable_rules.append({
                    'column': rule['column_name'],
                    'type': rule['replacement_type'],
                    'replacement': rule['replacement_text']
                })

        return {
            "success": True,
            "message": f"Отчет '{report_type}' загружен успешно",
            "filename": file.filename,
            "report_type": report_type,
            "rows": len(cleaned_data),
            "columns": len(cleaned_data.columns),
            "columns_info": columns_info,
            "applicable_rules": applicable_rules,  # Правила, совместимые со структурой отчета
            "applicable_rules_count": len(applicable_rules),
            "total_rules_in_config": len(all_rules)
        }

    except Exception as e:
        print(f"❌ Ошибка загрузки отчета: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки: {str(e)}")


@router.post("/anonymize")
async def anonymize_report(
        report_type: str = Form(...),
        config_json: str = Form(...),
        use_default_rules: bool = Form(True)
):
    """
    Применяет правила обезличивания к загруженному отчету.

    Поддерживает комбинирование правил по умолчанию и пользовательских настроек.
    Правила обезличивания едины для всех типов отчетов.

    Args:
        report_type: Тип отчета, используемый для поиска загруженных данных
                    в временном хранилище.
        config_json: JSON-строка с пользовательской конфигурацией обезличивания.
        use_default_rules: Флаг использования базовых правил из конфигурации.

    Returns:
        dict: Результаты обезличивания с детальной статистикой по примененным правилам.

    Raises:
        HTTPException: 400 - при отсутствии загруженного отчета или
                      некорректном формате конфигурации,
                      500 - при ошибках в процессе обезличивания.
    """
    try:
        # Проверка наличия загруженного отчета выполняется по ключу в временном хранилище
        if report_type not in _temp_files:
            raise HTTPException(
                status_code=400,
                detail=f"Отчет '{report_type}' не загружен"
            )

        # Извлечение предобработанных данных
        file_info = _temp_files[report_type]
        cleaned_data = file_info['data']

        # Парсинг пользовательской конфигурации из JSON-строки
        user_config = json.loads(config_json)

        # Инициализация анонимайзера
        anonymizer = DataAnonymizer()

        # Формирование итоговой конфигурации выполняется в два этапа
        final_config = []

        # Добавление правил по умолчанию происходит при включенном флаге
        if use_default_rules:
            # Фильтрация выполняется только для правил, соответствующих колонкам отчета
            for rule in anonymizer.all_rules:
                if rule['column_name'] in cleaned_data.columns:
                    final_config.append({
                        'column': rule['column_name'],
                        'type': rule['replacement_type'],
                        'replacement': rule['replacement_text']
                    })

        # Обработка пользовательских правил
        # Создание множества колонок из пользовательской конфигурации для быстрого поиска
        user_columns = {rule['column'] for rule in user_config}

        # Удаление правил по умолчанию для колонок, переопределенных пользователем
        final_config = [rule for rule in final_config if rule['column'] not in user_columns]

        # Добавление пользовательских правил
        final_config.extend(user_config)

        # Применение правил обезличивания к данным
        anonymized_data = anonymizer.anonymize_dataframe(
            cleaned_data,
            config=final_config,
            use_all_rules=False
        )

        # Сохранение результатов обезличивания
        _temp_files[f"anonymized_{report_type}"] = {
            'data': anonymized_data,
            'config': final_config,
            'original_filename': file_info['filename'],
            'report_type': report_type
        }

        # Сбор статистики по результатам обезличивания для каждой колонки
        result_info = []
        for rule in final_config:
            if rule['column'] in cleaned_data.columns:
                orig_unique = cleaned_data[rule['column']].nunique()
                anon_unique = anonymized_data[rule['column']].nunique()
                result_info.append({
                    'column': rule['column'],
                    'type': rule['type'],
                    'original_unique': int(orig_unique),
                    'anonymized_unique': int(anon_unique),
                    'replacement': rule.get('replacement', '')
                })

        return {
            "success": True,
            "message": "Обезличивание выполнено успешно",
            "report_type": report_type,
            "rows": len(anonymized_data),
            "columns": len(anonymized_data.columns),
            "total_rules_applied": len(final_config),
            "anonymization_results": result_info
        }

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Неверный формат конфигурации: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Ошибка обезличивания: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка обезличивания: {str(e)}"
        )


@router.get("/download_anonymized")
async def download_anonymized_report(
        report_type: str = Query(...)
):
    """
    Предоставляет обезличенный отчет для скачивания.

    Args:
        report_type: Тип отчета, для которого требуется скачивание.

    Returns:
        FileResponse: Файл с обезличенными данными в формате Excel.

    Raises:
        HTTPException: 400 - если обезличенный отчет не найден,
                      500 - при ошибках создания файла для скачивания.
    """
    try:
        key = f"anonymized_{report_type}"
        if key not in _temp_files:
            raise HTTPException(
                status_code=400,
                detail="Обезличенный отчет не найден"
            )

        anonymized_data = _temp_files[key]['data']
        original_filename = _temp_files[key]['original_filename']

        # Создание временного файла для экспорта
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            filepath = tmp_file.name

        # Сохранение данных с применением форматирования
        save_with_xlsxwriter_formatting(anonymized_data, filepath, 'Обезличенный отчет')

        # Генерация имени файла для скачивания на основе оригинального имени
        base_name = os.path.splitext(original_filename)[0]
        download_filename = f"{base_name}_anonymized.xlsx"

        return FileResponse(
            path=filepath,
            filename=download_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        print(f"❌ Ошибка скачивания отчета: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка скачивания: {str(e)}"
        )


@router.get("/get_default_rules")
async def get_default_rules():
    """
    Возвращает все доступные правила обезличивания из конфигурации.

    Правила представлены в формате, совместимом с фронтенд-приложением.

    Returns:
        dict: Список всех правил обезличивания с метаинформацией.

    Raises:
        HTTPException: 500 - при ошибках загрузки правил из конфигурации.
    """
    try:
        anonymizer = DataAnonymizer()

        # Преобразование правил в legacy-формат для совместимости
        legacy_rules = []
        for rule in anonymizer.all_rules:
            legacy_rules.append({
                'column': rule['column_name'],
                'type': rule['replacement_type'],
                'replacement': rule['replacement_text']
            })

        return {
            "success": True,
            "rules": legacy_rules,
            "total_rules": len(legacy_rules),
            "note": "Правила одинаковые для всех типов отчетов"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения правил: {str(e)}"
        )


@router.delete("/clear_temp_data")
async def clear_temp_data(
        report_type: Optional[str] = Query(None)
):
    """
    Очищает временные данные из памяти и файловой системы.

    Args:
        report_type: Опциональный фильтр для удаления данных только
                    определенного типа отчета. Если None, очищаются все данные.

    Returns:
        dict: Результат операции очистки с количеством удаленных записей.

    Raises:
        HTTPException: 500 - при ошибках удаления файлов или очистки памяти.
    """
    try:
        keys_to_delete = []

        # Поиск ключей для удаления с учетом фильтра по типу отчета
        for key in list(_temp_files.keys()):
            if report_type is None or report_type in key:
                # Удаление временных файлов с диска (если они существуют)
                if 'filepath' in _temp_files[key] and os.path.exists(_temp_files[key]['filepath']):
                    os.unlink(_temp_files[key]['filepath'])
                keys_to_delete.append(key)

        # Удаление записей из временного хранилища
        for key in keys_to_delete:
            del _temp_files[key]

        return {
            "success": True,
            "message": f"Очищено {len(keys_to_delete)} записей",
            "cleared_count": len(keys_to_delete)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка очистки: {str(e)}"
        )