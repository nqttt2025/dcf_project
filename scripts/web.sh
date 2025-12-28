#!/bin/bash
# Web Service Scripts
# Usage: ./scripts/web.sh [start|install|help]
# This script is independent and can be run standalone

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# ============================================================================
# Constants
# ============================================================================

WEB_APP="$WEB_DIR/app.py"
WEB_REQUIREMENTS="$WEB_DIR/requirements.txt"

# ============================================================================
# Web Service Functions
# ============================================================================

start_web_service() {
    log_info "Starting DCF Web Service (Development)..."
    
    if ! file_exists "$WEB_APP"; then
        exit_with_error "Web app not found: $WEB_APP"
    fi
    
    log_info "Open http://localhost:5000 in your browser"
    cd "$WEB_DIR" && "$PYTHON" app.py
}

install_web_dependencies() {
    log_info "Installing web service dependencies..."
    
    if ! file_exists "$WEB_REQUIREMENTS"; then
        exit_with_error "Requirements file not found: $WEB_REQUIREMENTS"
    fi
    
    "$PYTHON" -m pip install -r "$WEB_REQUIREMENTS"
    check_result
    log_success "Web service dependencies installed"
}

# ============================================================================
# Help Function
# ============================================================================

show_help() {
    print_help_header "Web Service Commands"
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start    - Start web service (development, http://localhost:5000)"
    echo "  install  - Install web service dependencies"
    echo "  help     - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 install"
}

# ============================================================================
# Main
# ============================================================================

main() {
    local command="${1:-start}"
    
    case "$command" in
        start)
            start_web_service
            ;;
        install)
            install_web_dependencies
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
