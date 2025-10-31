# backend/app/terms_of_support_v2/routes/terms_v2.py
from fastapi import APIRouter

# Импортируем роутеры искового и приказного производства (v2)
from .lawsuit_terms_v2 import router as lawsuit_router
from .order_terms_v2 import router as order_router

# Общий роутер с префиксом /api/terms/v2
router = APIRouter(prefix="/api/terms/v2", tags=["terms_v2"])

# Подключаем с разными префиксами
router.include_router(lawsuit_router, prefix="/lawsuit", tags=["lawsuit_terms_v2"])
router.include_router(order_router, prefix="/order", tags=["order_terms_v2"])