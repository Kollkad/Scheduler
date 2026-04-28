# backend/app/common/routes/case.py
"""
Модуль для работы с данными судебных дел (v3).

Предоставляет API для получения детальной информации по делам,
включая поиск, преобразование данных и автоматическую категоризацию полей.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import pandas as pd

from backend.app.common.config.column_names import COLUMNS
from backend.app.common.modules.field_grouping import (
    safe_convert_value,
    group_fields_by_category
)
from backend.app.common.config.special_fields_case import SPECIAL_FIELDS
from backend.app.data_management.modules.normalized_data_manager import normalized_manager

router = APIRouter(prefix="/api/case", tags=["case"])


@router.get("/{case_code}")
async def get_case_details(case_code: str):
    """
    Получение детальной информации по конкретному судебному делу.

    Args:
        case_code (str): Код дела для поиска

    Returns:
        dict: Данные дела в формате {
            "success": bool,
            "caseCode": str,
            "data": dict,
            "fieldGroups": dict,
            "totalFields": int,
            "caseStage": str,
            "rainbowColor": str
        }
    """
    try:
        # Получение данных дел из нормализованного менеджера
        df = normalized_manager.get_cases_data()
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="Данные не загружены")

        case_col = COLUMNS["CASE_CODE"]
        if case_col not in df.columns:
            raise HTTPException(status_code=500, detail=f"Колонка '{case_col}' не найдена в данных")

        # Поиск дела по коду
        mask = df[case_col].astype(str).str.strip() == str(case_code).strip()
        if not mask.any():
            raise HTTPException(status_code=404, detail=f"Дело {case_code} не найдено")

        case_row = df[mask].iloc[0]
        case_data = case_row.to_dict()

        # Безопасное преобразование значений
        safe_case_data = {}
        for key, value in case_data.items():
            safe_case_data[key] = safe_convert_value(value)

        # Получение цвета радуги (добавляется модулем радуги)
        rainbow_color = safe_case_data.get(COLUMNS["CURRENT_PERIOD_COLOR"])

        # Получение этапа дела (stageCode присваивается при анализе производства)
        case_stage = safe_case_data.get("stageCode")

        # Группировка полей по категориям
        field_groups = group_fields_by_category(safe_case_data, SPECIAL_FIELDS)

        return {
            "success": True,
            "caseCode": case_code,
            "data": safe_case_data,
            "fieldGroups": field_groups,
            "totalFields": len(safe_case_data),
            "caseStage": case_stage,
            "rainbowColor": rainbow_color
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Критическая ошибка в get_case_details: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных дела: {str(e)}")


@router.get("/stages/{production_type}")
async def get_production_stages(production_type: str):
    """
    Возвращает этапы для указанного типа производства в правильном порядке.

    Args:
        production_type: "lawsuit" или "order"

    Returns:
        dict: Список этапов {stageCode, stageName}
    """
    try:
        stages_df = normalized_manager.get_stages_data()

        if production_type == "lawsuit":
            filtered = stages_df[stages_df["stageCode"].str.endswith("L")]
        elif production_type == "order":
            filtered = stages_df[stages_df["stageCode"].str.endswith("O")]
        else:
            raise HTTPException(status_code=400, detail=f"Неизвестный тип производства: {production_type}")

        if filtered.empty:
            raise HTTPException(status_code=404, detail="Этапы не найдены")

        stages_list = filtered[["stageCode", "stageName"]].to_dict(orient="records")

        return {
            "success": True,
            "stages": stages_list,
            "message": f"Найдено {len(stages_list)} этапов"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения этапов: {str(e)}")

@router.get("/stages/{production_type}/with-checks")
async def get_production_stages_with_checks(production_type: str):
    """
    Возвращает этапы с вложенными проверками для указанного типа производства.

    Args:
        production_type: "lawsuit" или "order"

    Returns:
        dict: Список этапов с проверками [{stageCode, stageName, checks: [{checkCode, checkName}]}]
    """
    try:
        stages_df = normalized_manager.get_stages_data()
        checks_df = normalized_manager.get_checks_data()

        if production_type == "lawsuit":
            suffix = "L"
        elif production_type == "order":
            suffix = "O"
        else:
            raise HTTPException(status_code=400, detail=f"Неизвестный тип производства: {production_type}")

        # Фильтруем этапы по суффиксу
        filtered_stages = stages_df[stages_df["stageCode"].str.endswith(suffix)]

        if filtered_stages.empty:
            raise HTTPException(status_code=404, detail="Этапы не найдены")

        # Для каждого этапа находим проверки
        result = []
        for _, stage in filtered_stages.iterrows():
            stage_code = stage["stageCode"]
            stage_checks = checks_df[checks_df["stageCode"] == stage_code]

            result.append({
                "stageCode": stage_code,
                "stageName": stage["stageName"],
                "checks": stage_checks[["checkCode", "checkName"]].to_dict(orient="records")
            })

        return {
            "success": True,
            "stages": result,
            "message": f"Найдено {len(result)} этапов с проверками"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения этапов с проверками: {str(e)}")



