# Scripts Architecture

**Last Updated:** 2025-12-30  
**Version:** 2.1

## Overview

Scripts directory đã được refactor theo nguyên tắc SOLID để cải thiện maintainability và code reuse.

## Cấu Trúc

```
scripts/
├── lib/              # Core library modules (Single Responsibility)
│   ├── common.sh     # Main entry point - loads all modules
│   ├── config.sh     # Configuration and constants
│   ├── logging.sh    # Logging functions
│   ├── file_ops.sh   # File/directory operations
│   ├── validation.sh # Input validation
│   ├── error_handler.sh # Error handling
│   ├── python_utils.sh # Python helpers
│   ├── docker_utils.sh # Docker helpers
│   ├── display.sh    # Display/formatting functions
│   ├── version.sh    # Version management
│   └── base_script.sh # Base script class
│
├── version/          # Version management scripts
│   ├── docker_version.sh
│   ├── create_git_tag.sh
│   ├── auto_version.sh
│   └── auto_tag_from_commit.sh
│
├── docker/           # Docker-related scripts
│   └── build_base.sh
│
├── analysis/         # Analysis scripts (DCF, PE)
│   ├── dcf.sh
│   ├── pe.sh
│   ├── run_all_dcf.sh
│   ├── calculate_pe.py
│   ├── run_all_dcf.py
│   └── run_all_dcf_with_retry.py
│
├── dev/              # Development tools
│   ├── test.sh
│   ├── lint.sh
│   ├── clean.sh
│   ├── health_check.sh
│   ├── run_backend_dev.sh
│   └── run_backend_local.sh
│
├── utils/            # Utility scripts
│   ├── get_version.sh
│   ├── web.sh
│   └── update_configs_with_ttm_info.py
│
├── common.sh         # Backward compatibility wrapper
├── docker.sh         # Main Docker management script
└── git.sh            # Git tag management script
```

## SOLID Principles

### Single Responsibility Principle (SRP)
- Mỗi module trong `lib/` có một trách nhiệm rõ ràng
- Scripts được tổ chức theo chức năng

### Open/Closed Principle (OCP)
- Base script class cung cấp foundation có thể mở rộng
- Scripts mới có thể mở rộng mà không cần sửa code cũ

### Dependency Inversion Principle (DIP)
- Scripts phụ thuộc vào abstractions (lib modules) không phải implementations cụ thể

## Module Details

### lib/ - Core Library

#### config.sh
- Project root resolution
- Directory constants
- Docker constants

#### logging.sh
- Logging functions (log_info, log_error, log_warn, log_success)
- File logging support

#### file_ops.sh
- File/directory operations
- Path validation

#### validation.sh
- Input validation (ticker, version)
- Config file validation

#### error_handler.sh
- Error handling utilities
- Result checking

#### python_utils.sh
- Python command checking
- Python script execution

#### docker_utils.sh
- Docker image operations
- Image name generation

#### display.sh
- Display formatting
- Help generation

#### version.sh
- Version management functions
- Git tag integration

#### base_script.sh
- Base script initialization
- Common patterns

## Script Categories

### Version Management (`version/`)
- **docker_version.sh**: Docker image versioning
- **create_git_tag.sh**: Git tag creation
- **auto_version.sh**: Auto-increment versions
- **auto_tag_from_commit.sh**: Tag from commit messages

### Docker (`docker/`)
- **build_base.sh**: Base image builder

### Analysis (`analysis/`)
- **dcf.sh**: DCF analysis runner
- **pe.sh**: PE calculation runner
- **calculate_pe.py**: PE calculation (Python)
- **run_all_dcf.py**: Run all DCF (Python)
- **run_all_dcf_with_retry.py**: DCF with retry logic

### Development (`dev/`)
- **test.sh**: Test runner
- **lint.sh**: Linting
- **clean.sh**: Cleanup
- **health_check.sh**: Health check
- **run_backend_dev.sh**: Backend dev runner
- **run_backend_local.sh**: Local backend runner

### Utilities (`utils/`)
- **get_version.sh**: Version getter
- **web.sh**: Web service management
- **update_configs_with_ttm_info.py**: Config updater

## Usage Patterns

### Creating New Scripts

```bash
#!/bin/bash
set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/scripts/lib/common.sh"

# Initialize script
init_script "$(basename "${BASH_SOURCE[0]}")"

# Your script logic here
```

### Python Scripts

```python
#!/usr/bin/env python3
import os
import sys

# Get script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get project root (2 levels up from scripts/analysis/)
project_root = os.path.dirname(os.path.dirname(script_dir))
# Add to Python path
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))
```

## Testing

### Test Suite

```bash
# Test all scripts
make test-scripts

# Test bash scripts only
make test-scripts-bash

# Test Python scripts only
make test-scripts-python
```

### Test Coverage

- ✅ Script existence
- ✅ Syntax validation
- ✅ Executability
- ✅ Help/usage functionality
- ✅ Path resolution (Python scripts)

## Benefits

1. **Code Reuse**: Common functionality centralized in `lib/`
2. **Maintainability**: Changes to one module don't affect others
3. **Testability**: Each module can be tested independently
4. **Clarity**: Clear organization makes it easy to find scripts
5. **Extensibility**: Easy to add new scripts following the same pattern

## Backward Compatibility

File `scripts/common.sh` vẫn tồn tại như một wrapper để đảm bảo tương thích ngược. Nó tự động load `scripts/lib/common.sh`.

## Migration Notes

### Old Paths → New Paths

- `scripts/get_version.sh` → `scripts/utils/get_version.sh`
- `scripts/docker_version.sh` → `scripts/version/docker_version.sh`
- `scripts/build_base.sh` → `scripts/docker/build_base.sh`
- `scripts/create_git_tag.sh` → `scripts/version/create_git_tag.sh`
- `scripts/auto_version.sh` → `scripts/version/auto_version.sh`
- `scripts/dcf.sh` → `scripts/analysis/dcf.sh`
- `scripts/pe.sh` → `scripts/analysis/pe.sh`
- `scripts/test.sh` → `scripts/dev/test.sh`
- `scripts/lint.sh` → `scripts/dev/lint.sh`
- `scripts/clean.sh` → `scripts/dev/clean.sh`

## References

- [Scripts README](../../scripts/README.md) - Detailed scripts documentation
- [Test Suite](../../tests/scripts/README.md) - Scripts testing documentation

---

**Last Updated:** 2025-12-30  
**Version:** 2.1

