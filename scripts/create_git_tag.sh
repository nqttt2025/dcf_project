#!/bin/bash
# Create git tag for versioning

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 v1.0.0"
    exit 1
fi

VERSION=$1

# Remove 'v' prefix if present
VERSION_TAG="${VERSION#v}"

# Check if tag already exists
if git rev-parse "$VERSION" >/dev/null 2>&1; then
    echo "Tag $VERSION already exists!"
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
git tag -a "$VERSION" -m "Release version $VERSION_TAG"

echo "Created tag: $VERSION"
echo "To push tag: git push origin $VERSION"

