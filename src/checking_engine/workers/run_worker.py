import asyncio

from checking_engine.config import settings
from checking_engine.utils.logging import setup_logging, get_logger
from checking_engine.mq.consumers.worker_task_consumer import DetectionTaskConsumer

logger = get_logger(__name__)


async def _run():
    consumer = DetectionTaskConsumer()
    await consumer.start_consuming()

    # Keep process alive
    try:
        await asyncio.Future()
    finally:
        await consumer.stop_consuming()


def main() -> None:
    setup_logging(
        log_level=settings.log_level,
        log_file=settings.log_file,
        json_format=settings.log_json_format,
        console_output=settings.log_console_output,
    )
    asyncio.run(_run())


if __name__ == "__main__":
    main()
