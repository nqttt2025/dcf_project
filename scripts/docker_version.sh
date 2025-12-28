#!/bin/bash
# Docker Version Management Script
# Manages versions for Docker images, including base image
# Usage: ./scripts/docker_version.sh [get|set|check-base|update|sync-git]

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# ============================================================================
# Constants
# ============================================================================

VERSIONS_FILE="$PROJECT_ROOT/docker-versions.json"
REQUIREMENTS_FILE="$PROJECT_ROOT/services/common/requirements.txt"

# ============================================================================
# Version Management Functions
# ============================================================================

# Get hash of requirements.txt
get_requirements_hash() {
    if [[ -f "$REQUIREMENTS_FILE" ]]; then
        sha256sum "$REQUIREMENTS_FILE" | awk '{print $1}'
    else
        echo ""
    fi
}

# Read version from JSON file
get_version() {
    local service="${1:-base}"
    
    if [[ ! -f "$VERSIONS_FILE" ]]; then
        log_error "Version file not found: $VERSIONS_FILE"
        return 1
    fi
    
    if [[ "$service" == "base" ]]; then
        python3 -c "import json; print(json.load(open('$VERSIONS_FILE'))['base']['current'])" 2>/dev/null || echo ""
    else
        python3 -c "import json; print(json.load(open('$VERSIONS_FILE'))['services']['$service']['current'])" 2>/dev/null || echo ""
    fi
}

