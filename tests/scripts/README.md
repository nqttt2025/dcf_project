# Scripts Test Suite

This directory contains test suites for all scripts in the `scripts/` directory.

## Test Files

- `test_bash_scripts.sh` - Tests for all bash scripts
- `test_python_scripts.py` - Tests for all Python scripts

## Running Tests

### Run all script tests
```bash
make test-scripts
```

### Run bash script tests only
```bash
./tests/scripts/test_bash_scripts.sh
```

### Run Python script tests only
```bash
python3 tests/scripts/test_python_scripts.py
```

## What Tests Cover

### Bash Script Tests
- Script existence
- Script syntax validation
- Script executability
- Help/usage functionality
- Module loading

### Python Script Tests
- File existence
- Python syntax validation
- Import checks
- Shebang presence
- Help/docstring presence
- Path resolution

## Adding New Tests

When adding new scripts, update the appropriate test file:

1. **For bash scripts**: Add to `test_bash_scripts.sh` in the appropriate section
2. **For Python scripts**: Add to `test_python_scripts.py` in the appropriate function

## Test Output

Tests use color coding:
- ✓ Green: Test passed
- ✗ Red: Test failed
- ⊘ Yellow: Test skipped (not applicable)

