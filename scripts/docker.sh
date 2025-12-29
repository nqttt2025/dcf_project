#!/bin/bash
# Docker Management Scripts
# Usage: ./scripts/docker.sh [build|rebuild|up|down|logs|clean|clean-all|ps|...]
# This script is independent and can be run standalone

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

# Initialize script
init_script "$(basename "${BASH_SOURCE[0]}")"

# ============================================================================
# Docker-specific Functions
# ============================================================================

docker_build_images() {
    local version="$1"
    local log_file="$2"
    local parallel="${3:-false}"
    
    # Enable BuildKit for faster builds
    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1
    
    log_to_file "$log_file" "Building images with tag: $version"
    log_to_file "$log_file" "BuildKit enabled: $DOCKER_BUILDKIT"
    
    # Check if base image needs rebuild
    log_to_file "$log_file" "Checking base image version..."
    local base_version
    base_version=$("$PROJECT_ROOT/scripts/version/docker_version.sh" get base 2>/dev/null)
    
    # Ensure base_version is set (required, no default to latest)
    if [[ -z "$base_version" ]]; then
        log_error "Cannot get base version from docker-versions.json"
        log_error "Please ensure docker-versions.json exists and has base version set"
        exit 1
    fi
    
    log_to_file "$log_file" "Base version: $base_version"
    local base_needs_rebuild
    base_needs_rebuild=$("$PROJECT_ROOT/scripts/version/docker_version.sh" check-base 2>/dev/null && echo "yes" || echo "no")
    
    # Get project version (from git tag - single source of truth)
    local project_version
    project_version=$("$PROJECT_ROOT/scripts/utils/get_version.sh")
    project_version="${project_version%-dirty}"  # Remove -dirty suffix
    log_to_file "$log_file" "Project version (from git tag): $project_version"
    
    # Build base image if needed
    if [[ "$base_needs_rebuild" == "yes" ]] || ! docker_image_exists "dcf-project-base" "$base_version"; then
        log_to_file "$log_file" "Building base image (version: $base_version)..."
        BASE_VERSION="$base_version" docker-compose build base 2>&1 | tee -a "$log_file" || true
        
        # Tag base image with version only (no latest tag)
        if docker_image_exists "dcf-project-base" "latest"; then
            docker tag "dcf-project-base:latest" "dcf-project-base:$base_version" 2>&1 | tee -a "$log_file" || true
            # Remove latest tag to avoid confusion
            docker rmi "dcf-project-base:latest" 2>/dev/null | tee -a "$log_file" || true
            log_to_file "$log_file" "Removed latest tag (using version tag only)"
        fi
        
        # Update hash after successful build
        "$PROJECT_ROOT/scripts/version/docker_version.sh" update base >/dev/null 2>&1 || true
    else
        log_to_file "$log_file" "Base image unchanged (version: $base_version), using cached version"
        # Ensure base image is tagged correctly (version only)
        if docker_image_exists "dcf-project-base" "latest"; then
            docker tag "dcf-project-base:latest" "dcf-project-base:$base_version" 2>&1 | tee -a "$log_file" || true
            # Remove latest tag to avoid confusion
            docker rmi "dcf-project-base:latest" 2>/dev/null | tee -a "$log_file" || true
        fi
    fi
    
    # Ensure base image exists before building services
    if ! docker_image_exists "dcf-project-base" "$base_version"; then
        log_error "Base image not found! Building base image first..."
        BASE_VERSION="$base_version" docker-compose build base 2>&1 | tee -a "$log_file" || true
        if docker_image_exists "dcf-project-base" "latest"; then
            docker tag "dcf-project-base:latest" "dcf-project-base:$base_version" 2>&1 | tee -a "$log_file" || true
            # Remove latest tag to avoid confusion
            docker rmi "dcf-project-base:latest" 2>/dev/null | tee -a "$log_file" || true
        fi
    fi
    
    # Build service images
    # IMPORTANT: Set both BASE_VERSION and VERSION to ensure correct base image is used
    log_to_file "$log_file" "Building service images with BASE_VERSION=$base_version, VERSION=$version"
    if [[ "$parallel" == "true" ]]; then
        log_to_file "$log_file" "Building images in parallel..."
        BASE_VERSION="$base_version" VERSION="$version" docker-compose build --parallel 2>&1 | tee -a "$log_file"
    else
        BASE_VERSION="$base_version" VERSION="$version" docker-compose build 2>&1 | tee -a "$log_file"
    fi
    return $?
}

