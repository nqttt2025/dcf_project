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

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
import httpx
from typing import Optional
from datetime import datetime
import asyncio
import logging
from collections import defaultdict
from time import time
import subprocess
import json

# Setup service-specific logger với rotation và tối ưu hiệu năng
from src.utils.service_logger import setup_service_logger
logger = setup_service_logger('gateway', level=logging.INFO)

# Rate limiting storage (in-memory, can be moved to Redis for distributed systems)
_rate_limit_store = defaultdict(list)

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

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple rate limiting middleware"""
    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/api/health"]:
        return await call_next(request)
    
    # Rate limit for DCF analysis endpoints
    if request.url.path.startswith("/api/stocks/") and request.method == "POST":
        # Limit to 10 requests per minute per IP
        client_ip = request.client.host if request.client else "unknown"
        current_time = time()
        minute_ago = current_time - 60
        
        # Clean old entries
        _rate_limit_store[client_ip] = [
            t for t in _rate_limit_store[client_ip] if t > minute_ago
        ]
        
        # Check limit
        if len(_rate_limit_store[client_ip]) >= 10:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Maximum 10 analysis requests per minute.",
                    "retry_after": 60
                }
            )
        
        # Add current request
        _rate_limit_store[client_ip].append(current_time)
    
    return await call_next(request)

# Get service URLs
service_urls = get_service_urls()
DCF_SERVICE_URL = service_urls["dcf"]
STOCK_SERVICE_URL = service_urls["stock"]
DATABASE_SERVICE_URL = service_urls["database"]

# Shared HTTP client with connection pooling
_http_client: Optional[httpx.AsyncClient] = None
_request_semaphore = asyncio.Semaphore(50)  # Max 50 concurrent requests to services

def get_http_client() -> httpx.AsyncClient:
    """Get or create shared HTTP client with connection pooling"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(
                max_keepalive_connections=50,  # Increased for better concurrency
                max_connections=200,  # Increased for high load
                keepalive_expiry=60.0  # Longer keepalive
            ),
            follow_redirects=True
        )
    return _http_client

@app.on_event("shutdown")
async def shutdown_event():
    """Close HTTP client on shutdown"""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


