# backend/app/data_management/models/check.py

"""
Модель проверки.

Определяет, какая функция выполняется для проверки условия,
и к какому этапу и типу объектов она относится.
"""

from pydantic import BaseModel


class Check(BaseModel):
    """
    Модель проверки.

    checkCode - уникальный идентификатор (например, "executionDocumentTransfer").
    checkName - русскоязычное название проверки.
    stageCode ссылается на этап, на котором выполняется проверка.
    functionName содержит имя вызываемой функции в коде.
    isActive определяет, выполняется ли проверка в текущем анализе.
    """
    checkCode: str
    checkName: str
    stageCode: str
    functionName: str
    isActive: bool = True

    class Config:
        from_attributes = True

