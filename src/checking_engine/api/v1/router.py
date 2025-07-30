from fastapi import APIRouter

from .health import router as health_router
from .operations import router as operations_router
from .executions import router as executions_router
from .detections import router as detections_router

# Main API Router
router = APIRouter()

# Include all endpoint routers
router.include_router(health_router)
router.include_router(operations_router)
router.include_router(executions_router)
router.include_router(detections_router) 