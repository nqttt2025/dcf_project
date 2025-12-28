#!/bin/bash
# Linting Scripts
# Usage: ./scripts/lint.sh [pylint|flake8|all]
# This script is independent and can be run standalone

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# ============================================================================
# Constants
# ============================================================================

PYTHON_LIB_PATH="src"
PYTHON_CHECK_DIR="src tests"
PYLINT_DIR="$REPORT_DIR/pylint"
PYLINT_IGNORE_WARN="W1514,W1202,W0703,W0511,W0102,W0201,W1203,W0120"
PYLINT_LEVEL="-E"

# ============================================================================
# Linting Functions
# ============================================================================

run_pylint() {
    log_info "Running pylint..."
    ensure_dir "$PYLINT_DIR"
    
    "$PYTHON" -m pylint --version |& tee "$PYLINT_DIR/pylint.log"
    
    local pythonpath
    pythonpath=$(echo "$PYTHON_LIB_PATH" | tr ' ' ':')
    env PYTHONPATH="$pythonpath:$PYTHONPATH" \
        "$PYTHON" -m pylint -v -j 0 $PYLINT_LEVEL \
        $(find $PYTHON_CHECK_DIR -type f -name "*.py") \
        |& tee -a "$PYLINT_DIR/pylint.log"
    
    log_success "Pylint log: $(realpath "$PYLINT_DIR")/pylint.log"
}

run_flake8() {
    log_info "Running flake8..."
    if ! "$PYTHON" -m flake8 --version >/dev/null 2>&1; then
        log_warn "flake8 not installed, skipping..."
        return 0
    fi
    
    "$PYTHON" -m flake8 $PYTHON_CHECK_DIR \
        --max-line-length=120 \
        --ignore=E501,W503 || true
}

run_all_linters() {
    log_info "Running all linters..."
    run_pylint
    echo ""
    run_flake8
    echo ""
    log_success "Linting completed"
}

# ============================================================================
# Help Function
# ============================================================================

show_help() {
    print_help_header "Linting Script"
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  pylint  - Run pylint only"
    echo "  flake8  - Run flake8 only"
    echo "  all     - Run all linters (default)"
    echo "  help    - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 all"
    echo "  $0 pylint"
    echo "  $0 flake8"
}

# ============================================================================
# Main
# ============================================================================

main() {
    local command="${1:-all}"
    
    case "$command" in
        pylint)
            run_pylint
            ;;
        flake8)
            run_flake8
            ;;
        all)
            run_all_linters
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
