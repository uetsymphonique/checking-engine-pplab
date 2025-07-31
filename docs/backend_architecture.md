# Backend Architecture Documentation

This document describes the folder structure and design architecture of the Checking Engine backend.

## Project Overview

The Checking Engine is a Purple Team platform that integrates with MITRE Caldera to process Red Team execution results and simulate Blue Team detection activities. The backend is built using FastAPI, PostgreSQL, and follows clean architecture principles.

## Folder Structure

```
expand/checking-engine/
├── docs/                           # Documentation
│   ├── backend_architecture.md     # This document
│   ├── db.md                       # Database schema documentation
│   ├── mq_architecture.md          # RabbitMQ architecture
│   └── caldera_integration.md      # Caldera integration guide
├── setup/                          # Setup scripts and configurations
│   ├── db_setup/                   # Database setup scripts
│   └── mq_setup/                   # RabbitMQ setup scripts
├── tests/                          # Test scripts
│   ├── test_operations_crud.py     # Operations CRUD tests
│   ├── test_executions_crud.py     # Executions CRUD tests
│   ├── test_detections_crud.py     # Detections CRUD tests
│   ├── test_caldera_publisher.py   # RabbitMQ publisher tests
│   ├── test_app.py                 # Basic app tests
│   └── README.md                   # Testing documentation
├── src/                            # Source code
│   └── checking_engine/            # Main application package
│       ├── api/                    # API layer
│       │   ├── v1/                 # API version 1
│       │   │   ├── health.py       # Health check endpoints
│       │   │   ├── operations.py   # Operations endpoints
│       │   │   ├── executions.py   # Executions endpoints
│       │   │   ├── detection_executions.py  # Detection execution endpoints
│       │   │   ├── detection_results.py     # Detection result endpoints
│       │   │   └── router.py       # Main API router
│       │   └── deps.py             # API dependencies
│       ├── application/            # Application layer (use case orchestration)
│       │   └── message_service.py  # Message processing orchestration
│       ├── domain/                 # Domain layer (business logic)
│       │   ├── operation_service.py # Operation business logic
│       │   ├── execution_service.py # Execution business logic
│       │   └── detection_service.py # Detection business logic
│       ├── database/               # Database infrastructure
│       │   └── connection.py       # Database connection management
│       ├── mq/                     # Message queue infrastructure
│       │   ├── connection.py       # RabbitMQ connection utilities
│       │   ├── consumers/          # Message consumers
│       │   │   └── caldera_execution_consumer.py
│       │   └── publishers/         # Message publishers
│       │       └── task_dispatcher.py
│       ├── models/                 # SQLAlchemy ORM models
│       │   ├── base.py             # Base model class
│       │   ├── operation.py        # Operation model
│       │   ├── execution.py        # Execution result model
│       │   └── detection.py        # Detection models
│       ├── repositories/           # Data access layer
│       │   ├── base.py             # Base repository class
│       │   ├── operation_repo.py   # Operations repository
│       │   ├── execution_repo.py   # Executions repository
│       │   └── detection_repo.py   # Detections repository
│       ├── schemas/                # Pydantic schemas
│       │   ├── operation.py        # Operation schemas
│       │   ├── execution.py        # Execution schemas
│       │   └── detection.py        # Detection schemas
│       ├── utils/                  # Utility functions
│       │   └── logging.py          # Centralized logging
│       ├── config.py               # Application configuration
│       └── main.py                 # FastAPI application entry point
├── .env                           # Environment variables
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Project configuration
└── README.md                      # Project README
```

## Architecture Design

### 1. Clean Architecture Principles

The backend follows clean architecture patterns with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                            │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│  │   Health API    │ │ Operations API  │ │ Detections API  ││
│  │   /health       │ │ /operations     │ │ /detections     ││
│  └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                     │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│  │   Domain        │ │   Repositories  │ │    Schemas      ││
│  │   Services      │ │   Data Access   │ │   Validation    ││
│  └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                 Infrastructure Layer                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│  │   Database      │ │   Message Queue │ │   External      ││
│  │   PostgreSQL    │ │   RabbitMQ      │ │   Integrations  ││
│  └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 2. System Architecture Overview

![Checking Engine Architecture](images/checking-engine.png)

*The Checking Engine integrates Caldera execution results with Blue Team detection capabilities through distributed infrastructure components.*

### 3. Layer Responsibilities

#### **API Layer (`api/`)**
- **Purpose**: Handle HTTP requests and responses
- **Components**:
  - `v1/`: API version 1 endpoints
  - `deps.py`: Dependency injection for database sessions
  - `router.py`: Main API router combining all endpoints

**Key Features**:
- RESTful API design
- Request/response validation using Pydantic
- Error handling and HTTP status codes
- API versioning support
- Dependency injection for database sessions

#### **Application Layer (`application/`)**
- **Purpose**: Use case orchestration and cross-cutting concerns
- **Components**:
  - `message_service.py`: Processes incoming Caldera messages and coordinates domain services

