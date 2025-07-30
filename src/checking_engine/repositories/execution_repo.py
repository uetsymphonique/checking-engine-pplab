from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime

from .base import BaseRepository
from ..models.execution import ExecutionResult
from ..schemas.execution import ExecutionResultCreate, ExecutionResultUpdate


class ExecutionResultRepository(BaseRepository[ExecutionResult, ExecutionResultCreate, ExecutionResultUpdate]):
    """Repository for ExecutionResult model with specific methods"""
    
    def __init__(self):
        super().__init__(ExecutionResult)
    
    async def get_by_link_id(self, db: AsyncSession, link_id: UUID) -> Optional[ExecutionResult]:
        """Get execution result by Caldera link_id"""
        query = select(ExecutionResult).where(ExecutionResult.link_id == link_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_operation_id(self, db: AsyncSession, operation_id: UUID, skip: int = 0, limit: int = 100) -> List[ExecutionResult]:
        """Get all execution results for a specific operation"""
        query = select(ExecutionResult).where(
            ExecutionResult.operation_id == operation_id
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_agent_paw(self, db: AsyncSession, agent_paw: str, skip: int = 0, limit: int = 100) -> List[ExecutionResult]:
        """Get execution results by agent PAW"""
        query = select(ExecutionResult).where(
            ExecutionResult.agent_paw == agent_paw
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_status(self, db: AsyncSession, status: int, skip: int = 0, limit: int = 100) -> List[ExecutionResult]:
        """Get execution results by status code"""
        query = select(ExecutionResult).where(
            ExecutionResult.status == status
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_link_state(self, db: AsyncSession, link_state: str, skip: int = 0, limit: int = 100) -> List[ExecutionResult]:
        """Get execution results by link state (SUCCESS, FAILED, etc.)"""
        query = select(ExecutionResult).where(
            ExecutionResult.link_state == link_state
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_with_operation(self, db: AsyncSession, execution_id: UUID) -> Optional[ExecutionResult]:
        """Get execution result with related operation data"""
        query = select(ExecutionResult).options(
            selectinload(ExecutionResult.operation)
        ).where(ExecutionResult.id == execution_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def exists_by_link_id(self, db: AsyncSession, link_id: UUID) -> bool:
        """Check if execution result exists by Caldera link_id"""
        query = select(ExecutionResult).where(ExecutionResult.link_id == link_id)
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def get_recent_executions(self, db: AsyncSession, hours: int = 24, skip: int = 0, limit: int = 100) -> List[ExecutionResult]:
        """Get execution results from the last N hours"""
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        query = select(ExecutionResult).where(
            ExecutionResult.created_at >= cutoff_time
        ).order_by(ExecutionResult.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_failed_executions(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ExecutionResult]:
        """Get execution results with failed status or link_state"""
        query = select(ExecutionResult).where(
            or_(
                ExecutionResult.status != 0,  # Non-zero exit code
                ExecutionResult.link_state == 'FAILED'
            )
        ).order_by(ExecutionResult.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all() 