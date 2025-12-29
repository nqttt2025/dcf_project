#!/bin/bash
# Version Management Module
# Single Responsibility: Version-related functions

# Prevent direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: version.sh should be sourced, not executed directly"
    exit 1
fi

# Source dependencies
source "$(dirname "${BASH_SOURCE[0]}")/config.sh"

# Get current project version from git tag (single source of truth)
# This is the main version used for Docker service images
get_project_version() {
    "$PROJECT_ROOT/scripts/utils/get_version.sh"
}

# Alias for backward compatibility
get_version() {
    get_project_version
}

# Export version functions
export -f get_project_version
export -f get_version

