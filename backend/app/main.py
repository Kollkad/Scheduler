from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sys
import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from starlette.responses import FileResponse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импорты роутеров
from backend.app.data_management.routes.file_management import router as file_management_router
from backend.app.data_management.routes.data_status import router as data_status_router
from backend.app.rainbow.routes.rainbow import router as rainbow_router
from backend.app.common.routes.case import router as case_router
from backend.app.task_manager.routes.tasks import router as tasks_router
from backend.app.document_monitoring_v2.routes.document_terms_v2 import router as document_router
from backend.app.terms_of_support_v2.routes.terms_v2 import router as terms_v2_router
from backend.app.saving_results.routes.saving import router as saving_router
from backend.app.additional_processing.routes.anonymization import router as additional_processing_router
from backend.app.common.routes.search import router as search_router
from backend.app.table_sorter.routes.filters import router as filters_router
from backend.app.administration_settings.routes.authorization import router as authorization_router

logger = logging.getLogger("uvicorn")

@asynccontextmanager
async def lifespan(app: FastAPI):
    #Документация: http://localhost:8000/docs, Frontend: http://localhost:8080
    yield
    logger.info("Сервер остановлен")

app = FastAPI(title="Legal Cases Analyzer API", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутеры
app.include_router(file_management_router)
app.include_router(data_status_router)
app.include_router(filters_router)
app.include_router(rainbow_router)
app.include_router(case_router)
app.include_router(tasks_router)
app.include_router(document_router)
app.include_router(terms_v2_router)
app.include_router(saving_router)
app.include_router(additional_processing_router)
app.include_router(search_router)
app.include_router(authorization_router)

# При наличии - используются статичные файлы фронта
frontend_path = Path(__file__).parent.parent.parent / "frontend" / "dist" / "spa"
if frontend_path.exists():
    # Файлы из assets
    app.mount("/assets", StaticFiles(directory=str(frontend_path / "assets")), name="assets")
    # Отдача конкретных файлов из корня
    @app.get("/logo-icon.png")
    async def get_logo():
        return FileResponse(frontend_path / "logo-icon.png")
    # Для всех остальных путей index.html
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Не обрабатываются API пути
        if full_path.startswith("api/") or full_path == "test":
            return {"message": "Not found"}
        return FileResponse(frontend_path / "index.html")
else:
    @app.get("/")
    async def root():
        return {"message": "API работает. Фронтенд отдельно"}

@app.get("/test")
async def test():
    return {"status": "ok", "message": "Сервер работает!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)