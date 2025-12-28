#!/bin/bash
# Docker Management Scripts
# Usage: ./scripts/docker.sh [build|rebuild|up|down|logs|clean|clean-all|ps|...]
# This script is independent and can be run standalone

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# ============================================================================
# Docker-specific Functions
# ============================================================================

docker_build_images() {
    local version="$1"
    local log_file="$2"
    
    log_to_file "$log_file" "Building images with tag: $version"
    VERSION="$version" docker-compose build 2>&1 | tee -a "$log_file"
    return $?
}

docker_tag_images() {
    local version="$1"
    local log_file="$2"
    
    log_to_file "$log_file" "Tagging images with version $version and latest..."
    for img in $DOCKER_IMAGES; do
        local image_name
        image_name=$(get_docker_image_name "$img")
        if docker_image_exists "$image_name" "$version"; then
            docker tag "${image_name}:${version}" "${image_name}:latest" 2>&1 | tee -a "$log_file" || true
        elif docker_image_exists "$image_name" "latest"; then
            docker tag "${image_name}:latest" "${image_name}:${version}" 2>&1 | tee -a "$log_file" || true
        fi
    done
}

docker_remove_old_images() {
    local version="$1"
    local log_file="$2"
    
    log_to_file "$log_file" "Removing old versioned images..."
    for img in $DOCKER_IMAGES; do
        local image_name
        image_name=$(get_docker_image_name "$img")
        docker images --format "{{.Repository}}:{{.Tag}}" | \
            grep "^${image_name}:" | \
            grep -v "$version" | \
            xargs -r docker rmi -f 2>&1 | tee -a "$log_file" || true
    done
}

docker_cleanup_after_build() {
    local log_file="$1"
    
    log_to_file "$log_file" ""
    log_to_file "$log_file" "Cleaning up unused images and containers..."
    docker-compose down --remove-orphans 2>&1 | tee -a "$log_file" || true
    docker image prune -f --filter "dangling=true" 2>&1 | tee -a "$log_file" || true
}

# ============================================================================
# Docker Commands
# ============================================================================

cmd_build() {
    local version
    version=$(get_version)
    local log_file="$DOCKER_LOG_DIR/docker-build-$(date +%Y%m%d-%H%M%S).log"
    
    log_to_file "$log_file" "Building Docker images for microservices..."
    log_to_file "$log_file" "Version: $version"
    log_to_file "$log_file" "Log file: $log_file"
    log_to_file "$log_file" "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    log_to_file "$log_file" "========================================"
    
    docker_remove_old_images "$version" "$log_file"
    
    if docker_build_images "$version" "$log_file"; then
        docker_tag_images "$version" "$log_file"
    fi
    
    docker_cleanup_after_build "$log_file"
    
    log_to_file "$log_file" "✓ Build completed and cleanup done"
    log_to_file "$log_file" "Version: $version"
    log_to_file "$log_file" "Log saved to: $log_file"
}

cmd_rebuild() {
    local version
    version=$(get_version)
    local log_file="$DOCKER_LOG_DIR/docker-rebuild-$(date +%Y%m%d-%H%M%S).log"
    
    log_to_file "$log_file" "Rebuilding Docker images (with cleanup)..."
    log_to_file "$log_file" "Version: $version"
    log_to_file "$log_file" "Log file: $log_file"
    log_to_file "$log_file" "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    log_to_file "$log_file" "========================================"
    
    log_to_file "$log_file" "Stopping containers..."
    docker-compose down --remove-orphans 2>&1 | tee -a "$log_file" || true
    
    log_to_file "$log_file" "Removing old containers..."
    docker-compose rm -f 2>&1 | tee -a "$log_file" || true
    
    docker_remove_old_images "$version" "$log_file"
    
    log_to_file "$log_file" "Cleaning up unused images..."
    docker image prune -f --filter "dangling=true" 2>&1 | tee -a "$log_file" || true
    
    log_to_file "$log_file" "Building new images (--no-cache) with tag: $version..."
    if VERSION="$version" docker-compose build --no-cache 2>&1 | tee -a "$log_file"; then
        docker_tag_images "$version" "$log_file"
    fi
    
    log_to_file "$log_file" "✓ Rebuild completed"
    log_to_file "$log_file" "Version: $version"
    log_to_file "$log_file" "Log saved to: $log_file"
}

