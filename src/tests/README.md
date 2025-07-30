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
cd expand/checking-engine/src/tests
python test_operations_crud.py
```

**Test Coverage:**
- ✅ Health endpoints (`/health`, `/health/db`)
- ✅ CREATE operation (`POST /operations/`)
- ✅ READ operations (`GET /operations/{id}`, `GET /operations/by-caldera-id/{id}`)
- ✅ LIST operations (`GET /operations/` with pagination)
- ✅ UPDATE operation (`PUT /operations/{id}`)
- ✅ DELETE operation (`DELETE /operations/{id}`)
- ✅ Error handling and validation

**Expected Output:**
```
Starting Operations CRUD Tests
==================================================
Testing health endpoints...
Health check: 200
Response: {'status': 'healthy', 'app_name': 'Checking Engine', 'version': '0.1.0'}
DB health check: 200
Response: {'status': 'healthy', 'database': 'connected', 'message': 'Database connection successful'}

Testing CREATE operation...
CREATE response: 201
Created operation ID: 12345678-1234-1234-1234-123456789abc
Operation name: Test Operation
Caldera operation ID: 87654321-4321-4321-4321-cba987654321

Testing GET operation by ID...
GET by ID response: 200
Retrieved operation: Test Operation
Created at: 2024-01-15T10:30:00Z

Testing GET operation by Caldera ID...
GET by Caldera ID response: 200
Retrieved operation by Caldera ID: Test Operation

Testing LIST operations...
LIST response: 200
Total operations: 4
Page: 1
Size: 100
Operations count: 4

Testing UPDATE operation...
UPDATE response: 200
Updated operation name: Updated Test Operation
Updated at: 2024-01-15T10:30:00Z

Testing DELETE operation...
DELETE response: 204
Operation deleted successfully

==================================================
All tests completed!
```

## Running Tests

### Prerequisites
1. FastAPI app must be running on `http://127.0.0.1:1337`
2. Database must be accessible and tables created
3. Environment variables must be configured (`.env` file)

### Test Execution
```bash
# Start the app
cd expand/checking-engine
uvicorn checking_engine.main:app --host 127.0.0.1 --port 1337 --reload

# Run tests
cd src/tests
python test_operations_crud.py
```

### Troubleshooting
- **Connection Error**: Make sure the app is running on port 1337
- **Database Error**: Check database connection and table creation
- **Import Error**: Make sure you're running from the correct directory
- **Validation Error**: Check that test data matches schema requirements
- **HTTP Redirect**: The test handles 307 redirects automatically with `follow_redirects=True`

## Adding New Tests

To add tests for other tables (executions, detections):

1. Create new test file: `test_executions_crud.py`
2. Follow the same pattern as `test_operations_crud.py`
3. Update this README with new test information
4. Add test data and expected responses

## Test Data

The test script creates test operations with:
- Random UUID for `operation_id`
- Current timestamp for `operation_start`
- Test metadata with description
- Unique names to avoid conflicts

Test data is cleaned up automatically after each test run.

## Test Architecture

The test uses:
- **httpx.AsyncClient**: For HTTP requests to FastAPI endpoints
- **follow_redirects=True**: To handle HTTP 307 redirects
- **Trailing slashes**: To ensure proper URL routing
- **Error handling**: Try-catch blocks for JSON parsing
- **Async/await**: For proper asynchronous testing 