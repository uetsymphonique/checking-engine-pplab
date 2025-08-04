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
│       │   ├── message_service.py  # Message processing orchestration
│       │   └── result_service.py   # Result processing orchestration
│       ├── domain/                 # Domain layer (business logic)
│       │   ├── operation_service.py # Operation business logic
│       │   ├── execution_service.py # Execution business logic
│       │   ├── detection_service.py # Detection business logic
│       │   └── result_service.py   # Detection result business logic
│       ├── database/               # Database infrastructure
│       │   └── connection.py       # Database connection management
│       ├── mq/                     # Message queue infrastructure
│       │   ├── connection.py       # RabbitMQ connection utilities
│       │   ├── consumers/          # Message consumers
│       │   │   ├── caldera_execution_consumer.py
│       │   │   ├── worker_task_consumer.py
│       │   │   ├── detection_result_consumer.py
│       │   │   └── __init__.py
│       │   └── publishers/         # Message publishers
│       │       ├── task_dispatcher.py
│       │       ├── result_publisher.py
│       │       └── __init__.py
│       ├── workers/                # Detection worker framework
│       │   ├── base_worker.py      # Base worker class
│       │   ├── api/                # API detection workers
│       │   │   ├── api_worker_base.py
│       │   │   ├── mock_api_worker.py
│       │   │   └── __init__.py
│       │   ├── agent/              # Agent detection workers (future)
│       │   │   └── __init__.py
│       │   └── __init__.py
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
│                    Application Layer                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│  │   Message       │ │   Result        │ │   Task          ││
│  │   Processing    │ │   Processing    │ │   Dispatching   ││
│  └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                    Domain Layer                             │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│  │   Operation     │ │   Detection     │ │   Result        ││
│  │   Services      │ │   Services      │ │   Services      ││
│  └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────┐
│                 Infrastructure Layer                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│  │   Database      │ │   Message Queue │ │   Workers       ││
│  │   PostgreSQL    │ │   RabbitMQ      │ │   Framework     ││
│  └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 2. System Architecture Overview

