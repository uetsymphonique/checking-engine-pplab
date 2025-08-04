"""
API Workers Package

This package contains workers that interact with external APIs for detection tasks.
Includes base classes and implementations for various API-based detection platforms.
"""

from .api_worker_base import BaseAPIWorker
from .mock_api_worker import MockAPIWorker

__all__ = ["BaseAPIWorker", "MockAPIWorker"]