import json
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from checking_engine.models.detection import DetectionExecution, DetectionResult
from checking_engine.repositories.detection_repo import DetectionExecutionRepository, DetectionResultRepository
from checking_engine.schemas.detection import DetectionExecutionCreate, DetectionExecutionUpdate, DetectionType, DetectionStatus
from checking_engine.utils.logging import get_logger

logger = get_logger(__name__)

class DetectionService:
    """Business logic for detection execution and result management"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.execution_repo = DetectionExecutionRepository()
        self.result_repo = DetectionResultRepository()
    
    async def create_detection_executions_from_message(
        self, 
        execution_result_id: UUID, 
        operation_id: UUID, 
        detections_data: Any
    ) -> List[DetectionExecution]:
        """Create detection executions from Caldera message detections field"""
        try:
            if not detections_data:
                logger.debug(f"No detections data for execution_result_id={execution_result_id}")
                return []
            
            # Parse detections if it's a string
            if isinstance(detections_data, str):
                try:
                    # First try JSON parsing
                    detections_list = json.loads(detections_data)
                except json.JSONDecodeError:
                    try:
                        # If JSON fails, try Python literal evaluation (for single quotes)
                        import ast
                        detections_list = ast.literal_eval(detections_data)
                        logger.debug(f"Successfully parsed detections using ast.literal_eval")
                    except (ValueError, SyntaxError) as e:
                        logger.warning(f"Failed to parse detections as JSON or Python literal: {detections_data}")
                        logger.warning(f"Parse error: {e}")
                        return []
            else:
                detections_list = detections_data
            
            if not isinstance(detections_list, list):
                logger.warning(f"Detections data is not a list: {detections_list}")
                return []
            
            created_detections = []
            
            for detection_config in detections_list:
                try:
                    # Validate detection_type
                    detection_type = detection_config.get("detection_type")
                    if detection_type not in [dt.value for dt in DetectionType]:
                        logger.warning(f"Invalid detection_type: {detection_type}")
                        continue
                    
                    # Get max_retries, default to 3
                    max_retries = detection_config.get("max_retries", 3)
                    
                    # Create detection execution
                    create_data = DetectionExecutionCreate(
                        execution_result_id=execution_result_id,
                        operation_id=operation_id,
                        detection_type=DetectionType(detection_type),
                        detection_platform=detection_config.get("detection_platform", "unknown"),
                        detection_config=detection_config.get("detection_config", {}),
                        status=DetectionStatus.PENDING,
                        retry_count=0,
                        max_retries=max_retries,
                        execution_metadata={}
                    )
                    
                    detection_execution = await self.execution_repo.create(self.db, create_data)
                    created_detections.append(detection_execution)
                    
                    logger.info(f"Created detection execution: type={detection_type}, platform={detection_config.get('detection_platform')}")
                    
                except Exception as e:
                    logger.error(f"Error creating detection execution from config {detection_config}: {e}")
                    continue
            
            logger.info(f"Created {len(created_detections)} detection executions for execution_result_id={execution_result_id}")
            return created_detections
            
        except Exception as e:
            logger.error(f"Error creating detection executions: {e}")
            raise
    
    async def update_detection_status(
        self, 
        detection_id: UUID, 
        status: DetectionStatus, 
        completed_at: Optional[datetime] = None,
        execution_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[DetectionExecution]:
        """Update detection execution status"""
        try:
            update_data = DetectionExecutionUpdate(
                status=status,
                completed_at=completed_at,
                execution_metadata=execution_metadata
            )
            
            updated_detection = await self.execution_repo.update(self.db, detection_id, update_data)
            if updated_detection:
                logger.debug(f"Updated detection {detection_id} status to {status}")
            
            return updated_detection
            
        except Exception as e:
            logger.error(f"Error updating detection status: {e}")
            raise
    
    async def get_pending_detections(self, limit: int = 10) -> List[DetectionExecution]:
        """Get pending detection executions for processing"""
        try:
            return await self.execution_repo.get_by_status(self.db, DetectionStatus.PENDING, limit=limit)
        except Exception as e:
            logger.error(f"Error getting pending detections: {e}")
            raise
    
    async def increment_retry_count(self, detection_id: UUID) -> Optional[DetectionExecution]:
        """Increment retry count for failed detection"""
        try:
            detection = await self.execution_repo.get(self.db, detection_id)
            if not detection:
                return None
            
            new_retry_count = detection.retry_count + 1
            status = DetectionStatus.FAILED if new_retry_count >= detection.max_retries else DetectionStatus.PENDING
            
            update_data = DetectionExecutionUpdate(
                retry_count=new_retry_count,
                status=status
            )
            
            updated_detection = await self.execution_repo.update(self.db, detection_id, update_data)
            logger.debug(f"Incremented retry count for detection {detection_id}: {new_retry_count}/{detection.max_retries}")
            
            return updated_detection
            
        except Exception as e:
            logger.error(f"Error incrementing retry count: {e}")
            raise 