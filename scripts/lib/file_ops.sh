#!/bin/bash
# File Operations Module
# Single Responsibility: File and directory operations

# Prevent direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: file_ops.sh should be sourced, not executed directly"
    exit 1
fi

# Source dependencies
source "$(dirname "${BASH_SOURCE[0]}")/config.sh"
source "$(dirname "${BASH_SOURCE[0]}")/logging.sh"

# Check if file exists
file_exists() {
    [[ -f "$1" ]]
}

# Check if directory exists
dir_exists() {
    [[ -d "$1" ]]
}

# Ensure directory exists
ensure_dir() {
    local dir="$1"
    if ! dir_exists "$dir"; then
        mkdir -p "$dir"
        log_info "Created directory: $dir"
    fi
}

# Export file operations
export -f file_exists
export -f dir_exists
export -f ensure_dir

