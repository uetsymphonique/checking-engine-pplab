from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from ...api.deps import get_db
from ...repositories.detection_repo import DetectionExecutionRepository, DetectionResultRepository
from ...schemas.detection import (
    DetectionExecutionCreate, DetectionExecutionUpdate, DetectionExecutionResponse, DetectionExecutionListResponse,
    DetectionResultCreate, DetectionResultUpdate, DetectionResultResponse, DetectionResultListResponse
)

router = APIRouter(prefix="/detections", tags=["detections"])

# ============================================================================
# Detection Executions Endpoints
# ============================================================================

@router.post("/executions/", response_model=DetectionExecutionResponse, status_code=201)
async def create_detection_execution(
    detection: DetectionExecutionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new detection execution"""
    repo = DetectionExecutionRepository()
    return await repo.create(db, detection)


@router.get("/executions/", response_model=DetectionExecutionListResponse)
async def list_detection_executions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    execution_result_id: Optional[UUID] = Query(None, description="Filter by execution result ID"),
    operation_id: Optional[UUID] = Query(None, description="Filter by operation ID"),
    detection_type: Optional[str] = Query(None, description="Filter by detection type"),
    detection_platform: Optional[str] = Query(None, description="Filter by detection platform"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db)
):
    """List detection executions with optional filtering"""
    repo = DetectionExecutionRepository()
    
    if execution_result_id:
        detection_executions = await repo.get_by_execution_result_id(db, execution_result_id, skip, limit)
    elif operation_id:
        detection_executions = await repo.get_by_operation_id(db, operation_id, skip, limit)
    elif detection_type:
        detection_executions = await repo.get_by_detection_type(db, detection_type, skip, limit)
    elif detection_platform:
        detection_executions = await repo.get_by_platform(db, detection_platform, skip, limit)
    elif status:
        detection_executions = await repo.get_by_status(db, status, skip, limit)
    else:
        detection_executions = await repo.get_multi(db, skip, limit)
    
    total = await repo.count(db)
    
    return DetectionExecutionListResponse(
        detection_executions=detection_executions,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


@router.get("/executions/{execution_id}", response_model=DetectionExecutionResponse)
async def get_detection_execution(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get detection execution by ID"""
    repo = DetectionExecutionRepository()
    detection_execution = await repo.get(db, execution_id)
    
    if not detection_execution:
        raise HTTPException(
            status_code=404, 
            detail=f"Detection execution with id {execution_id} not found"
        )
    
    return detection_execution


@router.get("/executions/by-execution-result/{execution_result_id}", response_model=DetectionExecutionListResponse)
async def get_detection_executions_by_execution_result(
    execution_result_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get all detection executions for a specific execution result"""
    repo = DetectionExecutionRepository()
    detection_executions = await repo.get_by_execution_result_id(db, execution_result_id, skip, limit)
    
    # Count total for this execution result
    total_query = await repo.count(db, {"execution_result_id": execution_result_id})
    
    return DetectionExecutionListResponse(
        detection_executions=detection_executions,
        total=total_query,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


@router.get("/executions/by-operation/{operation_id}", response_model=DetectionExecutionListResponse)
async def get_detection_executions_by_operation(
    operation_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get all detection executions for a specific operation"""
    repo = DetectionExecutionRepository()
    detection_executions = await repo.get_by_operation_id(db, operation_id, skip, limit)
    
    # Count total for this operation
    total_query = await repo.count(db, {"operation_id": operation_id})
    
    return DetectionExecutionListResponse(
        detection_executions=detection_executions,
        total=total_query,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


@router.get("/executions/with-execution-result/{execution_id}", response_model=DetectionExecutionResponse)
async def get_detection_execution_with_execution_result(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get detection execution with related execution result data"""
    repo = DetectionExecutionRepository()
    detection_execution = await repo.get_with_execution_result(db, execution_id)
    
    if not detection_execution:
        raise HTTPException(
            status_code=404, 
            detail=f"Detection execution with id {execution_id} not found"
        )
    
    return detection_execution


@router.get("/executions/with-operation/{execution_id}", response_model=DetectionExecutionResponse)
async def get_detection_execution_with_operation(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get detection execution with related operation data"""
    repo = DetectionExecutionRepository()
    detection_execution = await repo.get_with_operation(db, execution_id)
    
    if not detection_execution:
        raise HTTPException(
            status_code=404, 
            detail=f"Detection execution with id {execution_id} not found"
        )
    
    return detection_execution


@router.get("/executions/with-results/{execution_id}", response_model=DetectionExecutionResponse)
async def get_detection_execution_with_results(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get detection execution with related detection results"""
    repo = DetectionExecutionRepository()
    detection_execution = await repo.get_with_results(db, execution_id)
    
    if not detection_execution:
        raise HTTPException(
            status_code=404, 
            detail=f"Detection execution with id {execution_id} not found"
        )
    
    return detection_execution


@router.get("/executions/pending/list", response_model=DetectionExecutionListResponse)
async def get_pending_detection_executions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get pending detection executions"""
    repo = DetectionExecutionRepository()
    detection_executions = await repo.get_pending_executions(db, skip, limit)
    
    # Note: total count for pending executions would need a separate method
    total = len(detection_executions)
    
    return DetectionExecutionListResponse(
        detection_executions=detection_executions,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


@router.get("/executions/failed/list", response_model=DetectionExecutionListResponse)
async def get_failed_detection_executions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get failed detection executions"""
    repo = DetectionExecutionRepository()
    detection_executions = await repo.get_failed_executions(db, skip, limit)
    
    total = len(detection_executions)
    
    return DetectionExecutionListResponse(
        detection_executions=detection_executions,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


@router.get("/executions/retryable/list", response_model=DetectionExecutionListResponse)
async def get_retryable_detection_executions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get failed detection executions that can be retried"""
    repo = DetectionExecutionRepository()
    detection_executions = await repo.get_retryable_executions(db, skip, limit)
    
    total = len(detection_executions)
    
    return DetectionExecutionListResponse(
        detection_executions=detection_executions,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


@router.get("/executions/completed/list", response_model=DetectionExecutionListResponse)
async def get_completed_detection_executions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get completed detection executions"""
    repo = DetectionExecutionRepository()
    detection_executions = await repo.get_completed_executions(db, skip, limit)
    
    total = len(detection_executions)
    
    return DetectionExecutionListResponse(
        detection_executions=detection_executions,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


@router.put("/executions/{execution_id}", response_model=DetectionExecutionResponse)
async def update_detection_execution(
    execution_id: UUID,
    detection_update: DetectionExecutionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update detection execution by ID"""
    repo = DetectionExecutionRepository()
    
    # Get existing detection execution
    db_detection_execution = await repo.get(db, execution_id)
    if not db_detection_execution:
        raise HTTPException(
            status_code=404, 
            detail=f"Detection execution with id {execution_id} not found"
        )
    
    return await repo.update(db, db_detection_execution, detection_update)


@router.delete("/executions/{execution_id}", status_code=204)
async def delete_detection_execution(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete detection execution by ID"""
    repo = DetectionExecutionRepository()
    
    # Check if detection execution exists
    if not await repo.exists(db, execution_id):
        raise HTTPException(
            status_code=404, 
            detail=f"Detection execution with id {execution_id} not found"
        )
    
    # Delete detection execution
    success = await repo.delete(db, execution_id)
    if not success:
        raise HTTPException(
            status_code=500, 
            detail="Failed to delete detection execution"
        )
    
    return None


# ============================================================================
# Detection Results Endpoints
# ============================================================================

@router.post("/results/", response_model=DetectionResultResponse, status_code=201)
async def create_detection_result(
    detection_result: DetectionResultCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new detection result"""
    repo = DetectionResultRepository()
    return await repo.create(db, detection_result)


@router.get("/results/", response_model=DetectionResultListResponse)
async def list_detection_results(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    detection_execution_id: Optional[UUID] = Query(None, description="Filter by detection execution ID"),
    detected: Optional[bool] = Query(None, description="Filter by detection status"),
    result_source: Optional[str] = Query(None, description="Filter by result source"),
    db: AsyncSession = Depends(get_db)
):
    """List detection results with optional filtering"""
    repo = DetectionResultRepository()
    
    if detection_execution_id:
        detection_results = await repo.get_by_detection_execution_id(db, detection_execution_id, skip, limit)
    elif detected is not None:
        if detected:
            detection_results = await repo.get_detected_results(db, skip, limit)
        else:
            detection_results = await repo.get_not_detected_results(db, skip, limit)
    elif result_source:
        detection_results = await repo.get_by_source(db, result_source, skip, limit)
    else:
        detection_results = await repo.get_multi(db, skip, limit)
    
    total = await repo.count(db)
    
    return DetectionResultListResponse(
        detection_results=detection_results,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


@router.get("/results/{result_id}", response_model=DetectionResultResponse)
async def get_detection_result(
    result_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get detection result by ID"""
    repo = DetectionResultRepository()
    detection_result = await repo.get(db, result_id)
    
    if not detection_result:
        raise HTTPException(
            status_code=404, 
            detail=f"Detection result with id {result_id} not found"
        )
    
    return detection_result


@router.get("/results/by-execution/{detection_execution_id}", response_model=DetectionResultListResponse)
async def get_detection_results_by_execution(
    detection_execution_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get all detection results for a specific detection execution"""
    repo = DetectionResultRepository()
    detection_results = await repo.get_by_detection_execution_id(db, detection_execution_id, skip, limit)
    
    # Count total for this detection execution
    total_query = await repo.count(db, {"detection_execution_id": detection_execution_id})
    
    return DetectionResultListResponse(
        detection_results=detection_results,
        total=total_query,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


@router.get("/results/with-execution/{result_id}", response_model=DetectionResultResponse)
async def get_detection_result_with_execution(
    result_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get detection result with related detection execution data"""
    repo = DetectionResultRepository()
    detection_result = await repo.get_with_detection_execution(db, result_id)
    
    if not detection_result:
        raise HTTPException(
            status_code=404, 
            detail=f"Detection result with id {result_id} not found"
        )
    
    return detection_result


@router.get("/results/detected/list", response_model=DetectionResultListResponse)
async def get_detected_results(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get detection results where activity was detected"""
    repo = DetectionResultRepository()
    detection_results = await repo.get_detected_results(db, skip, limit)
    
    total = len(detection_results)
    
    return DetectionResultListResponse(
        detection_results=detection_results,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


@router.get("/results/not-detected/list", response_model=DetectionResultListResponse)
async def get_not_detected_results(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get detection results where activity was not detected"""
    repo = DetectionResultRepository()
    detection_results = await repo.get_not_detected_results(db, skip, limit)
    
    total = len(detection_results)
    
    return DetectionResultListResponse(
        detection_results=detection_results,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


@router.get("/results/recent/{hours}", response_model=DetectionResultListResponse)
async def get_recent_detection_results(
    hours: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get detection results from the last N hours"""
    repo = DetectionResultRepository()
    detection_results = await repo.get_recent_results(db, hours, skip, limit)
    
    total = len(detection_results)
    
    return DetectionResultListResponse(
        detection_results=detection_results,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )


@router.get("/results/stats/summary", response_model=dict)
async def get_detection_statistics(
    db: AsyncSession = Depends(get_db)
):
    """Get detection statistics"""
    repo = DetectionResultRepository()
    return await repo.get_detection_statistics(db)


@router.put("/results/{result_id}", response_model=DetectionResultResponse)
async def update_detection_result(
    result_id: UUID,
    detection_result_update: DetectionResultUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update detection result by ID"""
    repo = DetectionResultRepository()
    
    # Get existing detection result
    db_detection_result = await repo.get(db, result_id)
    if not db_detection_result:
        raise HTTPException(
            status_code=404, 
            detail=f"Detection result with id {result_id} not found"
        )
    
    return await repo.update(db, db_detection_result, detection_result_update)


@router.delete("/results/{result_id}", status_code=204)
async def delete_detection_result(
    result_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete detection result by ID"""
    repo = DetectionResultRepository()
    
    # Check if detection result exists
    if not await repo.exists(db, result_id):
        raise HTTPException(
            status_code=404, 
            detail=f"Detection result with id {result_id} not found"
        )
    
    # Delete detection result
    success = await repo.delete(db, result_id)
    if not success:
        raise HTTPException(
            status_code=500, 
            detail="Failed to delete detection result"
        )
    
    return None 