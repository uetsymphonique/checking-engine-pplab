"""Domain service: business rules for detection results."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import update as sa_update
from typing import Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from checking_engine.schemas.detection import (
    DetectionResultCreate,
    DetectionResultUpdate,
    DetectionStatus,
)
from checking_engine.repositories.detection_repo import DetectionResultRepository, DetectionExecutionRepository
from checking_engine.utils.logging import get_logger

logger = get_logger(__name__)


class DetectionResultService:  # pylint: disable=too-few-public-methods
    """Business logic around storing detection results and updating executions."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.result_repo = DetectionResultRepository()
        self.exec_repo = DetectionExecutionRepository()

    # ------------------------------------------------------------------
    async def store_result(self, data: Dict[str, Any]) -> None:
        """Insert or update DetectionResult and sync DetectionExecution."""

        # 1. Upsert detection_results
        result_id: UUID = UUID(data["id"])
        create_obj = DetectionResultCreate.model_validate(data)
        existing = await self.result_repo.get(self.db, result_id)
        if existing:
            await self.result_repo.update(self.db, result_id, DetectionResultUpdate(**data))
        else:
            # pylint: disable=not-callable
            await self.result_repo.create(self.db, create_obj)

        # 2. Update detection_execution
        exec_id = UUID(data["detection_execution_id"])
        execution = await self.exec_repo.get(self.db, exec_id)
        if not execution:
            logger.warning("DetectionExecution %s not found while storing result", exec_id)
            return

        # determine new retry_count (count results so far)
        retry_count = execution.retry_count + 1
        status = DetectionStatus.COMPLETED if data.get("status") == "completed" else DetectionStatus.FAILED

        fields: Dict[str, Any] = {
            "retry_count": retry_count,
            "status": status.value if isinstance(status, DetectionStatus) else status,
            "completed_at": datetime.fromisoformat(data["result_timestamp"]),
        }
        if execution.started_at is None and data.get("started_at"):
            fields["started_at"] = datetime.fromisoformat(data["started_at"])

        # direct SQL UPDATE to avoid mutable UUID issue
        await self.db.execute(
            sa_update(self.exec_repo.model)
            .where(self.exec_repo.model.id == exec_id)
            .values(**fields)
        )