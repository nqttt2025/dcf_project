#!/bin/bash
# Get version from git tag or generate one

# Try to get latest git tag
GIT_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

if [ -z "$GIT_TAG" ]; then
    # No tag exists, generate version from commit hash
    GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null)
    if [ -z "$GIT_COMMIT" ]; then
        # Not a git repo, use timestamp
        VERSION="dev-$(date +%Y%m%d-%H%M%S)"
    else
        VERSION="dev-${GIT_COMMIT}"
    fi
else
    # Use git tag
    VERSION="${GIT_TAG}"
    
    # Check if there are uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        VERSION="${VERSION}-dirty"
    fi
fi

echo "$VERSION"

