"""
Application Layer - Use Case Orchestration

Orchestrates domain services to implement use cases.
Handles cross-cutting concerns and transaction management.

Services:
- message_service.py: Processes incoming Caldera messages and coordinates
  domain services for operation, execution, and detection management

This layer coordinates between external systems (Caldera, RabbitMQ) and domain services.
"""

from .message_service import MessageProcessingService

__all__ = [
    "MessageProcessingService"
]