# backend/app/data_management/models/task.py

"""
Модель задачи.

Связывает задачу с результатом проверки, который вызвал её создание.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Task(BaseModel):
    """
    Модель задачи.

    taskCode - уникальный идентификатор задачи.
    checkResultCode ссылается на результат проверки, из-за которого задача создана.
    taskText - текст задачи с указанием действия для сотрудника.
    reasonText - причина постановки задачи (что именно пошло не так).
    createdAt - дата и время создания задачи.
    isCompleted - флаг выполнения задачи.
    executionDateTimeFact - дата и время фактического выполнения (NULL если не выполнена).
    createdBy - логин пользователя создателя
    """
    taskCode: str
    checkResultCode: str
    taskText: str
    reasonText: str
    createdAt: datetime
    isCompleted: bool = False
    executionDateTimeFact: Optional[datetime] = None
    createdBy: str

    class Config:
        from_attributes = True


