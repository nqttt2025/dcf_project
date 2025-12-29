#!/bin/bash
# Create a git tag and sync Docker versions
# Usage: ./scripts/create_git_tag.sh <version>

set -e

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Error: Version is required"
    echo "Usage: ./scripts/create_git_tag.sh <version>"
    exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

# Source common utilities
source "$PROJECT_ROOT/scripts/lib/common.sh"

# Check if tag already exists
if git rev-parse "$VERSION" >/dev/null 2>&1; then
    log_error "Tag $VERSION already exists!"
    exit 1
fi

# Create git tag
git tag "$VERSION"

# Sync Docker versions with git tag
log_info "Syncing Docker versions with git tag: $VERSION"
"$PROJECT_ROOT/scripts/version/docker_version.sh" sync-git

# Push tag to remote (optional)
echo "Tag created: $VERSION"
echo "Docker versions synced"
echo "To push: git push origin $VERSION"
