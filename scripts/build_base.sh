#!/bin/bash
# Build Base Image Script
# Force rebuild base image after dependency updates
# Usage: ./scripts/build_base.sh [--no-cache]

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get base version
BASE_VERSION=$("$PROJECT_ROOT/scripts/docker_version.sh" get base 2>/dev/null || echo "latest")

# Check for --no-cache flag
NO_CACHE_FLAG=""
if [[ "${1:-}" == "--no-cache" ]]; then
    NO_CACHE_FLAG="--no-cache"
    log_info "Building base image with --no-cache flag"
fi

log_info "Building base image..."
log_info "Base version: $BASE_VERSION"
log_info "Requirements file: services/common/requirements.txt"

# Enable BuildKit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build base image
if BASE_VERSION="$BASE_VERSION" docker-compose build $NO_CACHE_FLAG base; then
    log_success "Base image built successfully"
    
    # Tag base image with version only (no latest tag)
    # Version tag is sufficient and clearer
    if docker_image_exists "dcf-project-base" "latest"; then
        docker tag "dcf-project-base:latest" "dcf-project-base:$BASE_VERSION" || true
        log_info "Tagged as: dcf-project-base:$BASE_VERSION"
    fi
    
    # Update hash after successful build
    "$PROJECT_ROOT/scripts/docker_version.sh" update base >/dev/null 2>&1 || true
    log_success "Updated requirements hash in docker-versions.json"
    
    log_info ""
    log_info "✅ Base image rebuild completed!"
    log_info "   Image: dcf-project-base:$BASE_VERSION"
    log_info ""
    log_info "Next steps:"
    log_info "   1. Rebuild service images: make docker-build"
    log_info "   2. Or rebuild all: make docker-rebuild"
else
    log_error "Failed to build base image"
    exit 1
fi

