#!/bin/bash
# Common Library - Main Entry Point
# Loads all modules in correct order
# Single Responsibility: Module loader and initialization

# Prevent direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: common.sh should be sourced, not executed directly"
    echo "Usage: source common.sh"
    exit 1
fi

# Get lib directory
LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load modules in dependency order
source "$LIB_DIR/config.sh"
source "$LIB_DIR/logging.sh"
source "$LIB_DIR/file_ops.sh"
source "$LIB_DIR/validation.sh"
source "$LIB_DIR/error_handler.sh"
source "$LIB_DIR/python_utils.sh"
source "$LIB_DIR/docker_utils.sh"
source "$LIB_DIR/display.sh"
source "$LIB_DIR/version.sh"

