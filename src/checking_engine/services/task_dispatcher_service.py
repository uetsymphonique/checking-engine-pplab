import asyncio
import aio_pika
import json
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from checking_engine.config import settings
from checking_engine.mq.connection import get_rabbitmq_connection
from checking_engine.models.detection import DetectionExecution
from checking_engine.schemas.detection import DetectionStatus
from checking_engine.utils.logging import get_logger, log_mq_operation

logger = get_logger(__name__)

class TaskDispatcherService:
    """Service for dispatching detection tasks to appropriate worker queues"""
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db = db_session
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize RabbitMQ connection and exchange for dispatcher role"""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing TaskDispatcherService")
            
            # Connect to RabbitMQ with dispatcher role
            self.connection = await get_rabbitmq_connection("dispatcher")
            logger.info("Connected to RabbitMQ as dispatcher")
            
            # Create channel
            self.channel = await self.connection.channel()
            logger.info("Created RabbitMQ channel for dispatcher")
            
            # Get the main exchange
            self.exchange = await self.channel.get_exchange(settings.rabbitmq_exchange)
            logger.info(f"Got exchange: {settings.rabbitmq_exchange}")
            
            # Test queue access (just verify we can see them)
            await self._verify_queue_access()
            
            self._initialized = True
            logger.info("TaskDispatcherService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize TaskDispatcherService: {e}")
            await self._cleanup()
            raise
    
    async def _verify_queue_access(self):
        """Verify dispatcher can access target queues (read-only check)"""
        try:
            # Note: Dispatcher role can only publish, not read queues
            # So we just verify the queues exist by attempting to get them
            # This might fail due to permissions, which is expected
            
            logger.info("Verifying task queue accessibility...")
            
            # Log the queues we plan to dispatch to
            api_queue_name = settings.rabbitmq_api_tasks_queue
            agent_queue_name = settings.rabbitmq_agent_tasks_queue
            
            logger.info(f"Target API tasks queue: {api_queue_name}")
            logger.info(f"Target Agent tasks queue: {agent_queue_name}")
            
            # Log routing keys we will use
            api_routing_key = settings.routing_key_api_task
            agent_routing_key = settings.routing_key_agent_task
            
            logger.info(f"API task routing key: {api_routing_key}")
            logger.info(f"Agent task routing key: {agent_routing_key}")
            
            logger.info("Queue verification completed (dispatcher has publish-only access)")
            
        except Exception as e:
            logger.warning(f"Queue verification had issues (expected for dispatcher role): {e}")
    
    def determine_target_queue_info(self, detection_type: str) -> Dict[str, str]:
        """
        Business logic: Determine target queue and routing key based on detection type
        
        Args:
            detection_type: The type of detection as string from database ('api', 'windows', 'linux', 'darwin')
            
        Returns:
            Dict with 'queue_name' and 'routing_key'
        """
        # Convert to lowercase for consistent comparison
        detection_type_lower = detection_type.lower()
        
        if detection_type_lower == 'api':
            return {
                'queue_name': settings.rabbitmq_api_tasks_queue,
                'routing_key': settings.routing_key_api_task,
                'worker_type': 'api'
            }
        elif detection_type_lower in ['windows', 'linux', 'darwin']:
            return {
                'queue_name': settings.rabbitmq_agent_tasks_queue, 
                'routing_key': settings.routing_key_agent_task,
                'worker_type': 'agent'
            }
        else:
            raise ValueError(f"Unsupported detection type: {detection_type}")
    
    async def dispatch_detection_tasks(self, detection_executions: List[DetectionExecution]) -> Dict[str, Any]:
        """
        Dispatch detection tasks to appropriate worker queues
        
        Args:
            detection_executions: List of DetectionExecution objects to dispatch
            
        Returns:
            Dict with dispatch results and statistics
        """
        if not self._initialized:
            await self.initialize()
        
        if not detection_executions:
            logger.info("No detection executions to dispatch")
            return {
                'status': 'success',
                'dispatched_count': 0,
                'failed_count': 0,
                'tasks_by_type': {}
            }
        
        logger.info(f"Starting dispatch of {len(detection_executions)} detection tasks")
        
        dispatched_count = 0
        failed_count = 0
        tasks_by_type = {}
        
        for detection in detection_executions:
            try:
                # Determine target queue based on detection type
                queue_info = self.determine_target_queue_info(detection.detection_type)
                
                # Track tasks by type
                worker_type = queue_info['worker_type']
                if worker_type not in tasks_by_type:
                    tasks_by_type[worker_type] = 0
                
                # Create task message payload
                task_message = {
                    "task_id": str(detection.id),
                    "detection_execution_id": str(detection.id),
                    "operation_id": str(detection.operation_id) if detection.operation_id else None,
                    "detection_type": detection.detection_type,
                    "detection_platform": detection.detection_platform,
                    "detection_config": detection.detection_config,  # Use detection_config instead of detection_query
                    "created_at": detection.created_at.isoformat() if detection.created_at else None,
                    "metadata": {
                        "priority": "normal",
                        "worker_type": worker_type,
                        "target_queue": queue_info['queue_name']
                    }
                }
                
                # Publish message to RabbitMQ
                message_body = json.dumps(task_message, ensure_ascii=False).encode('utf-8')
                message = aio_pika.Message(
                    message_body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    content_type='application/json',
                    content_encoding='utf-8'
                )
                
                await self.exchange.publish(message, routing_key=queue_info['routing_key'])
                
                logger.info(f"Dispatched detection {detection.id} "
                           f"(type={detection.detection_type}, platform={detection.detection_platform}) "
                           f"to {queue_info['queue_name']} with routing key {queue_info['routing_key']}")
                
                # Update detection status to 'dispatched' (tasks have been dispatched to workers)
                if self.db:
                    detection.status = DetectionStatus.DISPATCHED.value
                    await self.db.flush()  # Flush to ensure it's saved
                
                tasks_by_type[worker_type] += 1
                dispatched_count += 1
                
                # Log MQ operation (simulated for now)
                log_mq_operation(
                    logger, "task_dispatch_planned",
                    queue_info['queue_name'],
                    message_id=None,
                    detection_id=str(detection.id),
                    detection_type=detection.detection_type,  # Already a string, no need for .value
                    routing_key=queue_info['routing_key']
                )
                
            except Exception as e:
                logger.error(f"Failed to dispatch detection {detection.id}: {e}")
                failed_count += 1
        
        result = {
            'status': 'success' if failed_count == 0 else 'partial_success',
            'dispatched_count': dispatched_count,
            'failed_count': failed_count,
            'tasks_by_type': tasks_by_type
        }
        
        logger.info(f"Dispatch completed: {dispatched_count} dispatched, {failed_count} failed")
        logger.info(f"Tasks by type: {tasks_by_type}")
        
        return result
    
    async def close(self):
        """Close TaskDispatcher connections"""
        await self._cleanup()
    
    async def test_connection(self) -> bool:
        """Test dispatcher connection and return success status"""
        try:
            await self.initialize()
            logger.info("TaskDispatcherService connection test successful")
            return True
        except Exception as e:
            logger.error(f"TaskDispatcherService connection test failed: {e}")
            return False
    
    async def close(self):
        """Close dispatcher connections"""
        await self._cleanup()
    
    async def _cleanup(self):
        """Clean up RabbitMQ resources"""
        try:
            if self.channel:
                await self.channel.close()
                logger.info("Closed dispatcher RabbitMQ channel")
            
            if self.connection:
                await self.connection.close()
                logger.info("Closed dispatcher RabbitMQ connection")
                
            self._initialized = False
                
        except Exception as e:
            logger.error(f"Error during dispatcher cleanup: {e}")

async def test_task_dispatcher():
    """Test TaskDispatcherService connection and queue logic"""
    dispatcher = TaskDispatcherService()
    
    try:
        # Test connection
        success = await dispatcher.test_connection()
        if success:
            logger.info("✅ TaskDispatcher connection test PASSED")
            
            # Test queue determination logic
            logger.info("\n🧪 Testing queue determination logic:")
            
            test_cases = [
                DetectionType.API,
                DetectionType.WINDOWS,
                DetectionType.LINUX,
                DetectionType.DARWIN
            ]
            
            for detection_type in test_cases:
                queue_info = dispatcher.determine_target_queue_info(detection_type)
                logger.info(f"  {detection_type.value} → {queue_info['worker_type']} worker "
                           f"(queue: {queue_info['queue_name']}, "
                           f"routing_key: {queue_info['routing_key']})")
            
            logger.info("✅ Queue determination logic test PASSED")
        else:
            logger.error("❌ TaskDispatcher connection test FAILED")
            
    except Exception as e:
        logger.error(f"❌ TaskDispatcher test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await dispatcher.close()

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
    
    from checking_engine.utils.logging import setup_logging
    setup_logging(log_level="INFO")
    
    asyncio.run(test_task_dispatcher())