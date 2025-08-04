import asyncio
import random
from typing import Dict, Any

from .api_worker_base import BaseAPIWorker
from checking_engine.workers.base_worker import TaskProcessingException
from checking_engine.utils.logging import get_logger

logger = get_logger(__name__)


class MockAPIWorker(BaseAPIWorker):
    """Mock API Worker

    Does not send real requests, just sleeps 1 second and returns mock results.
    Used for end-to-end flow demonstration.
    """

    def supports_detection(self, detection_type: str, detection_platform: str) -> bool:
        """Check if this worker supports the given detection type and platform."""
        return detection_type == "api" and detection_platform == "apitest"
    
    async def _do_work(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task.get("task_id")
        detection_exec_id = task.get("detection_execution_id")
        command = task.get("detection_config", {}).get("command")

        logger.info(
            "[MOCK-API] Processing task %s for detection_execution_id=%s, command=%s",
            task_id,
            detection_exec_id,
            command,
        )

        # Simulate failure 40% of the time to test retry logic
        if random.random() < 0.6:
            logger.warning("[MOCK-API] Simulating failure for task %s", task_id)
            raise TaskProcessingException("Simulated API failure for testing retry logic")

        # Simulate processing time
        await asyncio.sleep(1)

        # Raw response from a fictional SIEM API
        raw_resp = {
            "events_found": random.randint(0, 5),
            "search_id": "abc-123",
        }

        # Simple parsing rule: detected == events_found > 0
        events_found = raw_resp["events_found"]
        detected = events_found > 0

        parsed_results = {
            "events_found": events_found,
        }

        result_msg = self._build_result_message(
            task,
            detected=detected,
            raw_response=raw_resp,
            parsed_results=parsed_results,
            result_source="mock_siem_api",
            result_metadata={
                "worker_note": "Mock worker returns default result.",
            },
            status="completed",
            retry_count=1,  # Single attempt for successful completion
        )

        logger.info("[MOCK-API] Completed task %s successfully (detected=%s)", task_id, detected)
        return result_msg
