#backend/app/data_management/models/file.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import uuid


class FileModel(BaseModel):
    id: str
    name: str
    type: str              # тип данных: "detailed_report", "documents_report"
    server_path: str       # полный путь во временной папке
    uploaded_at: datetime
    uploaded_by: str       # имя пользователя (из ОС или заголовка)

    @classmethod
    def create(cls, name: str, file_type: str, server_path: str, uploaded_by: str):
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            type=file_type,
            server_path=server_path,
            uploaded_at=datetime.now(),
            uploaded_by=uploaded_by
        )