#### **Domain Layer (`domain/`)**
- **Purpose**: Business logic and core domain services
- **Components**:
  - `operation_service.py`: Operation management and business rules
  - `execution_service.py`: Execution result processing logic
  - `detection_service.py`: Detection task creation and management

#### **Infrastructure Layer (Distributed)**

**Database Infrastructure (`database/`)**:
- **Purpose**: Database connection and session management
- **Components**:
  - `connection.py`: Async database connections and session lifecycle

**Message Queue Infrastructure (`mq/`)**:
- **Purpose**: RabbitMQ integration for async messaging
- **Components**:
  - `connection.py`: RabbitMQ connection utilities for different user roles
  - `consumers/`: Message consumers for processing incoming messages
  - `publishers/`: Message publishers for dispatching tasks

#### **Data Layer (`models/`, `schemas/`, `repositories/`)**

**Models (`models/`)**:
- **Purpose**: Database schema definition
- **Components**:
  - SQLAlchemy ORM models
  - Table relationships
  - Database constraints

**Schemas (`schemas/`)**:
- **Purpose**: Data validation and serialization
- **Components**:
  - Request/response models using Pydantic
  - Data validation rules
  - Type safety and documentation

**Repositories (`repositories/`)**:
- **Purpose**: Data access abstraction layer
- **Pattern**: Repository pattern for database operations
- **Components**:
  - `base.py`: Generic CRUD operations
  - `*_repo.py`: Specialized repository classes

### 4. Data Flow Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Caldera       │────│   RabbitMQ      │────│  Backend        │
│   (Red Team)    │    │   Message       │    │  Consumer       │
│                 │    │   Queue         │    │  (Future)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend Processing                           │
│                                                                 │
│  1. Receive Execution Results                                   │
│  2. Store in execution_results table                           │
│  3. Create Detection Executions                                │
│  4. Process Detections (API/Agent)                             │
│  5. Store Detection Results                                    │
│  6. Generate Statistics                                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   Statistics    │    │   Dashboard     │
│   Database      │    │   API           │    │   (Future)      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Database Design

### 5. Entity Relationship Diagram

```mermaid
erDiagram
    operations ||--o{ execution_results : has
    operations ||--o{ detection_executions : belongs_to
    execution_results ||--o{ detection_executions : triggers
    detection_executions ||--o{ detection_results : produces
    
    operations {
        uuid id PK
        string name
        uuid operation_id
        timestamp operation_start
        timestamp created_at
        timestamp updated_at
        jsonb metadata
    }
    
    execution_results {
        uuid id PK
        uuid operation_id FK
        string agent_host
        string agent_paw
        uuid link_id
        string command
        integer pid
        integer status
        jsonb result_data
        timestamp agent_reported_time
        string link_state
        timestamp created_at
        jsonb raw_message
    }
    
    detection_executions {
        uuid id PK
        uuid execution_result_id FK
        uuid operation_id FK
        string detection_type
        string detection_platform
        jsonb detection_config
        string status
        timestamp started_at
        timestamp completed_at
        integer retry_count
        integer max_retries
        jsonb execution_metadata
        timestamp created_at
    }
    
    detection_results {
        uuid id PK
        uuid detection_execution_id FK
        boolean detected
        jsonb raw_response
        jsonb parsed_results
        timestamp result_timestamp
        string result_source
        jsonb metadata
        timestamp created_at
    }
```

![Database Schema](images/db_schema.png)

*The database schema supports the Purple Team workflow by storing Caldera operations, execution results, and detection outcomes across multiple platforms.*

### 6. Table Relationships

**Operations (1:N) Execution Results**:
- One operation can have multiple execution results
- Foreign key: `execution_results.operation_id → operations.operation_id`

**Execution Results (1:N) Detection Executions**:
- One execution result can trigger multiple detection executions
- Foreign key: `detection_executions.execution_result_id → execution_results.id`

**Operations (1:N) Detection Executions**:
- Direct relationship for easier querying
- Foreign key: `detection_executions.operation_id → operations.operation_id`

**Detection Executions (1:N) Detection Results**:
- One detection execution can have multiple results (retries, multiple sources)
- Foreign key: `detection_results.detection_execution_id → detection_executions.id`

## API Design

### 7. RESTful API Structure

**Base URL**: `http://localhost:1337/api/v1`

#### **Health Endpoints**
```
GET /health                 # Basic health check
GET /health/db             # Database health check
```

#### **Operations Endpoints**
```
POST   /operations/                           # Create operation
GET    /operations/                           # List operations
GET    /operations/{id}                       # Get operation by ID
GET    /operations/by-caldera-id/{id}         # Get by Caldera operation_id
PUT    /operations/{id}                       # Update operation
DELETE /operations/{id}                       # Delete operation
```

