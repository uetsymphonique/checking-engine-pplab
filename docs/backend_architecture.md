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
│       │   │   ├── detections.py   # Detections endpoints
│       │   │   └── router.py       # Main API router
│       │   └── deps.py             # API dependencies
│       ├── core/                   # Core application logic
│       ├── database/               # Database layer
│       │   └── connection.py       # Database connection management
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
│       ├── services/               # Business logic layer
│       ├── utils/                  # Utility functions
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
│  │   Services      │ │   Repositories  │ │    Schemas      ││
│  │   (Future)      │ │   Data Access   │ │   Validation    ││
│  └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                     Data Layer                              │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│  │   ORM Models    │ │   Database      │ │   RabbitMQ      ││
│  │   SQLAlchemy    │ │   PostgreSQL    │ │   (Future)      ││
│  └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 2. Layer Responsibilities

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

#### **Business Logic Layer (`repositories/`, `services/`, `schemas/`)**

**Repositories (`repositories/`)**:
- **Purpose**: Data access abstraction layer
- **Pattern**: Repository pattern for database operations
- **Components**:
  - `base.py`: Generic CRUD operations
  - `*_repo.py`: Specialized repository classes

**Schemas (`schemas/`)**:
- **Purpose**: Data validation and serialization
- **Components**:
  - Request/response models using Pydantic
  - Data validation rules
  - Type safety and documentation

**Services (`services/`)**:
- **Purpose**: Business logic and complex operations (Future implementation)
- **Planned Components**:
  - Detection orchestration
  - Message processing
  - Purple Team workflow management

#### **Data Layer (`models/`, `database/`)**

**Models (`models/`)**:
- **Purpose**: Database schema definition
- **Components**:
  - SQLAlchemy ORM models
  - Table relationships
  - Database constraints

**Database (`database/`)**:
- **Purpose**: Database connection and session management
- **Components**:
  - Async database connections
  - Session lifecycle management
  - Health checks

### 3. Data Flow Architecture

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

### 4. Entity Relationship Diagram

```
┌─────────────────┐
│   operations    │
│                 │
│ id (PK)         │
│ name            │
│ operation_id    │◄─────────┐
│ operation_start │          │
│ created_at      │          │
│ updated_at      │          │
│ metadata        │          │
└─────────────────┘          │
         │                   │
         │ 1:N               │
         ▼                   │
┌─────────────────┐          │
│execution_results│          │
│                 │          │
│ id (PK)         │          │
│ operation_id    │──────────┘
│ agent_host      │
│ agent_paw       │
│ link_id         │
│ command         │
│ status          │
│ result_data     │
│ created_at      │
│ raw_message     │
└─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐          ┌─────────────────┐
│detection_exec.  │          │   operations    │
│                 │          │                 │
│ id (PK)         │          │ id (PK)         │
│ exec_result_id  │          │ operation_id    │◄┐
│ operation_id    │──────────┘                 │ │
│ detection_type  │                            │ │
│ detection_plat. │                            │ │
│ detection_conf. │                            │ │
│ status          │                            │ │
│ started_at      │                            │ │
│ completed_at    │                            │ │
│ retry_count     │                            │ │
│ created_at      │                            │ │
└─────────────────┘                            │ │
         │                                     │ │
         │ 1:N                                 │ │
         ▼                                     │ │
┌─────────────────┐                            │ │
│detection_results│                            │ │
│                 │                            │ │
│ id (PK)         │                            │ │
│ detection_ex_id │                            │ │
│ detected        │                            │ │
│ raw_response    │                            │ │
│ parsed_results  │                            │ │
│ result_timestamp│                            │ │
│ result_source   │                            │ │
│ metadata        │                            │ │
│ created_at      │                            │ │
└─────────────────┘                            │ │
                                               │ │
           ┌───────────────────────────────────┘ │
           │                                     │
           └─────────────────────────────────────┘
```

### 5. Table Relationships

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

### 6. RESTful API Structure

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

### 7. Request/Response Patterns

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

### 8. Environment Variables

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

### 9. Environment File (.env)
```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://db_caldera:password@localhost:5432/caldera_purple

# Application Configuration
APP_NAME=Checking Engine
APP_VERSION=0.1.0
DEBUG=true

# RabbitMQ Configuration (Future)
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=checking_consumer
RABBITMQ_PASSWORD=your_password
```

## Technology Stack

### 10. Core Technologies

**Backend Framework**:
- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI applications
- **Pydantic**: Data validation and settings management

**Database**:
- **PostgreSQL**: Primary database for storing application data
- **SQLAlchemy**: ORM for database operations
- **AsyncPG**: Async PostgreSQL driver

**Message Queue** (Planned):
- **RabbitMQ**: Message broker for async communication
- **aio-pika**: Async Python client for RabbitMQ

**Development Tools**:
- **httpx**: HTTP client for testing
- **pytest**: Testing framework (planned)

## Testing Strategy

### 11. Test Architecture

**Test Types**:
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **End-to-End Tests**: Complete workflow testing

**Test Structure**:
```
tests/
├── test_operations_crud.py     # Operations API tests
├── test_executions_crud.py     # Executions API tests
├── test_detections_crud.py     # Detections API tests
├── test_caldera_publisher.py   # RabbitMQ integration tests
└── test_app.py                 # Basic application tests
```

**Test Coverage**:
- ✅ **Operations**: 100% CRUD coverage
- ✅ **Executions**: 100% CRUD + special methods
- ✅ **Detections**: 100% CRUD + statistics
- ✅ **Health Checks**: 100% coverage