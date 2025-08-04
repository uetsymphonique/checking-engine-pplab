"""ResultPublisher

Publishes standardized detection result messages produced by workers to the
corresponding *responses* queue (API or Agent) via the central exchange.

Uses RabbitMQ *checking_worker* credentials because workers already own write
rights to the exchange and response queues.
"""

from __future__ import annotations

import aio_pika
import json
from typing import Optional, Dict, Any

from checking_engine.config import settings
from checking_engine.mq.connection import get_rabbitmq_connection
from checking_engine.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)
setup_logging(log_level=settings.log_level)

class ResultPublisher:  # pylint: disable=too-few-public-methods
    """Publish detection results to api/agent response queues."""

    def __init__(self) -> None:
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        self._initialized = False

    # -------------------------------------------------------------
    async def initialize(self) -> None:
        if self._initialized:
            return
        try:
            logger.debug("Initializing ResultPublisher (worker user)")
            self.connection = await get_rabbitmq_connection("worker")
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.get_exchange(settings.rabbitmq_exchange)
            self._initialized = True
            logger.debug("ResultPublisher initialized")
        except Exception:  # pragma: no cover
            await self._cleanup()
            raise

    # -------------------------------------------------------------
    def _determine_target(self, worker_type: str) -> Dict[str, str]:
        wt = worker_type.lower()
        if wt == "api":
            return {
                "queue_name": settings.rabbitmq_api_responses_queue,
                "routing_key": settings.routing_key_api_response,
            }
        else:
            # Default all non-API detections to agent responses queue
            return {
                "queue_name": settings.rabbitmq_agent_responses_queue,
                "routing_key": settings.routing_key_agent_response,
            }

    # -------------------------------------------------------------
    async def publish_detection_result(self, result_msg: Dict[str, Any], *, worker_type: str) -> None:
        if not self._initialized:
            await self.initialize()

        target = self._determine_target(worker_type)
        body = json.dumps(result_msg, ensure_ascii=False).encode("utf-8")
        message = aio_pika.Message(
            body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
            content_encoding="utf-8",
        )
        await self.exchange.publish(message, routing_key=target["routing_key"])
        logger.debug(
            "Published detection_result to %s (routing_key=%s)",
            target["queue_name"],
            target["routing_key"],
        )

    # -------------------------------------------------------------
    async def _cleanup(self) -> None:
        if self.channel:
            await self.channel.close()
            self.channel = None
        if self.connection:
            await self.connection.close()
            self.connection = None
        self._initialized = False

    async def close(self) -> None:
        await self._cleanup()
