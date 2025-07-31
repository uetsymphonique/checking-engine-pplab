"""
Checking Engine - Purple Team Detection System

A backend system for processing Caldera execution results and simulating Blue Team detection.
Integrates with MITRE Caldera to provide Purple Team capabilities.

Core Components:
- API Layer: FastAPI REST endpoints
- Domain Layer: Business logic services
- Application Layer: Message processing orchestration
- Database Infrastructure: PostgreSQL connection and session management
- Message Queue Infrastructure: RabbitMQ integration (distributed across mq/ module)
- Models: SQLAlchemy ORM entities
- Schemas: Pydantic data validation
- Repositories: Data access layer
- Utils: Common utilities and logging

Architecture follows Clean Architecture principles with clear separation of concerns.
Infrastructure layer is distributed across specialized modules rather than a single directory.
"""

__version__ = "0.1.0"
__author__ = "Purple Team"
