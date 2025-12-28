#!/bin/bash
# Run backend services locally (without Docker) for faster development
# Usage: ./scripts/run_backend_local.sh [gateway|dcf|stock|all]

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/src"

# Function to run a service
run_service() {
    local service=$1
    local port=$2
    
    echo -e "${BLUE}Starting $service on port $port...${NC}"
    cd "$PROJECT_ROOT/services/$service"
    
    # Install dependencies if needed
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv venv
        source venv/bin/activate
        pip install -q -r ../common/requirements.txt
    else
        source venv/bin/activate
    fi
    
    # Run with uvicorn reload
    echo -e "${GREEN}$service running on http://localhost:$port${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    uvicorn main:app --host 0.0.0.0 --port "$port" --reload
}

# Check which service to run
SERVICE=${1:-all}

case $SERVICE in
    gateway)
        run_service gateway 8000
        ;;
    dcf)
        run_service dcf 8001
        ;;
    stock)
        run_service stock 8002
        ;;
    all)
        echo -e "${BLUE}Starting all backend services...${NC}"
        echo -e "${YELLOW}Note: Run each service in a separate terminal for best experience${NC}"
        echo ""
        echo "Terminal 1: ./scripts/run_backend_local.sh gateway"
        echo "Terminal 2: ./scripts/run_backend_local.sh dcf"
        echo "Terminal 3: ./scripts/run_backend_local.sh stock"
        ;;
    *)
        echo "Usage: $0 [gateway|dcf|stock|all]"
        exit 1
        ;;
esac

