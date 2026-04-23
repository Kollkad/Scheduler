from fastapi import APIRouter

from .lawsuit_terms_v3 import router as lawsuit_router
from .order_terms_v3 import router as order_router

router = APIRouter(prefix="/api/terms/v3", tags=["terms_v3"])

router.include_router(lawsuit_router, prefix="/lawsuit", tags=["lawsuit_terms_v3"])
router.include_router(order_router, prefix="/order", tags=["order_terms_v3"])