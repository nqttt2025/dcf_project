#!/bin/bash
# Docker Utilities Module
# Single Responsibility: Docker-related helper functions

# Prevent direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: docker_utils.sh should be sourced, not executed directly"
    exit 1
fi

# Source dependencies
source "$(dirname "${BASH_SOURCE[0]}")/config.sh"

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

# Export Docker utilities
export -f get_docker_image_name
export -f docker_image_exists
export -f list_docker_images

