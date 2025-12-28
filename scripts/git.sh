#!/bin/bash
# Git Tag Management Scripts
# Usage: ./scripts/git.sh [tag|tag-patch|tag-minor|tag-major|tag-from-commit|version|help]
# This script is independent and can be run standalone

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# ============================================================================
# Constants
# ============================================================================

CREATE_TAG_SCRIPT="$PROJECT_ROOT/scripts/create_git_tag.sh"
AUTO_VERSION_SCRIPT="$PROJECT_ROOT/scripts/auto_version.sh"
AUTO_TAG_FROM_COMMIT_SCRIPT="$PROJECT_ROOT/scripts/auto_tag_from_commit.sh"

# ============================================================================
# Git Tag Functions
# ============================================================================

create_tag() {
    local version="$1"
    
    if ! validate_version "$version"; then
        exit 1
    fi
    
    log_info "Creating git tag: $version"
    "$CREATE_TAG_SCRIPT" "$version"
    check_result
    log_success "Created tag: $version"
    echo "To push: git push origin $version"
}

create_tag_patch() {
    log_info "Incrementing patch version..."
    local version
    version=$("$AUTO_VERSION_SCRIPT" patch)
    check_result
    log_success "Created tag: $version"
    echo "To push: git push origin $version"
}

create_tag_minor() {
    log_info "Incrementing minor version..."
    local version
    version=$("$AUTO_VERSION_SCRIPT" minor)
    check_result
    log_success "Created tag: $version"
    echo "To push: git push origin $version"
}

create_tag_major() {
    log_info "Incrementing major version..."
    local version
    version=$("$AUTO_VERSION_SCRIPT" major)
    check_result
    log_success "Created tag: $version"
    echo "To push: git push origin $version"
}

create_tag_from_commit() {
    log_info "Creating tag from commit message..."
    local version
    version=$("$AUTO_TAG_FROM_COMMIT_SCRIPT")
    check_result
    log_success "Created tag: $version"
    echo "To push: git push origin $version"
}

show_version() {
    get_version
}

# ============================================================================
# Help Function
# ============================================================================

show_help() {
    print_help_header "Git Tag Management Commands"
    echo "Usage: $0 [COMMAND] [VERSION]"
    echo ""
    echo "Commands:"
    echo "  tag <VERSION>        - Create a git tag"
    echo "  tag-patch            - Auto-increment patch version"
    echo "  tag-minor            - Auto-increment minor version"
    echo "  tag-major            - Auto-increment major version"
    echo "  tag-from-commit     - Create tag from commit message"
    echo "  version              - Show current version"
    echo "  help                 - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 tag v1.0.0"
    echo "  $0 tag-patch"
    echo "  $0 version"
}

# ============================================================================
# Main
# ============================================================================

main() {
    local command="${1:-help}"
    
    case "$command" in
        tag)
            local version="${2:-}"
            if [[ -z "$version" ]]; then
                log_error "Version is required for 'tag' command"
                show_help
                exit 1
            fi
            create_tag "$version"
            ;;
        tag-patch)
            create_tag_patch
            ;;
        tag-minor)
            create_tag_minor
            ;;
        tag-major)
            create_tag_major
            ;;
        tag-from-commit)
            create_tag_from_commit
            ;;
        version)
            show_version
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
