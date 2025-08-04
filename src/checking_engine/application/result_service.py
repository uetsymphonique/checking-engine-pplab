"""Application service for processing detection result messages."""
from __future__ import annotations

from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from checking_engine.domain.result_service import DetectionResultService
from checking_engine.utils.logging import get_logger

logger = get_logger(__name__)


class ResultProcessingService:  # pylint: disable=too-few-public-methods
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.svc = DetectionResultService(db_session)

    async def process_detection_result(self, message_data: Dict[str, Any]) -> None:
        await self.svc.store_result(message_data)
