#!/bin/bash
# Error Handling Module
# Single Responsibility: Error handling and result checking

# Prevent direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: error_handler.sh should be sourced, not executed directly"
    exit 1
fi

# Source dependencies
source "$(dirname "${BASH_SOURCE[0]}")/logging.sh"

# Exit with error message
exit_with_error() {
    log_error "$@"
    exit 1
}

# Check command result and exit on error
check_result() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        exit_with_error "Command failed with exit code: $exit_code"
    fi
}

# Export error handling functions
export -f exit_with_error
export -f check_result

