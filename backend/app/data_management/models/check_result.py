# backend/app/data_management/models/check_result.py

"""
Модель результата проверки.

Фиксирует результат выполнения конкретной проверки
для конкретного документа или дела.
"""

from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


class CheckResult(BaseModel):
    """
    Модель результата проверки.

    checkResultCode - уникальный идентификатор записи.
    checkCode ссылается на выполненную проверку.
    targetId содержит transferCode (для документа) или caseCode (для дела).
    monitoringStatus - статус соблюдения срока (вовремя/просрочено/нет данных).
    completionStatus - статус выполнения условия (выполнено/не выполнено).
    checkedAt - дата и время выполнения проверки.
    executionDatePlan - плановая дата исправления проблемы (устанавливается функцией проверки).
    """
    checkResultCode: str
    checkCode: str
    targetId: str
    monitoringStatus: Literal["timely", "overdue", "no_data"]
    completionStatus: Optional[bool] = None
    checkedAt: datetime
    executionDatePlan: Optional[datetime] = None

    class Config:
        from_attributes = True

