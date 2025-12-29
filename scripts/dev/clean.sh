#!/bin/bash
# Cleanup Scripts
# Usage: ./scripts/clean.sh [reports|cache|logs|results|data|all|full]
# This script is independent and can be run standalone

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$PROJECT_ROOT/scripts/lib/common.sh"
init_script "$(basename "${BASH_SOURCE[0]}")"

# ============================================================================
# Cleanup Functions
# ============================================================================

clean_reports() {
    log_info "Cleaning reports..."
    rm -rf "$REPORT_DIR"
    rm -f "$PROJECT_ROOT/test-pylint.log"
    log_success "Reports cleaned"
}

clean_cache() {
    log_info "Cleaning cache files..."
    clean_python_cache
    log_success "Cache cleaned"
}

clean_logs() {
    log_info "Cleaning log files..."
    clean_log_files
    log_success "Logs cleaned"
}

clean_results() {
    log_info "Cleaning result files..."
    rm -rf "$DATA_DIR/results"/*.json "$DATA_DIR/results"/*.text 2>/dev/null || true
    log_success "Results cleaned"
}

clean_data() {
    log_info "Cleaning data cache..."
    rm -rf "$DATA_DIR/cache"/*.json 2>/dev/null || true
    log_success "Data cache cleaned"
}

clean_all() {
    log_info "Cleaning all generated files..."
    clean_reports
    clean_cache
    clean_logs
    log_success "Cleanup completed"
}

clean_full() {
    log_info "Full cleanup (including data and results)..."
    clean_reports
    clean_cache
    clean_logs
    clean_results
    clean_data
    log_success "Full cleanup completed"
}

# ============================================================================
# Help Function
# ============================================================================

show_help() {
    print_help_header "Cleanup Script"
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  reports  - Clean report files"
    echo "  cache    - Clean Python cache files"
    echo "  logs     - Clean log files"
    echo "  results  - Clean result files"
    echo "  data     - Clean data cache"
    echo "  all      - Clean all generated files (default)"
    echo "  full     - Full cleanup including data and results"
    echo "  help     - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 all"
    echo "  $0 cache"
    echo "  $0 full"
}

# ============================================================================
# Main
# ============================================================================

main() {
    local command="${1:-all}"
    
    case "$command" in
        reports)
            clean_reports
            ;;
        cache)
            clean_cache
            ;;
        logs)
            clean_logs
            ;;
        results)
            clean_results
            ;;
        data)
            clean_data
            ;;
        all)
            clean_all
            ;;
        full)
            clean_full
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
