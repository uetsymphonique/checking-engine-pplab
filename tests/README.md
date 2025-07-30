# Testing

This folder contains test scripts for the Checking Engine backend.

## Test Scripts

### `test_operations_crud.py`
Comprehensive test script for Operations CRUD endpoints.

**Features:**
- Tests all CRUD operations (Create, Read, Update, Delete)
- Tests health check endpoints
- Tests pagination and filtering
- Tests error handling
- Uses httpx for HTTP client testing

**Usage:**
```bash
# Make sure the FastAPI app is running
cd expand/checking-engine
uvicorn checking_engine.main:app --host 127.0.0.1 --port 1337 --reload

# In another terminal, run the test
cd expand/checking-engine
python tests/test_operations_crud.py
```

**Test Coverage:**
- ✅ Health endpoints (`/health`, `/health/db`)
- ✅ CREATE operation (`POST /operations/`)
- ✅ READ operations (`GET /operations/{id}`, `GET /operations/by-caldera-id/{id}`)
- ✅ LIST operations (`GET /operations/` with pagination)
- ✅ UPDATE operation (`PUT /operations/{id}`)
- ✅ DELETE operation (`DELETE /operations/{id}`)
- ✅ Error handling and validation

### `test_executions_crud.py`
Comprehensive test script for Execution Results CRUD endpoints.

**Features:**
- Tests all CRUD operations for execution results
- Tests foreign key relationships with operations
- Tests filtering by operation, agent, status, link_state
- Tests special endpoints (recent, failed, by-link-id)
- Tests realistic Caldera execution data

**Usage:**
```bash
cd expand/checking-engine
python tests/test_executions_crud.py
```

**Test Coverage:**
- ✅ CREATE execution result (`POST /executions/`)
- ✅ READ operations (`GET /executions/{id}`, `GET /executions/by-link-id/{id}`)
- ✅ LIST operations with filters (`GET /executions/`)
- ✅ Special endpoints (`GET /executions/recent/{hours}`, `GET /executions/failed/list`)
- ✅ UPDATE operation (`PUT /executions/{id}`)
- ✅ DELETE operation (`DELETE /executions/{id}`)
- ✅ Foreign key validation with operations

### `test_detections_crud.py`
Comprehensive test script for Detection Executions and Results CRUD endpoints.

**Features:**
- Tests both detection_executions and detection_results tables
- Tests complex foreign key relationships (operation → execution → detection)
- Tests enum validation for detection types and statuses
- Tests JSONB data structures for detection configs and results
- Tests statistics endpoint
- Tests realistic Purple Team detection scenarios

**Usage:**
```bash
cd expand/checking-engine
python tests/test_detections_crud.py
```

**Test Coverage:**
- ✅ **Detection Executions**:
  - CREATE detection execution (`POST /detections/executions/`)
  - READ operations (`GET /detections/executions/{id}`)
  - LIST with filters (`GET /detections/executions/`)
  - Special endpoints (pending, failed, retryable, completed)
  - UPDATE operation (`PUT /detections/executions/{id}`)
  - DELETE operation (`DELETE /detections/executions/{id}`)

- ✅ **Detection Results**:
  - CREATE detection result (`POST /detections/results/`)
  - READ operations (`GET /detections/results/{id}`)
  - LIST with filters (`GET /detections/results/`)
  - Statistics endpoint (`GET /detections/results/stats/summary`)
  - UPDATE operation (`PUT /detections/results/{id}`)
  - DELETE operation (`DELETE /detections/results/{id}`)

### `test_caldera_publisher.py`
Test script for Caldera's RabbitMQ publisher integration.

**Features:**
- Tests Caldera's message publishing to RabbitMQ
- Tests realistic execution result messages
- Tests RabbitMQ connection and message delivery
- Tests message persistence and routing

**Usage:**
```bash
cd expand/checking-engine
python tests/test_caldera_publisher.py
```

### `test_app.py`
Basic application startup and database connection test.

**Features:**
- Tests FastAPI app startup
- Tests database connection
- Tests basic health endpoints
- Simple integration test

**Usage:**
```bash
cd expand/checking-engine
python tests/test_app.py
```

## Running Tests

### Prerequisites
1. FastAPI app must be running on `http://127.0.0.1:1337`
2. Database must be accessible and tables created
3. Environment variables must be configured (`.env` file)
4. RabbitMQ must be running (for publisher tests)

### Test Execution
```bash
# Start the app
cd expand/checking-engine
uvicorn checking_engine.main:app --host 127.0.0.1 --port 1337 --reload

# Run individual tests
python tests/test_operations_crud.py
python tests/test_executions_crud.py
python tests/test_detections_crud.py
python tests/test_caldera_publisher.py
python tests/test_app.py

# Or run all tests in sequence
for test in tests/test_*.py; do
    echo "Running $test..."
    python $test
    echo "Completed $test"
    echo "---"
done
```

