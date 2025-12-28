#!/bin/bash
# DCF Analysis Scripts
# Usage: ./scripts/dcf.sh [single|all|all-fast|help] [TICKER]
# This script is independent and can be run standalone

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# ============================================================================
# Constants
# ============================================================================

DCF_SCRIPT="$PROJECT_ROOT/run_dcf.py"
DCF_ALL_RETRY_SCRIPT="$PROJECT_ROOT/scripts/run_all_dcf_with_retry.py"
DCF_ALL_FAST_SCRIPT="$PROJECT_ROOT/run_all_dcf_main.py"

# ============================================================================
# DCF Analysis Functions
# ============================================================================

run_single_dcf() {
    local ticker="$1"
    
    if ! validate_ticker "$ticker"; then
        exit 1
    fi
    
    log_info "Running DCF analysis for $ticker..."
    run_python "$DCF_SCRIPT" "${ticker}.cfg"
    check_result
    log_success "DCF analysis completed for $ticker"
}

run_all_dcf_with_retry() {
    log_info "Running DCF analysis for all VN30 stocks (with retry & delay for API stability)..."
    run_python "$DCF_ALL_RETRY_SCRIPT"
    check_result
    log_success "DCF analysis completed for all stocks"
}

run_all_dcf_fast() {
    log_warn "Running DCF analysis for all VN30 stocks (fast mode, no retry)..."
    log_warn "Warning: This may fail due to API rate limiting. Use 'all' for stable runs."
    run_python "$DCF_ALL_FAST_SCRIPT"
    check_result
    log_success "DCF analysis completed (fast mode)"
}

# ============================================================================
# Help Function
# ============================================================================

show_help() {
    print_help_header "DCF Analysis Commands"
    echo "Usage: $0 [COMMAND] [TICKER]"
    echo ""
    echo "Commands:"
    echo "  single <TICKER>  - Run DCF analysis for a specific stock"
    echo "  all              - Run DCF analysis for all VN30 stocks (with retry & delay)"
    echo "  all-fast         - Run DCF analysis for all VN30 stocks (fast, no retry)"
    echo "  help             - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 single VNM"
    echo "  $0 single VCB"
    echo "  $0 single FPT"
    echo "  $0 all                 # Recommended: includes retry & delay for API stability"
    echo ""
    echo "Note: 'all' uses retry logic and delays to ensure API stability."
    echo "      Use 'all-fast' only if you need faster execution (may fail due to rate limits)."
    echo ""
    echo "Available tickers (VN30):"
    ls -1 "$CONFIG_DIR"/*.cfg 2>/dev/null | \
        sed "s|$CONFIG_DIR/||" | \
        sed 's|\.cfg||' | \
        sort | \
        tr '\n' ' ' && echo ""
}

# ============================================================================
# Main
# ============================================================================

main() {
    local command="${1:-help}"
    
    case "$command" in
        single)
            local ticker="${2:-}"
            if [[ -z "$ticker" ]]; then
                log_error "Ticker is required for 'single' command"
                show_help
                exit 1
            fi
            run_single_dcf "$ticker"
            ;;
        all)
            run_all_dcf_with_retry
            ;;
        all-fast)
            run_all_dcf_fast
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
