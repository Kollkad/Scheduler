# backend/app/data_management/models/document.py

"""
Модель документа из отчёта документов.

Хранит исходные данные документа. Системные поля вынесены отдельно,
все остальные колонки из отчёта сохраняются как дополнительные поля.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
from backend.app.common.config.column_names import COLUMNS


class Document(BaseModel):
    """
    Модель документа.

    transferCode является первичным ключом.
    caseCode - внешний ключ на дело.
    stageCode - текущий этап документа, присваивается программно позже.
    Любые другие поля из Excel-файла сохраняются как есть.
    """
    transferCode: str = Field(alias=COLUMNS["TRANSFER_CODE"])
    caseCode: Optional[str] = Field(default=None, alias=COLUMNS["DOCUMENT_CASE_CODE"])
    stageCode: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True
        extra = "allow"  # разрешает любые дополнительные поля из отчёта
