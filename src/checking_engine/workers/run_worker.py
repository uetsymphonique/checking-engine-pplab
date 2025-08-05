import asyncio
import signal
import sys

from checking_engine.config import settings
from checking_engine.utils.logging import setup_logging, get_logger
from checking_engine.mq.consumers.worker_task_consumer import DetectionTaskConsumer

logger = get_logger(__name__)


async def _run():
    consumer = DetectionTaskConsumer()
    shutdown_event = asyncio.Event()
    
    shutting_down = False
    
    def signal_handler(signum, frame):
        nonlocal shutting_down
        if shutting_down:
            # Second Ctrl+C → force quit immediately
            logger.warning("Second interrupt received, forcing exit now!")
            sys.exit(1)
        shutting_down = True
        logger.info("Received signal %s, shutting down worker gracefully...", signum)
        shutdown_event.set()
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)   # CTRL+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    try:
        await consumer.start_consuming()
        logger.info("Worker started. Press CTRL+C to stop.")
        
        # Wait for shutdown signal
        await shutdown_event.wait()
        
    except Exception as e:
        logger.error("Worker error: %s", e)
        raise
    finally:
        logger.info("Stopping worker...")
        try:
            await asyncio.wait_for(consumer.stop_consuming(), timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("Graceful shutdown timed out; forcing exit.")
        logger.info("Worker stopped.")


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
        logger.info("KeyboardInterrupt received, worker shutdown complete.")
        sys.exit(0)
    except Exception as e:
        logger.error("Fatal error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
