from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from ...api.deps import get_db
from ...repositories.detection_repo import DetectionResultRepository
from ...schemas.detection import (
    DetectionResultCreate, DetectionResultUpdate, DetectionResultResponse, DetectionResultListResponse
)

router = APIRouter(prefix="/detections", tags=["detection-results"])

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