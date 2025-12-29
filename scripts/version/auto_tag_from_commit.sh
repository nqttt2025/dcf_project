#!/bin/bash
# Auto tag from commit message
# Looks for version patterns in commit messages like: [version: v1.0.0] or [release: v1.0.0]

set -e

# Get latest commit message
COMMIT_MSG=$(git log -1 --pretty=%B)

# Try to extract version from commit message
VERSION=$(echo "$COMMIT_MSG" | grep -oE '\[(version|release):\s*v?[0-9]+\.[0-9]+\.[0-9]+\]' | grep -oE 'v?[0-9]+\.[0-9]+\.[0-9]+' | head -1)

if [ -z "$VERSION" ]; then
    # No version found in commit message, use auto increment
    VERSION=$(./scripts/auto_version.sh patch)
    echo "No version in commit message. Auto-incremented to: $VERSION"
else
    # Add 'v' prefix if not present
    if [[ ! "$VERSION" =~ ^v ]]; then
        VERSION="v${VERSION}"
    fi
    
    # Check if tag already exists
    if git rev-parse "$VERSION" >/dev/null 2>&1; then
        echo "Tag $VERSION already exists!"
        exit 1
    fi
    
    # Create tag
    git tag -a "$VERSION" -m "$COMMIT_MSG"
    
    # Sync Docker versions with git tag
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    echo "Syncing Docker versions with git tag: $VERSION"
    "$PROJECT_ROOT/scripts/version/docker_version.sh" sync-git >/dev/null 2>&1 || true
    
    echo "✓ Created tag: $VERSION from commit message"
    echo "✓ Docker versions synced"
fi

echo "$VERSION"

