#!/bin/bash
# Test scripts - Run various test suites
# Usage: ./scripts/test.sh [ut|ft|st|complete|all|config|cache|result|dcf]
# This script is independent and can be run standalone

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# ============================================================================
# Test Execution Functions
# ============================================================================

run_unit_tests() {
    log_info "Running unit tests..."
    make -C "$TEST_DIR" ut
    check_result
}

run_function_tests() {
    log_info "Running function tests..."
    make -C "$TEST_DIR" ft
    check_result
}

run_system_tests() {
    log_info "Running system tests..."
    make -C "$TEST_DIR" st
    check_result
}

run_complete_tests() {
    log_info "Running complete functionality test..."
    make -C "$TEST_DIR" complete
    check_result
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
    make -C "$TEST_DIR" test-config
    check_result
}

run_cache_tests() {
    make -C "$TEST_DIR" test-cache
    check_result
}

run_result_tests() {
    make -C "$TEST_DIR" test-result
    check_result
}

run_dcf_tests() {
    make -C "$TEST_DIR" test-dcf
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
