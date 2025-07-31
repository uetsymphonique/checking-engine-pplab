#!/usr/bin/env python3
"""
Test script for message consumption
Push a fake message to the instructions queue to test consumer
"""

import asyncio
import json
import aio_pika
from datetime import datetime, timezone
from checking_engine.config import settings
from checking_engine.mq.connection import get_rabbitmq_connection
from checking_engine.utils.logging import get_logger, log_mq_operation

logger = get_logger(__name__)

async def publish_test_message():
    """Publish a test message to the instructions queue"""
    try:
        logger.info("Connecting to RabbitMQ as publisher")
        connection = await get_rabbitmq_connection("publisher")
        
        async with connection:
            channel = await connection.channel()
            exchange = await channel.get_exchange(settings.rabbitmq_exchange)
            
            # Create test message
            test_message = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message_type": "link_result",
                "operation": {
                    "name": "Test Operation",
                    "id": "test-op-123",
                    "start": datetime.now(timezone.utc).isoformat(),
                },
                "execution": {
                    "link_id": "test-link-456",
                    "agent_host": "test-host.local",
                    "agent_paw": "test-paw-789",
                    "command": "whoami",
                    "pid": 12345,
                    "status": 0,
                    "result_data": json.dumps({
                        "stdout": "testuser",
                        "stderr": "",
                        "exit_code": 0
                    }),
                    "agent_reported_time": datetime.now(timezone.utc).isoformat(),
                    "state": "SUCCESS"
                },
                "detections": {
                    "api": {
                        "siem": {
                            "query": "search index=security user=testuser",
                            "platform": "splunk"
                        }
                    },
                    "agent": {
                        "windows": {
                            "command": "Get-EventLog Security -InstanceId 4624",
                            "platform": "powershell"
                        }
                    }
                }
            }
            
            # Create message
            message_body = json.dumps(test_message, ensure_ascii=False).encode('utf-8')
            message = aio_pika.Message(
                message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type='application/json',
                content_encoding='utf-8',
                timestamp=datetime.now(timezone.utc)
            )
            
            # Publish message
            await exchange.publish(
                message,
                routing_key=settings.routing_key_execution_result
            )
            
            log_mq_operation(
                logger, "test_message_published",
                settings.rabbitmq_instructions_queue,
                message_id="test-msg-001",
                routing_key=settings.routing_key_execution_result,
                message_size=len(message_body)
            )
            
            logger.info(f"Test message published successfully")
            logger.info(f"Message size: {len(message_body)} bytes")
            logger.info(f"Routing key: {settings.routing_key_execution_result}")
            
    except Exception as e:
        logger.error(f"Failed to publish test message: {e}")
        raise

async def main():
    """Main test function"""
    logger.info("Starting message consumption test")
    
    # Publish test message
    await publish_test_message()
    
    logger.info("Test message published - check consumer logs")
    logger.info("You should see the message being consumed in the consumer logs")

if __name__ == "__main__":
    asyncio.run(main()) 