async def make_service_request(
    service_url: str,
    method: str = "GET",
    endpoint: str = "",
    timeout: float = 10.0,
    json_data: Optional[dict] = None,
    max_retries: int = 3,
    retry_delay: float = 1.0
):
    """
    Make a request to a microservice with retry logic and connection pooling.
    
    Args:
        service_url: Base URL of the service
        method: HTTP method (GET, POST, etc.)
        endpoint: Endpoint path (e.g., "/stocks")
        timeout: Request timeout in seconds
        json_data: Optional JSON data for POST requests
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Initial delay between retries in seconds (default: 1.0)
    
    Returns:
        Response JSON data
    
    Raises:
        HTTPException: If request fails after all retries
    """
    service_name = service_url.split("://")[1].split(":")[0] if "://" in service_url else "service"
    url = f"{service_url}{endpoint}"
    client = get_http_client()
    
    last_exception = None
    
    # Use semaphore to limit concurrent requests
    async with _request_semaphore:
        for attempt in range(max_retries):
            try:
                # Use exponential backoff for retries
                if attempt > 0:
                    delay = retry_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying {service_name} request (attempt {attempt + 1}/{max_retries}) after {delay}s")
                    await asyncio.sleep(delay)
                
                # Make request
                if method.upper() == "GET":
                    response = await client.get(url, timeout=timeout)
                elif method.upper() == "POST":
                    response = await client.post(url, json=json_data, timeout=timeout)
                else:
                    raise HTTPException(status_code=400, detail=f"Unsupported method: {method}")
                
                # Check response status
                if response.status_code not in [200, 201]:
                    error_detail = "Unknown error"
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("detail", str(response.status_code))
                    except:
                        error_detail = f"HTTP {response.status_code}: {response.text[:200]}"
                    
                    # Retry on 5xx errors, but not on 4xx
                    if response.status_code >= 500 and attempt < max_retries - 1:
                        logger.warning(f"{service_name} returned {response.status_code}, retrying...")
                        last_exception = HTTPException(status_code=response.status_code, detail=error_detail)
                        continue
                    else:
                        raise HTTPException(status_code=response.status_code, detail=error_detail)
                
                # Success - return response
                return response.json()
                
            except httpx.TimeoutException as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.warning(f"{service_name} timeout (attempt {attempt + 1}/{max_retries}), retrying...")
                    continue
                else:
                    raise HTTPException(
                        status_code=504, 
                        detail=f"{service_name} service timeout after {max_retries} attempts: {str(e)}"
                    )
            except httpx.ConnectError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.warning(f"{service_name} connection error (attempt {attempt + 1}/{max_retries}), retrying...")
                    continue
                else:
                    raise HTTPException(
                        status_code=503,
                        detail=f"{service_name} service unavailable: All connection attempts failed. Service may be overloaded or down."
                    )
            except httpx.RequestError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.warning(f"{service_name} request error (attempt {attempt + 1}/{max_retries}), retrying...")
                    continue
                else:
                    raise HTTPException(
                        status_code=503,
                        detail=f"{service_name} service unavailable: {str(e)}"
                    )
            except HTTPException:
                # Re-raise HTTP exceptions (already handled)
                raise
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.warning(f"{service_name} error (attempt {attempt + 1}/{max_retries}), retrying...")
                    continue
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error calling {service_name} service after {max_retries} attempts: {str(e)}"
                    )
    
    # If we get here, all retries failed
    if last_exception:
        if isinstance(last_exception, HTTPException):
            raise last_exception
        raise HTTPException(
            status_code=503,
            detail=f"{service_name} service unavailable: All {max_retries} connection attempts failed"
        )

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

async def get_health_status():
    """Get health status for all services"""
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return await get_health_status()

@app.get("/api/health")
async def api_health_check():
    """API health check endpoint (for frontend)"""
    return await get_health_status()

# ==================== Stock Service Routes ====================

@app.get("/api/stocks")
async def list_stocks():
    """Lấy danh sách tất cả cổ phiếu"""
    return await make_service_request(STOCK_SERVICE_URL, "GET", "/stocks", timeout=30.0, max_retries=2)

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
    # Increase retries and timeout for DCF analysis (can take longer)
    return await make_service_request(
        DCF_SERVICE_URL,
        "POST",
        f"/analyze/{ticker}",
        timeout=300.0,
        max_retries=5,
        retry_delay=2.0
    )

@app.get("/api/analysis/{ticker}")
async def get_analysis_result(ticker: str):
    """Lấy kết quả phân tích DCF"""
    return await make_service_request(
        DCF_SERVICE_URL,
        "GET",
        f"/analysis/{ticker}",
        timeout=30.0,
        max_retries=3,
        retry_delay=1.0
    )

# ==================== Database Service Routes ====================

@app.get("/api/database/health")
async def get_database_health():
    """Lấy trạng thái health của database service"""
    return await make_service_request(DATABASE_SERVICE_URL, "GET", "/health")

@app.get("/api/database/stats")
async def get_database_stats():
    """Lấy thống kê database"""
    return await make_service_request(DATABASE_SERVICE_URL, "GET", "/api/database/stats")

@app.get("/api/database/tables")
async def get_database_tables():
    """Lấy danh sách các bảng trong database"""
    return await make_service_request(DATABASE_SERVICE_URL, "GET", "/api/database/tables")

@app.get("/api/database/tables/{table_name}/schema")
async def get_table_schema(table_name: str):
    """Lấy thông tin chi tiết schema của một bảng"""
    return await make_service_request(DATABASE_SERVICE_URL, "GET", f"/api/database/tables/{table_name}/schema")

