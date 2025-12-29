# Makefile Test Suite

Test suite để đảm bảo tất cả Makefile commands chạy ổn định và không có trùng lặp.

## Test Files

- `test_makefile_commands.sh` - Tests syntax, existence, và dry-run của tất cả targets
- `test_makefile_functionality.sh` - Tests thực tế các commands an toàn (non-destructive)

## Running Tests

### Run all Makefile tests
```bash
make test-makefile-all
```

### Run individual test suites
```bash
make test-makefile              # Commands + functionality
make test-makefile-commands     # Command tests only
make test-makefile-functionality # Functionality tests only
./tests/makefile/test_makefile_duplicates.sh    # Duplicate check
./tests/makefile/test_all_commands.sh          # All commands test
```

## What Tests Cover

### Command Tests (`test_makefile_commands.sh`)
- ✅ Makefile syntax validation
- ✅ Target existence
- ✅ Dry-run testing (make -n)
- ✅ Script path validation
- ✅ Error handling
- ✅ Duplicate functionality detection

### Functionality Tests (`test_makefile_functionality.sh`)
- ✅ Help command execution
- ✅ Version commands
- ✅ Docker version commands
- ✅ Help commands (dcf-help, pe-help)
- ✅ Error message validation
- ✅ Script execution verification

## Test Categories

### Safe Tests (Always Run)
- Help commands
- Version commands
- Dry-run tests
- Syntax validation

### Conditional Tests (Skipped if Requirements Missing)
- Docker commands (requires Docker)
- Backend commands (requires Python dependencies)
- Build commands (takes too long)

## Adding New Tests

Khi thêm target mới vào Makefile:

1. Thêm test vào `test_makefile_commands.sh` trong section phù hợp
2. Nếu command an toàn, thêm vào `test_makefile_functionality.sh`
3. Cập nhật documentation này

## Test Output

Tests use color coding:
- ✓ Green: Test passed
- ✗ Red: Test failed
- ⊘ Yellow: Test skipped (not applicable)
- ⚠ Yellow: Warning (potential issue)

