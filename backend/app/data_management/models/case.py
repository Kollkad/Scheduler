# backend/app/data_management/models/case.py

"""
Модель дела из детального отчета.

Хранит исходные данные дела. Системные поля вынесены отдельно,
все остальные колонки из отчёта сохраняются как дополнительные поля.
"""

from pydantic import BaseModel, Field
from typing import Optional
from backend.app.common.config.column_names import COLUMNS


class Case(BaseModel):
    """
    Модель дела.

    caseCode является первичным ключом.
    stageCode - текущий этап дела, присваивается программно позже.
    Любые другие поля из Excel-файла сохраняются как есть.
    """
    caseCode: str = Field(alias=COLUMNS["CASE_CODE"])
    stageCode: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True
        extra = "allow"  # разрешает любые дополнительные поля из отчёта