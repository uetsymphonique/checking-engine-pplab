"""
Data Access Layer - Repository Pattern

Implements the Repository pattern for database access.
Provides clean abstraction over database operations and query logic.

Components:
- base.py: Generic base repository with common CRUD operations
- operation_repo.py: Operation-specific queries and operations
- execution_repo.py: Execution result queries and operations
- detection_repo.py: Detection execution and result operations

All repositories use async/await patterns and proper error handling.
""" 