### Test Results Summary

**Operations CRUD Test:**
```
Starting Operations CRUD Tests
==================================================
Testing health endpoints...
Health check: 200
DB health check: 200

Testing CREATE operation...
CREATE response: 201
Created operation ID: [UUID]

Testing GET operation by ID...
GET by ID response: 200
Retrieved operation: Test Operation

Testing LIST operations...
LIST response: 200
Total operations: [count]

Testing UPDATE operation...
UPDATE response: 200
Updated operation name: Updated Test Operation

Testing DELETE operation...
DELETE response: 204
Operation deleted successfully

==================================================
Operations CRUD Tests Completed
```

**Executions CRUD Test:**
```
Starting Execution Results CRUD Tests
==================================================
Creating test operation for foreign key...
Created test operation: [UUID]

Testing CREATE execution result...
CREATE response: 201
Created execution ID: [UUID]
Link ID: [UUID]
Command: whoami
Status: 0

Testing GET execution by ID...
GET by ID response: 200
Retrieved execution: whoami
Agent: test-host.local

Testing LIST executions...
LIST response: 200
Total executions: [count]
Returned executions: [count]

Testing UPDATE execution...
UPDATE response: 200
Updated command: whoami && pwd

Testing DELETE execution...
DELETE response: 204
Execution deleted successfully

==================================================
Execution Results CRUD Tests Completed
```

**Detections CRUD Test:**
```
Starting Detection Executions and Results CRUD Tests
============================================================
Creating test operation for foreign key...
Created test operation: [UUID]
Creating test execution result for foreign key...
Created test execution result: [UUID]

Testing CREATE detection execution...
CREATE detection execution response: 201
Created detection execution ID: [UUID]
Detection type: api
Platform: cym
Status: pending

Testing CREATE detection result...
CREATE detection result response: 201
Created detection result ID: [UUID]
Detected: True
Source: api.example.com

Testing GET detection statistics...
Statistics response: 200
Total detections: 3
Detected count: 2
Not detected count: 1
Detection rate: 66.67%

Testing DELETE detection result...
DELETE detection result response: 204
Detection result deleted successfully

Testing DELETE detection execution...
DELETE detection execution response: 204
Detection execution deleted successfully

============================================================
Detection Executions and Results CRUD Tests Completed
```

### Troubleshooting
- **Connection Error**: Make sure the app is running on port 1337
- **Database Error**: Check database connection and table creation
- **Import Error**: Make sure you're running from the correct directory
- **Validation Error**: Check that test data matches schema requirements
- **HTTP Redirect**: The test handles 307 redirects automatically with `follow_redirects=True`
- **Foreign Key Error**: Make sure dependencies are created in correct order
- **RabbitMQ Error**: Check RabbitMQ server is running and accessible

## Test Architecture

The tests use:
- **httpx.AsyncClient**: For HTTP requests to FastAPI endpoints
- **follow_redirects=True**: To handle HTTP 307 redirects
- **Trailing slashes**: To ensure proper URL routing
- **Error handling**: Try-catch blocks for JSON parsing
- **Async/await**: For proper asynchronous testing
- **Realistic data**: Test data matches actual Purple Team scenarios
- **Foreign key dependencies**: Proper setup of related records
- **Cleanup**: Automatic deletion of test records

## Test Data

### Operations Test Data:
- Random UUID for `operation_id`
- Current timestamp for `operation_start`
- Test metadata with description
- Unique names to avoid conflicts

### Executions Test Data:
- Realistic Caldera execution data
- `command`: "whoami", "netstat -an"
- `result_data`: stdout, stderr, exit_code
- `link_state`: "SUCCESS", "FAILED"
- Foreign key to operations

### Detections Test Data:
- **Detection Executions**:
  - `detection_type`: "api", "windows", "linux", "darwin"
  - `detection_platform`: "cym", "ajant", "psh", "sh"
  - `detection_config`: API endpoints, timeouts, headers
  - `status`: "pending", "running", "completed", "failed"

- **Detection Results**:
  - `detected`: True/False
  - `raw_response`: API responses, command outputs
  - `parsed_results`: Confidence, severity, rules matched
  - `result_metadata`: Additional context

Test data is cleaned up automatically after each test run.

## Test Coverage Summary

**Complete CRUD Coverage:**
- ✅ **Operations**: 6 endpoints (CRUD + special)
- ✅ **Executions**: 10 endpoints (CRUD + filters + special)
- ✅ **Detections**: 20+ endpoints (CRUD + filters + special + statistics)

**Success Rate: 100% (All tests passing)**
- Operations CRUD: ✅ 100%
- Executions CRUD: ✅ 100%
- Detections CRUD: ✅ 100%
- Statistics: ✅ 100%

**Ready for Phase 2: RabbitMQ Integration** 