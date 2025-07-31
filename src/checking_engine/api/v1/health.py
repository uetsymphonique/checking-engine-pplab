from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from checking_engine.api.deps import get_db
from checking_engine.config import settings
from checking_engine.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version
    }

@router.get("/db")
async def database_health_check(db: AsyncSession = Depends(get_db)):
    """Database connection health check"""
    try:
        # Test database connection
        result = await db.execute(text("SELECT 1 as test"))
        result.fetchone()
        
        logger.debug("Database health check successful")
        return {
            "status": "healthy",
            "database": "connected",
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        ) 