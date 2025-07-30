from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from checking_engine.database.connection import get_db_session
 
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session"""
    async for session in get_db_session():
        yield session 