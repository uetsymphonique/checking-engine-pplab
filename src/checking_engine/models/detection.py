from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel
from sqlalchemy import func

class DetectionExecution(BaseModel):
    """Detection execution model for Blue Team detection tracking"""
    
    __tablename__ = "detection_executions"
    
    # Fields
    execution_result_id = Column(UUID(as_uuid=True), ForeignKey("execution_results.id"), nullable=False)
    operation_id = Column(UUID(as_uuid=True), ForeignKey("operations.operation_id"), nullable=False)
    detection_type = Column(String(50), nullable=False)  # 'api', 'windows', 'linux', 'darwin'
    detection_platform = Column(String(50), nullable=False)  # 'cym', 'ajant', 'psh', 'pwsh', 'sh'
    detection_config = Column(JSONB, nullable=False)  # Platform-specific configuration
    status = Column(String(50), default='pending')  # pending, running, completed, failed, cancelled
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    execution_metadata = Column(JSONB, default={})  # Timing, errors, context
    
    # Relationships
    execution_result = relationship("ExecutionResult", back_populates="detection_executions")
    operation = relationship("Operation", back_populates="detection_executions")
    detection_results = relationship("DetectionResult", back_populates="detection_execution")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("detection_type IN ('api', 'windows', 'linux', 'darwin')", name='chk_detection_type'),
        CheckConstraint("status IN ('pending', 'running', 'completed', 'failed', 'cancelled')", name='chk_status'),
        CheckConstraint("retry_count >= 0 AND retry_count <= max_retries", name='chk_retry_count'),
    )
    
    def __repr__(self):
        return f"<DetectionExecution(id={self.id}, type='{self.detection_type}', platform='{self.detection_platform}', status='{self.status}')>"

class DetectionResult(BaseModel):
    """Detection result model for Blue Team detection results"""
    
    __tablename__ = "detection_results"
    
    # Fields
    detection_execution_id = Column(UUID(as_uuid=True), ForeignKey("detection_executions.id"), nullable=False)
    detected = Column(Boolean)
    raw_response = Column(JSONB)  # Raw response from API/command
    parsed_results = Column(JSONB)  # Structured/parsed detection results
    result_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    result_source = Column(String(255))  # API endpoint, hostname, etc.
    result_metadata = Column('metadata', JSONB, default={})  # Confidence, severity, rules matched
    
    # Relationships
    detection_execution = relationship("DetectionExecution", back_populates="detection_results")
    
    def __repr__(self):
        return f"<DetectionResult(id={self.id}, detected={self.detected}, source='{self.result_source}')>" 