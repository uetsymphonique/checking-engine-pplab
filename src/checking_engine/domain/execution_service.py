import json
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from checking_engine.models.execution import ExecutionResult
from checking_engine.repositories.execution_repo import ExecutionResultRepository
from checking_engine.schemas.execution import ExecutionResultCreate, ExecutionResultUpdate
from checking_engine.utils.logging import get_logger

logger = get_logger(__name__)

class ExecutionService:
    """Business logic for execution result management"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.repo = ExecutionResultRepository()
    
    async def create_execution_result(self, execution_data: Dict[str, Any], raw_message: Dict[str, Any]) -> ExecutionResult:
        """Create execution result from Caldera message"""
        try:
            # Parse agent_reported_time if provided
            agent_reported_time = None
            if execution_data.get("agent_reported_time"):
                if isinstance(execution_data["agent_reported_time"], str):
                    agent_reported_time = datetime.fromisoformat(execution_data["agent_reported_time"].replace('Z', '+00:00'))
                else:
                    agent_reported_time = execution_data["agent_reported_time"]
            
            # Parse result_data if it's a string
            result_data = execution_data.get("result_data")
            if isinstance(result_data, str):
                try:
                    result_data = json.loads(result_data)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse result_data as JSON: {result_data}")
                    result_data = {"raw": result_data}
            
            # Create execution result
            create_data = ExecutionResultCreate(
                operation_id=UUID(execution_data["operation_id"]) if "operation_id" in execution_data else UUID(raw_message["operation"]["operation_id"]),
                agent_host=execution_data.get("agent_host"),
                agent_paw=execution_data.get("agent_paw"),
                link_id=UUID(execution_data["link_id"]),
                command=execution_data.get("command"),
                pid=execution_data.get("pid"),
                status=execution_data.get("status"),
                result_data=result_data,
                agent_reported_time=agent_reported_time,
                link_state=execution_data.get("link_state"),
                raw_message=raw_message
            )
            
            execution_result = await self.repo.create(self.db, create_data)
            logger.debug(f"Created execution result: link_id={execution_result.link_id}, operation_id={execution_result.operation_id}")
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Error creating execution result: {e}")
            raise
    
    async def get_execution_by_link_id(self, link_id: UUID) -> Optional[ExecutionResult]:
        """Get execution result by link_id"""
        try:
            return await self.repo.get_by_link_id(self.db, link_id)
        except Exception as e:
            logger.error(f"Error getting execution by link_id {link_id}: {e}")
            raise
    
    async def update_execution_status(self, execution_id: UUID, status: int, link_state: str = None) -> Optional[ExecutionResult]:
        """Update execution status and link_state"""
        try:
            update_data = ExecutionResultUpdate(
                status=status,
                link_state=link_state
            )
            
            updated_execution = await self.repo.update(self.db, execution_id, update_data)
            if updated_execution:
                logger.debug(f"Updated execution {execution_id} status to {status}")
            
            return updated_execution
            
        except Exception as e:
            logger.error(f"Error updating execution status: {e}")
            raise 