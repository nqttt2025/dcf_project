#!/bin/bash
# Configuration and Constants Module
# Single Responsibility: Manage project configuration and constants

# Prevent direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: config.sh should be sourced, not executed directly"
    exit 1
fi

# Get project root directory (works even if script is symlinked)
get_project_root() {
    local script_dir
    # When sourced from lib/, go up 2 levels; when sourced from scripts/, go up 1 level
    if [[ "${BASH_SOURCE[1]}" == *"/lib/"* ]]; then
        script_dir="$(cd "$(dirname "${BASH_SOURCE[1]}")/.." && pwd)"
    else
        script_dir="$(cd "$(dirname "${BASH_SOURCE[1]}")" && pwd)"
    fi
    echo "$(cd "$script_dir/.." && pwd)"
}

# Initialize project root and script directory
PROJECT_ROOT="${PROJECT_ROOT:-$(get_project_root)}"
SCRIPT_DIR="${SCRIPT_DIR:-$(cd "$(dirname "${BASH_SOURCE[1]}")" && pwd)}"

# Default values
PYTHON="${PYTHON:-python3}"
TEST_DIR="${TEST_DIR:-$PROJECT_ROOT/tests}"
CONFIG_DIR="${CONFIG_DIR:-$PROJECT_ROOT/config}"
DATA_DIR="${DATA_DIR:-$PROJECT_ROOT/data}"
REPORT_DIR="${REPORT_DIR:-$PROJECT_ROOT/reports}"
DOCKER_LOG_DIR="${DOCKER_LOG_DIR:-$PROJECT_ROOT/logs/docker}"
WEB_DIR="${WEB_DIR:-$PROJECT_ROOT/web}"

# Docker constants
DOCKER_IMAGE_PREFIX="${DOCKER_IMAGE_PREFIX:-dcf-project}"
DOCKER_IMAGES="${DOCKER_IMAGES:-gateway dcf stock frontend}"

# Export constants
export PROJECT_ROOT
export SCRIPT_DIR
export PYTHON
export TEST_DIR
export CONFIG_DIR
export DATA_DIR
export REPORT_DIR
export DOCKER_LOG_DIR
export WEB_DIR
export DOCKER_IMAGE_PREFIX
export DOCKER_IMAGES

