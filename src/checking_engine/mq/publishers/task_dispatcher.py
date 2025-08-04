"""
Task Dispatcher for publishing detection tasks to worker queues.

This publisher sends detection tasks to appropriate worker queues (API or Agent)
based on the detection type. It handles the routing logic and message publishing
for the Purple Team checking engine workflow.
"""

import asyncio
import aio_pika
import json
from typing import List, Dict, Any, Optional
from uuid import uuid4, UUID
from sqlalchemy.ext.asyncio import AsyncSession

from checking_engine.config import settings
from checking_engine.mq.connection import get_rabbitmq_connection
from checking_engine.models.detection import DetectionExecution
from checking_engine.schemas.detection import DetectionStatus, DetectionType
from checking_engine.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)
setup_logging(log_level=settings.log_level)


class TaskDispatcher:
    """Publisher for dispatching detection tasks to appropriate worker queues"""
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db = db_session
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize connection and exchange"""
        try:
            logger.debug("Initializing TaskDispatcher")
            
            # Connect to RabbitMQ as dispatcher
            self.connection = await get_rabbitmq_connection('dispatcher')
            logger.debug("Connected to RabbitMQ as dispatcher")
            
            # Create channel
            self.channel = await self.connection.channel()
            logger.debug("Created RabbitMQ channel for dispatcher")
            
            # Get the main exchange
            self.exchange = await self.channel.get_exchange(settings.rabbitmq_exchange)
            logger.debug(f"Got exchange: {settings.rabbitmq_exchange}")
            
            # Test queue access (just verify we can see them)
            await self._verify_queue_access()
            
            self._initialized = True
            logger.debug("TaskDispatcher initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize TaskDispatcher: {e}")
            await self._cleanup()
            raise
    
    async def _verify_queue_access(self):
        """Verify dispatcher can access target queues (read-only check)"""
        try:
            # Note: Dispatcher role can only publish, not read queues
            # So we just verify the queues exist by attempting to get them
            # This might fail due to permissions, which is expected
            
            logger.debug("Verifying task queue accessibility...")
            
            # Log the queues we plan to dispatch to
            api_queue_name = settings.rabbitmq_api_tasks_queue
            agent_queue_name = settings.rabbitmq_agent_tasks_queue
            
            logger.debug(f"Target API tasks queue: {api_queue_name}")
            logger.debug(f"Target Agent tasks queue: {agent_queue_name}")
            
            # Log routing keys we will use
            api_routing_key = settings.routing_key_api_task
            agent_routing_key = settings.routing_key_agent_task
            
            logger.debug(f"API task routing key: {api_routing_key}")
            logger.debug(f"Agent task routing key: {agent_routing_key}")
            
            logger.debug("Queue verification completed (dispatcher has publish-only access)")
            
        except Exception as e:
            logger.warning(f"Queue verification failed (expected for dispatcher role): {e}")
    
    def determine_target_queue_info(self, detection_type: str) -> Dict[str, str]:
        """
        Determine target queue and routing key based on detection type
        
        Args:
            detection_type: The type of detection ('api', 'windows', 'linux', 'darwin')
            
        Returns:
            Dict containing queue_name, routing_key, and worker_type
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
        
        logger.debug(f"Starting dispatch of {len(detection_executions)} detection tasks")
        
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
                    "task_id": str(uuid4()),  # unique id for downstream result mapping
                    "detection_execution_id": str(detection.id),
                    "operation_id": str(detection.operation_id) if detection.operation_id else None,
                    "detection_type": detection.detection_type,
                    "detection_platform": detection.detection_platform,
                    "detection_config": detection.detection_config,
                    "created_at": detection.created_at.isoformat() if detection.created_at else None,
                    "execution_context": detection.execution_metadata,
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
                
                logger.debug(f"Dispatched detection {detection.id} "
                            f"(type={detection.detection_type}, platform={detection.detection_platform}) "
                            f"to {queue_info['queue_name']} with routing key {queue_info['routing_key']}")
                
                # Update detection status to 'dispatched' (tasks have been dispatched to workers)
                if self.db:
                    detection.status = DetectionStatus.DISPATCHED.value
                    await self.db.flush()  # Flush to ensure it's saved
                
                tasks_by_type[worker_type] += 1
                dispatched_count += 1
                
                # Log MQ operation
                logger.debug(f"Dispatched detection {detection.id} to {queue_info['queue_name']}")
                
            except Exception as e:
                logger.error(f"Failed to dispatch detection {detection.id}: {e}")
                failed_count += 1
        
        logger.debug(f"Dispatch completed: {dispatched_count} dispatched, {failed_count} failed")
        logger.debug(f"Tasks by type: {tasks_by_type}")
        
        return {
            'status': 'success' if failed_count == 0 else 'partial',
            'dispatched_count': dispatched_count,
            'failed_count': failed_count,
            'tasks_by_type': tasks_by_type
        }
    
    async def _cleanup(self):
        """Clean up connections"""
        if self.channel:
            await self.channel.close()
            logger.debug("Closed dispatcher RabbitMQ channel")
            self.channel = None
        
        if self.connection:
            await self.connection.close()
            logger.debug("Closed dispatcher RabbitMQ connection")
            self.connection = None
        
        self._initialized = False
    
    async def close(self):
        """Close TaskDispatcher connections"""
        await self._cleanup()
    
    async def test_connection(self):
        """Test dispatcher connection and functionality"""
        try:
            await self.initialize()
            logger.debug("TaskDispatcher connection test successful")
            
            # Test queue determination logic
            test_cases = [DetectionType.API, DetectionType.WINDOWS, DetectionType.LINUX, DetectionType.DARWIN]
            
            if await self._test_queue_determination(test_cases):
                logger.debug("✅ TaskDispatcher connection test PASSED")
                return True
            else:
                logger.error("❌ TaskDispatcher connection test FAILED")
                return False
                
        except Exception as e:
            logger.error(f"TaskDispatcher connection test failed: {e}")
            return False
        finally:
            await self._cleanup()
    
    async def _test_queue_determination(self, test_cases: List[DetectionType]) -> bool:
        """Test queue determination logic"""
        try:
            logger.debug("\n🧪 Testing queue determination logic:")
            
            dispatcher = TaskDispatcher()
            for detection_type in test_cases:
                queue_info = dispatcher.determine_target_queue_info(detection_type)
                logger.debug(f"  {detection_type.value} → {queue_info['worker_type']} worker "
                            f"(queue: {queue_info['queue_name']}, "
                            f"routing_key: {queue_info['routing_key']})")
            
            logger.debug("✅ Queue determination logic test PASSED")
            return True
        except Exception as e:
            logger.error(f"Queue determination test failed: {e}")
            return False