```mermaid
graph TB
    subgraph RABBITMQ["RABBITMQ MESSAGE BROKER"]
        IQ["caldera.checking.instructions"]
        ATQ["caldera.checking.api.tasks"]
        GTQ["caldera.checking.agent.tasks"]
        ARQ["caldera.checking.api.responses"]
        GRQ["caldera.checking.agent.responses"]
    end

    subgraph BACKEND["CHECKING ENGINE BACKEND"]
        subgraph CONSUMERS["Message Consumers"]
            IC["Caldera Execution Consumer<br/>Processes Red Team results"]
            WTC["Worker Task Consumer<br/>Processes detection tasks"]
            RC["Detection Result Consumer<br/>Processes detection outcomes"]
        end
        
        subgraph LOGIC["Core Logic"]
            MP["Message Processor<br/>Orchestrates data flow"]
            DS["Detection Service<br/>Creates detection tasks"]
            TD["Task Dispatcher<br/>Routes tasks by type"]
            RS["Result Service<br/>Processes detection results"]
        end
        
        subgraph API_SERVER["API Server"]
            API["FastAPI Server<br/>Operations • Executions<br/>Detections • Results"]
            Health["Health Endpoints<br/>System monitoring"]
        end
        
        subgraph DATA_LAYER["Data Layer"]
            Repos["Repository Layer<br/>Data access patterns"]
            Models["SQLAlchemy Models<br/>4 core entities"]
            DB[("PostgreSQL<br/>checking_engine schema")]
        end
        
        subgraph DOMAIN_SERVICES["Domain Services"]
            OS["Operation Service<br/>Red Team operations"]
            ES["Execution Service<br/>Command results"]
            DetS["Detection Service<br/>Blue Team tasks"]
            ResS["Result Service<br/>Detection outcomes"]
        end
    end

    subgraph WORKERS["DETECTION WORKERS"]
        APIWorker["API Detection Workers<br/>SIEM queries • EDR calls<br/>Splunk • CrowdStrike • Elastic"]
        AgentWorker["Agent Detection Workers<br/>OS commands • Log analysis<br/>Windows • Linux • macOS"]
    end

    subgraph EXTERNAL["EXTERNAL SYSTEMS"]
        Caldera["MITRE Caldera<br/>Red Team platform"]
        BlueSystems["Blue Team Systems<br/>SIEM • EDR • Logs"]
    end

    %% External to Message Broker
    Caldera --> IQ
    
    %% Message flow - Instructions
    IQ --> IC
    IC --> MP
    MP --> OS
    MP --> ES
    MP --> DS
    DS --> TD
    TD --> ATQ
    TD --> GTQ
    
    %% Workers consume tasks
    ATQ --> WTC
    GTQ --> WTC
    WTC --> APIWorker
    WTC --> AgentWorker
    
    %% Workers interact with Blue Team systems
    APIWorker --> BlueSystems
    AgentWorker --> BlueSystems
    
    %% Workers publish results
    APIWorker --> ARQ
    AgentWorker --> GRQ
    
    %% Results flow back
    ARQ --> RC
    GRQ --> RC
    RC --> RS
    
    %% Data persistence
    OS --> Repos
    ES --> Repos
    DetS --> Repos
    RS --> Repos
    Repos --> Models
    Models --> DB
    
    %% API access to data
    API --> Repos
    Health --> DB
    
    %% Styling
    classDef consumer fill:#e3f2fd,stroke:#1976d2
    classDef logic fill:#e8f5e8,stroke:#388e3c
    classDef api fill:#fff3e0,stroke:#f57c00
    classDef data fill:#f3e5f5,stroke:#7b1fa2
    classDef domain fill:#e1f5fe,stroke:#0277bd
    classDef external fill:#fafafa,stroke:#616161

    class IC,WTC,RC consumer
    class MP,DS,TD,RS logic
    class API,Health api
    class Repos,Models,DB data
    class OS,ES,DetS,ResS domain
    class IQ,ATQ,GTQ,ARQ,GRQ,APIWorker,AgentWorker,Caldera,BlueSystems external
```

### 3. Worker Framework Architecture

The detection worker framework provides a scalable and extensible system for processing detection tasks:

```mermaid
graph TB
    subgraph "Worker Framework"
        BW[BaseWorker<br/>Abstract base class]
        BAW[BaseAPIWorker<br/>API worker base]
        MAW[MockAPIWorker<br/>Mock implementation]
        
        BW --> BAW
        BAW --> MAW
    end
    
    subgraph "Worker Features"
        Jitter[Jitter Logic<br/>Random delay 0.1-0.5s]
        Retry[Retry Logic<br/>Max retries + delay]
        Result[Result Builder<br/>Standardized messages]
    end
    
    subgraph "Task Processing"
        Task[Task Message]
        Process[Process Task]
        ResultMsg[Result Message]
        
        Task --> Process
        Process --> ResultMsg
    end
    
    BW -.-> Jitter
    BW -.-> Retry
    BW -.-> Result
    
    Process -.-> Jitter
    Process -.-> Retry
    Process -.-> Result
```

### 4. Message Flow Architecture

```mermaid
sequenceDiagram
    participant C as Caldera
    participant MQ as RabbitMQ
    participant CE as Caldera Consumer
    participant TD as Task Dispatcher
    participant WTC as Worker Task Consumer
    participant W as Worker
    participant RP as Result Publisher
    participant RC as Result Consumer
    participant DB as Database
    
    C->>MQ: Execution Result
    MQ->>CE: Consume Message
    CE->>DB: Store Execution
    CE->>TD: Create Detection Tasks
    TD->>MQ: Publish Tasks
    MQ->>WTC: Consume Task
    WTC->>W: Process Task
    W->>W: Apply Jitter
    W->>W: Execute Detection
    W->>W: Handle Retries
    W->>W: Build Result
    W->>RP: Publish Result
    RP->>MQ: Send to Response Queue
    MQ->>RC: Consume Result
    RC->>DB: Store Detection Result
    RC->>DB: Update Execution Status
```

