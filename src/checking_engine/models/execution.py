from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel

class ExecutionResult(BaseModel):
    """Execution result model for Caldera agent execution results"""
    
    __tablename__ = "execution_results"
    
    # Fields
    operation_id = Column(UUID(as_uuid=True), ForeignKey("operations.operation_id"), nullable=False)
    agent_host = Column(String(255))
    agent_paw = Column(String(255))
    link_id = Column(UUID(as_uuid=True), nullable=False)
    command = Column(Text)
    pid = Column(Integer)
    status = Column(Integer)
    result_data = Column(JSONB)  # Contains stdout, stderr, exit_code
    agent_reported_time = Column(DateTime(timezone=True))
    link_state = Column(String(50))  # SUCCESS, FAILED, etc.
    raw_message = Column(JSONB)  # Complete original message from queue
    
    # Relationships
    operation = relationship("Operation", back_populates="execution_results")
    detection_executions = relationship("DetectionExecution", back_populates="execution_result")
    
    def __repr__(self):
        return f"<ExecutionResult(id={self.id}, operation_id={self.operation_id}, link_id={self.link_id})>" 