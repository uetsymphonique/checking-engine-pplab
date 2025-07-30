from fastapi import APIRouter

from .health import router as health_router
from .operations import router as operations_router

# Main API Router
router = APIRouter()

# Include all endpoint routers
router.include_router(health_router)
router.include_router(operations_router) 