cmd_up() {
    log_info "Starting Docker microservices..."
    local version
    version=$(get_version)
    echo "Using version: $version"
    VERSION="$version" docker-compose up -d
    echo ""
    echo "Microservices started:"
    echo "  - Frontend: http://localhost:8080"
    echo "  - Gateway: http://localhost:8000"
    echo "  - DCF Service: http://localhost:8001"
    echo "  - Stock Service: http://localhost:8002"
    echo ""
    echo "View logs: make docker-logs"
    echo "Stop: make docker-down"
}

cmd_down() {
    log_info "Stopping Docker containers..."
    local version
    version=$(get_version)
    VERSION="$version" docker-compose down
}

cmd_logs() {
    local log_file="$DOCKER_LOG_DIR/docker-logs-$(date +%Y%m%d-%H%M%S).log"
    log_to_file "$log_file" "Saving container logs..."
    log_to_file "$log_file" "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    log_to_file "$log_file" "========================================"
    docker-compose logs --tail=100 2>&1 | tee -a "$log_file"
    echo "" | tee -a "$log_file"
    echo "Log saved to: $log_file" | tee -a "$log_file"
}

cmd_clean() {
    local log_file="$DOCKER_LOG_DIR/docker-clean-$(date +%Y%m%d-%H%M%S).log"
    log_to_file "$log_file" "Cleaning Docker containers and images..."
    log_to_file "$log_file" "Log file: $log_file"
    log_to_file "$log_file" "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    log_to_file "$log_file" "========================================"
    docker-compose down -v --remove-orphans 2>&1 | tee -a "$log_file"
    log_to_file "$log_file" "Removing unused images..."
    docker image prune -f --filter "dangling=true" 2>&1 | tee -a "$log_file"
    log_to_file "$log_file" "Removing unused containers..."
    docker container prune -f 2>&1 | tee -a "$log_file"
    log_to_file "$log_file" "✓ Cleanup completed"
    log_to_file "$log_file" "Log saved to: $log_file"
}

cmd_clean_all() {
    local log_file="$DOCKER_LOG_DIR/docker-clean-all-$(date +%Y%m%d-%H%M%S).log"
    log_to_file "$log_file" "Deep cleaning Docker (removes all unused resources)..."
    log_to_file "$log_file" "Log file: $log_file"
    log_to_file "$log_file" "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    log_to_file "$log_file" "========================================"
    docker-compose down -v --remove-orphans 2>&1 | tee -a "$log_file"
    log_to_file "$log_file" "Removing all unused images (not just dangling)..."
    docker image prune -af 2>&1 | tee -a "$log_file"
    log_to_file "$log_file" "Removing all unused containers..."
    docker container prune -f 2>&1 | tee -a "$log_file"
    log_to_file "$log_file" "Removing unused networks..."
    docker network prune -f 2>&1 | tee -a "$log_file"
    log_to_file "$log_file" "Removing unused volumes..."
    docker volume prune -f 2>&1 | tee -a "$log_file"
    log_to_file "$log_file" "✓ Deep cleanup completed"
    log_to_file "$log_file" "Log saved to: $log_file"
}

cmd_images() {
    echo "Docker Images:"
    echo "=============="
    for img in $DOCKER_IMAGES; do
        echo ""
        echo "$img:"
        list_docker_images "$img"
    done
}

cmd_clean_old() {
    local keep="${2:-3}"
    log_info "Removing old Docker images (keeping last $keep versions)..."
    for img in $DOCKER_IMAGES; do
        log_info "Processing $img..."
        local image_name
        image_name=$(get_docker_image_name "$img")
        docker images --format "{{.Repository}}:{{.Tag}} {{.CreatedAt}}" | \
            grep "^${image_name}:" | \
            sort -k2 -r | tail -n +$((keep + 1)) | awk '{print $1}' | \
            xargs -r docker rmi -f || true
    done
    log_success "Cleanup completed"
}

# ============================================================================
# Help Function
# ============================================================================

