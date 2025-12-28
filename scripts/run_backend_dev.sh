#!/bin/bash
# Quick development script - Run backend services locally with hot reload
# This is faster than Docker rebuild for development

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Backend Development Mode${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -q -r services/common/requirements.txt
else
    source venv/bin/activate
fi

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/src"

echo -e "${GREEN}Starting backend services...${NC}"
echo ""
echo -e "${YELLOW}Services will run with hot reload enabled${NC}"
echo -e "${YELLOW}Code changes will be reflected automatically${NC}"
echo ""
echo "Services:"
echo "  - Gateway: http://localhost:8000"
echo "  - DCF Service: http://localhost:8001"
echo "  - Stock Service: http://localhost:8002"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping services...${NC}"
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start services in background
cd "$PROJECT_ROOT/services/gateway"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
GATEWAY_PID=$!

cd "$PROJECT_ROOT/services/dcf"
uvicorn main:app --host 0.0.0.0 --port 8001 --reload &
DCF_PID=$!

cd "$PROJECT_ROOT/services/stock"
uvicorn main:app --host 0.0.0.0 --port 8002 --reload &
STOCK_PID=$!

# Wait for all processes
wait

