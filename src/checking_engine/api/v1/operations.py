from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from ...api.deps import get_db
from ...repositories.operation_repo import OperationRepository
from ...schemas.operation import (
    OperationCreate, 
    OperationUpdate, 
    OperationResponse, 
    OperationListResponse
)
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/operations", tags=["operations"])


@router.post("/", response_model=OperationResponse, status_code=201)
async def create_operation(
    operation: OperationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new operation"""
    repo = OperationRepository()
    
    # Check if operation_id already exists
    if await repo.exists_by_operation_id(db, operation.operation_id):
        raise HTTPException(
            status_code=400, 
            detail=f"Operation with operation_id {operation.operation_id} already exists"
        )
    
    return await repo.create(db, operation)


@router.get("/", response_model=OperationListResponse)
async def list_operations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    name: Optional[str] = Query(None, description="Filter by operation name"),
    db: AsyncSession = Depends(get_db)
):
    """List operations with optional filtering"""
    repo = OperationRepository()
    
    if name:
        operations = await repo.search_by_name(db, name, skip, limit)
    else:
        operations = await repo.get_multi(db, skip, limit)
    
    total = await repo.count(db)
    
    return OperationListResponse(
        operations=operations,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


@router.get("/{operation_id}", response_model=OperationResponse)
async def get_operation(
    operation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get operation by ID"""
    repo = OperationRepository()
    operation = await repo.get(db, operation_id)
    
    if not operation:
        raise HTTPException(
            status_code=404, 
            detail=f"Operation with id {operation_id} not found"
        )
    
    return operation


@router.get("/by-caldera-id/{caldera_operation_id}", response_model=OperationResponse)
async def get_operation_by_caldera_id(
    caldera_operation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get operation by Caldera operation_id"""
    repo = OperationRepository()
    operation = await repo.get_by_operation_id(db, caldera_operation_id)
    
    if not operation:
        raise HTTPException(
            status_code=404, 
            detail=f"Operation with Caldera operation_id {caldera_operation_id} not found"
        )
    
    return operation


@router.put("/{operation_id}", response_model=OperationResponse)
async def update_operation(
    operation_id: UUID,
    operation_update: OperationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update operation by ID"""
    repo = OperationRepository()
    
    # Get existing operation
    db_operation = await repo.get(db, operation_id)
    if not db_operation:
        raise HTTPException(
            status_code=404, 
            detail=f"Operation with id {operation_id} not found"
        )
    
    return await repo.update(db, db_operation, operation_update)


@router.delete("/{operation_id}", status_code=204)
async def delete_operation(
    operation_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete operation by ID"""
    repo = OperationRepository()
    
    # Check if operation exists
    if not await repo.exists(db, operation_id):
        raise HTTPException(
            status_code=404, 
            detail=f"Operation with id {operation_id} not found"
        )
    
    # Delete operation
    success = await repo.delete(db, operation_id)
    if not success:
        raise HTTPException(
            status_code=500, 
            detail="Failed to delete operation"
        )
    
    return None 