### 5. Layer Responsibilities

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
  - `result_service.py`: Orchestrates detection result processing

#### **Domain Layer (`domain/`)**
- **Purpose**: Business logic and core domain services
- **Components**:
  - `operation_service.py`: Operation management and business rules
  - `execution_service.py`: Execution result processing logic
  - `detection_service.py`: Detection task creation and management
  - `result_service.py`: Detection result business logic

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
  - `publishers/`: Message publishers for dispatching tasks and publishing results

**Worker Framework (`workers/`)**:
- **Purpose**: Detection task processing framework
- **Components**:
  - `base_worker.py`: Abstract base class with jitter, retry, and result building
  - `api/`: API detection workers (SIEM, EDR, etc.)
  - `agent/`: Agent detection workers (OS commands, log analysis)

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

### 6. Data Flow Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Caldera       │────│   RabbitMQ      │────│  Backend        │
│   (Red Team)    │    │   Message       │    │  Consumer       │
│                 │    │   Queue         │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend Processing                           │
│                                                                 │
│  1. Receive Execution Results                                   │
│  2. Store in execution_results table                           │
│  3. Create Detection Executions                                │
│  4. Dispatch Tasks to Workers                                  │
│  5. Workers Process Tasks (with jitter/retry)                 │
│  6. Workers Publish Results                                    │
│  7. Store Detection Results                                    │
│  8. Update Detection Execution Status                          │
│  9. Generate Statistics                                        │
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

### 7. Entity Relationship Diagram

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
        jsonb result_metadata
        timestamp created_at
    }
```

### 8. Table Relationships

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

### 9. RESTful API Structure

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

### 10. Request/Response Patterns

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

## Worker Framework

### 11. Worker Architecture

The detection worker framework provides a scalable and extensible system for processing detection tasks:

#### **BaseWorker Class**
- **Purpose**: Abstract base class for all detection workers
- **Features**:
  - Jitter logic (random delay 0.1-0.5s before processing)
  - Retry logic (configurable max retries and delay)
  - Standardized result message building
  - Error handling with custom exceptions

#### **Worker Types**
- **API Workers** (`workers/api/`): SIEM queries, EDR calls, external API integrations
- **Agent Workers** (`workers/agent/`): OS commands, log analysis, local system checks

#### **Worker Features**
- **Jitter**: Random delay before processing to avoid thundering herd
- **Retry**: Automatic retry with exponential backoff for transient failures
- **Result Standardization**: Consistent result message format
- **Error Handling**: Custom exceptions for different failure types

### 12. Message Processing Flow

1. **Task Reception**: Worker receives task from RabbitMQ
2. **Jitter Application**: Random delay (0.1-0.5s) before processing
3. **Task Processing**: Execute detection logic
4. **Result Building**: Create standardized result message
5. **Result Publishing**: Send result to appropriate response queue
6. **Error Handling**: Handle failures with retry logic

## Configuration Management

### 13. Environment Variables

The application uses Pydantic Settings for configuration management:

```python
# config.py
class Settings(BaseSettings):
    app_name: str = "Checking Engine"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Database
    database_url: str
    
    # RabbitMQ
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_username: str
    rabbitmq_password: str
    
    # Worker Configuration
    worker_jitter_range: tuple[float, float] = (0.1, 0.5)
    worker_max_retries: int = 1
    worker_retry_delay: int = 3
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }
```

### 14. Environment File (.env)
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

# Worker Configuration
WORKER_JITTER_RANGE_MIN=0.1
WORKER_JITTER_RANGE_MAX=0.5
WORKER_MAX_RETRIES=1
WORKER_RETRY_DELAY=3

# Logging
LOG_LEVEL=INFO
```

## Technology Stack

### 15. Core Technologies

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

**Worker Framework**:
- **asyncio**: Async task processing
- **Custom Exceptions**: Error handling and retry logic
- **Structured Logging**: Comprehensive logging with correlation IDs

**Development Tools**:
- **httpx**: HTTP client for testing
- **pytest**: Testing framework (planned)
