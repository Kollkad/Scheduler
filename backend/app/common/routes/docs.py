# backend/app/common/routes/docs.py

"""
Маршруты для отдачи пользовательской документации.

Предоставляет API для получения списка PDF-инструкций
и скачивания конкретного файла.
"""
from urllib.parse import quote
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/docs", tags=["docs"])

# Путь к папке с пользовательскими инструкциями (PDF)
DOCS_USER_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "docs" / "user"


@router.get("/list")
async def get_docs_list():
    """
    Возвращает список доступных PDF-инструкций.

    Сканирует папку docs/user/ и возвращает имена файлов без расширения.

    Returns:
        dict: Список файлов
    """
    try:
        if not DOCS_USER_DIR.exists():
            return {
                "success": True,
                "files": [],
                "message": "Папка с документацией не найдена"
            }

        files = []
        for file_path in DOCS_USER_DIR.iterdir():
            if file_path.is_file() and file_path.suffix.lower() == ".pdf":
                files.append({
                    "filename": file_path.name,
                    "name": file_path.stem,  # имя без расширения (вопрос)
                })

        # Сортировка по имени
        files.sort(key=lambda f: f["name"])

        return {
            "success": True,
            "files": files,
            "message": f"Найдено {len(files)} инструкций"
        }

    except Exception as e:
        print(f"❌ Ошибка получения списка документации: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.get("/{filename}")
async def get_doc_file(filename: str):
    """
    Отдаёт PDF-файл инструкции по имени файла.

    Args:
        filename: Имя файла с расширением (например, "как-загрузить-файлы.pdf")

    Returns:
        FileResponse: PDF-файл
    """
    try:
        file_path = DOCS_USER_DIR / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Инструкция '{filename}' не найдена")

        if not file_path.is_file():
            raise HTTPException(status_code=404, detail=f"'{filename}' не является файлом")

        return FileResponse(
            path=str(file_path),
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename*=UTF-8''{quote(filename)}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Ошибка отдачи документации: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")



