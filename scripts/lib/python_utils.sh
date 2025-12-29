#!/bin/bash
# Python Utilities Module
# Single Responsibility: Python-related helper functions

# Prevent direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: python_utils.sh should be sourced, not executed directly"
    exit 1
fi

# Source dependencies
source "$(dirname "${BASH_SOURCE[0]}")/config.sh"
source "$(dirname "${BASH_SOURCE[0]}")/logging.sh"
source "$(dirname "${BASH_SOURCE[0]}")/file_ops.sh"
source "$(dirname "${BASH_SOURCE[0]}")/error_handler.sh"

# Check if Python command exists
python_exists() {
    command -v "$PYTHON" >/dev/null 2>&1
}

# Run Python script with error handling
run_python() {
    local script="$1"
    shift
    
    if ! python_exists; then
        log_error "Python not found: $PYTHON"
        return 1
    fi
    
    if ! file_exists "$script"; then
        log_error "Python script not found: $script"
        return 1
    fi
    
    "$PYTHON" "$script" "$@"
}

# Export Python utilities
export -f python_exists
export -f run_python

