import asyncio
import signal
import sys

from checking_engine.config import settings
from checking_engine.utils.logging import setup_logging, get_logger
from checking_engine.mq.consumers.worker_task_consumer import DetectionTaskConsumer

logger = get_logger(__name__)


async def _run():
    consumer = DetectionTaskConsumer()
    await consumer.start_consuming()

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Received signal %d, initiating graceful shutdown...", signum)
        # Cancel the future to break the await loop
        if hasattr(_run, '_future'):
            _run._future.cancel()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)   # CTRL+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

    # Keep process alive with graceful shutdown capability
    try:
        _run._future = asyncio.Future()
        await _run._future
    except asyncio.CancelledError:
        logger.info("Shutdown requested, stopping consumer...")
    finally:
        logger.info("Stopping worker consumer...")
        await consumer.stop_consuming()
        logger.info("Worker shutdown complete")


def main() -> None:
    setup_logging(
        log_level=settings.log_level,
        log_file=settings.log_file,
        json_format=settings.log_json_format,
        console_output=settings.log_console_output,
    )
    
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, exiting...")
        sys.exit(0)
    except Exception as e:
        logger.error("Worker process failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
