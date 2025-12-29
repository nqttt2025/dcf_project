# Container Tests Guide

## Overview

Container tests verify Docker containers using Docker API, similar to the reference project `/home/eenitug/aat_ims_load`.

## Test Files Created

### Function Tests (`tests/ft/`)
- `test_container_gateway.py` - Gateway container tests
- `test_container_dcf.py` - DCF service container tests
- `test_container_stock.py` - Stock service container tests
- `test_container_database.py` - Database service container tests
- `test_container_frontend.py` - Frontend container tests

### System Tests (`tests/st/`)
- `test_container_integration.py` - Container integration tests
- `test_container_health.py` - Health check tests
- `test_container_networking.py` - Networking tests

### Utilities (`tests/lib/`)
- `docker_utils.py` - DockerContainerManager class for Docker API operations

## Docker API Usage

The tests use Docker Python SDK (`docker>=5.0.0`) to:
- List and inspect containers
- Check container status and health
- Execute commands in containers
- Get container logs
- Check service endpoints

## Running Tests

### Prerequisites
```bash
# Install Docker Python SDK (if not already installed)
pip install docker>=5.0.0

# Start containers (optional - tests will skip if not running)
make docker-up
```

### Run Tests
```bash
# All container function tests
python3 -m unittest discover -s tests/ft -p "test_container_*.py" -v

# All container system tests
python3 -m unittest discover -s tests/st -p "test_container_*.py" -v

# Specific container test
python3 -m unittest tests.ft.test_container_gateway -v
```

## Test Behavior

- **When containers are running**: Tests verify functionality
- **When containers are not running**: Tests skip gracefully with `skipTest`
- **When Docker is not available**: Tests skip at class level

## Test Coverage

### Container Level
- Container existence
- Container status (running/stopped)
- Container health checks
- Container information (ports, env, volumes)
- Container logs
- Container exec commands

### Service Level
- HTTP health endpoints
- API endpoints
- Service-to-service communication
- Port mappings
- Network configuration

### Integration Level
- All containers running
- Container dependencies
- Network connectivity
- Health status monitoring

## Example Test Output

```
test_container_exists ... ok
test_container_running ... ok
test_container_health ... ok
test_service_health_endpoint ... ok
test_container_info ... ok

Ran 5 tests in 2.345s
OK
```

## Notes

- Tests are non-destructive
- Tests can run in CI/CD pipelines
- Tests gracefully handle missing containers
- Tests verify both Docker-level and service-level functionality

