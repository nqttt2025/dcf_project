#!/bin/bash
# Base Script Class
# Single Responsibility: Provide base functionality for all scripts
# Open/Closed Principle: Open for extension, closed for modification

# Prevent direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: base_script.sh should be sourced, not executed directly"
    exit 1
fi

# Note: base_script.sh is loaded by common.sh, so we don't need to source common.sh here
# This prevents circular dependency

# Base script initialization
init_script() {
    local script_name="${1:-$(basename "${BASH_SOURCE[1]}")}"
    export SCRIPT_NAME="$script_name"
}

# Standard help function template
show_help_template() {
    local title="$1"
    local usage="$2"
    local commands="$3"
    
    print_help_header "$title"
    echo "Usage: $SCRIPT_NAME $usage"
    echo ""
    echo "$commands"
    echo ""
    echo "  help     - Show this help message"
}

# Standard main function template
main_template() {
    local command="${1:-help}"
    local handler_func="$2"
    
    case "$command" in
        help|--help|-h)
            shift
            eval "$handler_func" "$@"
            ;;
        *)
            if ! eval "$handler_func" "$command" "$@"; then
                log_error "Unknown command: $command"
                exit 1
            fi
            ;;
    esac
}

# Export base script functions
export -f init_script
export -f show_help_template
export -f main_template

