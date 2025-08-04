"""
Message Queue Layer - RabbitMQ Integration

Handles asynchronous message processing with RabbitMQ.
Provides publishers and consumers for different message types.

Components:
- connection.py: RabbitMQ connection utilities for different roles
- consumers/: Message consumers for processing incoming messages
- publishers/: Message publishers for dispatching tasks

Supports multiple RabbitMQ user roles with different permissions.
"""

from .connection import get_rabbitmq_connection, test_connect_all_roles
from .consumers import CalderaExecutionConsumer, DetectionTaskConsumer
from .publishers import TaskDispatcher

__all__ = [
    # Connection utilities
    'get_rabbitmq_connection',
    'test_connect_all_roles',
    
    # Consumers
    'CalderaExecutionConsumer',
    'DetectionTaskConsumer',
    
    # Publishers
    'TaskDispatcher'
]