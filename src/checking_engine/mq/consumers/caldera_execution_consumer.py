"""
Consumer for receiving execution results from Caldera via RabbitMQ.

This consumer listens to the 'caldera.checking.instructions' queue and processes
messages containing execution results from Caldera operations. Each message
triggers the creation of operations, execution results, and detection executions
in the database, followed by task dispatching to appropriate workers.
"""

import asyncio
import json
from typing import Optional, Dict, Any

import aio_pika
from sqlalchemy.ext.asyncio import AsyncSession

from checking_engine.config import settings
from checking_engine.mq.connection import get_rabbitmq_connection
from checking_engine.application.message_service import MessageProcessingService
from checking_engine.database.connection import get_db_session
from checking_engine.utils.logging import get_logger

logger = get_logger(__name__)


class CalderaExecutionConsumer:
    """Consumer for processing execution results from Caldera"""
    
    def __init__(self):
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None
        self._running = False
    
    async def start_consuming(self):
        """Start consuming messages from the instructions queue"""
        try:
            logger.debug("Starting CalderaExecutionConsumer")
            
            # Connect to RabbitMQ as consumer
            self.connection = await get_rabbitmq_connection('consumer')
            logger.debug("Connected to RabbitMQ as consumer")
            
            # Create channel
            self.channel = await self.connection.channel()
            logger.debug("Created RabbitMQ channel")
            
            # Get the instructions queue
            self.queue = await self.channel.get_queue(settings.rabbitmq_instructions_queue)
            logger.debug(f"Got queue: {settings.rabbitmq_instructions_queue}")
            
            # Log queue status
            await self._log_queue_status()
            
            # Start consuming messages
            await self.queue.consume(self.process_message)
            self._running = True
            logger.debug("Started consuming messages from queue")
            
        except Exception as e:
            logger.error(f"Failed to start CalderaExecutionConsumer: {e}")
            await self._cleanup()
            raise
    
    async def _log_queue_status(self):
        """Log current queue status"""
        try:
            # Get queue info - aio-pika doesn't have declare(passive=True)
            # Instead, we get the queue and check its properties
            queue_info = await self.queue.declare()
            
            logger.debug(f"Queue status - Messages: {queue_info.message_count}, Consumers: {queue_info.consumer_count}")
            
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            # Log basic info even if detailed status fails
            logger.debug(f"Queue connected: {settings.rabbitmq_instructions_queue}")
    
    async def process_message(self, message: aio_pika.IncomingMessage):
        """Process incoming message from queue"""
        delivery_tag = getattr(message, 'delivery_tag', 'unknown')
        
        try:
            logger.debug(f"Received message - Delivery tag: {delivery_tag}")
            
            # Get message body and process outside of message.process() context
            body = message.body.decode('utf-8')
            logger.debug(f"Message body length: {len(body)} bytes")
            
            # Log message content (first 200 chars for safety)
            preview = body[:200] + "..." if len(body) > 200 else body
            logger.debug(f"Message preview: {preview}")
            
            # Process message with database session
            processing_success = False
            processing_result = None
            processing_error = None
            
            try:
                async for db_session in get_db_session():
                    message_service = MessageProcessingService(db_session)
                    processing_result = await message_service.process_caldera_message(body)
                    processing_success = True
                    break  # Only use first session
                    
            except Exception as e:
                processing_error = e
                logger.error(f"Failed to process message content: {e}")
                logger.error(f"Message body: {body}")
            
            # Now handle message acknowledgment/rejection
            async with message.process():
                if processing_success and processing_result:
                    # Log processing result
                    logger.debug(f"Message processed successfully - Delivery tag: {delivery_tag}")
                    logger.debug(f"Processing result: operation={processing_result['operation']['name']}, "
                                f"execution={processing_result['execution_result']['link_id']}, "
                                f"detections={len(processing_result['detection_executions'])}")
                    
                    # Message will be auto-acknowledged
                else:
                    # Raise error to trigger message rejection
                    if processing_error:
                        raise processing_error
                    else:
                        raise RuntimeError("Unknown processing error")
                
        except Exception as e:
            logger.error(f"Error processing message - Delivery tag: {delivery_tag}: {e}")
            # Don't try to reject here - message may already be processed
            # Let the exception propagate for aio-pika to handle
            raise
    
    async def stop_consuming(self):
        """Stop consuming messages"""
        if self._running:
            self._running = False
            logger.info("Stopping CalderaExecutionConsumer")
        
        await self._cleanup()
    
    async def _cleanup(self):
        """Clean up connections"""
        if self.channel:
            await self.channel.close()
            logger.debug("Closed RabbitMQ channel")
            self.channel = None
        
        if self.connection:
            await self.connection.close()
            logger.debug("Closed RabbitMQ connection")
            self.connection = None
    
    async def test_connection(self):
        """Test consumer connection"""
        try:
            await self.start_consuming()
            await asyncio.sleep(0.1)  # Brief test
            await self.stop_consuming()
            logger.debug("Consumer connection test successful")
            return True
        except Exception as e:
            logger.error(f"Consumer connection test failed: {e}")
            return False