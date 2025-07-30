# Detection Repository
# Data access for detection_executions and detection_results tables

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime

from .base import BaseRepository
from ..models.detection import DetectionExecution, DetectionResult
from ..schemas.detection import (
    DetectionExecutionCreate, DetectionExecutionUpdate,
    DetectionResultCreate, DetectionResultUpdate
)


class DetectionExecutionRepository(BaseRepository[DetectionExecution, DetectionExecutionCreate, DetectionExecutionUpdate]):
    """Repository for DetectionExecution model with specific methods"""
    
    def __init__(self):
        super().__init__(DetectionExecution)
    
    async def get_by_execution_result_id(self, db: AsyncSession, execution_result_id: UUID, skip: int = 0, limit: int = 100) -> List[DetectionExecution]:
        """Get detection executions by execution result ID"""
        query = select(DetectionExecution).where(
            DetectionExecution.execution_result_id == execution_result_id
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_operation_id(self, db: AsyncSession, operation_id: UUID, skip: int = 0, limit: int = 100) -> List[DetectionExecution]:
        """Get detection executions by operation ID"""
        query = select(DetectionExecution).where(
            DetectionExecution.operation_id == operation_id
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_detection_type(self, db: AsyncSession, detection_type: str, skip: int = 0, limit: int = 100) -> List[DetectionExecution]:
        """Get detection executions by type (api, windows, linux, darwin)"""
        query = select(DetectionExecution).where(
            DetectionExecution.detection_type == detection_type
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_platform(self, db: AsyncSession, detection_platform: str, skip: int = 0, limit: int = 100) -> List[DetectionExecution]:
        """Get detection executions by platform (cym, ajant, psh, etc.)"""
        query = select(DetectionExecution).where(
            DetectionExecution.detection_platform == detection_platform
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_status(self, db: AsyncSession, status: str, skip: int = 0, limit: int = 100) -> List[DetectionExecution]:
        """Get detection executions by status"""
        query = select(DetectionExecution).where(
            DetectionExecution.status == status
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_pending_executions(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[DetectionExecution]:
        """Get pending detection executions"""
        query = select(DetectionExecution).where(
            DetectionExecution.status == 'pending'
        ).order_by(DetectionExecution.created_at.asc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_failed_executions(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[DetectionExecution]:
        """Get failed detection executions"""
        query = select(DetectionExecution).where(
            DetectionExecution.status == 'failed'
        ).order_by(DetectionExecution.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_with_execution_result(self, db: AsyncSession, detection_id: UUID) -> Optional[DetectionExecution]:
        """Get detection execution with related execution result data"""
        query = select(DetectionExecution).options(
            selectinload(DetectionExecution.execution_result)
        ).where(DetectionExecution.id == detection_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_with_operation(self, db: AsyncSession, detection_id: UUID) -> Optional[DetectionExecution]:
        """Get detection execution with related operation data"""
        query = select(DetectionExecution).options(
            selectinload(DetectionExecution.operation)
        ).where(DetectionExecution.id == detection_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_with_results(self, db: AsyncSession, detection_id: UUID) -> Optional[DetectionExecution]:
        """Get detection execution with related detection results"""
        query = select(DetectionExecution).options(
            selectinload(DetectionExecution.detection_results)
        ).where(DetectionExecution.id == detection_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_retryable_executions(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[DetectionExecution]:
        """Get failed executions that can be retried"""
        query = select(DetectionExecution).where(
            and_(
                DetectionExecution.status == 'failed',
                DetectionExecution.retry_count < DetectionExecution.max_retries
            )
        ).order_by(DetectionExecution.created_at.asc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_completed_executions(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[DetectionExecution]:
        """Get completed detection executions"""
        query = select(DetectionExecution).where(
            DetectionExecution.status == 'completed'
        ).order_by(DetectionExecution.completed_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()


class DetectionResultRepository(BaseRepository[DetectionResult, DetectionResultCreate, DetectionResultUpdate]):
    """Repository for DetectionResult model with specific methods"""
    
    def __init__(self):
        super().__init__(DetectionResult)
    
    async def get_by_detection_execution_id(self, db: AsyncSession, detection_execution_id: UUID, skip: int = 0, limit: int = 100) -> List[DetectionResult]:
        """Get detection results by detection execution ID"""
        query = select(DetectionResult).where(
            DetectionResult.detection_execution_id == detection_execution_id
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_detected_results(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[DetectionResult]:
        """Get detection results where activity was detected"""
        query = select(DetectionResult).where(
            DetectionResult.detected == True
        ).order_by(DetectionResult.result_timestamp.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_not_detected_results(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[DetectionResult]:
        """Get detection results where activity was not detected"""
        query = select(DetectionResult).where(
            DetectionResult.detected == False
        ).order_by(DetectionResult.result_timestamp.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_source(self, db: AsyncSession, result_source: str, skip: int = 0, limit: int = 100) -> List[DetectionResult]:
        """Get detection results by source"""
        query = select(DetectionResult).where(
            DetectionResult.result_source == result_source
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_with_detection_execution(self, db: AsyncSession, result_id: UUID) -> Optional[DetectionResult]:
        """Get detection result with related detection execution data"""
        query = select(DetectionResult).options(
            selectinload(DetectionResult.detection_execution)
        ).where(DetectionResult.id == result_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_recent_results(self, db: AsyncSession, hours: int = 24, skip: int = 0, limit: int = 100) -> List[DetectionResult]:
        """Get detection results from the last N hours"""
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        query = select(DetectionResult).where(
            DetectionResult.result_timestamp >= cutoff_time
        ).order_by(DetectionResult.result_timestamp.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_detection_statistics(self, db: AsyncSession) -> Dict[str, Any]:
        """Get detection statistics"""
        from sqlalchemy import func
        
        # Total detections
        total_query = select(func.count(DetectionResult.id))
        total_result = await db.execute(total_query)
        total = total_result.scalar()
        
        # Detected count
        detected_query = select(func.count(DetectionResult.id)).where(DetectionResult.detected == True)
        detected_result = await db.execute(detected_query)
        detected_count = detected_result.scalar()
        
        # Not detected count
        not_detected_query = select(func.count(DetectionResult.id)).where(DetectionResult.detected == False)
        not_detected_result = await db.execute(not_detected_query)
        not_detected_count = not_detected_result.scalar()
        
        return {
            "total_detections": total,
            "detected_count": detected_count,
            "not_detected_count": not_detected_count,
            "detection_rate": (detected_count / total * 100) if total > 0 else 0
        } 