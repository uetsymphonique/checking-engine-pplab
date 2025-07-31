"""
Message Consumers - RabbitMQ Message Processing

Consumers handle incoming messages from RabbitMQ queues.
Process messages asynchronously and coordinate with application services.

Consumers:
- caldera_execution_consumer.py: Processes execution results from Caldera
  and triggers detection task creation

All consumers implement proper error handling and message acknowledgment.
"""

from .caldera_execution_consumer import CalderaExecutionConsumer

__all__ = [
    'CalderaExecutionConsumer'
]