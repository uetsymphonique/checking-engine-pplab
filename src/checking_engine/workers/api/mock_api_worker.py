import asyncio
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from .api_worker_base import BaseAPIWorker
from checking_engine.workers.base_worker import TaskProcessingException
from checking_engine.utils.logging import get_logger
from checking_engine.config import Settings
from pydantic import Field

class MockAPIWorkerSettings(Settings):
    api_key: str = Field(default="mock_api_key", env="MOCK_API_KEY")
    api_url: str = Field(default="mock_api_url", env="MOCK_API_URL")

settings = MockAPIWorkerSettings()

logger = get_logger(__name__)


class MockAPIWorker(BaseAPIWorker):
    """Mock API Worker

    Does not send real requests, just sleeps 1 second and returns mock results.
    Used for end-to-end flow demonstration.
    """
    result_source: str = "mock_api"

    def supports_detection(self, detection_type: str, detection_platform: str) -> bool:
        """Check if this worker supports the given detection type and platform."""
        return detection_type == "api" and detection_platform == "apitest"
    
    async def _do_work(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_id = task.get("task_id")
        detection_exec_id = task.get("detection_execution_id")
        command = task.get("detection_config", {}).get("command")

                # Parse ISO-8601 strings to datetime
        agent_reported_time = task.get("execution_context", {}).get("agent_reported_time")
        started_at_least = task.get("execution_context", {}).get("started_at_least")

        if isinstance(agent_reported_time, str):
            try:
                agent_reported_time = datetime.fromisoformat(agent_reported_time)
            except ValueError as exc:
                raise TaskProcessingException(f"Invalid agent_reported_time: {agent_reported_time}") from exc
        if isinstance(started_at_least, str):
            try:
                started_at_least = datetime.fromisoformat(started_at_least)
            except ValueError as exc:
                raise TaskProcessingException(f"Invalid started_at_least: {started_at_least}") from exc

        if agent_reported_time is None or started_at_least is None:
            raise TaskProcessingException("Missing execution timestamps in task metadata")

        time_from = started_at_least - timedelta(seconds=task.get("detection_config", {}).get("before_reported_time", 0))
        time_to = agent_reported_time + timedelta(seconds=task.get("detection_config", {}).get("after_reported_time", 0))

        # TODO: convert to Unix timestamps in milliseconds.
        time_from_ms = int(time_from.timestamp() * 1000)
        time_to_ms = int(time_to.timestamp() * 1000)

        if time_from_ms > time_to_ms:
            raise TaskProcessingException("Started at least time is greater than agent reported time")

        api_key = settings.api_key
        api_url = settings.api_url

        logger.info(
            "[MOCK-API] Processing task %s for detection_execution_id=%s, command=%s, time_from_ms=%s, time_to_ms=%s, api_key=%s, api_url=%s",
            task_id,
            detection_exec_id,
            command,
            time_from_ms,
            time_to_ms,
            api_key,
            api_url,
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
            result_metadata={
                "worker_note": "Mock worker returns default result.",
            },
            status="completed",
            retry_count=1,  # Single attempt for successful completion
        )

        logger.info("[MOCK-API] Completed task %s successfully (detected=%s)", task_id, detected)
        return result_msg
