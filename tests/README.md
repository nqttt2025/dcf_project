# Unit Tests

This directory contains unit tests for the DCF project, following the test structure pattern from the reference project.

## Directory Structure

```
tests/
├── lib/                    # Test utilities (logger, decorators)
│   ├── __init__.py
│   └── test_logger.py      # Border decorator and logger for tests
├── ut/                     # Unit tests
│   ├── __init__.py
│   ├── run_ut              # Test runner script
│   ├── test_config_manager.py
│   ├── test_cache_manager.py
│   ├── test_result_manager.py
│   └── test_dcf_calculator.py
└── test_dcf_complete.py    # Integration test (existing)
```

## Running Tests

### Using Makefile (Recommended)

```bash
# From project root
make              # Run all tests (default)
make test         # Run all tests
make ut           # Run unit tests only
make complete     # Run complete functionality test
make all          # Run all tests (unit + complete)

# Run specific test modules
make test-config  # Run ConfigManager tests
make test-cache   # Run CacheManager tests
make test-result  # Run ResultManager tests
make test-dcf     # Run DCFCalculator tests

# From tests directory
cd tests
make ut           # Run unit tests
make complete     # Run complete test
```

### Using Python directly

```bash
# Run all unit tests using the test runner script
python3 tests/ut/run_ut

# Or using unittest directly
python3 -m unittest discover -s tests/ut -p "test_*.py" -v
```

### Run a specific test file

```bash
python3 -m unittest tests.ut.test_config_manager -v
python3 -m unittest tests.ut.test_cache_manager -v
python3 -m unittest tests.ut.test_result_manager -v
python3 -m unittest tests.ut.test_dcf_calculator -v
```

### Run a specific test case

```bash
python3 -m unittest tests.ut.test_config_manager.TestConfigManager.test_singleton_pattern -v
```

## Test Coverage

### test_config_manager.py
- Singleton pattern verification
- DCF parameters retrieval
- Graham parameters retrieval
- Ticker and data source retrieval
- Factory function testing

### test_cache_manager.py
- Singleton pattern verification
- Cache set/get operations
- Timestamp handling
- File persistence
- Cache clearing

### test_result_manager.py
- Result saving (JSON and text formats)
- Result loading
- Result listing
- Result deletion
- Result serialization

### test_dcf_calculator.py
- DCFCalculator initialization
- DCF calculation logic
- Graham valuation calculation
- Async data fetching (mocked)
- Full calculation flow (mocked)

## Test Utilities

### Border Decorator

The `@border` decorator adds visual borders around test methods for better log readability:

```python
from lib.test_logger import border, logger

@border
def test_something(self):
    logger.info("Test message")
```

### Logger

The test logger provides colored console output and structured logging:

```python
from lib.test_logger import logger

logger.info("Information message")
logger.debug("Debug message")
logger.warning("Warning message")
logger.error("Error message")
```

## Notes

- Unit tests use mocking to avoid external API calls
- Test data is created in temporary directories and cleaned up after tests
- Singleton instances are reset between tests to ensure isolation
- Async tests use `asyncio.run()` to execute async code in sync test methods

