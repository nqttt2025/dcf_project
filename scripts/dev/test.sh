#!/bin/bash
# Test scripts - Run various test suites
# Usage: ./scripts/test.sh [ut|ft|st|complete|all|config|cache|result|dcf]
# This script is independent and can be run standalone

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/scripts/lib/common.sh"

# Initialize script
init_script "$(basename "${BASH_SOURCE[0]}")"

# ============================================================================
# Test Execution Functions
# ============================================================================

run_unit_tests() {
    log_info "Running unit tests..."
    cd "$PROJECT_ROOT"
    export PYTHONPATH="src:${PYTHONPATH:-}"
    python3 tests/ut/run_ut
    check_result
}

run_function_tests() {
    log_info "Running function tests..."
    cd "$PROJECT_ROOT"
    export PYTHONPATH="src:${PYTHONPATH:-}"
    python3 -m unittest discover -s tests/ft -p "test_*.py" -v
    check_result
}

run_system_tests() {
    log_info "Running system tests..."
    cd "$PROJECT_ROOT"
    export PYTHONPATH="src:${PYTHONPATH:-}"
    python3 -m unittest discover -s tests/st -p "test_*.py" -v
    check_result
}

run_complete_tests() {
    log_info "Running complete functionality test..."
    cd "$PROJECT_ROOT"
    export PYTHONPATH="src:${PYTHONPATH:-}"
    python3 tests/test_dcf_complete.py || log_warn "Complete test failed (may require external API access)"
}

run_all_tests() {
    log_info "Running all tests..."
    run_unit_tests
    run_function_tests
    run_system_tests
    run_complete_tests
    log_success "All tests completed"
}

run_config_tests() {
    cd "$PROJECT_ROOT"
    export PYTHONPATH="src:${PYTHONPATH:-}"
    python3 -m unittest tests.ut.test_config_manager -v
    check_result
}

run_cache_tests() {
    cd "$PROJECT_ROOT"
    export PYTHONPATH="src:${PYTHONPATH:-}"
    python3 -m unittest tests.ut.test_cache_manager -v
    check_result
}

run_result_tests() {
    cd "$PROJECT_ROOT"
    export PYTHONPATH="src:${PYTHONPATH:-}"
    python3 -m unittest tests.ut.test_result_manager -v
    check_result
}

run_dcf_tests() {
    cd "$PROJECT_ROOT"
    export PYTHONPATH="src:${PYTHONPATH:-}"
    python3 -m unittest tests.ut.test_dcf_calculator -v
    check_result
}

# ============================================================================
# Help Function
# ============================================================================

show_help() {
    print_help_header "Test Script - Run various test suites"
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  ut       - Run unit tests"
    echo "  ft       - Run function tests"
    echo "  st       - Run system tests"
    echo "  complete - Run complete functionality test"
    echo "  all      - Run all tests"
    echo "  config   - Run ConfigManager tests"
    echo "  cache    - Run CacheManager tests"
    echo "  result   - Run ResultManager tests"
    echo "  dcf      - Run DCFCalculator tests"
    echo "  help     - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 ut"
    echo "  $0 all"
    echo "  $0 config"
}

# ============================================================================
# Main
# ============================================================================

main() {
    local command="${1:-ut}"
    
    case "$command" in
        ut)
            run_unit_tests
            ;;
        ft)
            run_function_tests
            ;;
        st)
            run_system_tests
            ;;
        complete)
            run_complete_tests
            ;;
        all)
            run_all_tests
            ;;
        config)
            run_config_tests
            ;;
        cache)
            run_cache_tests
            ;;
        result)
            run_result_tests
            ;;
        dcf)
            run_dcf_tests
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
