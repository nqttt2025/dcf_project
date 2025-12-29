"""
API Gateway - Microservice Architecture
Routes requests to appropriate microservices
"""
import sys
from pathlib import Path

# Setup project path first (before importing services.common)
if Path('/app').exists():
    project_root = Path('/app')
else:
    project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
import httpx
from typing import Optional

# Import common utilities after path setup
from services.common import (
    setup_cors,
    check_service_health,
    get_database_health_status,
    get_service_urls,
)

app = FastAPI(title="DCF Analysis API Gateway")

# Setup CORS
setup_cors(app)

# Get service URLs
service_urls = get_service_urls()
DCF_SERVICE_URL = service_urls["dcf"]
STOCK_SERVICE_URL = service_urls["stock"]
DATABASE_SERVICE_URL = service_urls["database"]


async def make_service_request(
    service_url: str,
    method: str = "GET",
    endpoint: str = "",
    timeout: float = 10.0,
    json_data: Optional[dict] = None
):
    """
    Make a request to a microservice.
    
    Args:
        service_url: Base URL of the service
        method: HTTP method (GET, POST, etc.)
        endpoint: Endpoint path (e.g., "/stocks")
        timeout: Request timeout in seconds
        json_data: Optional JSON data for POST requests
    
    Returns:
        Response JSON data
    
    Raises:
        HTTPException: If request fails
    """
    try:
        async with httpx.AsyncClient() as client:
            url = f"{service_url}{endpoint}"
            if method.upper() == "GET":
                response = await client.get(url, timeout=timeout)
            elif method.upper() == "POST":
                response = await client.post(url, json=json_data, timeout=timeout)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported method: {method}")
            
            if response.status_code not in [200, 201]:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    except httpx.RequestError as e:
        service_name = service_url.split("://")[1].split(":")[0] if "://" in service_url else "service"
        raise HTTPException(status_code=503, detail=f"{service_name} service unavailable: {str(e)}")

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "DCF Analysis API Gateway",
        "version": "1.0",
        "services": {
            "dcf": DCF_SERVICE_URL,
            "stock": STOCK_SERVICE_URL
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # Check all services
    services_status = {
        "dcf": await check_service_health(DCF_SERVICE_URL),
        "stock": await check_service_health(STOCK_SERVICE_URL),
        "database": await check_service_health(DATABASE_SERVICE_URL),
    }
    
    # Check database connection directly
    gateway_db_status = get_database_health_status()
    
    return {
        "status": "healthy",
        "service": "gateway",
        "services": services_status,
        "gateway_database": gateway_db_status
    }

# ==================== Stock Service Routes ====================

@app.get("/api/stocks")
async def list_stocks():
    """Lấy danh sách tất cả cổ phiếu"""
    return await make_service_request(STOCK_SERVICE_URL, "GET", "/stocks")

@app.get("/api/stocks/{ticker}")
async def get_stock_detail(ticker: str):
    """Lấy thông tin chi tiết của một cổ phiếu"""
    return await make_service_request(STOCK_SERVICE_URL, "GET", f"/stocks/{ticker}")

@app.get("/api/stocks/{ticker}/config")
async def get_stock_config(ticker: str):
    """Lấy config của một cổ phiếu"""
    return await make_service_request(STOCK_SERVICE_URL, "GET", f"/stocks/{ticker}/config")

@app.get("/api/stocks/{ticker}/status")
async def get_stock_status(ticker: str):
    """Lấy trạng thái của một cổ phiếu"""
    return await make_service_request(STOCK_SERVICE_URL, "GET", f"/stocks/{ticker}/status")

@app.get("/api/status")
async def get_system_status():
    """Lấy trạng thái tổng thể của hệ thống"""
    return await make_service_request(STOCK_SERVICE_URL, "GET", "/status")

# ==================== DCF Service Routes ====================

@app.post("/api/stocks/{ticker}/run")
async def run_dcf_analysis(ticker: str):
    """Chạy phân tích DCF cho một cổ phiếu"""
    return await make_service_request(
        DCF_SERVICE_URL,
        "POST",
        f"/analyze/{ticker}",
        timeout=300.0
    )

@app.get("/api/analysis/{ticker}")
async def get_analysis_result(ticker: str):
    """Lấy kết quả phân tích DCF"""
    return await make_service_request(
        DCF_SERVICE_URL,
        "GET",
        f"/analysis/{ticker}"
    )

