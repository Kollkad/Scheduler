# backend/app/data_management/routes/file_management.py
"""
Модуль маршрутов FastAPI для загрузки и управления файлами в хранилище.

Предоставляет API эндпоинты:
- Универсальная загрузка файлов любого допустимого типа
- Получение статуса всех файлов в хранилище
- Проверка наличия конкретного файла
- Удаление файла по типу
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Query
import tempfile
import shutil
import os
import getpass

from ..services.file_storage import file_storage
from ..models.file import FileModel
from ..config.file_types import ALLOWED_FILE_TYPES

router = APIRouter(prefix="/api/data", tags=["data-upload"])


@router.post("/upload-file")
async def upload_file(file_type: str, file: UploadFile = File(...)):
    """
    Загружает файл в хранилище с указанием типа.

    Args:
        file_type (str): Тип файла (должен входить в ALLOWED_FILE_TYPES)
        file (UploadFile): Загружаемый файл

    Returns:
        dict: Результат загрузки:
            {
                "message": str,
                "file": dict (данные FileModel)
            }

    Raises:
        HTTPException:
            400 — если тип файла или расширение некорректны
            500 — при ошибке сохранения файла
    """

    # Проверка допустимого типа файла
    if file_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail="Неверный тип файла")

    # Проверка расширения файла
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Только Excel файлы разрешены")

    try:
        # Сохранение файла во временную директорию
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name

        # Определение пользователя, загрузившего файл
        uploaded_by = getpass.getuser()

        # Создание модели файла
        file_model = FileModel.create(
            name=file.filename,
            file_type=file_type,
            server_path=tmp_path,
            uploaded_by=uploaded_by
        )

        # Регистрация файла с заменой предыдущего того же типа
        file_storage.register(file_model)

        return {
            "message": "Файл успешно загружен",
            "file": file_model.dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки файла: {str(e)}")

    finally:
        # Гарантированное закрытие файлового потока
        file.file.close()


@router.get("/files-status")
async def get_files_status():
    """
    Возвращает статус всех файлов, зарегистрированных в хранилище.

    Returns:
        dict: Структура:
            {
                "files": {
                    file_type: {
                        "loaded": bool,
                        "exists": bool,
                        "file": dict | None
                    }
                },
                "total_files": int
            }
    """

    files = file_storage.list_all()
    status = {}

    # Формирование статуса для каждого зарегистрированного файла
    for file_type, file in files.items():
        status[file_type] = {
            "loaded": True,
            "exists": os.path.exists(file.server_path),
            "file": file.dict()
        }

    return {
        "files": status,
        "total_files": len(status)
    }


@router.get("/file-status")
async def get_file_status(file_type: str = Query(...)):
    """
    Возвращает статус конкретного файла по его типу.

    Args:
        file_type (str): Тип файла

    Returns:
        dict: Структура:
            {
                "file_type": str,
                "exists": bool,
                "file": dict | None
            }

    Raises:
        HTTPException: 400 если тип файла некорректен
    """

    # Проверка допустимого типа файла
    if file_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail="Неверный тип файла")

    file = file_storage.get(file_type)

    return {
        "file_type": file_type,
        "exists": file is not None,
        "file": file.dict() if file else None
    }


@router.delete("/remove-file")
async def remove_file(file_type: str):
    """
    Удаляет файл из хранилища по его типу.

    Args:
        file_type (str): Тип файла

    Returns:
        dict: Результат удаления:
            {
                "message": str,
                "file_type": str,
                "removed": bool
            }

    Raises:
        HTTPException: 400 если тип файла некорректен
    """

    # Проверка допустимого типа файла
    if file_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail="Неверный тип файла")

    # Удаление файла из хранилища и с диска
    removed = file_storage.delete(file_type)

    return {
        "message": f"Файл {file_type} удален",
        "file_type": file_type,
        "removed": removed
    }


