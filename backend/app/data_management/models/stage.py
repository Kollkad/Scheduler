#backend/app/data_management/models/stage.py
"""
Модель этапа.

Определяет, на каком этапе процесса (документа или дела)
должны выполняться определённые проверки.
"""

from pydantic import BaseModel
from typing import Literal


class Stage(BaseModel):
    """
    Модель этапа.

    stageCode - уникальный идентификатор (например, "closed").
    fileType определяет, к данным из какого типа файла применяется этап.
    """
    stageCode: str
    stageName: str
    fileType: Literal["documents_report", "detailed_report"]

    class Config:
        from_attributes = True