@app.get("/api/database/tables/{table_name}/data")
async def get_table_data(
    table_name: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Lấy dữ liệu từ một bảng với phân trang"""
    return await make_service_request(DATABASE_SERVICE_URL, "GET", f"/api/database/tables/{table_name}/data?skip={skip}&limit={limit}")

@app.get("/api/database/relationships")
async def get_database_relationships():
    """Lấy thông tin về mối quan hệ giữa các bảng"""
    return await make_service_request(DATABASE_SERVICE_URL, "GET", "/api/database/relationships")

@app.post("/api/database/sync/growth-metrics")
async def sync_growth_metrics(ticker: Optional[str] = Query(None)):
    """Tính toán và sync growth metrics từ financial_data"""
    url = f"/api/database/sync/growth-metrics"
    if ticker:
        url += f"?ticker={ticker}"
    return await make_service_request(DATABASE_SERVICE_URL, "POST", url)

@app.post("/api/database/sync/{table_name}")
async def sync_table(
    table_name: str,
    ticker: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365)
):
    """Sync data for a specific table (runs in background)"""
    url = f"/api/database/sync/{table_name}"
    params = []
    if ticker:
        params.append(f"ticker={ticker}")
    if table_name == "market_data":
        params.append(f"days={days}")
    if params:
        url += "?" + "&".join(params)
    # Increase timeout for sync start (not the actual sync)
    return await make_service_request(DATABASE_SERVICE_URL, "POST", url, timeout=30.0)

@app.get("/api/database/sync/{table_name}/status")
async def get_sync_status(
    table_name: str,
    ticker: Optional[str] = Query(None)
):
    """Get sync status for a table"""
    url = f"/api/database/sync/{table_name}/status"
    if ticker:
        url += f"?ticker={ticker}"
    return await make_service_request(DATABASE_SERVICE_URL, "GET", url, timeout=10.0)

@app.get("/api/database/sync/jobs")
async def list_sync_jobs():
    """List all active sync jobs"""
    return await make_service_request(DATABASE_SERVICE_URL, "GET", "/api/database/sync/jobs", timeout=10.0)

# ==================== Logs Routes ====================

# Service container name mapping
SERVICE_CONTAINERS = {
    "gateway": "dcf-gateway",
    "dcf": "dcf-service",
    "stock": "dcf-stock",
    "database": "dcf-database",
    "frontend": "dcf-frontend",
    "postgres": "dcf-postgres",
    "redis": "dcf-redis"
}

@app.get("/api/logs")
async def get_logs(
    service: Optional[str] = Query(None, description="Service name (gateway, dcf, stock, database, frontend, postgres, redis)"),
    lines: Optional[int] = Query(100, description="Number of lines to retrieve (default: 100, max: 1000)")
):
    """
    Get logs from Docker containers.
    
    Args:
        service: Service name to get logs for. If None, returns logs for all services.
        lines: Number of lines to retrieve (default: 100, max: 1000)
    
    Returns:
        Dictionary with service names as keys and log lines as values
    """
    try:
        # Limit lines to prevent excessive data
        lines = min(max(1, lines), 1000)
        
        result = {}
        
        if service:
            # Get logs for specific service
            container_name = SERVICE_CONTAINERS.get(service.lower())
            if not container_name:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown service: {service}. Available services: {', '.join(SERVICE_CONTAINERS.keys())}"
                )
            
            try:
                # Try to read from log file first (service_logger writes to /app/logs/app/{service}.log)
                log_file_path = f"/app/logs/app/{service.lower()}.log"
                
                # If requesting gateway logs, read directly from file (same container)
                if service.lower() == "gateway":
                    try:
                        with open(log_file_path, 'r', encoding='utf-8', errors='replace') as f:
                            all_lines = f.readlines()
                            log_lines = [line.rstrip('\n') for line in all_lines[-lines:]]
                        if log_lines:
                            result[service] = {
                                "logs": log_lines,
                                "container": container_name,
                                "lines": len(log_lines),
                                "source": "log_file"
                            }
                        else:
                            raise FileNotFoundError("Log file is empty")
                    except (FileNotFoundError, IOError) as e:
                        # Fallback to Docker logs
                        pass
                else:
                    # For other services, use docker exec
                    cmd_read_file = ["docker", "exec", container_name, "tail", "-n", str(lines), log_file_path]
                    process_file = await asyncio.create_subprocess_exec(
                        *cmd_read_file,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout_file, stderr_file = await process_file.communicate()
                    
                    if process_file.returncode == 0 and stdout_file and stdout_file.strip():
                        log_output = stdout_file.decode('utf-8', errors='replace')
                        log_lines = [line.rstrip('\n') for line in log_output.split('\n') if line.strip()]
                        if log_lines:
                            result[service] = {
                                "logs": log_lines,
                                "container": container_name,
                                "lines": len(log_lines),
                                "source": "log_file"
                            }
                        else:
                            raise FileNotFoundError("Log file is empty")
                
                # If we didn't set result yet, fallback to Docker logs
                if service not in result:
                    # Fallback to Docker logs if file doesn't exist
                    cmd = ["docker", "logs", "--tail", str(lines), "--timestamps", container_name]
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode == 0:
                        log_output = stdout.decode('utf-8', errors='replace')
                        result[service] = {
                            "logs": log_output.split('\n') if log_output else [],
                            "container": container_name,
                            "lines": len(log_output.split('\n')) if log_output else 0,
                            "source": "docker_logs"
                        }
                    else:
                        error_msg = stderr.decode('utf-8', errors='replace')
                        # Provide user-friendly error messages
                        if "No such file or directory" in error_msg or "No such container" in error_msg:
                            friendly_msg = "No logs available for this service. The service may not have generated any logs yet."
                        elif "permission denied" in error_msg.lower():
                            friendly_msg = "Permission denied. Unable to access logs for this service."
                        else:
                            friendly_msg = f"Unable to retrieve logs: {error_msg[:100]}"
                        
                        result[service] = {
                            "logs": [],
                            "error": friendly_msg,
                            "container": container_name,
                            "lines": 0
                        }
            except Exception as e:
                error_str = str(e)
                # Provide user-friendly error messages
                if "No such file or directory" in error_str or "No such container" in error_str:
                    friendly_msg = "No logs available for this service. The service may not have generated any logs yet."
                elif "permission denied" in error_str.lower():
                    friendly_msg = "Permission denied. Unable to access logs for this service."
                else:
                    friendly_msg = f"Unable to retrieve logs: {error_str[:100]}"
                
                result[service] = {
                    "logs": [],
                    "error": friendly_msg,
                    "container": container_name,
                    "lines": 0
                }
        else:
            # Get logs for all services
            for svc_name, container_name in SERVICE_CONTAINERS.items():
                try:
                    log_file_path = f"/app/logs/app/{svc_name.lower()}.log"
                    
                    # If gateway, read directly from file (same container)
                    if svc_name.lower() == "gateway":
                        try:
                            with open(log_file_path, 'r', encoding='utf-8', errors='replace') as f:
                                all_lines = f.readlines()
                                log_lines = [line.rstrip('\n') for line in all_lines[-lines:]]
                            if log_lines:
                                result[svc_name] = {
                                    "logs": log_lines,
                                    "container": container_name,
                                    "lines": len(log_lines),
                                    "source": "log_file"
                                }
                            else:
                                raise FileNotFoundError("Log file is empty")
                        except (FileNotFoundError, IOError):
                            # Fallback to Docker logs
                            pass
                    else:
                        # For other services, use docker exec to read log file
                        cmd_read_file = ["docker", "exec", container_name, "tail", "-n", str(lines), log_file_path]
                        process_file = await asyncio.create_subprocess_exec(
                            *cmd_read_file,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        stdout_file, stderr_file = await process_file.communicate()
                        
                        if process_file.returncode == 0 and stdout_file and stdout_file.strip():
                            log_output = stdout_file.decode('utf-8', errors='replace')
                            log_lines = [line.rstrip('\n') for line in log_output.split('\n') if line.strip()]
                            if log_lines:
                                result[svc_name] = {
                                    "logs": log_lines,
                                    "container": container_name,
                                    "lines": len(log_lines),
                                    "source": "log_file"
                                }
                            else:
                                raise FileNotFoundError("Log file is empty")
                    
                    # If we didn't set result yet, fallback to Docker logs
                    if svc_name not in result:
                        cmd = ["docker", "logs", "--tail", str(lines), "--timestamps", container_name]
                        process = await asyncio.create_subprocess_exec(
                            *cmd,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        stdout, stderr = await process.communicate()
                        
                        if process.returncode == 0:
                            log_output = stdout.decode('utf-8', errors='replace')
                            log_lines = [line.rstrip('\n') for line in log_output.split('\n') if line.strip()]
                            result[svc_name] = {
                                "logs": log_lines,
                                "container": container_name,
                                "lines": len(log_lines),
                                "source": "docker_logs"
                            }
                        else:
                            error_msg = stderr.decode('utf-8', errors='replace')
                            # Provide user-friendly error messages
                        if "No such file or directory" in error_msg or "No such container" in error_msg:
                            friendly_msg = "No logs available for this service. The service may not have generated any logs yet."
                        elif "permission denied" in error_msg.lower():
                            friendly_msg = "Permission denied. Unable to access logs for this service."
                        else:
                            friendly_msg = f"Unable to retrieve logs: {error_msg[:100]}"
                        
                        result[svc_name] = {
                            "logs": [],
                            "error": friendly_msg,
                            "container": container_name,
                            "lines": 0
                        }
                except Exception as e:
                    error_str = str(e)
                    # Provide user-friendly error messages
                    if "No such file or directory" in error_str or "No such container" in error_str:
                        friendly_msg = "No logs available for this service. The service may not have generated any logs yet."
                    elif "permission denied" in error_str.lower():
                        friendly_msg = "Permission denied. Unable to access logs for this service."
                    else:
                        friendly_msg = f"Unable to retrieve logs: {error_str[:100]}"
                    
                    result[svc_name] = {
                        "logs": [],
                        "error": friendly_msg,
                        "container": container_name,
                        "lines": 0
                    }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "service": service,
            "lines": lines,
            "logs": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")

# ==================== Monitoring & Architecture Routes ====================

@app.get("/api/architecture")
async def get_architecture():
    """Lấy thông tin kiến trúc hệ thống"""
    return {
        "architecture": {
            "type": "microservices",
            "services": [
                {
                    "name": "Frontend",
                    "type": "nginx",
                    "port": 8081,
                    "description": "Static file server và reverse proxy",
                    "dependencies": ["gateway"]
                },
                {
                    "name": "Gateway",
                    "type": "fastapi",
                    "port": 8000,
                    "description": "API Gateway - routes requests to microservices",
                    "dependencies": ["dcf", "stock", "database", "postgres", "redis"]
                },
                {
                    "name": "DCF Service",
                    "type": "fastapi",
                    "port": 8001,
                    "description": "DCF Analysis Service - xử lý phân tích DCF",
                    "dependencies": ["postgres", "redis"]
                },
                {
                    "name": "Stock Service",
                    "type": "fastapi",
                    "port": 8002,
                    "description": "Stock Data Service - quản lý dữ liệu cổ phiếu",
                    "dependencies": ["postgres", "redis"]
                },
                {
                    "name": "Database Service",
                    "type": "fastapi",
                    "port": 8003,
                    "description": "Database Management Service - quản lý database operations",
                    "dependencies": ["postgres", "redis"]
                },
                {
                    "name": "PostgreSQL",
                    "type": "database",
                    "port": 5432,
                    "description": "Primary database",
                    "dependencies": []
                },
                {
                    "name": "Redis",
                    "type": "cache",
                    "port": 6379,
                    "description": "Cache và session storage",
                    "dependencies": []
                }
            ],
            "connections": [
                {"from": "Frontend", "to": "Gateway", "protocol": "HTTP", "endpoints": ["/api/*"]},
                {"from": "Gateway", "to": "DCF Service", "protocol": "HTTP", "endpoints": ["/analyze/*", "/analysis/*"]},
                {"from": "Gateway", "to": "Stock Service", "protocol": "HTTP", "endpoints": ["/stocks/*"]},
                {"from": "Gateway", "to": "Database Service", "protocol": "HTTP", "endpoints": ["/api/database/*"]},
                {"from": "DCF Service", "to": "PostgreSQL", "protocol": "PostgreSQL"},
                {"from": "DCF Service", "to": "Redis", "protocol": "Redis"},
                {"from": "Stock Service", "to": "PostgreSQL", "protocol": "PostgreSQL"},
                {"from": "Stock Service", "to": "Redis", "protocol": "Redis"},
                {"from": "Database Service", "to": "PostgreSQL", "protocol": "PostgreSQL"},
                {"from": "Database Service", "to": "Redis", "protocol": "Redis"},
                {"from": "Gateway", "to": "PostgreSQL", "protocol": "PostgreSQL"},
                {"from": "Gateway", "to": "Redis", "protocol": "Redis"}
            ]
        }
    }

@app.get("/api/monitoring")
async def get_monitoring_data():
    """Lấy thông tin monitoring tổng hợp từ tất cả services"""
    try:
        # Get health status
        health_data = await get_health_status()
        
        # Get DCF service status (running analyses)
        dcf_status = {}
        try:
            dcf_status_response = await make_service_request(
                DCF_SERVICE_URL, 
                "GET", 
                "/status", 
                timeout=10.0,
                max_retries=2  # Fewer retries for status checks
            )
            dcf_status = dcf_status_response
        except Exception as e:
            dcf_status = {"error": str(e)}
        
        # Get Stock service status
        stock_status = {}
        try:
            stock_status_response = await make_service_request(
                STOCK_SERVICE_URL, 
                "GET", 
                "/status", 
                timeout=10.0,
                max_retries=2
            )
            stock_status = stock_status_response
        except Exception as e:
            stock_status = {"error": str(e)}
        
        # Get Database service stats
        db_stats = {}
        try:
            try:
                db_stats_response = await make_service_request(
                    DATABASE_SERVICE_URL, 
                    "GET", 
                    "/api/database/stats", 
                    timeout=10.0,
                    max_retries=2
                )
            except HTTPException:
                # Database service unavailable - continue without it
                db_stats_response = {"error": "Database service unavailable"}
            db_stats = db_stats_response
        except Exception as e:
            db_stats = {"error": str(e)}
        
        # Convert analyses dict to array format
        analyses_dict = dcf_status.get("analyses", {})
        analyses_list = []
        if isinstance(analyses_dict, dict):
            for ticker, analysis_data in analyses_dict.items():
                analyses_list.append({
                    "ticker": ticker,
                    **analysis_data
                })
        elif isinstance(analyses_dict, list):
            analyses_list = analyses_dict
        
        return {
            "timestamp": datetime.now().isoformat(),
            "health": health_data,
            "services": {
                "dcf": {
                    "status": health_data.get("services", {}).get("dcf", {}).get("status", "unknown"),
                    "running_analyses": dcf_status.get("running_analyses", 0),
                    "analyses": analyses_list
                },
                "stock": {
                    "status": health_data.get("services", {}).get("stock", {}).get("status", "unknown"),
                    "details": stock_status
                },
                "database": {
                    "status": health_data.get("services", {}).get("database", {}).get("status", "unknown"),
                    "stats": db_stats
                }
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

