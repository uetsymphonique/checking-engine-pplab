# Checking Engine - Source Code Documentation

## Overview

The Checking Engine is a Purple Team detection system that integrates with MITRE Caldera to simulate Blue Team detection capabilities. The system processes Caldera execution results and creates detection tasks for various platforms.

## Architecture

The codebase follows Clean Architecture principles with clear separation of concerns:

```
src/checking_engine/
├── api/           # HTTP REST API layer
├── application/   # Use case orchestration
├── domain/        # Business logic services
├── database/      # Database infrastructure (connection, session management)
├── mq/           # Message queue infrastructure (RabbitMQ)
├── models/        # Database ORM entities
├── schemas/       # Data validation models
├── repositories/  # Data access layer
└── utils/         # Common utilities
```

**Note:** Infrastructure layer is distributed across `database/` and `mq/` modules rather than a separate `infrastructure/` directory.

## Module Documentation

### Core Modules

#### `config.py`
Application configuration using Pydantic Settings. Manages database, RabbitMQ, and logging settings.

#### `main.py`
FastAPI application entry point. Configures middleware, lifespan events, and API routing.

### API Layer (`api/`)

#### `api/deps.py`
Dependency injection utilities for FastAPI, providing database sessions and other shared resources.

#### `api/v1/`
Version 1 REST API endpoints:
- `health.py`: System health checks
- `operations.py`: Operation CRUD endpoints
- `executions.py`: Execution result endpoints
- `detection_executions.py`: Detection execution management
- `detection_results.py`: Detection result endpoints
- `router.py`: API route configuration

### Domain Layer (`domain/`)

Business logic services implementing core business rules:

#### `operation_service.py`
Manages Caldera operations and campaigns. Handles operation lifecycle and metadata.

#### `execution_service.py`
Processes execution results from Caldera agents. Creates detection tasks based on successful executions.

#### `detection_service.py`
Manages detection task creation and execution. Handles different detection types (API, Windows, Linux, Darwin).

### Application Layer (`application/`)

#### `message_service.py`
Orchestrates message processing from Caldera. Coordinates domain services to process execution results and create detection tasks.

### Infrastructure Layer

Infrastructure concerns are distributed across specialized modules:

#### Database Infrastructure (`database/`)
- `connection.py`: Async database connection and session management
- Handles PostgreSQL connection pooling and async SQLAlchemy patterns

#### Message Queue Infrastructure (`mq/`)
- `connection.py`: RabbitMQ connection utilities for different user roles
- `consumers/`: Message consumers for processing incoming messages
- `publishers/`: Message publishers for dispatching tasks

#### External Integrations
- Caldera integration: Handled in `application/message_service.py`
- RabbitMQ integration: Distributed across `mq/` module

### Data Layer

#### Models (`models/`)
SQLAlchemy ORM entities:
- `operation.py`: Caldera operations
- `execution.py`: Agent execution results
- `detection.py`: Detection executions and results

#### Schemas (`schemas/`)
Pydantic validation models for API requests/responses:
- `operation.py`: Operation data validation
- `execution.py`: Execution result validation
- `detection.py`: Detection data validation

#### Repositories (`repositories/`)
Data access layer implementing Repository pattern:
- `base.py`: Generic CRUD operations
- `operation_repo.py`: Operation-specific queries
- `execution_repo.py`: Execution result queries
- `detection_repo.py`: Detection queries

### Utilities (`utils/`)

#### `logging.py`
Centralized logging configuration with structured logging, correlation IDs, and configurable log levels.

## Key Features

1. **Async Architecture**: Full async/await patterns throughout
2. **Clean Architecture**: Clear separation of concerns
3. **Type Safety**: Comprehensive type hints and Pydantic validation
4. **Structured Logging**: Centralized logging with correlation IDs
5. **Message Queue Integration**: RabbitMQ for async task processing
6. **Database Abstraction**: Repository pattern with SQLAlchemy async
7. **API Documentation**: Auto-generated OpenAPI documentation

## Development Guidelines

- All modules use async patterns
- Business logic belongs in domain layer
- External integrations in infrastructure layer
- Data validation with Pydantic schemas
- Comprehensive error handling and logging
- Type hints required for all functions 