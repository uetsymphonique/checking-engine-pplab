import asyncio
import aio_pika
from typing import Optional
from checking_engine.config import settings
from checking_engine.mq.connection import get_rabbitmq_connection
from checking_engine.database.connection import get_db_session
from checking_engine.services.message_service import MessageProcessingService
from checking_engine.utils.logging import get_logger, log_mq_operation

logger = get_logger(__name__)

class ExecutionResultConsumer:
    """Consumer for execution results from Caldera"""
    
    def __init__(self):
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None
        self._running = False
    
    async def start_consuming(self):
        """Start consuming execution results from RabbitMQ"""
        try:
            logger.info("Starting ExecutionResultConsumer")
            
            # Connect to RabbitMQ with consumer role
            self.connection = await get_rabbitmq_connection("consumer")
            logger.info("Connected to RabbitMQ as consumer")
            
            # Create channel
            self.channel = await self.connection.channel()
            logger.info("Created RabbitMQ channel")
            
            # Get the instructions queue
            self.queue = await self.channel.get_queue(settings.rabbitmq_instructions_queue)
            logger.info(f"Got queue: {settings.rabbitmq_instructions_queue}")
            
            # Log queue status
            await self._log_queue_status()
            
            # Start consuming messages
            await self.queue.consume(self.process_message)
            self._running = True
            logger.info("Started consuming messages from queue")
            
        except Exception as e:
            logger.error(f"Failed to start ExecutionResultConsumer: {e}")
            await self._cleanup()
            raise
    
    async def _log_queue_status(self):
        """Log current queue status"""
        try:
            # Get queue info - aio-pika doesn't have declare(passive=True)
            # Instead, we get the queue and check its properties
            queue_info = await self.queue.declare()
            
            log_mq_operation(
                logger, "queue_status", 
                settings.rabbitmq_instructions_queue,
                message_id=None,
                queue_name=settings.rabbitmq_instructions_queue,
                message_count=queue_info.message_count,
                consumer_count=queue_info.consumer_count,
                status="connected"
            )
            
            logger.info(f"Queue status - Messages: {queue_info.message_count}, Consumers: {queue_info.consumer_count}")
            
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            # Log basic info even if detailed status fails
            logger.info(f"Queue connected: {settings.rabbitmq_instructions_queue}")
    
    async def process_message(self, message: aio_pika.IncomingMessage):
        """Process incoming message from queue"""
        delivery_tag = getattr(message, 'delivery_tag', 'unknown')
        
        try:
            # Log message received
            log_mq_operation(
                logger, "message_received",
                settings.rabbitmq_instructions_queue,
                message_id=str(getattr(message, 'message_id', 'unknown')),
                delivery_tag=delivery_tag,
                routing_key=getattr(message, 'routing_key', 'unknown'),
                exchange=getattr(message, 'exchange', 'unknown'),
                redelivered=getattr(message, 'redelivered', False)
            )
            
            logger.info(f"Received message - Delivery tag: {delivery_tag}")
            
            # Get message body and process outside of message.process() context
            body = message.body.decode('utf-8')
            logger.info(f"Message body length: {len(body)} bytes")
            
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
                
                # Log MQ operation failure
                log_mq_operation(
                    logger, "message_processing_failed",
                    settings.rabbitmq_instructions_queue,
                    message_id=str(getattr(message, 'message_id', 'unknown')),
                    delivery_tag=delivery_tag,
                    error=str(e)
                )
            
            # Now handle message acknowledgment/rejection
            async with message.process():
                if processing_success and processing_result:
                    # Log processing result
                    logger.info(f"Message processed successfully - Delivery tag: {delivery_tag}")
                    logger.info(f"Processing result: operation={processing_result['operation']['name']}, "
                               f"execution={processing_result['execution_result']['link_id']}, "
                               f"detections={len(processing_result['detection_executions'])}")
                    
                    # Log MQ operation success
                    log_mq_operation(
                        logger, "message_processed",
                        settings.rabbitmq_instructions_queue,
                        message_id=str(getattr(message, 'message_id', 'unknown')),
                        delivery_tag=delivery_tag,
                        operation_id=processing_result['operation']['operation_id'],
                        link_id=processing_result['execution_result']['link_id'],
                        detections_count=len(processing_result['detection_executions'])
                    )
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
            logger.info("Stopping ExecutionResultConsumer")
        
        await self._cleanup()
    
    async def _cleanup(self):
        """Clean up resources"""
        try:
            if self.channel:
                await self.channel.close()
                logger.info("Closed RabbitMQ channel")
            
            if self.connection:
                await self.connection.close()
                logger.info("Closed RabbitMQ connection")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

async def test_consumer_connection():
    """Test consumer connection and queue access"""
    consumer = ExecutionResultConsumer()
    try:
        await consumer.start_consuming()
        logger.info("Consumer connection test successful")
        
        # Wait a bit to see logs
        await asyncio.sleep(2)
        
    except Exception as e:
        logger.error(f"Consumer connection test failed: {e}")
    finally:
        await consumer.stop_consuming()

if __name__ == "__main__":
    asyncio.run(test_consumer_connection()) 