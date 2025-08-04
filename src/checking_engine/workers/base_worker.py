from __future__ import annotations

import asyncio
import json
import random
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from checking_engine.utils.logging import get_logger

logger = get_logger(__name__)


class MaxRetriesExceededException(Exception):
    """Raised when max retries are exceeded; carries failure result message."""
    
    def __init__(self, task_id: str, attempts: int, last_error: Exception, result_msg: Dict[str, Any]):
        self.task_id = task_id
        self.attempts = attempts
        self.last_error = last_error
        self.result_msg = result_msg
        super().__init__(f"Task {task_id} failed after {attempts} attempts: {last_error}")


class TaskProcessingException(Exception):
    """Base exception for task processing errors that should be retried."""
    pass


class BaseWorker(ABC):
    """Abstract base class for all detection workers.

    A worker receives one task message (dict) and returns a detection
    *result* (also dict).  All I/O must be executed asynchronously so that a
    single event-loop can handle many tasks concurrently.
    """

    #: Logical worker type.  Must match the ``worker_type`` field inside task
    #: message metadata so that the consumer can pick the correct worker.
    worker_type: str = "base"

    #: Concurrency limit per worker instance (``None`` → unlimited)
    max_concurrency: Optional[int] = 5
    
    #: Retry configuration defaults
    jitter_range: tuple[float, float] = (0.1, 0.5)  # additional random jitter range

    def __init__(self) -> None:  # noqa: D401
        self._semaphore: Optional[asyncio.Semaphore] = None

    async def initialize(self) -> None:
        """Optional one-time initialization hook (HTTP session, etc.)."""
        # Default implementation does nothing.
        return None

    async def _acquire(self):
        """Internal helper to honour ``max_concurrency`` using a semaphore."""
        if self.max_concurrency is None:
            # Dummy async context-manager
            class _Noop:  # pylint: disable=too-few-public-methods
                async def __aenter__(self_inner):  # noqa: D401
                    return None
                async def __aexit__(self_inner, exc_type, exc, tb):  # noqa: D401
                    return False
            return _Noop()

        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrency)
        return self._semaphore

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process one task message with retry logic.
        
        This is the public interface. Subclasses should implement _do_work instead.
        """
        # Acquire semaphore to limit concurrency
        async with await self._acquire():
            return await self._execute_with_retry(task)
    
    async def _execute_with_retry(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task with jitter and retry logic."""
        # Extract configuration from task
        detection_config = task.get("detection_config", {})
        task_id = task.get("task_id", "unknown")
        
        # Log full task message (debug)
        logger.debug("Processing task message: %s", json.dumps(task, indent=2))
        
        # Calculate and apply jitter
        config_jitter = detection_config.get("jitter", 0)
        random_jitter = random.uniform(*self.jitter_range)
        total_jitter = config_jitter + random_jitter
        
        logger.debug("Task %s - Config jitter: %.2fs, Random jitter: %.2fs, Total: %.2fs",
                    task_id, config_jitter, random_jitter, total_jitter)
        
        if total_jitter > 0:
            await asyncio.sleep(total_jitter)
        
        # Get retry configuration (max_retries = max_attempts)
        max_attempts = task.get("max_retries", 1)
        delay = detection_config.get("delay", 3.0)
        
        logger.debug("Task %s - Max attempts: %d, Delay between retries: %.2fs",
                    task_id, max_attempts, delay)
        
        # Attempt loop
        last_error = None
        start_time = datetime.utcnow()
        
        for attempt in range(max_attempts):
            try:
                logger.debug("Task %s - Attempt %d/%d", task_id, attempt + 1, max_attempts)
                result = await self._do_work(task)
                # Ensure required metadata present
                if "started_at" not in result or result["started_at"] is None:
                    result["started_at"] = start_time.isoformat()
                result["status"] = "completed"
                result["retry_count"] = attempt + 1  # Số attempts thực tế đã thực hiện
                logger.debug("Task %s - Completed successfully on attempt %d", task_id, attempt + 1)
                return result
                
            except Exception as e:
                last_error = e
                if attempt < max_attempts - 1:  # Còn attempts để retry
                    logger.warning("Task %s - Attempt %d failed, retrying in %.2fs: %s",
                                 task_id, attempt + 1, delay, str(e))
                    await asyncio.sleep(delay)
                else:
                    logger.error("Task %s - Max attempts exceeded (%d attempts). Last error: %s",
                               task_id, max_attempts, str(e))

                    fail_msg = self._build_result_message(
                        task,
                        detected=None,
                        raw_response=None,
                        parsed_results=None,
                        result_source="worker",
                        result_metadata={"error": str(e)},
                        status="failed",
                        started_at=start_time.isoformat(),
                        retry_count=max_attempts,  # Số attempts thực tế đã thực hiện
                    )
                    raise MaxRetriesExceededException(task_id, max_attempts, e, fail_msg) from e
        
        # Should never reach here
        raise Exception(f"Unexpected end of attempt loop: {last_error}")

    # ------------------------------------------------------------------
    # Helper: build standardized detection result message
    # ------------------------------------------------------------------
    def _build_result_message(
        self,
        task: Dict[str, Any],
        *,
        detected: Optional[bool] = None,
        raw_response: Optional[Dict[str, Any]] = None,
        parsed_results: Optional[Dict[str, Any]] = None,
        result_source: Optional[str] = None,
        result_metadata: Optional[Dict[str, Any]] = None,
        result_timestamp: Optional[str] = None,
        started_at: Optional[str] = None,
        status: Optional[str] = None,
        retry_count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Return dict ready to be published to \*.responses queue.

        The structure aligns with DetectionResultCreate schema so that the
        backend listener can persist without additional parsing.
        """
        return {
            "id": task.get("task_id"),
            "detection_execution_id": task.get("detection_execution_id"),
            "detected": detected,
            "raw_response": raw_response,
            "parsed_results": parsed_results,
            "result_timestamp": result_timestamp or datetime.utcnow().isoformat(),
            "result_source": result_source,
            "result_metadata": result_metadata or {},
            "started_at": started_at,
            "status": status,
            "retry_count": retry_count,
        }

    # ------------------------------------------------------------------
    @abstractmethod
    async def _do_work(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform the actual work for this task.

        Implementations should raise an exception if the task cannot be
        processed. The retry logic will handle retries automatically.
        Must return a *standardized* result message built via
        ``self._build_result_message``.
        """
