# Checking Engine - Source Code Documentation

## Overview

The Checking Engine is a Purple Team detection system that integrates with MITRE Caldera to simulate Blue Team detection capabilities. The system processes Caldera execution results and creates detection tasks for various platforms using a scalable worker framework.

## Architecture

The codebase follows Clean Architecture principles with clear separation of concerns:

```
src/checking_engine/
├── api/           # HTTP REST API layer
├── application/   # Use case orchestration
├── domain/        # Business logic services
├── database/      # Database infrastructure (connection, session management)
├── mq/           # Message queue infrastructure (RabbitMQ)
├── workers/       # Detection worker framework
├── models/        # Database ORM entities
├── schemas/       # Data validation models
├── repositories/  # Data access layer
└── utils/         # Common utilities
```

**Note:** Infrastructure layer is distributed across `database/` and `mq/` modules rather than a separate `infrastructure/` directory.

## Module Documentation

### Core Modules

#### `config.py`
Application configuration using Pydantic Settings. Manages database, RabbitMQ, worker settings, and logging configuration.

#### `main.py`
FastAPI application entry point. Configures middleware, lifespan events, API routing, and manages RabbitMQ consumers lifecycle.

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

### Application Layer (`application/`)

Use case orchestration and cross-cutting concerns:

#### `message_service.py`
Orchestrates message processing from Caldera. Coordinates domain services to process execution results and create detection tasks.

#### `result_service.py`
Orchestrates detection result processing. Coordinates domain services to store detection results and update execution status.

### Domain Layer (`domain/`)

Business logic services implementing core business rules:

#### `operation_service.py`
Manages Caldera operations and campaigns. Handles operation lifecycle and metadata.

#### `execution_service.py`
Processes execution results from Caldera agents. Creates detection tasks based on successful executions.

#### `detection_service.py`
Manages detection task creation and execution. Handles different detection types (API, Windows, Linux, Darwin).

#### `result_service.py`
Manages detection result business logic. Handles result storage and execution status updates.

### Infrastructure Layer

Infrastructure concerns are distributed across specialized modules:

#### Database Infrastructure (`database/`)
- `connection.py`: Async database connection and session management
- Handles PostgreSQL connection pooling and async SQLAlchemy patterns

#### Message Queue Infrastructure (`mq/`)
- `connection.py`: RabbitMQ connection utilities for different user roles
- `consumers/`: Message consumers for processing incoming messages
  - `caldera_execution_consumer.py`: Processes Caldera execution results
  - `worker_task_consumer.py`: Processes detection tasks for workers
  - `detection_result_consumer.py`: Processes detection results from workers
- `publishers/`: Message publishers for dispatching tasks and publishing results
  - `task_dispatcher.py`: Dispatches detection tasks to appropriate queues
  - `result_publisher.py`: Publishes detection results to response queues

#### Worker Framework (`workers/`)
Detection task processing framework:
- `base_worker.py`: Abstract base class with jitter, retry, and result building
- `api/`: API detection workers (SIEM, EDR, etc.)
  - `api_worker_base.py`: Base class for API workers
  - `mock_api_worker.py`: Mock implementation for testing
- `agent/`: Agent detection workers (OS commands, log analysis) - future

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

## Worker Framework

### Overview
The detection worker framework provides a scalable and extensible system for processing detection tasks with built-in resilience patterns.

### Key Components

#### BaseWorker Class
- **Purpose**: Abstract base class for all detection workers
- **Features**:
  - Jitter logic (random delay 0.1-0.5s before processing)
  - Retry logic (configurable max retries and delay)
  - Standardized result message building
  - Error handling with custom exceptions (`MaxRetriesExceededException`, `TaskProcessingException`)

#### Worker Types
- **API Workers** (`workers/api/`): SIEM queries, EDR calls, external API integrations
- **Agent Workers** (`workers/agent/`): OS commands, log analysis, local system checks

#### Worker Features
- **Jitter**: Random delay before processing to avoid thundering herd
- **Retry**: Automatic retry with exponential backoff for transient failures
- **Result Standardization**: Consistent result message format with required fields
- **Error Handling**: Custom exceptions for different failure types

### Message Processing Flow

1. **Task Reception**: Worker receives task from RabbitMQ
2. **Jitter Application**: Random delay (0.1-0.5s) before processing
3. **Task Processing**: Execute detection logic
4. **Result Building**: Create standardized result message with required fields
5. **Result Publishing**: Send result to appropriate response queue
6. **Error Handling**: Handle failures with retry logic

## Message Flow Architecture

### Caldera Integration Flow
1. Caldera sends execution results to `caldera.checking.instructions` queue
2. `CalderaExecutionConsumer` processes messages and stores in database
3. `DetectionService` creates detection tasks based on execution results
4. `TaskDispatcher` publishes tasks to appropriate worker queues (`api.tasks` or `agent.tasks`)

### Worker Processing Flow
1. `WorkerTaskConsumer` consumes tasks from worker queues
2. Workers process tasks with jitter and retry logic
3. Workers publish results to response queues (`api.responses` or `agent.responses`)
4. `DetectionResultConsumer` processes results and stores in database
5. Detection execution status is updated based on worker results

## Key Features

1. **Async Architecture**: Full async/await patterns throughout
2. **Clean Architecture**: Clear separation of concerns
3. **Type Safety**: Comprehensive type hints and Pydantic validation
4. **Structured Logging**: Centralized logging with correlation IDs
5. **Message Queue Integration**: RabbitMQ for async task processing
6. **Database Abstraction**: Repository pattern with SQLAlchemy async
7. **Worker Framework**: Scalable detection task processing
8. **Resilience Patterns**: Jitter, retry, and error handling
9. **API Documentation**: Auto-generated OpenAPI documentation

## Development Guidelines

- All modules use async patterns
- Business logic belongs in domain layer
- External integrations in infrastructure layer
- Data validation with Pydantic schemas
- Comprehensive error handling and logging
- Type hints required for all functions
- Workers must implement standardized result message format
- Use custom exceptions for error handling
- Follow jitter and retry patterns for resilience 