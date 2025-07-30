from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from uuid import UUID
from datetime import datetime

from .base import BaseRepository
from ..models.operation import Operation
from ..schemas.operation import OperationCreate, OperationUpdate


class OperationRepository(BaseRepository[Operation, OperationCreate, OperationUpdate]):
    """Repository for Operation model with specific methods"""
    
    def __init__(self):
        super().__init__(Operation)
    
    async def get_by_operation_id(self, db: AsyncSession, operation_id: UUID) -> Optional[Operation]:
        """Get operation by Caldera operation_id"""
        query = select(Operation).where(Operation.operation_id == operation_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Operation]:
        """Get operation by name"""
        query = select(Operation).where(Operation.name == name)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def search_by_name(self, db: AsyncSession, name_pattern: str, skip: int = 0, limit: int = 100) -> List[Operation]:
        """Search operations by name pattern (case-insensitive)"""
        query = select(Operation).where(
            Operation.name.ilike(f"%{name_pattern}%")
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_date_range(
        self, 
        db: AsyncSession, 
        start_date: datetime, 
        end_date: datetime,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Operation]:
        """Get operations within date range"""
        query = select(Operation).where(
            and_(
                Operation.created_at >= start_date,
                Operation.created_at <= end_date
            )
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_with_executions(self, db: AsyncSession, operation_id: UUID) -> Optional[Operation]:
        """Get operation with related execution results"""
        query = select(Operation).options(
            selectinload(Operation.execution_results)
        ).where(Operation.id == operation_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def exists_by_operation_id(self, db: AsyncSession, operation_id: UUID) -> bool:
        """Check if operation exists by Caldera operation_id"""
        query = select(Operation).where(Operation.operation_id == operation_id)
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def get_active_operations(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Operation]:
        """Get operations that have started but not completed (based on operation_start)"""
        query = select(Operation).where(
            Operation.operation_start.isnot(None)
        ).order_by(Operation.operation_start.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all() 