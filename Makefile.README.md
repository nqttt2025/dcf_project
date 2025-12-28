# Makefile Usage Guide

This Makefile provides convenient commands for running tests, linters, and cleanup tasks for the DCF Project.

## Quick Start

```bash
# Run all tests (default)
make

# Show help
make help
```

## Test Commands

### Run All Tests
```bash
make test        # Run all tests (unit + complete)
make ut          # Run unit tests only
make complete    # Run complete functionality test
make all         # Run all tests (unit + complete)
```

### Run Specific Test Modules
```bash
make test-config  # Run ConfigManager tests
make test-cache   # Run CacheManager tests
make test-result  # Run ResultManager tests
make test-dcf     # Run DCFCalculator tests
```

## Linting Commands

```bash
make lint        # Run all linters (pylint + flake8)
make pylint      # Run pylint only
make flake8      # Run flake8 only
```

## Cleanup Commands

```bash
make clean       # Clean generated files (logs, cache, reports)
make clean-all   # Clean everything including data and results
```

### What gets cleaned:

- `make clean`: Removes logs, cache files, and reports
- `make clean-all`: Additionally removes test data and results

## Examples

```bash
# Run only unit tests
make ut

# Run specific test module
make test-config

# Run linters
make lint

# Clean up and run tests
make clean && make test
```

## Notes

- All test commands can also be run from the `tests/` directory using the same Makefile
- The Makefile follows the same structure as the reference project (`/home/eenitug/aat_ims_load`)
- Test results and logs are saved in the `reports/` directory when running linters

