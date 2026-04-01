# backend/app/additional_processing/routes/anonymization.py
"""
FastAPI роутер для эндпоинтов обезличивания отчетов.
Работает с файлами, загруженными через универсальное файловое хранилище.
"""

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import FileResponse
from typing import Optional, Dict, Any
import tempfile
import json
import getpass

from backend.app.data_management.services.file_storage import file_storage
from backend.app.data_management.models.file import FileModel
from backend.app.data_management.config.file_types import ALLOWED_FILE_TYPES
from backend.app.additional_processing.modules.data_anonymizer import DataAnonymizer
from backend.app.saving_results.modules.saving_results_settings import save_with_xlsxwriter_formatting
from backend.app.data_management.modules.data_import import load_excel_data
from backend.app.data_management.modules.data_clean_detailed import clean_data as clean_detailed
from backend.app.data_management.modules.data_clean_documents import clean_documents_data as clean_documents
from backend.app.data_management.modules.gosb_normalization import normalize_detailed_report
from backend.app.common.config.column_names import COLUMNS, VALUES

router = APIRouter(prefix="/api/additional_processing", tags=["additional_processing"])

# Временное хранение для нормализованных данных (не сохраняются в file_storage)
_normalized_cache = {}


def _normalize_detailed_file(filepath: str) -> Any:
    """Нормализует файл детального отчета."""
    raw_df = load_excel_data(filepath)
    cleaned_df = clean_detailed(raw_df)

    # Нормализация метода защиты
    method_col = COLUMNS["METHOD_OF_PROTECTION"]
    simplified_value = VALUES["SIMPLIFIED_PRODUCTION"]
    claim_value = VALUES["CLAIM_PROCEEDINGS"]

    if method_col in cleaned_df.columns:
        cleaned_df[method_col] = cleaned_df[method_col].replace(simplified_value, claim_value)

    return normalize_detailed_report(cleaned_df)


def _normalize_documents_file(filepath: str) -> Any:
    """Нормализует файл отчета документов."""
    raw_df = load_excel_data(filepath)
    cleaned_df = clean_documents(raw_df)

    # Нормализация названия колонки суда
    court_alt_name = COLUMNS["COURT_NAME"]
    court_std_name = COLUMNS["COURT"]

    if court_alt_name in cleaned_df.columns and court_std_name not in cleaned_df.columns:
        cleaned_df.rename(columns={court_alt_name: court_std_name}, inplace=True)

    # Нормализация метода защиты
    method_col = COLUMNS["METHOD_OF_PROTECTION"]
    simplified_value = VALUES["SIMPLIFIED_PRODUCTION"]
    claim_value = VALUES["CLAIM_PROCEEDINGS"]

    if method_col in cleaned_df.columns:
        cleaned_df[method_col] = cleaned_df[method_col].replace(simplified_value, claim_value)

    return cleaned_df


def _load_file_as_is(filepath: str) -> Any:
    """Загружает файл без нормализации."""
    return load_excel_data(filepath)


@router.post("/normalize")
async def normalize_for_anonymization(
        file_type: str = Query(..., description="Тип файла в хранилище (anonymization_source)"),
        normalization_type: str = Query(..., description="Тип нормализации: detailed_report, documents_report, none")
):
    """
    Нормализует загруженный файл перед обезличиванием.

    Args:
        file_type: Тип файла в хранилище (должен быть anonymization_source)
        normalization_type: Тип нормализации (detailed_report, documents_report, none)

    Returns:
        dict: Информация о нормализованных данных
    """
    # Проверка типа файла
    if file_type != "anonymization_source":
        raise HTTPException(status_code=400, detail="Для обезличивания используйте file_type=anonymization_source")

    # Получение файла из хранилища
    file_model = file_storage.get(file_type)
    if file_model is None:
        raise HTTPException(status_code=404, detail=f"Файл типа '{file_type}' не загружен")

    try:
        # Нормализация в зависимости от типа
        if normalization_type == "detailed_report":
            normalized_df = _normalize_detailed_file(file_model.server_path)
        elif normalization_type == "documents_report":
            normalized_df = _normalize_documents_file(file_model.server_path)
        else:
            normalized_df = _load_file_as_is(file_model.server_path)

        # Сохранение нормализованных данных в кэш
        _normalized_cache[file_type] = {
            'data': normalized_df,
            'normalization_type': normalization_type,
            'filename': file_model.name
        }

        # Получение правил для фронтенда
        anonymizer = DataAnonymizer()
        columns_info = anonymizer.get_available_columns(normalized_df)
        all_rules = anonymizer.all_rules

        applicable_rules = []
        for rule in all_rules:
            if rule['column_name'] in normalized_df.columns:
                applicable_rules.append({
                    'column': rule['column_name'],
                    'type': rule['replacement_type'],
                    'replacement': rule['replacement_text']
                })

        return {
            "success": True,
            "message": f"Файл нормализован как {normalization_type}",
            "filename": file_model.name,
            "rows": len(normalized_df),
            "columns": len(normalized_df.columns),
            "columns_info": columns_info,
            "applicable_rules": applicable_rules,
            "applicable_rules_count": len(applicable_rules),
            "total_rules_in_config": len(all_rules)
        }

    except Exception as e:
        print(f"❌ Ошибка нормализации: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка нормализации: {str(e)}")


