import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from .api_worker_base import BaseAPIWorker
from checking_engine.workers.base_worker import TaskProcessingException
from checking_engine.utils.logging import get_logger

logger = get_logger(__name__)


class CymAPIWorker(BaseAPIWorker):
    """Cym API Worker

    Sends requests to the Cym API and returns the results.
    """
    result_source: str = "cym_api"

    def supports_detection(self, detection_type: str, detection_platform: str) -> bool:
        """Check if this worker supports the given detection type and platform."""
        return detection_type == "api" and detection_platform == "cym"
    
    async def _do_work(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process the task and return the results."""

        logger.info("[CymAPIWorker] Processing task %s - detection_execution_id=%s", task.get("task_id"), task.get("detection_execution_id"))

        # TODO: implement Cym API worker.
        agent_reported_time = task.get("execution_context", {}).get("agent_reported_time")
        started_at_least = task.get("execution_context", {}).get("started_at_least")

        # Convert ISO strings to datetime
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

        time_from_ms = int(time_from.timestamp() * 1000)
        time_to_ms = int(time_to.timestamp() * 1000)

        if time_from_ms > time_to_ms:
            raise TaskProcessingException("Started at least time is greater than agent reported time")

        logger.info("[CymAPIWorker] Processing task %s - detection_execution_id=%s, time_from_ms=%s, time_to_ms=%s", task.get("task_id"), task.get("detection_execution_id"), time_from_ms, time_to_ms)

        # TODO: send the request to the Cym API.
        # TODO: get the response from the Cym API.

        result_msg = self._build_result_message(
            task,
            detected=True,
            raw_response={"result": "success"},
            parsed_results={"result": "success"}, 
            result_metadata={"worker_note": "Cym API worker returns default result."},
            status="completed",
            retry_count=1,
        )
        return result_msg
    