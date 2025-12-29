# Scripts Directory Structure

This directory has been refactored following SOLID principles for better maintainability and code reuse.

## Directory Structure

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
│   └── run_all_dcf.sh
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
│   └── web.sh
│
├── common.sh         # Backward compatibility wrapper
├── docker.sh         # Main Docker management script
└── git.sh            # Git tag management script
```

## SOLID Principles Applied

### Single Responsibility Principle (SRP)
- Each module in `lib/` has a single, well-defined responsibility
- Scripts are organized by functionality (version, docker, analysis, dev, utils)

### Open/Closed Principle (OCP)
- Base script class (`lib/base_script.sh`) provides extensible foundation
- New scripts can extend functionality without modifying existing code

### Liskov Substitution Principle (LSP)
- All scripts follow the same interface pattern
- Can be substituted without breaking functionality

### Interface Segregation Principle (ISP)
- Small, focused modules instead of one large common.sh
- Scripts only source what they need

### Dependency Inversion Principle (DIP)
- Scripts depend on abstractions (lib modules) not concrete implementations
- Easy to swap implementations if needed

## Usage

### For New Scripts

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

### Backward Compatibility

The old `scripts/common.sh` still exists as a wrapper for backward compatibility. It automatically loads `scripts/lib/common.sh`.

## Benefits

1. **Code Reuse**: Common functionality is centralized in `lib/`
2. **Maintainability**: Changes to one module don't affect others
3. **Testability**: Each module can be tested independently
4. **Clarity**: Clear organization makes it easy to find scripts
5. **Extensibility**: Easy to add new scripts following the same pattern