# Set Docker version in JSON file (Docker-specific versions)
set_docker_version() {
    local service="$1"
    local version="$2"
    
    if [[ ! -f "$VERSIONS_FILE" ]]; then
        log_error "Version file not found: $VERSIONS_FILE"
        return 1
    fi
    
    python3 << EOF
import json
import sys
from datetime import datetime

with open('$VERSIONS_FILE', 'r') as f:
    data = json.load(f)

if '$service' == 'base':
    data['base']['current'] = '$version'
    data['base']['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
else:
    data['services']['$service']['current'] = '$version'

with open('$VERSIONS_FILE', 'w') as f:
    json.dump(data, f, indent=2)
EOF
    check_result
}

# Alias for backward compatibility
set_version() {
    set_docker_version "$@"
}

# Check if base image needs rebuild
check_base_needs_rebuild() {
    local current_hash
    current_hash=$(get_requirements_hash)
    
    if [[ -z "$current_hash" ]]; then
        log_error "Cannot get requirements hash"
        return 1
    fi
    
    local stored_hash
    stored_hash=$(python3 -c "import json; print(json.load(open('$VERSIONS_FILE'))['base'].get('last_requirements_hash', ''))" 2>/dev/null || echo "")
    
    if [[ "$current_hash" != "$stored_hash" ]]; then
        log_info "Base image needs rebuild (requirements.txt changed)"
        return 0  # Needs rebuild
    else
        log_info "Base image unchanged, no rebuild needed"
        return 1  # No rebuild needed
    fi
}

# Update base image hash after rebuild
update_base_hash() {
    local new_hash
    new_hash=$(get_requirements_hash)
    
    python3 << EOF
import json
from datetime import datetime

with open('$VERSIONS_FILE', 'r') as f:
    data = json.load(f)

data['base']['last_requirements_hash'] = '$new_hash'
data['base']['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

with open('$VERSIONS_FILE', 'w') as f:
    json.dump(data, f, indent=2)
EOF
    check_result
    log_success "Updated base image hash"
}

# Get all service versions
get_all_versions() {
    if [[ ! -f "$VERSIONS_FILE" ]]; then
        log_error "Version file not found: $VERSIONS_FILE"
        return 1
    fi
    
    python3 << EOF
import json

with open('$VERSIONS_FILE', 'r') as f:
    data = json.load(f)

print("Base Image:")
print(f"  Version: {data['base']['current']}")
print(f"  Last Updated: {data['base'].get('last_updated', 'N/A')}")
print(f"  Requirements Hash: {data['base'].get('last_requirements_hash', 'N/A')[:16]}...")
print()
print("Services:")
for service, info in data['services'].items():
    depends = "✓" if info.get('depends_on_base', False) else "✗"
    print(f"  {service:12} Version: {info['current']:10} Depends on base: {depends}")
EOF
}

# Sync versions with git tag
# Git tag is the single source of truth for project version
sync_with_git_tag() {
    # Get project version from git tag (single source of truth)
    local git_version
    git_version=$("$PROJECT_ROOT/scripts/get_version.sh")
    
    # Remove -dirty suffix if present
    git_version="${git_version%-dirty}"
    
    if [[ -z "$git_version" ]] || [[ "$git_version" =~ ^dev- ]]; then
        log_warn "No git tag found or using dev version: $git_version"
        log_warn "Service versions will not be updated"
        return 0
    fi
    
    log_info "Syncing Docker versions with git tag: $git_version"
    
    # Base image version: Only update if requirements.txt changed
    # Otherwise keep current base version (independent versioning)
    local base_version
    base_version=$(get_docker_version "base")
    
    if check_base_needs_rebuild; then
        # Requirements changed - increment base version
        log_info "Base image needs rebuild (requirements.txt changed)"
        increment_base_version >/dev/null 2>&1
        base_version=$(get_docker_version "base")
        log_info "Base image version incremented to: $base_version"
    else
        log_info "Base image unchanged, keeping version: $base_version"
    fi
    
    # Update all service versions to match git tag
    for service in gateway dcf stock frontend; do
        set_docker_version "$service" "$git_version"
    done
    
    log_success "Service versions synced with git tag: $git_version"
    log_info "Base image version: $base_version (independent)"
}

# Increment base version (only when requirements.txt changes)
increment_base_version() {
    local current_version
    current_version=$(get_docker_version "base")
    
    if [[ -z "$current_version" ]]; then
        log_error "Cannot get current base version"
        return 1
    fi
    
    # Extract version parts (v1.0.0 -> 1.0.0)
    local version_part="${current_version#v}"
    local major minor patch
    IFS='.' read -r major minor patch <<< "$version_part"
    
    # Increment patch
    patch=$((patch + 1))
    local new_version="v${major}.${minor}.${patch}"
    
    set_docker_version "base" "$new_version"
    update_base_hash
    
    log_success "Base version incremented: $current_version -> $new_version"
    echo "$new_version"
}

# ============================================================================
# Commands
# ============================================================================

cmd_get() {
    local service="${1:-all}"
    
    if [[ "$service" == "all" ]]; then
        get_all_versions
        echo ""
        echo "Project Version (from git tag):"
        local project_version
        project_version=$("$PROJECT_ROOT/scripts/get_version.sh")
        echo "  $project_version"
    elif [[ "$service" == "project" ]]; then
        # Get project version from git tag
        "$PROJECT_ROOT/scripts/get_version.sh"
    else
        local version
        version=$(get_docker_version "$service")
        if [[ -n "$version" ]]; then
            echo "$version"
        else
            log_error "Cannot get version for service: $service"
            exit 1
        fi
    fi
}

cmd_set() {
    local service="$1"
    local version="$2"
    
    if [[ -z "$service" ]] || [[ -z "$version" ]]; then
        log_error "Usage: $0 set <service> <version>"
        exit 1
    fi
    
    if [[ "$service" == "project" ]]; then
        log_error "Cannot set project version directly. Use git tag instead:"
        log_error "  make git-tag VERSION=$version"
        exit 1
    fi
    
    set_docker_version "$service" "$version"
    log_success "Set $service version to $version"
}

cmd_check_base() {
    if check_base_needs_rebuild; then
        echo "rebuild"
        exit 0
    else
        echo "no-rebuild"
        exit 1
    fi
}

cmd_update() {
    local service="${1:-base}"
    
    if [[ "$service" == "base" ]]; then
        increment_base_version
    else
        # Get project version from git tag (single source of truth)
        local git_version
        git_version=$("$PROJECT_ROOT/scripts/get_version.sh")
        git_version="${git_version%-dirty}"  # Remove -dirty suffix
        
        if [[ -n "$git_version" ]] && [[ ! "$git_version" =~ ^dev- ]]; then
            set_docker_version "$service" "$git_version"
            log_success "Updated $service to $git_version"
        else
            log_error "Cannot get valid git version: $git_version"
            log_error "Create a git tag first: make git-tag VERSION=v1.0.0"
            exit 1
        fi
    fi
}

cmd_sync_git() {
    sync_with_git_tag
}

# ============================================================================
# Help Function
# ============================================================================

show_help() {
    print_help_header "Docker Version Management"
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  get [service]     - Get version for service (default: all)"
    echo "  set <service> <version> - Set version for service"
    echo "  check-base        - Check if base image needs rebuild"
    echo "  update [service]  - Update version (base: increment, services: sync with git)"
    echo "  sync-git          - Sync all versions with git tag"
    echo "  help              - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 get                    # Show all versions"
    echo "  $0 get base               # Get base version"
    echo "  $0 get gateway            # Get gateway version"
    echo "  $0 set base v1.1.0        # Set base version"
    echo "  $0 check-base             # Check if base needs rebuild"
    echo "  $0 sync-git               # Sync with git tag"
}

# ============================================================================
# Main
# ============================================================================

main() {
    local command="${1:-help}"
    
    case "$command" in
        get)
            cmd_get "${2:-all}"
            ;;
        set)
            cmd_set "$2" "$3"
            ;;
        check-base)
            cmd_check_base
            ;;
        update)
            cmd_update "${2:-base}"
            ;;
        sync-git)
            cmd_sync_git
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

