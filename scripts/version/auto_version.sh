#!/bin/bash
# Auto versioning script - Automatically increments version and creates git tag
# Also syncs Docker versions

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

# Source common utilities
source "$PROJECT_ROOT/scripts/lib/common.sh"

# Get current version from git tag
CURRENT_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$CURRENT_TAG" ]; then
    # No tag exists, start with v1.0.0
    NEW_VERSION="v1.0.0"
    echo "No existing tag found. Starting with $NEW_VERSION"
else
    # Parse version (remove 'v' prefix)
    VERSION_NUM="${CURRENT_TAG#v}"
    
    # Determine increment type (major, minor, patch)
    INCREMENT_TYPE="${1:-patch}"
    
    # Split version into parts
    IFS='.' read -ra VERSION_PARTS <<< "$VERSION_NUM"
    MAJOR="${VERSION_PARTS[0]:-0}"
    MINOR="${VERSION_PARTS[1]:-0}"
    PATCH="${VERSION_PARTS[2]:-0}"
    
    # Increment version based on type
    case "$INCREMENT_TYPE" in
        major)
            MAJOR=$((MAJOR + 1))
            MINOR=0
            PATCH=0
            ;;
        minor)
            MINOR=$((MINOR + 1))
            PATCH=0
            ;;
        patch|*)
            PATCH=$((PATCH + 1))
            ;;
    esac
    
    NEW_VERSION="v${MAJOR}.${MINOR}.${PATCH}"
fi

# Check if tag already exists
if git rev-parse "$NEW_VERSION" >/dev/null 2>&1; then
    echo "Tag $NEW_VERSION already exists!"
    exit 1
fi

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "Warning: You have uncommitted changes!"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create tag
git tag -a "$NEW_VERSION" -m "Release version $NEW_VERSION"

# Sync Docker versions with new git tag
echo "Syncing Docker versions with git tag: $NEW_VERSION"
    "$PROJECT_ROOT/scripts/version/docker_version.sh" sync-git >/dev/null 2>&1 || true

echo "✓ Created tag: $NEW_VERSION"
echo "✓ Docker versions synced"
echo "To push tag: git push origin $NEW_VERSION"
echo "$NEW_VERSION"
