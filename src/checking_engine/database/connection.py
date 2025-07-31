import asyncio
from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from checking_engine.config import settings
from checking_engine.utils.logging import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize database connection"""
        if self._initialized:
            return
        
        # Get database URL from settings
        database_url = settings.database_url
        logger.debug(f"Database URL from settings: {self._mask_url(database_url)}")
        
        if not database_url:
            logger.error("Database URL not found in settings")
            return
        
        logger.info(f"Connecting to database: {self._mask_url(database_url)}")
        
        # Create engine
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )
        
        # Create session factory
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        self._initialized = True
        logger.info("Database connection initialized")
    
    def _mask_url(self, url: str) -> str:
        """Mask password in URL for logging"""
        if "@" in url:
            parts = url.split("@")
            credentials = parts[0].split(":")
            if len(credentials) > 2:  # Has password
                username = credentials[1]
                return f"{credentials[0]}://{username}:***@{parts[1]}"
        return url
    
    async def health_check(self) -> bool:
        """Test database connection"""
        if not self._initialized:
            return False
        
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                result.fetchone()  # Remove await
                logger.info("Database health check: OK")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        if not self._initialized:
            raise RuntimeError("Database not initialized")
        
        async with self.session_factory() as session:
            yield session
    
    async def close(self) -> None:
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("Database connections closed")

# Global instance
db = DatabaseManager()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session"""
    async for session in db.get_session():
        yield session

async def test_connection() -> None:
    """Test database connection"""
    try:
        await db.initialize()
        
        # Test connection
        if await db.health_check():
            logger.info("Database connection successful")
            
            # Test query
            async for session in db.get_session():
                result = await session.execute(text("SELECT version()"))
                version = result.scalar()
                logger.info(f"PostgreSQL version: {version}")
                break  # Only get first session
        else:
            logger.error("Database connection failed")
    
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
    finally:
        await db.close()

if __name__ == "__main__":
            # Logging is initialized in main.py
        # setup_logging(log_level="DEBUG")
    asyncio.run(test_connection())
