"""Consumer for detection tasks from RabbitMQ.

Listens to two queues:
- settings.rabbitmq_api_tasks_queue
- settings.rabbitmq_agent_tasks_queue

After receiving a message, the consumer routes to the appropriate worker based on
`metadata.worker_type` (currently only supports 'api' with MockAPIWorker).
"""

import asyncio
import json
from datetime import datetime
from typing import Optional, Dict, Any

import aio_pika

from checking_engine.config import settings
from checking_engine.mq.connection import get_rabbitmq_connection
from checking_engine.utils.logging import get_logger
from checking_engine.workers.api.mock_api_worker import MockAPIWorker
from checking_engine.workers.base_worker import MaxRetriesExceededException
from checking_engine.mq.publishers import ResultPublisher

logger = get_logger(__name__)


class DetectionTaskConsumer:
    """Async consumer for detection tasks."""

    def __init__(self) -> None:
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queues: list[aio_pika.Queue] = []
        self._running: bool = False

        # Result publisher shared across tasks
        self.result_publisher = ResultPublisher()

        # Worker registry (map by detection_type)
        self.worker_registry = {
            "api": MockAPIWorker(),
            # "windows": WindowsAgentWorker(), # to be implemented
            # "linux": LinuxAgentWorker(),
            # "darwin": MacAgentWorker(),
        }

    async def start_consuming(self) -> None:
        """Connect RabbitMQ and start consuming both task queues."""
        try:
            logger.debug("Starting DetectionTaskConsumer...")

            self.connection = await get_rabbitmq_connection("worker")
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=20)

            queue_names = [
                settings.rabbitmq_api_tasks_queue,
                settings.rabbitmq_agent_tasks_queue,
            ]

            for qname in queue_names:
                queue = await self.channel.get_queue(qname)
                self.queues.append(queue)
                await queue.consume(self.process_message, no_ack=False)
                logger.info("Listening queue '%s'", qname)

            self._running = True
            logger.info("DetectionTaskConsumer started - waiting for tasks...")

        except Exception as exc:  # pragma: no cover
            logger.error("Failed to start DetectionTaskConsumer: %s", exc)
            await self._cleanup()
            raise

    async def process_message(self, message: aio_pika.IncomingMessage) -> None:
        """Handle one message from task queues."""
        delivery_tag = getattr(message, "delivery_tag", "unknown")
        async with message.process(requeue=True):  # auto-ack on return / exception → nack & requeue
            try:
                body = message.body.decode("utf-8")
                task_data = json.loads(body)

                detection_type = task_data.get("detection_type")
                detection_platform = task_data.get("detection_platform")
                
                if not detection_type or not detection_platform:
                    raise ValueError(f"Missing detection_type or detection_platform in task: {task_data}")
                
                worker = self._get_worker_for_task(detection_type, detection_platform)
                if not worker:
                    logger.warning(
                        "No worker found for detection_type=%s, platform=%s - publishing cancelled result",
                        detection_type, detection_platform
                    )

                    # Build failure result message (unsupported)
                    fail_result = {
                        "id": task_data.get("task_id"),
                        "detection_execution_id": task_data.get("detection_execution_id"),
                        "detected": None,
                        "raw_response": None,
                        "parsed_results": None,
                        "result_timestamp": datetime.utcnow().isoformat(),
                        "result_source": "dispatcher",
                        "result_metadata": {"error": "unsupported worker"},
                        "started_at": None,
                        "status": "cancelled",
                        "retry_count": 0,
                    }
                    await self.result_publisher.publish_detection_result(
                        fail_result,
                        worker_type=task_data.get("metadata", {}).get("worker_type", detection_type),
                    )
                    logger.debug("Published cancelled-unsupported result for task %s", delivery_tag)
                    return  # ACK message
                # Ensure worker initialized once
                if hasattr(worker, "_initialized") and not getattr(worker, "_initialized"):
                    await worker.initialize()
                    setattr(worker, "_initialized", True)

                logger.debug(
                    "Dispatching message %s to worker (type=%s, platform=%s)", 
                    delivery_tag, detection_type, detection_platform
                )

                result = await worker.process_task(task_data)
                logger.debug("Task %s result built", delivery_tag)

                # Determine worker_type from task metadata
                worker_type = task_data.get("metadata", {}).get("worker_type", detection_type)

                # Publish detection result to response queue
                await self.result_publisher.publish_detection_result(
                    result,
                    worker_type=worker_type,
                )
                logger.debug("Task %s result published", delivery_tag)

            except MaxRetriesExceededException as exc:
                logger.error("Task %s permanently failed after all retries: %s", 
                           delivery_tag, str(exc.last_error))
                # Publish failure result message
                await self.result_publisher.publish_detection_result(
                    exc.result_msg,
                    worker_type=task_data.get("metadata", {}).get("worker_type", detection_type),
                )
                logger.debug("Task %s failure result published", delivery_tag)
                # ACK (by returning) to prevent infinite requeue
                return
            
            except Exception as exc:
                logger.error("Error processing message %s: %s", delivery_tag, exc)
                raise  # re-raise so aio-pika will NACK (requeue=True)

    async def stop_consuming(self) -> None:
        if self._running:
            self._running = False
            logger.info("Stopping DetectionTaskConsumer...")
        await self._cleanup()

    async def _cleanup(self) -> None:
        if self.channel is not None:
            await self.channel.close()
            self.channel = None
            logger.debug("Closed RabbitMQ channel (worker)")
        if self.connection is not None:
            await self.connection.close()
            self.connection = None
            logger.debug("Closed RabbitMQ connection (worker)")
        # Close result publisher connection
        if self.result_publisher:
            await self.result_publisher.close()
    
    def _get_worker_for_task(self, detection_type: str, detection_platform: str):
        """Get appropriate worker based on detection_type and detection_platform."""
        for worker in self.worker_registry.values():
            if hasattr(worker, 'supports_detection'):
                if worker.supports_detection(detection_type, detection_platform):
                    return worker
        
        # Fallback to worker_type matching for backward compatibility
        # for worker in self.workers:
        #     if hasattr(worker, 'worker_type'):
        #         if worker.worker_type == detection_type:
        #             return worker
        
        return None
