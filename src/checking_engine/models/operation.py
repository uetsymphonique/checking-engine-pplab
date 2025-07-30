from sqlalchemy import Column, String, DateTime, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel

class Operation(BaseModel):
    """Operation model for Caldera operations"""
    
    __tablename__ = "operations"
    
    # Fields
    name = Column(String(255), nullable=False)
    operation_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    operation_start = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    operation_metadata = Column('metadata', JSONB, default={})
    
    # Relationships
    execution_results = relationship("ExecutionResult", back_populates="operation")
    detection_executions = relationship("DetectionExecution", back_populates="operation")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('operation_id', name='idx_operations_operation_id'),
    )
    
    def __repr__(self):
        return f"<Operation(id={self.id}, name='{self.name}', operation_id={self.operation_id})>" 