#backend/app/data_management/services/file_storage.py

import os
import shutil
from typing import Optional, Dict
from ..models.file import FileModel


class FileStorage:
    """Синглтон для хранения и управления файлами по их типу."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._files: Dict[str, FileModel] = {}
        return cls._instance

    def register(self, file: FileModel) -> None:
        """Сохраняет файл, заменяя предыдущий с тем же типом."""
        existing = self._files.get(file.type)
        if existing:
            # удаляем старый файл с диска
            if os.path.exists(existing.server_path):
                os.unlink(existing.server_path)
        self._files[file.type] = file

    def get(self, file_type: str) -> Optional[FileModel]:
        """Возвращает модель файла по типу или None."""
        return self._files.get(file_type)

    def get_path(self, file_type: str) -> Optional[str]:
        """Возвращает путь к файлу по типу."""
        file = self.get(file_type)
        return file.server_path if file else None

    def delete(self, file_type: str) -> bool:
        """Удаляет файл с диска и из хранилища. Возвращает True если был удалён."""
        file = self._files.pop(file_type, None)
        if file and os.path.exists(file.server_path):
            os.unlink(file.server_path)
            return True
        return False

    def exists(self, file_type: str) -> bool:
        """Проверяет, зарегистрирован ли файл данного типа."""
        return file_type in self._files

    def list_all(self) -> Dict[str, FileModel]:
        """Возвращает копию словаря всех файлов."""
        return self._files.copy()


# Глобальный экземпляр для использования во всём приложении
file_storage = FileStorage()