docker_tag_images() {
    local version="$1"
    local log_file="$2"
    
    log_to_file "$log_file" "Tagging images with version $version..."
    # Only tag with version, no latest tag
    # Version tag is sufficient and clearer
    for img in $DOCKER_IMAGES; do
        local image_name
        image_name=$(get_docker_image_name "$img")
        if docker_image_exists "$image_name" "$version"; then
            log_to_file "$log_file" "  ✓ ${image_name}:${version} already tagged"
        elif docker_image_exists "$image_name" "latest"; then
            # If image exists with latest tag, tag it with version
            docker tag "${image_name}:latest" "${image_name}:${version}" 2>&1 | tee -a "$log_file" || true
            log_to_file "$log_file" "  ✓ Tagged ${image_name}:latest → ${image_name}:${version}"
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
    # Get project version from git tag (single source of truth)
    local version
    version=$("$PROJECT_ROOT/scripts/utils/get_version.sh")
    version="${version%-dirty}"  # Remove -dirty suffix
    local parallel="${PARALLEL:-false}"
    local log_file="$DOCKER_LOG_DIR/docker-build-$(date +%Y%m%d-%H%M%S).log"
    
    log_to_file "$log_file" "Building Docker images for microservices..."
    log_to_file "$log_file" "Version: $version"
    log_to_file "$log_file" "Parallel: $parallel"
    log_to_file "$log_file" "Log file: $log_file"
    log_to_file "$log_file" "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    log_to_file "$log_file" "========================================"
    
    docker_remove_old_images "$version" "$log_file"
    
    if docker_build_images "$version" "$log_file" "$parallel"; then
        docker_tag_images "$version" "$log_file"
    fi
    
    docker_cleanup_after_build "$log_file"
    
    log_to_file "$log_file" "✓ Build completed and cleanup done"
    log_to_file "$log_file" "Version: $version"
    log_to_file "$log_file" "Log saved to: $log_file"
}

cmd_rebuild() {
    # Get project version from git tag (single source of truth)
    local version
    version=$("$PROJECT_ROOT/scripts/utils/get_version.sh")
    version="${version%-dirty}"  # Remove -dirty suffix
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
    
    # Rebuild base image first
    log_to_file "$log_file" "Rebuilding base image..."
    local base_version
    base_version=$("$PROJECT_ROOT/scripts/version/docker_version.sh" get base 2>/dev/null)
    
    # Ensure base_version is set (required, no default to latest)
    if [[ -z "$base_version" ]]; then
        log_error "Cannot get base version from docker-versions.json"
        log_error "Please ensure docker-versions.json exists and has base version set"
        exit 1
    fi
    
    BASE_VERSION="$base_version" docker-compose build --no-cache base 2>&1 | tee -a "$log_file" || true
    
    # Tag base image with version only
    if docker_image_exists "dcf-project-base" "latest"; then
        docker tag "dcf-project-base:latest" "dcf-project-base:$base_version" 2>&1 | tee -a "$log_file" || true
        # Remove latest tag to avoid confusion
        docker rmi "dcf-project-base:latest" 2>/dev/null | tee -a "$log_file" || true
        log_to_file "$log_file" "Removed latest tag (using version tag only)"
    fi
    
    # Update hash after rebuild
    "$PROJECT_ROOT/scripts/version/docker_version.sh" update base >/dev/null 2>&1 || true
    
    log_to_file "$log_file" "Building new images (--no-cache) with tag: $version..."
    log_to_file "$log_file" "Using BASE_VERSION=$base_version, VERSION=$version"
    if BASE_VERSION="$base_version" VERSION="$version" docker-compose build --no-cache 2>&1 | tee -a "$log_file"; then
        docker_tag_images "$version" "$log_file"
    fi
    
    log_to_file "$log_file" "✓ Rebuild completed"
    log_to_file "$log_file" "Version: $version"
    log_to_file "$log_file" "Log saved to: $log_file"
}

