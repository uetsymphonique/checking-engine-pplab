from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from checking_engine.models.operation import Operation
from checking_engine.repositories.operation_repo import OperationRepository
from checking_engine.schemas.operation import OperationCreate, OperationUpdate
from checking_engine.utils.logging import get_logger

logger = get_logger(__name__)

class OperationService:
    """Business logic for operation management"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.repo = OperationRepository()
    
    async def create_or_get_operation(self, operation_data: Dict[str, Any]) -> Operation:
        """Create new operation or get existing one by operation_id"""
        try:
            operation_id = UUID(operation_data["operation_id"])
            
            # Check if operation already exists
            existing_operation = await self.repo.get_by_operation_id(self.db, operation_id)
            if existing_operation:
                logger.debug(f"Operation {operation_id} already exists, returning existing")
                return existing_operation
            
            # Parse operation_start if provided
            operation_start = None
            if operation_data.get("operation_start"):
                if isinstance(operation_data["operation_start"], str):
                    operation_start = datetime.fromisoformat(operation_data["operation_start"].replace('Z', '+00:00'))
                else:
                    operation_start = operation_data["operation_start"]
            
            # Create new operation
            create_data = OperationCreate(
                name=operation_data["name"],
                operation_id=operation_id,
                operation_start=operation_start,
                operation_metadata={}
            )
            
            operation = await self.repo.create(self.db, create_data)
            logger.info(f"Created new operation: {operation.name} ({operation.operation_id})")
            
            return operation
            
        except Exception as e:
            logger.error(f"Error creating/getting operation: {e}")
            raise
    
    async def update_operation_metadata(self, operation_id: UUID, metadata: Dict[str, Any]) -> Optional[Operation]:
        """Update operation metadata"""
        try:
            operation = await self.repo.get_by_operation_id(self.db, operation_id)
            if not operation:
                logger.warning(f"Operation {operation_id} not found for metadata update")
                return None
            
            # Merge metadata
            current_metadata = operation.operation_metadata or {}
            updated_metadata = {**current_metadata, **metadata}
            
            update_data = OperationUpdate(operation_metadata=updated_metadata)
            updated_operation = await self.repo.update(self.db, operation.id, update_data)
            
            logger.debug(f"Updated metadata for operation {operation_id}")
            return updated_operation
            
        except Exception as e:
            logger.error(f"Error updating operation metadata: {e}")
            raise 