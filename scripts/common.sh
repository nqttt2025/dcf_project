#!/bin/bash
# Common Library - Backward Compatibility Wrapper
# This file maintains backward compatibility with old scripts
# New scripts should use scripts/lib/common.sh instead

# Prevent direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: common.sh should be sourced, not executed directly"
    echo "Usage: source common.sh"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load new common library
source "$SCRIPT_DIR/lib/common.sh"

# This wrapper ensures backward compatibility
# All functions from lib/common.sh are already exported
