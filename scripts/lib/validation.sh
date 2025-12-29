#!/bin/bash
# Validation Module
# Single Responsibility: Input validation functions

# Prevent direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: validation.sh should be sourced, not executed directly"
    exit 1
fi

# Source dependencies
source "$(dirname "${BASH_SOURCE[0]}")/config.sh"
source "$(dirname "${BASH_SOURCE[0]}")/logging.sh"
source "$(dirname "${BASH_SOURCE[0]}")/file_ops.sh"

# Validate ticker parameter
validate_ticker() {
    local ticker="$1"
    
    if [[ -z "$ticker" ]]; then
        log_error "Ticker is required"
        return 1
    fi
    
    local config_file="$CONFIG_DIR/${ticker}.cfg"
    if ! file_exists "$config_file"; then
        log_error "Config file not found: $config_file"
        echo "Available config files:"
        ls -1 "$CONFIG_DIR"/*.cfg 2>/dev/null | \
            sed "s|$CONFIG_DIR/||" | \
            sed 's|\.cfg||' | \
            sort | \
            tr '\n' ' ' && echo ""
        return 1
    fi
    
    return 0
}

# Validate version parameter
validate_version() {
    local version="$1"
    
    if [[ -z "$version" ]]; then
        log_error "Version is required"
        return 1
    fi
    
    # Basic version format validation (vX.Y.Z)
    if ! [[ "$version" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_error "Invalid version format: $version (expected: vX.Y.Z)"
        return 1
    fi
    
    return 0
}

# Export validation functions
export -f validate_ticker
export -f validate_version

