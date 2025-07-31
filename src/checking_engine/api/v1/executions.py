from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from ...api.deps import get_db
from ...repositories.execution_repo import ExecutionResultRepository
from ...schemas.execution import (
    ExecutionResultCreate, 
    ExecutionResultUpdate, 
    ExecutionResultResponse, 
    ExecutionResultListResponse
)
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/executions", tags=["executions"])


@router.post("/", response_model=ExecutionResultResponse, status_code=201)
async def create_execution_result(
    execution: ExecutionResultCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new execution result"""
    repo = ExecutionResultRepository()
    
    # Check if link_id already exists
    if await repo.exists_by_link_id(db, execution.link_id):
        raise HTTPException(
            status_code=400, 
            detail=f"Execution result with link_id {execution.link_id} already exists"
        )
    
    return await repo.create(db, execution)


@router.get("/", response_model=ExecutionResultListResponse)
async def list_execution_results(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    operation_id: Optional[UUID] = Query(None, description="Filter by operation ID"),
    agent_paw: Optional[str] = Query(None, description="Filter by agent PAW"),
    status: Optional[int] = Query(None, description="Filter by status code"),
    link_state: Optional[str] = Query(None, description="Filter by link state"),
    db: AsyncSession = Depends(get_db)
):
    """List execution results with optional filtering"""
    repo = ExecutionResultRepository()
    
    if operation_id:
        execution_results = await repo.get_by_operation_id(db, operation_id, skip, limit)
    elif agent_paw:
        execution_results = await repo.get_by_agent_paw(db, agent_paw, skip, limit)
    elif status is not None:
        execution_results = await repo.get_by_status(db, status, skip, limit)
    elif link_state:
        execution_results = await repo.get_by_link_state(db, link_state, skip, limit)
    else:
        execution_results = await repo.get_multi(db, skip, limit)
    
    total = await repo.count(db)
    
    return ExecutionResultListResponse(
        execution_results=execution_results,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


@router.get("/{execution_id}", response_model=ExecutionResultResponse)
async def get_execution_result(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get execution result by ID"""
    repo = ExecutionResultRepository()
    execution_result = await repo.get(db, execution_id)
    
    if not execution_result:
        raise HTTPException(
            status_code=404, 
            detail=f"Execution result with id {execution_id} not found"
        )
    
    return execution_result


@router.get("/by-link-id/{link_id}", response_model=ExecutionResultResponse)
async def get_execution_result_by_link_id(
    link_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get execution result by Caldera link_id"""
    repo = ExecutionResultRepository()
    execution_result = await repo.get_by_link_id(db, link_id)
    
    if not execution_result:
        raise HTTPException(
            status_code=404, 
            detail=f"Execution result with link_id {link_id} not found"
        )
    
    return execution_result


@router.get("/by-operation/{operation_id}", response_model=ExecutionResultListResponse)
async def get_execution_results_by_operation(
    operation_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get all execution results for a specific operation"""
    repo = ExecutionResultRepository()
    execution_results = await repo.get_by_operation_id(db, operation_id, skip, limit)
    
    # Count total for this operation
    total_query = await repo.count(db, {"operation_id": operation_id})
    
    return ExecutionResultListResponse(
        execution_results=execution_results,
        total=total_query,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


@router.get("/with-operation/{execution_id}", response_model=ExecutionResultResponse)
async def get_execution_result_with_operation(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get execution result with related operation data"""
    repo = ExecutionResultRepository()
    execution_result = await repo.get_with_operation(db, execution_id)
    
    if not execution_result:
        raise HTTPException(
            status_code=404, 
            detail=f"Execution result with id {execution_id} not found"
        )
    
    return execution_result


@router.get("/recent/{hours}", response_model=ExecutionResultListResponse)
async def get_recent_execution_results(
    hours: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get execution results from the last N hours"""
    repo = ExecutionResultRepository()
    execution_results = await repo.get_recent_executions(db, hours, skip, limit)
    
    # Note: total count for recent executions would need a separate method
    # For now, returning the count of returned results
    total = len(execution_results)
    
    return ExecutionResultListResponse(
        execution_results=execution_results,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


@router.get("/failed/list", response_model=ExecutionResultListResponse)
async def get_failed_execution_results(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get execution results with failed status or link_state"""
    repo = ExecutionResultRepository()
    execution_results = await repo.get_failed_executions(db, skip, limit)
    
    # Note: total count for failed executions would need a separate method
    # For now, returning the count of returned results
    total = len(execution_results)
    
    return ExecutionResultListResponse(
        execution_results=execution_results,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


@router.put("/{execution_id}", response_model=ExecutionResultResponse)
async def update_execution_result(
    execution_id: UUID,
    execution_update: ExecutionResultUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update execution result by ID"""
    repo = ExecutionResultRepository()
    
    # Get existing execution result
    db_execution_result = await repo.get(db, execution_id)
    if not db_execution_result:
        raise HTTPException(
            status_code=404, 
            detail=f"Execution result with id {execution_id} not found"
        )
    
    return await repo.update(db, db_execution_result, execution_update)


@router.delete("/{execution_id}", status_code=204)
async def delete_execution_result(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete execution result by ID"""
    repo = ExecutionResultRepository()
    
    # Check if execution result exists
    if not await repo.exists(db, execution_id):
        raise HTTPException(
            status_code=404, 
            detail=f"Execution result with id {execution_id} not found"
        )
    
    # Delete execution result
    success = await repo.delete(db, execution_id)
    if not success:
        raise HTTPException(
            status_code=500, 
            detail="Failed to delete execution result"
        )
    
    return None 