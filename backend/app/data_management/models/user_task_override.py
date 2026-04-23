"""
Модель пользовательского переопределения задачи.

Хранит изменения, внесённые пользователем в задачу.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserTaskOverride(BaseModel):
    """
    Модель пользовательского переопределения задачи.

    Содержит копию оригинальной задачи с изменёнными полями.
    """
    taskCode: str
    checkResultCode: str
    taskText: str
    reasonText: str
    createdAt: datetime
    isCompleted: bool = False
    executionDatePlan: Optional[datetime] = None
    executionDateTimeFact: Optional[datetime] = None
    shiftCode: Optional[str] = None
    createdBy: str

    class Config:
        from_attributes = True