cmd_up() {
    log_info "Starting Docker microservices..."
    # Get project version from git tag (single source of truth)
    local version
    version=$("$PROJECT_ROOT/scripts/utils/get_version.sh")
    version="${version%-dirty}"  # Remove -dirty suffix
    
    # Get base version
    local base_version
    base_version=$("$PROJECT_ROOT/scripts/version/docker_version.sh" get base 2>/dev/null)
    if [[ -z "$base_version" ]]; then
        log_error "Cannot get base version from docker-versions.json"
        exit 1
    fi
    
    echo "Using version: $version, base version: $base_version"
    BASE_VERSION="$base_version" VERSION="$version" docker-compose up -d
    echo ""
    echo "Microservices started:"
    echo "  - Frontend: http://localhost:8080"
    echo "  - Gateway: http://localhost:8000"
    echo "  - DCF Service: http://localhost:8001"
    echo "  - Stock Service: http://localhost:8002"
    echo "  - Database Service: http://localhost:8003"
    echo "  - PostgreSQL: localhost:5432"
    echo ""
    echo "View logs: make docker-logs"
    echo "Stop: make docker-down"
    echo "Database only: make docker-db-start"
}

cmd_down() {
    log_info "Stopping Docker containers..."
    # Get project version from git tag (single source of truth)
    local version
    version=$("$PROJECT_ROOT/scripts/utils/get_version.sh")
    version="${version%-dirty}"  # Remove -dirty suffix
    
    # Get base version
    local base_version
    base_version=$("$PROJECT_ROOT/scripts/version/docker_version.sh" get base 2>/dev/null)
    if [[ -z "$base_version" ]]; then
        log_error "Cannot get base version from docker-versions.json"
        exit 1
    fi
    
    BASE_VERSION="$base_version" VERSION="$version" docker-compose down
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
        echo "  build-fast  - Build Docker images in parallel (faster)"
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
    echo "  logs-database - Database service logs"
    echo "  logs-postgres - PostgreSQL logs"
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
    echo "  exec-database - Exec into database container"
    echo "  exec-postgres - Exec into postgres container"
    echo ""
    echo "Database Management:"
    echo "  db-start    - Start database services (PostgreSQL + Database Service)"
    echo "  db-stop     - Stop database services"
    echo "  db-restart  - Restart database services"
    echo "  db-status   - Show database services status"
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
        build-fast)
            PARALLEL=true cmd_build
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
        logs-database)
            docker-compose logs -f database
            ;;
        logs-postgres)
            docker-compose logs -f postgres
            ;;
        restart)
            log_info "Restarting Docker containers..."
            # Get project version from git tag (single source of truth)
            local version
            version=$("$PROJECT_ROOT/scripts/utils/get_version.sh")
            version="${version%-dirty}"  # Remove -dirty suffix
            
            # Get base version
            local base_version
            base_version=$("$PROJECT_ROOT/scripts/version/docker_version.sh" get base 2>/dev/null)
            if [[ -z "$base_version" ]]; then
                log_error "Cannot get base version from docker-versions.json"
                exit 1
            fi
            
            BASE_VERSION="$base_version" VERSION="$version" docker-compose restart
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
        exec-database)
            docker-compose exec database /bin/bash
            ;;
        exec-postgres)
            docker-compose exec postgres /bin/sh
            ;;
        db-start)
            log_info "Starting database services (PostgreSQL + Database Service)..."
            docker-compose up -d postgres database
            echo ""
            echo "Database services started:"
            echo "  - PostgreSQL: localhost:5432"
            echo "  - Database Service: http://localhost:8003"
            echo ""
            echo "View logs: make docker-logs-database"
            ;;
        db-stop)
            log_info "Stopping database services..."
            docker-compose stop postgres database
            ;;
        db-restart)
            log_info "Restarting database services..."
            docker-compose restart postgres database
            ;;
        db-status)
            log_info "Database services status:"
            docker-compose ps postgres database
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
            echo "  - Database Service: http://localhost:8003 (hot reload enabled)"
            echo "  - PostgreSQL: localhost:5432"
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
