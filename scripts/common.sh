#!/bin/bash
# Common utilities and functions for DCF Project scripts
# This file should be sourced by other scripts, not executed directly
# Usage: source "$(dirname "$0")/common.sh" or source "$SCRIPT_DIR/common.sh"

# Prevent direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: common.sh should be sourced, not executed directly"
    echo "Usage: source common.sh"
    exit 1
fi

# ============================================================================
# Constants
# ============================================================================

# Get project root directory (works even if script is symlinked)
get_project_root() {
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[1]}")" && pwd)"
    echo "$(cd "$script_dir/.." && pwd)"
}

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

# ============================================================================
# Logging Functions
# ============================================================================

# Log to file with timestamp
log_to_file() {
    local log_file="$1"
    shift
    local message="$*"
    
    mkdir -p "$(dirname "$log_file")"
    echo "$message" | tee -a "$log_file"
}

# Log with timestamp
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $*"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
}

log_warn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARN: $*"
}

log_success() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✓ $*"
}

# ============================================================================
# Version Management
# ============================================================================

# Get current project version from git tag (single source of truth)
# This is the main version used for Docker service images
get_project_version() {
    "$PROJECT_ROOT/scripts/get_version.sh"
}

# Alias for backward compatibility
get_version() {
    get_project_version
}

# ============================================================================
# File/Directory Operations
# ============================================================================

# Check if file exists
file_exists() {
    [[ -f "$1" ]]
}

# Check if directory exists
dir_exists() {
    [[ -d "$1" ]]
}

# Ensure directory exists
ensure_dir() {
    local dir="$1"
    if ! dir_exists "$dir"; then
        mkdir -p "$dir"
        log_info "Created directory: $dir"
    fi
}

# ============================================================================
# Docker Helper Functions
# ============================================================================

# Get Docker image name
get_docker_image_name() {
    local service="$1"
    echo "${DOCKER_IMAGE_PREFIX}-${service}"
}

# Check if Docker image exists
docker_image_exists() {
    local image_name="$1"
    local tag="${2:-latest}"
    docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${image_name}:${tag}"
}

# List Docker images for a service
list_docker_images() {
    local service="$1"
    local image_name
    image_name=$(get_docker_image_name "$service")
    docker images --format "{{.Repository}}:{{.Tag}} {{.Size}} {{.CreatedAt}}" | \
        grep "^${image_name}:" | head -10
}

# ============================================================================
# Python Helper Functions
# ============================================================================

# Check if Python command exists
python_exists() {
    command -v "$PYTHON" >/dev/null 2>&1
}

# Run Python script with error handling
run_python() {
    local script="$1"
    shift
    
    if ! python_exists; then
        log_error "Python not found: $PYTHON"
        return 1
    fi
    
    if ! file_exists "$script"; then
        log_error "Python script not found: $script"
        return 1
    fi
    
    "$PYTHON" "$script" "$@"
}

# ============================================================================
# Validation Functions
# ============================================================================

# Validate ticker parameter
validate_ticker() {
    local ticker="$1"
    
    if [[ -z "$ticker" ]]; then
        log_error "Ticker is required"
        return 1
    fi
    
    local config_file="$CONFIG_DIR/${ticker}.cfg"
    if ! file_exists "$config_file"; then
        log_error "Config file not found: $config_file"
        echo "Available config files:"
        ls -1 "$CONFIG_DIR"/*.cfg 2>/dev/null | \
            sed "s|$CONFIG_DIR/||" | \
            sed 's|\.cfg||' | \
            sort | \
            tr '\n' ' ' && echo ""
        return 1
    fi
    
    return 0
}

# Validate version parameter
validate_version() {
    local version="$1"
    
    if [[ -z "$version" ]]; then
        log_error "Version is required"
        return 1
    fi
    
    # Basic version format validation (vX.Y.Z)
    if ! [[ "$version" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_error "Invalid version format: $version (expected: vX.Y.Z)"
        return 1
    fi
    
    return 0
}

# ============================================================================
# Error Handling
# ============================================================================

# Exit with error message
exit_with_error() {
    log_error "$@"
    exit 1
}

# Check command result and exit on error
check_result() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        exit_with_error "Command failed with exit code: $exit_code"
    fi
}

# ============================================================================
# Display Functions
# ============================================================================

# Print section header
print_section() {
    local title="$1"
    echo ""
    echo "========================================"
    echo "$title"
    echo "========================================"
    echo ""
}

# Print usage information
print_usage() {
    local script_name="$1"
    local usage="$2"
    
    echo "Usage: $script_name $usage"
}

# Print help header
print_help_header() {
    local title="$1"
    echo "$title"
    echo ""
}

# ============================================================================
# Cleanup Functions
# ============================================================================

# Clean Python cache files
clean_python_cache() {
    log_info "Cleaning Python cache files..."
    find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_ROOT" -type f -name "*.pyc" -delete 2>/dev/null || true
    find "$PROJECT_ROOT" -type f -name "*.pyo" -delete 2>/dev/null || true
    log_success "Python cache cleaned"
}

# Clean log files
clean_log_files() {
    log_info "Cleaning log files..."
    find "$PROJECT_ROOT" -type f -name "*.log" -delete 2>/dev/null || true
    rm -rf "$PROJECT_ROOT/log/*.log" 2>/dev/null || true
    log_success "Log files cleaned"
}

# ============================================================================
# Export functions that should be available to other scripts
# ============================================================================

export -f get_project_root
export -f log_to_file
export -f log_info
export -f log_error
export -f log_warn
export -f log_success
export -f get_version
export -f file_exists
export -f dir_exists
export -f ensure_dir
export -f get_docker_image_name
export -f docker_image_exists
export -f list_docker_images
export -f python_exists
export -f run_python
export -f validate_ticker
export -f validate_version
export -f exit_with_error
export -f check_result
export -f print_section
export -f print_usage
export -f print_help_header
export -f clean_python_cache
export -f clean_log_files

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

