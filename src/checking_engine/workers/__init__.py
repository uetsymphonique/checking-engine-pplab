"""
Worker Framework

This package provides base classes and concrete worker implementations for
processing detection tasks received from RabbitMQ.

Structure:
- base_worker.py:  abstract contract every worker must follow  
- api/:           API-based workers (SIEM/EDR platforms)
- agent/:         Agent-based workers (Windows/Linux/Darwin)
- run_worker.py:  CLI entry point for running workers

Current workers:
- BaseWorker:     abstract contract every worker must follow
- BaseAPIWorker:  shared helpers for API-style workers (SIEM / EDR)
- MockAPIWorker:  simple implementation used for integration tests
"""

from .base_worker import BaseWorker
from .api.api_worker_base import BaseAPIWorker
from .api.mock_api_worker import MockAPIWorker

__all__ = [
    "BaseWorker",
    "BaseAPIWorker",
    "MockAPIWorker",
]
