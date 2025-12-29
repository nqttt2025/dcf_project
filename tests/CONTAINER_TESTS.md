# Container Tests Documentation

## Overview

Container tests use Docker API to test individual containers and their integration. These tests verify:
- Container existence and status
- Container health checks
- Service endpoints
- Container networking
- Service-to-service communication

## Test Structure

### Function Tests (`tests/ft/`)

#### `test_container_gateway.py`
Tests Gateway container:
- Container existence and running status
- Health check configuration
- Service health endpoint
- Container information
- Container exec commands
- Container logs
- API endpoints

#### `test_container_dcf.py`
Tests DCF service container:
- Container existence and status
- Service health endpoint
- Environment variables
- Volume mounts

#### `test_container_stock.py`
Tests Stock service container:
- Container existence and status
- Service health endpoint

#### `test_container_database.py`
Tests Database service container:
- Container existence and status
- PostgreSQL container check
- Service health endpoint

#### `test_container_frontend.py`
Tests Frontend container:
- Container existence and status
- Frontend accessibility
- Container information

### System Tests (`tests/st/`)

#### `test_container_integration.py`
Tests container integration:
- All containers running
- Container networking
- Service communication
- Container dependencies
- Health status
- Logs accessibility
- Resource usage

#### `test_container_health.py`
Tests container health:
- Health check configuration
- Health endpoints
- Container restart recovery
- Health check timeout

#### `test_container_networking.py`
Tests container networking:
- Containers on same network
- Service-to-service communication
- Port mappings
- Internal service URLs

## Docker Utilities (`tests/lib/docker_utils.py`)

The `DockerContainerManager` class provides:

### Container Management
- `get_container(name)` - Get container by name
- `is_container_running(name)` - Check if container is running
- `get_container_status(name)` - Get container status
- `get_container_health(name)` - Get health status
- `wait_for_container_healthy(name, timeout)` - Wait for healthy status

### Container Operations
- `exec_command(name, command, user)` - Execute command in container
- `get_container_logs(name, tail)` - Get container logs
- `get_container_info(name)` - Get container information

### Service Checks
- `check_service_health(url, timeout)` - Check HTTP health endpoint
- `get_service_info(url)` - Get service information

### Utilities
- `list_containers(filters)` - List containers with filters
- `is_available()` - Check if Docker is available

## Running Container Tests

### Prerequisites
- Docker must be installed and running
- Containers must be built and started
- Docker Python SDK (`docker>=5.0.0`) must be installed

### Run All Container Tests
```bash
# Function tests
make ft
./scripts/dev/test.sh ft

# System tests
make st
./scripts/dev/test.sh st
```

### Run Specific Container Tests
```bash
# Test Gateway container
python3 -m unittest tests.ft.test_container_gateway -v

# Test DCF container
python3 -m unittest tests.ft.test_container_dcf -v

# Test container integration
python3 -m unittest tests.st.test_container_integration -v
```

### Run All Container Tests
```bash
# All function tests for containers
python3 -m unittest discover -s tests/ft -p "test_container_*.py" -v

# All system tests for containers
python3 -m unittest discover -s tests/st -p "test_container_*.py" -v
```

## Test Containers

The tests check these containers:
- `dcf-gateway` - API Gateway (port 8000)
- `dcf-service` - DCF Service (port 8001)
- `dcf-stock` - Stock Service (port 8002)
- `dcf-database` - Database Service (port 8003)
- `dcf-postgres` - PostgreSQL (port 5432)
- `dcf-redis` - Redis (port 6379)
- `dcf-frontend` - Frontend (port 8080)

## Test Behavior

### When Containers Are Running
- Tests verify container status, health, and functionality
- Tests check service endpoints and communication
- Tests validate networking and dependencies

### When Containers Are Not Running
- Tests skip gracefully with `skipTest`
- Tests log warnings but don't fail
- Tests can be run in CI/CD even if containers aren't started

## Example Usage

```python
from tests.lib.docker_utils import get_container_manager

# Get container manager
manager = get_container_manager()

# Check if Docker is available
if not manager.is_available():
    raise unittest.SkipTest("Docker not available")

# Check container status
is_running = manager.is_container_running("dcf-gateway")

# Get container info
info = manager.get_container_info("dcf-gateway")

# Check service health
is_healthy = manager.check_service_health("http://localhost:8000")

# Execute command in container
exit_code, output = manager.exec_command("dcf-gateway", "python --version")
```

## Notes

- Tests are designed to be non-destructive
- Tests skip gracefully when Docker or containers are not available
- Tests can run in CI/CD pipelines
- Tests verify both container-level and service-level functionality

