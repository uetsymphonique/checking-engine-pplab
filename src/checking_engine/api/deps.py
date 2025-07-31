"""
Dependency Injection Utilities

Provides FastAPI dependency injection for database sessions and other shared resources.
Ensures proper resource management and testability.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from ..database.connection import get_db_session

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.
    
    Yields:
        AsyncSession: Database session for request lifecycle
    """
    async for session in get_db_session():
        yield session 