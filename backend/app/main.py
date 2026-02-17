from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import logging
from contextlib import asynccontextmanager

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импорты роутеров
from backend.app.common.routes.common import router as common_router
from backend.app.rainbow.routes.rainbow import router as rainbow_router
from backend.app.common.routes.case import router as case_router
from backend.app.task_manager.routes.tasks import router as tasks_router
from backend.app.document_monitoring_v2.routes.document_terms_v2 import router as document_router
from backend.app.terms_of_support_v2.routes.terms_v2 import router as terms_v2_router
from backend.app.saving_results.routes.saving import router as saving_router
from backend.app.additional_processing.routes.anonymization import router as additional_processing_router
from backend.app.common.routes.search import router as search_router

logger = logging.getLogger("uvicorn")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("✅ Сервер запущен")
    logger.info("📍 API: http://localhost:8000")
    logger.info("📚 Документация: http://localhost:8000/docs")
    logger.info("🌐 Frontend: http://localhost:8080")
    yield
    logger.info("⏹️ Сервер остановлен")

app = FastAPI(title="Legal Cases Analyzer API", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутеры
app.include_router(common_router)
app.include_router(rainbow_router)
app.include_router(case_router)
app.include_router(tasks_router)
app.include_router(document_router)
app.include_router(terms_v2_router)
app.include_router(saving_router)
app.include_router(additional_processing_router)
app.include_router(search_router)

@app.get("/")
async def root():
    return {"message": "API работает"}

@app.get("/test")
async def test():
    return {"status": "ok", "message": "Сервер работает!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)