"""
Message Publishers - RabbitMQ Message Dispatching

Publishers send messages to RabbitMQ queues for task distribution.
Handle message formatting and routing to appropriate queues.

Publishers:
- task_dispatcher.py: Dispatches detection tasks to appropriate worker queues
  based on detection type (API, Windows, Linux, Darwin)

All publishers implement proper connection management and error handling.
"""

from .task_dispatcher import TaskDispatcher
from .result_publisher import ResultPublisher

__all__ = [
    'TaskDispatcher', 'ResultPublisher'
]