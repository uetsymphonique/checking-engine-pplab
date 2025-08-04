"""Consumer that listens to api/agent response queues and persists DetectionResult."""
from __future__ import annotations

import json
from typing import Optional, Dict, Any

import aio_pika

from checking_engine.config import settings
from checking_engine.mq.connection import get_rabbitmq_connection
from checking_engine.application.result_service import ResultProcessingService
from checking_engine.database.connection import get_db_session
from checking_engine.utils.logging import get_logger

logger = get_logger(__name__)


class DetectionResultConsumer:  # pylint: disable=too-many-instance-attributes
    def __init__(self):
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queues: list[aio_pika.Queue] = []
        self._running = False

    # -------------------------------------------------------------
    async def start_consuming(self):
        try:
            logger.debug("Starting DetectionResultConsumer...")
            self.connection = await get_rabbitmq_connection("result_consumer")
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=20)

            for qname in (
                settings.rabbitmq_api_responses_queue,
                settings.rabbitmq_agent_responses_queue,
            ):
                queue = await self.channel.get_queue(qname)
                self.queues.append(queue)
                await queue.consume(self.process_message, no_ack=False)
                logger.info("Listening response queue '%s'", qname)

            self._running = True
        except Exception as exc:  # pragma: no cover
            logger.error("Failed to start DetectionResultConsumer: %s", exc)
            await self._cleanup()
            raise

    # -------------------------------------------------------------
    async def process_message(self, message: aio_pika.IncomingMessage):
        delivery_tag = getattr(message, "delivery_tag", "unknown")
        async with message.process(requeue=True):
            try:
                body = json.loads(message.body.decode("utf-8"))
                async for db in get_db_session():
                    svc = ResultProcessingService(db)
                    await svc.process_detection_result(body)
                    await db.commit()
                    break
                logger.debug("Stored detection result %s", body.get("id"))
            except Exception as exc:
                logger.error("Error processing result message %s: %s", delivery_tag, exc)
                raise  # nack & requeue

    # -------------------------------------------------------------
    async def stop_consuming(self):
        if self._running:
            self._running = False
            logger.info("Stopping DetectionResultConsumer...")
        await self._cleanup()

    async def _cleanup(self):
        if self.channel:
            await self.channel.close()
            self.channel = None
        if self.connection:
            await self.connection.close()
            self.connection = None
