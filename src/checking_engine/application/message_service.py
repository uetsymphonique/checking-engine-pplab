import json
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from checking_engine.domain.operation_service import OperationService
from checking_engine.domain.execution_service import ExecutionService
from checking_engine.domain.detection_service import DetectionService
from checking_engine.mq.publishers import TaskDispatcher
from checking_engine.utils.logging import get_logger

logger = get_logger(__name__)

class MessageProcessingService:
    """Service for processing Caldera messages and storing in database"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.operation_service = OperationService(db_session)
        self.execution_service = ExecutionService(db_session)
        self.detection_service = DetectionService(db_session)
    
    async def process_caldera_message(self, message_body: str) -> Dict[str, Any]:
        """Process complete Caldera message and store in database"""
        try:
            # Parse message
            message_data = json.loads(message_body)
            logger.debug(f"Processing message type: {message_data.get('message_type')}")
            
            # Validate message structure
            if not self._validate_message_structure(message_data):
                raise ValueError("Invalid message structure")
            
            # Process with database transaction
            # 1. Create or get operation
            operation_data = message_data["operation"]
            operation = await self.operation_service.create_or_get_operation(operation_data)
            
            # 2. Create execution result
            execution_data = message_data["execution"]
            execution_result = await self.execution_service.create_execution_result(
                execution_data, message_data
            )
            
            # 3. Create detection executions if detections exist
            detections_data = execution_data.get("detections")
            detection_executions = []
            if detections_data:
                detection_executions = await self.detection_service.create_detection_executions_from_message(
                    execution_result.id,
                    operation.operation_id,
                    detections_data
                )
            
            # Commit transaction
            await self.db.commit()
            
            # IMMEDIATE DISPATCH: If execution was successful, dispatch detection tasks
            dispatch_result = None
            if execution_result.link_state == "SUCCESS" and detection_executions:
                try:
                    logger.info(f"Execution SUCCESS detected - dispatching {len(detection_executions)} detection tasks")
                    
                    # Initialize task dispatcher with database session
                    task_dispatcher = TaskDispatcher(db_session=self.db)
                    
                    # Dispatch tasks immediately after DB commit
                    dispatch_result = await task_dispatcher.dispatch_detection_tasks(detection_executions)
                    
                    # Commit status updates to database
                    await self.db.commit()
                    
                    logger.info(f"Task dispatch completed: {dispatch_result['dispatched_count']} dispatched, "
                               f"{dispatch_result['failed_count']} failed")
                    
                    # Close dispatcher connection
                    await task_dispatcher.close()
                    
                except Exception as e:
                    logger.error(f"Immediate task dispatch failed: {e}")
                    # Don't fail message processing if dispatch fails
                    # Tasks will remain in 'pending' status for periodic cleanup
                    dispatch_result = {
                        'status': 'failed',
                        'error': str(e),
                        'dispatched_count': 0,
                        'failed_count': len(detection_executions) if detection_executions else 0
                    }
            else:
                if execution_result.link_state != "SUCCESS":
                    logger.debug(f"Execution not successful (state={execution_result.link_state}) - skipping task dispatch")
                if not detection_executions:
                    logger.debug("No detection executions to dispatch")
            
            result = {
                "status": "success",
                "message_type": message_data.get("message_type"),
                "timestamp": message_data.get("timestamp"),
                "operation": {
                    "id": str(operation.id),
                    "operation_id": str(operation.operation_id),
                    "name": operation.name
                },
                "execution_result": {
                    "id": str(execution_result.id),
                    "link_id": str(execution_result.link_id),
                    "agent_paw": execution_result.agent_paw,
                    "command": execution_result.command,
                    "status": execution_result.status,
                    "link_state": execution_result.link_state
                },
                "detection_executions": [
                    {
                        "id": str(det.id),
                        "detection_type": det.detection_type,
                        "detection_platform": det.detection_platform,
                        "status": det.status
                    }
                    for det in detection_executions
                ],
                "task_dispatch": dispatch_result  # Include dispatch results
            }
            
            logger.info(f"Successfully processed message: operation={operation.name}, "
                       f"execution={execution_result.link_id}, "
                       f"detections={len(detection_executions)}")
            
            return result
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message JSON: {e}")
            await self.db.rollback()
            raise ValueError(f"Invalid JSON message: {e}")
            
        except Exception as e:
            logger.error(f"Error processing Caldera message: {e}")
            await self.db.rollback()
            raise
    
    def _validate_message_structure(self, message_data: Dict[str, Any]) -> bool:
        """Validate required fields in Caldera message"""
        try:
            # Check required top-level fields
            required_fields = ["timestamp", "message_type", "operation", "execution"]
            for field in required_fields:
                if field not in message_data:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Check operation fields
            operation = message_data["operation"]
            operation_required = ["name", "operation_id"]
            for field in operation_required:
                if field not in operation:
                    logger.error(f"Missing required operation field: {field}")
                    return False
            
            # Check execution fields
            execution = message_data["execution"]
            execution_required = ["link_id", "agent_host", "agent_paw", "command"]
            for field in execution_required:
                if field not in execution:
                    logger.error(f"Missing required execution field: {field}")
                    return False
            
            logger.debug("Message structure validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating message structure: {e}")
            return False
    
    async def get_processing_statistics(self) -> Dict[str, Any]:
        """Get statistics about message processing"""
        try:
            # This would typically query the database for stats
            # For now, return basic info
            return {
                "status": "active",
                "last_processed": datetime.now().isoformat(),
                "services": {
                    "operation_service": "active",
                    "execution_service": "active", 
                    "detection_service": "active"
                }
            }
        except Exception as e:
            logger.error(f"Error getting processing statistics: {e}")
            raise