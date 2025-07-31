from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class DetectionType(str, Enum):
    """Enum for detection types"""
    API = "api"
    WINDOWS = "windows"
    LINUX = "linux"
    DARWIN = "darwin"


class DetectionStatus(str, Enum):
    """Enum for detection execution status"""
    PENDING = "pending"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DetectionExecutionBase(BaseModel):
    """Base schema for DetectionExecution with common fields"""
    execution_result_id: UUID = Field(..., description="Reference to execution result")
    operation_id: UUID = Field(..., description="Reference to Caldera operation")
    detection_type: DetectionType = Field(..., description="Platform category: api, windows, linux, darwin")
    detection_platform: str = Field(..., max_length=50, description="Specific platform: cym, ajant, psh, sh, etc.")
    detection_config: Dict[str, Any] = Field(..., description="Platform-specific detection configuration")
    status: DetectionStatus = Field(DetectionStatus.PENDING, description="Execution status")
    started_at: Optional[datetime] = Field(None, description="When detection started")
    completed_at: Optional[datetime] = Field(None, description="When detection completed")
    retry_count: int = Field(0, ge=0, description="Number of retry attempts")
    max_retries: int = Field(3, ge=0, description="Maximum retry attempts")
    execution_metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution context, errors, performance metrics")


class DetectionExecutionCreate(DetectionExecutionBase):
    """Schema for creating a new detection execution"""
    pass


class DetectionExecutionUpdate(BaseModel):
    """Schema for updating a detection execution - all fields optional"""
    detection_type: Optional[DetectionType] = Field(None, description="Platform category")
    detection_platform: Optional[str] = Field(None, max_length=50, description="Specific platform")
    detection_config: Optional[Dict[str, Any]] = Field(None, description="Platform-specific configuration")
    status: Optional[DetectionStatus] = Field(None, description="Execution status")
    started_at: Optional[datetime] = Field(None, description="When detection started")
    completed_at: Optional[datetime] = Field(None, description="When detection completed")
    retry_count: Optional[int] = Field(None, ge=0, description="Number of retry attempts")
    max_retries: Optional[int] = Field(None, ge=0, description="Maximum retry attempts")
    execution_metadata: Optional[Dict[str, Any]] = Field(None, description="Execution context, errors, performance metrics")
    
    @validator('retry_count')
    def validate_retry_count(cls, v, values):
        if v is not None and 'max_retries' in values and values['max_retries'] is not None:
            if v > values['max_retries']:
                raise ValueError('retry_count cannot exceed max_retries')
        return v


class DetectionExecutionResponse(DetectionExecutionBase):
    """Schema for detection execution response"""
    id: UUID = Field(..., description="Detection execution ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True  # For SQLAlchemy model compatibility


class DetectionExecutionListResponse(BaseModel):
    """Schema for list of detection executions response"""
    detection_executions: list[DetectionExecutionResponse] = Field(..., description="List of detection executions")
    total: int = Field(..., description="Total number of detection executions")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")


class DetectionResultBase(BaseModel):
    """Base schema for DetectionResult with common fields"""
    detection_execution_id: UUID = Field(..., description="Reference to detection execution")
    detected: Optional[bool] = Field(None, description="Whether the activity was detected")
    raw_response: Optional[Dict[str, Any]] = Field(None, description="Raw response from API/command")
    parsed_results: Optional[Dict[str, Any]] = Field(None, description="Structured/parsed detection results")
    result_timestamp: Optional[datetime] = Field(None, description="When result was generated")
    result_source: Optional[str] = Field(None, max_length=255, description="API endpoint, hostname, etc.")
    result_metadata: Dict[str, Any] = Field(default_factory=dict, description="Confidence, severity, rules matched")


class DetectionResultCreate(DetectionResultBase):
    """Schema for creating a new detection result"""
    pass


class DetectionResultUpdate(BaseModel):
    """Schema for updating a detection result - all fields optional"""
    detected: Optional[bool] = Field(None, description="Whether the activity was detected")
    raw_response: Optional[Dict[str, Any]] = Field(None, description="Raw response from API/command")
    parsed_results: Optional[Dict[str, Any]] = Field(None, description="Structured/parsed detection results")
    result_timestamp: Optional[datetime] = Field(None, description="When result was generated")
    result_source: Optional[str] = Field(None, max_length=255, description="API endpoint, hostname, etc.")
    result_metadata: Optional[Dict[str, Any]] = Field(None, description="Confidence, severity, rules matched")


class DetectionResultResponse(DetectionResultBase):
    """Schema for detection result response"""
    id: UUID = Field(..., description="Detection result ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True  # For SQLAlchemy model compatibility


class DetectionResultListResponse(BaseModel):
    """Schema for list of detection results response"""
    detection_results: list[DetectionResultResponse] = Field(..., description="List of detection results")
    total: int = Field(..., description="Total number of detection results")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size") 