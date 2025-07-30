from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr
import uuid

Base = declarative_base()

class BaseModel(Base):
    """Base model with common fields"""
    
    __abstract__ = True
    
    @declared_attr
    def __tablename__(cls):
        """Generate table name from class name"""
        return cls.__name__.lower()
    
    # Common fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>" 