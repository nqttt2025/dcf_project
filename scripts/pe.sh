#!/bin/bash
# PE Calculation Scripts
# Usage: ./scripts/pe.sh [single|all|help] [TICKER] [INDUSTRY]
# This script is independent and can be run standalone

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# ============================================================================
# Constants
# ============================================================================

PE_SCRIPT="$PROJECT_ROOT/scripts/calculate_pe.py"

# ============================================================================
# PE Calculation Functions
# ============================================================================

run_single_pe() {
    local ticker="$1"
    local industry="${2:-}"
    
    if [[ -z "$ticker" ]]; then
        log_error "Ticker is required"
        show_help
        exit 1
    fi
    
    log_info "Calculating PE for $ticker"
    if [[ -n "$industry" ]]; then
        run_python "$PE_SCRIPT" "$ticker" "$industry" || true
    else
        run_python "$PE_SCRIPT" "$ticker" || true
    fi
}

run_all_pe() {
    log_info "Analyzing PE for all VN30 stocks..."
    run_python "$PE_SCRIPT"
    check_result
    log_success "PE analysis completed for all stocks"
}

# ============================================================================
# Help Function
# ============================================================================

show_help() {
    print_help_header "PE Calculation Commands"
    echo "Usage: $0 [COMMAND] [TICKER] [INDUSTRY]"
    echo ""
    echo "Commands:"
    echo "  single <TICKER> [INDUSTRY]  - Calculate PE for a specific stock"
    echo "  all                         - Analyze all VN30 stocks"
    echo "  help                         - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 single VNM"
    echo "  $0 single VCB banking"
    echo "  $0 single FPT technology"
    echo "  $0 all"
    echo ""
    echo "Available industries:"
    echo "  - banking      (Ngân hàng)"
    echo "  - real_estate  (Bất động sản)"
    echo "  - technology   (Công nghệ)"
    echo "  - consumer     (Tiêu dùng)"
    echo "  - energy       (Năng lượng)"
    echo "  - industrial   (Công nghiệp)"
    echo "  - aviation     (Hàng không)"
}

# ============================================================================
# Main
# ============================================================================

main() {
    local command="${1:-help}"
    
    case "$command" in
        single)
            local ticker="${2:-}"
            local industry="${3:-}"
            if [[ -z "$ticker" ]]; then
                log_error "Ticker is required for 'single' command"
                show_help
                exit 1
            fi
            run_single_pe "$ticker" "$industry"
            ;;
        all)
            run_all_pe
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
