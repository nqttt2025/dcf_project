#!/bin/bash
# Health Check Script for DCF Project Services
# Checks status and health of all microservices

set -e

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/scripts/lib/common.sh"

# Initialize script
init_script "$(basename "${BASH_SOURCE[0]}")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service URLs
GATEWAY_URL="${GATEWAY_URL:-http://localhost:8000}"
DCF_URL="${DCF_URL:-http://localhost:8001}"
STOCK_URL="${STOCK_URL:-http://localhost:8002}"
DATABASE_URL="${DATABASE_URL:-http://localhost:8003}"

# Function to check HTTP endpoint
check_service() {
    local service_name=$1
    local service_url=$2
    local endpoint="${service_url}/health"
    
    echo -n "  Checking ${service_name}... "
    
    # Try to get health status
    response=$(curl -s -w "\n%{http_code}" --max-time 5 "$endpoint" 2>/dev/null || echo -e "\n000")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ Healthy${NC}"
        
        # Try to parse JSON response
        if command -v python3 &> /dev/null; then
            echo "$body" | python3 -m json.tool 2>/dev/null | sed 's/^/    /' || echo "    $body"
        else
            echo "    $body" | head -n 5
        fi
        return 0
    elif [ "$http_code" = "000" ]; then
        echo -e "${RED}✗ Unreachable${NC}"
        return 1
    else
        echo -e "${YELLOW}⚠ Unhealthy (HTTP $http_code)${NC}"
        return 1
    fi
}

# Function to check Docker containers
check_docker_containers() {
    echo -e "\n${BLUE}=== Docker Containers Status ===${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}Docker not found${NC}"
        return 1
    fi
    
    if ! docker ps &> /dev/null; then
        echo -e "${YELLOW}Docker daemon not running${NC}"
        return 1
    fi
    
    # Check each service container
    containers=(
        "dcf-gateway:Gateway"
        "dcf-dcf:DCF Service"
        "dcf-stock:Stock Service"
        "dcf-database:Database Service"
        "dcf-postgres:PostgreSQL"
        "dcf-redis:Redis"
        "dcf-frontend:Frontend"
    )
    
    for container_info in "${containers[@]}"; do
        container_name=$(echo "$container_info" | cut -d: -f1)
        display_name=$(echo "$container_info" | cut -d: -f2)
        
        if docker ps --format "{{.Names}}" | grep -q "^${container_name}$"; then
            status=$(docker inspect --format='{{.State.Status}}' "$container_name" 2>/dev/null || echo "unknown")
            health=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "no-healthcheck")
            
            if [ "$status" = "running" ]; then
                if [ "$health" = "healthy" ]; then
                    echo -e "  ${GREEN}✓${NC} $display_name: Running (Healthy)"
                elif [ "$health" = "no-healthcheck" ]; then
                    echo -e "  ${GREEN}✓${NC} $display_name: Running"
                else
                    echo -e "  ${YELLOW}⚠${NC} $display_name: Running ($health)"
                fi
            else
                echo -e "  ${RED}✗${NC} $display_name: $status"
            fi
        else
            echo -e "  ${RED}✗${NC} $display_name: Not running"
        fi
    done
}

# Function to check service endpoints
check_service_endpoints() {
    echo -e "\n${BLUE}=== Service Health Endpoints ===${NC}"
    
    # Check Gateway (which aggregates other services)
    echo -e "\n${YELLOW}Gateway Service:${NC}"
    check_service "Gateway" "$GATEWAY_URL"
    
    # Check individual services
    echo -e "\n${YELLOW}Individual Services:${NC}"
    check_service "DCF Service" "$DCF_URL"
    check_service "Stock Service" "$STOCK_URL"
    check_service "Database Service" "$DATABASE_URL"
}

# Function to check database connection
check_database() {
    echo -e "\n${BLUE}=== Database Connection ===${NC}"
    
    if command -v psql &> /dev/null; then
        if PGPASSWORD=dcf_password psql -h localhost -U dcf_user -d dcf_db -c "SELECT 1;" &> /dev/null; then
            echo -e "  ${GREEN}✓${NC} PostgreSQL: Connected"
            
            # Get database info
            db_info=$(PGPASSWORD=dcf_password psql -h localhost -U dcf_user -d dcf_db -t -c "
                SELECT 
                    'Database: ' || current_database() || E'\n' ||
                    'Size: ' || pg_size_pretty(pg_database_size(current_database())) || E'\n' ||
                    'Tables: ' || count(*)::text
                FROM pg_tables 
                WHERE schemaname = 'public';
            " 2>/dev/null || echo "Unable to get info")
            echo "$db_info" | sed 's/^/    /'
        else
            echo -e "  ${RED}✗${NC} PostgreSQL: Connection failed"
        fi
    else
        echo -e "  ${YELLOW}⚠${NC} psql not found, skipping direct DB check"
    fi
}

# Function to check Redis connection
check_redis() {
    echo -e "\n${BLUE}=== Redis Connection ===${NC}"
    
    if command -v redis-cli &> /dev/null; then
        if redis-cli -h localhost ping &> /dev/null; then
            echo -e "  ${GREEN}✓${NC} Redis: Connected"
            
            # Get Redis info
            redis_info=$(redis-cli -h localhost info stats 2>/dev/null | grep -E "keyspace|total_commands" | head -n 3 || echo "")
            if [ -n "$redis_info" ]; then
                echo "$redis_info" | sed 's/^/    /'
            fi
        else
            echo -e "  ${RED}✗${NC} Redis: Connection failed"
        fi
    else
        echo -e "  ${YELLOW}⚠${NC} redis-cli not found, skipping direct Redis check"
    fi
}

# Main function
main() {
    echo -e "${BLUE}"
    echo "=========================================="
    echo "  DCF Project Health Check"
    echo "=========================================="
    echo -e "${NC}"
    
    # Check Docker containers
    check_docker_containers
    
    # Check service endpoints
    check_service_endpoints
    
    # Check database
    check_database
    
    # Check Redis
    check_redis
    
    echo -e "\n${BLUE}==========================================${NC}"
    echo -e "${GREEN}Health check completed${NC}"
    echo -e "${BLUE}==========================================${NC}\n"
}

# Run main function
main "$@"

