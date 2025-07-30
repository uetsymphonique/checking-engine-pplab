from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class ExecutionResultBase(BaseModel):
    """Base schema for ExecutionResult with common fields"""
    operation_id: UUID = Field(..., description="Reference to Caldera operation")
    agent_host: Optional[str] = Field(None, max_length=255, description="Agent hostname")
    agent_paw: Optional[str] = Field(None, max_length=255, description="Agent PAW identifier")
    link_id: UUID = Field(..., description="Caldera link ID")
    command: Optional[str] = Field(None, description="Executed command")
    pid: Optional[int] = Field(None, description="Process ID")
    status: Optional[int] = Field(None, description="Exit status code")
    result_data: Optional[Dict[str, Any]] = Field(None, description="JSON containing stdout, stderr, exit_code")
    agent_reported_time: Optional[datetime] = Field(None, description="When agent reported the result")
    link_state: Optional[str] = Field(None, max_length=50, description="SUCCESS, FAILED, etc.")
    raw_message: Optional[Dict[str, Any]] = Field(None, description="Complete original message from queue")


class ExecutionResultCreate(ExecutionResultBase):
    """Schema for creating a new execution result"""
    pass


class ExecutionResultUpdate(BaseModel):
    """Schema for updating an execution result - all fields optional"""
    agent_host: Optional[str] = Field(None, max_length=255, description="Agent hostname")
    agent_paw: Optional[str] = Field(None, max_length=255, description="Agent PAW identifier")
    command: Optional[str] = Field(None, description="Executed command")
    pid: Optional[int] = Field(None, description="Process ID")
    status: Optional[int] = Field(None, description="Exit status code")
    result_data: Optional[Dict[str, Any]] = Field(None, description="JSON containing stdout, stderr, exit_code")
    agent_reported_time: Optional[datetime] = Field(None, description="When agent reported the result")
    link_state: Optional[str] = Field(None, max_length=50, description="SUCCESS, FAILED, etc.")
    raw_message: Optional[Dict[str, Any]] = Field(None, description="Complete original message from queue")


class ExecutionResultResponse(ExecutionResultBase):
    """Schema for execution result response"""
    id: UUID = Field(..., description="Execution result ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True  # For SQLAlchemy model compatibility


class ExecutionResultListResponse(BaseModel):
    """Schema for list of execution results response"""
    execution_results: list[ExecutionResultResponse] = Field(..., description="List of execution results")
    total: int = Field(..., description="Total number of execution results")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size") 