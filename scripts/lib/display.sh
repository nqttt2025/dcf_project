#!/bin/bash
# Display Module
# Single Responsibility: Display and formatting functions

# Prevent direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: display.sh should be sourced, not executed directly"
    exit 1
fi

# Print section header
print_section() {
    local title="$1"
    echo ""
    echo "========================================"
    echo "$title"
    echo "========================================"
    echo ""
}

# Print usage information
print_usage() {
    local script_name="$1"
    local usage="$2"
    
    echo "Usage: $script_name $usage"
}

# Print help header
print_help_header() {
    local title="$1"
    echo "$title"
    echo ""
}

# Export display functions
export -f print_section
export -f print_usage
export -f print_help_header