@router.post("/anonymize")
async def anonymize_report(
        file_type: str = Query(..., description="Тип файла в хранилище (anonymization_source)"),
        config_json: str = Body(..., embed=True),
        use_default_rules: bool = Body(True, embed=True)
):
    """
    Применяет правила обезличивания к нормализованным данным.

    Args:
        file_type: Тип файла в хранилище
        config_json: JSON-строка с пользовательской конфигурацией
        use_default_rules: Использовать правила по умолчанию

    Returns:
        dict: Результаты обезличивания
    """
    # Проверка наличия нормализованных данных
    if file_type not in _normalized_cache:
        raise HTTPException(
            status_code=400,
            detail="Сначала выполните нормализацию через /normalize"
        )

    cache_entry = _normalized_cache[file_type]
    cleaned_data = cache_entry['data']
    original_filename = cache_entry['filename']

    try:
        # Парсинг пользовательской конфигурации
        user_config = json.loads(config_json)

        # Инициализация анонимайзера
        anonymizer = DataAnonymizer()

        # Формирование итоговой конфигурации
        final_config = []

        if use_default_rules:
            for rule in anonymizer.all_rules:
                if rule['column_name'] in cleaned_data.columns:
                    final_config.append({
                        'column_name': rule['column_name'],
                        'replacement_type': rule['replacement_type'],
                        'replacement_text': rule['replacement_text']
                    })

        # Удаление переопределенных правил
        user_columns = {rule['column'] for rule in user_config}
        final_config = [rule for rule in final_config if rule['column_name'] not in user_columns]

        # Добавление пользовательских правил
        for rule in user_config:
            final_config.append({
                'column_name': rule['column'],
                'replacement_type': rule['type'],
                'replacement_text': rule['replacement']
            })

        # Применение обезличивания
        anonymized_data = anonymizer.anonymize_dataframe(
            cleaned_data,
            config=final_config,
            use_all_rules=False
        )

        # Сохранение результата во временный файл
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
            result_path = tmp_file.name

        save_with_xlsxwriter_formatting(anonymized_data, result_path, 'Обезличенный отчет')

        # Регистрация результата в file_storage
        result_file = FileModel.create(
            name=f"anonymized_{original_filename}",
            file_type="anonymization_result",
            server_path=result_path,
            uploaded_by=getpass.getuser()
        )
        file_storage.register(result_file)

        # Сбор статистики
        result_info = []
        for rule in final_config:
            col = rule['column_name']
            if col in cleaned_data.columns:
                orig_unique = cleaned_data[col].nunique()
                anon_unique = anonymized_data[col].nunique()
                result_info.append({
                    'column': col,
                    'type': rule['replacement_type'],
                    'original_unique': int(orig_unique),
                    'anonymized_unique': int(anon_unique),
                    'replacement': rule.get('replacement_text', '')
                })

        return {
            "success": True,
            "message": "Обезличивание выполнено успешно",
            "result_file_type": "anonymization_result",
            "rows": len(anonymized_data),
            "columns": len(anonymized_data.columns),
            "total_rules_applied": len(final_config),
            "anonymization_results": result_info
        }

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Неверный формат конфигурации: {str(e)}")
    except Exception as e:
        print(f"❌ Ошибка обезличивания: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обезличивания: {str(e)}")


@router.get("/download")
async def download_anonymized_report(
        file_type: str = Query("anonymization_result", description="Тип файла для скачивания")
):
    """
    Скачивает обезличенный отчет.

    Args:
        file_type: Тип файла (обычно anonymization_result)

    Returns:
        FileResponse: Файл с обезличенными данными
    """
    try:
        file_model = file_storage.get(file_type)
        if file_model is None:
            raise HTTPException(status_code=404, detail="Обезличенный отчет не найден")

        return FileResponse(
            path=file_model.server_path,
            filename=file_model.name,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка скачивания: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка скачивания: {str(e)}")


@router.get("/get_default_rules")
async def get_default_rules():
    """
    Возвращает все доступные правила обезличивания из конфигурации.

    Returns:
        dict: Список всех правил обезличивания
    """
    try:
        anonymizer = DataAnonymizer()

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
        raise HTTPException(status_code=500, detail=f"Ошибка получения правил: {str(e)}")

