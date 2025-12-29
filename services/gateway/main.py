"""
API Gateway - Microservice Architecture
Routes requests to appropriate microservices
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import sys
from pathlib import Path

# Add project root to path for local development
if Path('/app').exists():
    project_root = Path('/app')
else:
    # Local development: go up from services/gateway/main.py to project root
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

app = FastAPI(title="DCF Analysis API Gateway")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs from environment variables
DCF_SERVICE_URL = os.getenv("DCF_SERVICE_URL", "http://dcf:8001")
STOCK_SERVICE_URL = os.getenv("STOCK_SERVICE_URL", "http://stock:8002")
DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "http://database:8003")

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
    services_status = {}
    
    # Check DCF service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{DCF_SERVICE_URL}/health", timeout=5.0)
            services_status["dcf"] = response.json() if response.status_code == 200 else {"status": "unhealthy"}
    except Exception as e:
        services_status["dcf"] = {"status": "unavailable", "error": str(e)}
    
    # Check Stock service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{STOCK_SERVICE_URL}/health", timeout=5.0)
            services_status["stock"] = response.json() if response.status_code == 200 else {"status": "unhealthy"}
    except Exception as e:
        services_status["stock"] = {"status": "unavailable", "error": str(e)}
    
    # Check Database service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{DATABASE_SERVICE_URL}/health", timeout=5.0)
            services_status["database"] = response.json() if response.status_code == 200 else {"status": "unhealthy"}
    except Exception as e:
        services_status["database"] = {"status": "unavailable", "error": str(e)}
    
    # Check database connection directly
    gateway_db_status = {}
    try:
        from src.utils.database_client import check_database_connection, get_database_info
        db_connected = check_database_connection()
        gateway_db_status["connected"] = db_connected
        if db_connected:
            gateway_db_status["info"] = get_database_info()
    except Exception as e:
        gateway_db_status["error"] = str(e)
    
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
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{STOCK_SERVICE_URL}/stocks", timeout=10.0)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Stock service unavailable: {str(e)}")

@app.get("/api/stocks/{ticker}")
async def get_stock_detail(ticker: str):
    """Lấy thông tin chi tiết của một cổ phiếu"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{STOCK_SERVICE_URL}/stocks/{ticker}", timeout=10.0)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Stock service unavailable: {str(e)}")

@app.get("/api/stocks/{ticker}/config")
async def get_stock_config(ticker: str):
    """Lấy config của một cổ phiếu"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{STOCK_SERVICE_URL}/stocks/{ticker}/config", timeout=10.0)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Stock service unavailable: {str(e)}")

@app.get("/api/stocks/{ticker}/status")
async def get_stock_status(ticker: str):
    """Lấy trạng thái của một cổ phiếu"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{STOCK_SERVICE_URL}/stocks/{ticker}/status", timeout=10.0)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Stock service unavailable: {str(e)}")

@app.get("/api/status")
async def get_system_status():
    """Lấy trạng thái tổng thể của hệ thống"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{STOCK_SERVICE_URL}/status", timeout=10.0)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Stock service unavailable: {str(e)}")

# ==================== DCF Service Routes ====================

@app.post("/api/stocks/{ticker}/run")
async def run_dcf_analysis(ticker: str):
    """Chạy phân tích DCF cho một cổ phiếu"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{DCF_SERVICE_URL}/analyze/{ticker}", timeout=300.0)
        if response.status_code not in [200, 201]:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"DCF service unavailable: {str(e)}")

@app.get("/api/analysis/{ticker}")
async def get_analysis_result(ticker: str):
    """Lấy kết quả phân tích DCF"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{DCF_SERVICE_URL}/analysis/{ticker}", timeout=10.0)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"DCF service unavailable: {str(e)}")

