from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class OperationBase(BaseModel):
    """Base schema for Operation with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Operation name")
    operation_id: UUID = Field(..., description="Original Caldera operation ID")
    operation_start: Optional[datetime] = Field(None, description="Operation start time")
    operation_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional operation context")


class OperationCreate(OperationBase):
    """Schema for creating a new operation"""
    pass


class OperationUpdate(BaseModel):
    """Schema for updating an operation - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Operation name")
    operation_start: Optional[datetime] = Field(None, description="Operation start time")
    operation_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional operation context")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Name cannot be empty')
        return v


class OperationResponse(OperationBase):
    """Schema for operation response"""
    id: UUID = Field(..., description="Operation ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True  # For SQLAlchemy model compatibility


class OperationListResponse(BaseModel):
    """Schema for list of operations response"""
    operations: list[OperationResponse] = Field(..., description="List of operations")
    total: int = Field(..., description="Total number of operations")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size") 