#### **Executions Endpoints**
```
POST   /executions/                           # Create execution result
GET    /executions/                           # List execution results
GET    /executions/{id}                       # Get execution by ID
GET    /executions/by-link-id/{id}            # Get by Caldera link_id
GET    /executions/by-operation/{id}          # Get by operation
GET    /executions/with-operation/{id}        # Get with operation data
GET    /executions/recent/{hours}             # Get recent executions
GET    /executions/failed/list                # Get failed executions
PUT    /executions/{id}                       # Update execution
DELETE /executions/{id}                       # Delete execution
```

#### **Detections Endpoints**
```
# Detection Executions
POST   /detections/executions/                # Create detection execution
GET    /detections/executions/                # List detection executions
GET    /detections/executions/{id}            # Get detection execution
GET    /detections/executions/by-execution-result/{id}  # Get by execution result
GET    /detections/executions/by-operation/{id}         # Get by operation
GET    /detections/executions/pending/list             # Get pending
GET    /detections/executions/failed/list              # Get failed
GET    /detections/executions/retryable/list           # Get retryable
PUT    /detections/executions/{id}            # Update detection execution
DELETE /detections/executions/{id}            # Delete detection execution

# Detection Results
POST   /detections/results/                   # Create detection result
GET    /detections/results/                   # List detection results
GET    /detections/results/{id}               # Get detection result
GET    /detections/results/by-execution/{id}  # Get by detection execution
GET    /detections/results/detected/list      # Get detected results
GET    /detections/results/not-detected/list  # Get not detected results
GET    /detections/results/recent/{hours}     # Get recent results
GET    /detections/results/stats/summary      # Get statistics
PUT    /detections/results/{id}               # Update detection result
DELETE /detections/results/{id}               # Delete detection result
```

### 8. Request/Response Patterns

#### **Standard Response Format**
```json
{
  "id": "uuid",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "field1": "value1",
  "field2": "value2"
}
```

#### **List Response Format**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 50
}
```

#### **Error Response Format**
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## Configuration Management

### 9. Environment Variables

The application uses Pydantic Settings for configuration management:

```python
# config.py
class Settings(BaseSettings):
    app_name: str = "Checking Engine"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Database
    database_url: str
    
    # RabbitMQ (Future)
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_username: str
    rabbitmq_password: str
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }
```

### 10. Environment File (.env)
```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://db_caldera:password@localhost:5432/caldera_purple

# Application Configuration
APP_NAME=Checking Engine
APP_VERSION=0.1.0
DEBUG=true

RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_VHOST=/caldera_checking
RABBITMQ_MANAGEMENT_PORT=15672

# User Credentials (update with actual passwords)
RABBITMQ_ADMIN_USER=caldera_admin
RABBITMQ_ADMIN_PASS=haha

RABBITMQ_PUBLISHER_USER=caldera_publisher
RABBITMQ_PUBLISHER_PASS=hihi

RABBITMQ_CONSUMER_USER=checking_consumer
RABBITMQ_CONSUMER_PASS=hehe

RABBITMQ_WORKER_USER=checking_worker
RABBITMQ_WORKER_PASS=huhu

RABBITMQ_DISPATCHER_USER=checking_dispatcher
RABBITMQ_DISPATCHER_PASS=hoho

RABBITMQ_RESULT_CONSUMER_USER=checking_result_consumer
RABBITMQ_RESULT_CONSUMER_PASS=hichic

RABBITMQ_MONITOR_USER=monitor_user
RABBITMQ_MONITOR_PASS=huhhuh

# Exchange and Queue Names
RABBITMQ_EXCHANGE=caldera.checking.exchange
RABBITMQ_INSTRUCTIONS_QUEUE=caldera.checking.instructions
RABBITMQ_API_TASKS_QUEUE=caldera.checking.api.tasks
RABBITMQ_AGENT_TASKS_QUEUE=caldera.checking.agent.tasks
RABBITMQ_API_RESPONSES_QUEUE=caldera.checking.api.responses
RABBITMQ_AGENT_RESPONSES_QUEUE=caldera.checking.agent.responses

# Routing Keys
ROUTING_KEY_EXECUTION_RESULT=caldera.execution.result
ROUTING_KEY_API_TASK=checking.api.task
ROUTING_KEY_AGENT_TASK=checking.agent.task
ROUTING_KEY_API_RESPONSE=checking.api.response
ROUTING_KEY_AGENT_RESPONSE=checking.agent.response

# Logging
LOG_LEVEL=INFO
```

## Technology Stack

### 11. Core Technologies

**Backend Framework**:
- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI applications
- **Pydantic**: Data validation and settings management

**Database**:
- **PostgreSQL**: Primary database for storing application data
- **SQLAlchemy**: ORM for database operations
- **AsyncPG**: Async PostgreSQL driver

**Message Queue**:
- **RabbitMQ**: Message broker for async communication
- **aio-pika**: Async Python client for RabbitMQ

**Development Tools**:
- **httpx**: HTTP client for testing
- **pytest**: Testing framework (planned)
