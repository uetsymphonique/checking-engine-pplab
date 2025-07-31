"""
Database Models - SQLAlchemy ORM Entities

Defines database table structures and relationships using SQLAlchemy ORM.
Models represent the core entities in the Checking Engine system.

Entities:
- Operation: Caldera operations and campaigns
- ExecutionResult: Agent execution results from Caldera
- DetectionExecution: Detection tasks to be executed
- DetectionResult: Results from detection executions

All models include audit fields (created_at, updated_at) and proper relationships.
"""
# Database Models Package
# SQLAlchemy ORM models for database tables 
from .base import Base, BaseModel
from .operation import Operation
from .execution import ExecutionResult
from .detection import DetectionExecution, DetectionResult

__all__ = [
    "Base",
    "BaseModel", 
    "Operation",
    "ExecutionResult",
    "DetectionExecution",
    "DetectionResult"
] 