show_help() {
    print_help_header "Docker Management Commands"
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Build & Deploy:"
    echo "  build       - Build Docker images (with auto cleanup)"
    echo "  rebuild     - Rebuild from scratch (with cleanup)"
    echo "  up          - Start Docker containers"
    echo "  down        - Stop Docker containers"
    echo "  restart     - Restart containers"
    echo ""
    echo "Development:"
    echo "  dev         - Start dev mode (hot reload)"
    echo "  dev-down    - Stop dev containers"
    echo "  dev-logs    - View dev logs"
    echo "  dev-restart - Restart dev services"
    echo ""
    echo "Logs:"
    echo "  logs        - View container logs (last 100 lines)"
    echo "  logs-follow - Follow logs (real-time)"
    echo "  logs-gateway - Gateway logs"
    echo "  logs-dcf    - DCF service logs"
    echo "  logs-stock  - Stock service logs"
    echo "  logs-frontend - Frontend logs"
    echo ""
    echo "Cleanup:"
    echo "  clean       - Clean unused containers and images"
    echo "  clean-all   - Deep clean (removes all unused resources)"
    echo "  clean-old [N] - Remove old images (keep last N versions, default 3)"
    echo ""
    echo "Info:"
    echo "  ps          - Show running containers"
    echo "  images     - List Docker images"
    echo ""
    echo "Exec:"
    echo "  exec-gateway  - Exec into gateway container"
    echo "  exec-dcf     - Exec into dcf container"
    echo "  exec-stock   - Exec into stock container"
    echo "  exec-frontend - Exec into frontend container"
    echo ""
    echo "Examples:"
    echo "  $0 build"
    echo "  $0 up"
    echo "  $0 logs"
    echo "  $0 clean-old 5"
}

# ============================================================================
# Main
# ============================================================================

main() {
    local command="${1:-help}"
    
    case "$command" in
        build)
            cmd_build
            ;;
        rebuild)
            cmd_rebuild
            ;;
        up)
            cmd_up
            ;;
        down)
            cmd_down
            ;;
        logs)
            cmd_logs
            ;;
        logs-follow)
            docker-compose logs -f
            ;;
        logs-gateway)
            docker-compose logs -f gateway
            ;;
        logs-dcf)
            docker-compose logs -f dcf
            ;;
        logs-stock)
            docker-compose logs -f stock
            ;;
        logs-frontend)
            docker-compose logs -f frontend
            ;;
        restart)
            log_info "Restarting Docker containers..."
            local version
            version=$(get_version)
            VERSION="$version" docker-compose restart
            ;;
        clean)
            cmd_clean
            ;;
        clean-all)
            cmd_clean_all
            ;;
        ps)
            docker-compose ps
            ;;
        images)
            cmd_images
            ;;
        clean-old)
            cmd_clean_old "$@"
            ;;
        exec-gateway)
            docker-compose exec gateway /bin/bash
            ;;
        exec-dcf)
            docker-compose exec dcf /bin/bash
            ;;
        exec-stock)
            docker-compose exec stock /bin/bash
            ;;
        exec-frontend)
            docker-compose exec frontend /bin/sh
            ;;
        dev)
            log_info "Starting Docker microservices in DEVELOPMENT mode (hot reload)..."
            log_warn "Code changes will be reflected automatically (no rebuild needed)"
            docker-compose -f docker-compose.dev.yml up -d
            echo ""
            echo "Development services started:"
            echo "  - Frontend: http://localhost:8080"
            echo "  - Gateway: http://localhost:8000 (hot reload enabled)"
            echo "  - DCF Service: http://localhost:8001 (hot reload enabled)"
            echo "  - Stock Service: http://localhost:8002 (hot reload enabled)"
            echo ""
            echo "View logs: make docker-dev-logs"
            echo "Stop: make docker-dev-down"
            echo ""
            echo "💡 Tip: Edit code in services/*/main.py or src/ and changes will auto-reload!"
            ;;
        dev-down)
            log_info "Stopping development Docker containers..."
            docker-compose -f docker-compose.dev.yml down
            ;;
        dev-logs)
            log_info "Showing development container logs..."
            docker-compose -f docker-compose.dev.yml logs --tail=100 -f
            ;;
        dev-restart)
            log_info "Restarting development services..."
            docker-compose -f docker-compose.dev.yml restart
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
