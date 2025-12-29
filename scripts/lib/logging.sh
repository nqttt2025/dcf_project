#!/bin/bash
# Logging Module
# Single Responsibility: Provide logging functionality

# Prevent direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: logging.sh should be sourced, not executed directly"
    exit 1
fi

# Source config first
source "$(dirname "${BASH_SOURCE[0]}")/config.sh"

# Log to file with timestamp
log_to_file() {
    local log_file="$1"
    shift
    local message="$*"
    
    mkdir -p "$(dirname "$log_file")"
    echo "$message" | tee -a "$log_file"
}

# Log with timestamp
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $*"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
}

log_warn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARN: $*"
}

log_success() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✓ $*"
}

# Export logging functions
export -f log_to_file
export -f log_info
export -f log_error
export -f log_warn
export -f log_success

