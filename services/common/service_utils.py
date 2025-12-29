"""
Common utilities for microservices
Provides shared functionality for path resolution, CORS, health checks, etc.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
from datetime import datetime


def get_project_root() -> Path:
    """
    Get project root directory.
    Handles both Docker (/app) and local development environments.
    
    Returns:
        Path: Project root directory
    """
    if Path('/app').exists():
        return Path('/app')
    else:
        # Local development: go up from services/{service}/main.py to project root
        return Path(__file__).parent.parent.parent


def setup_cors(app: FastAPI, allow_origins: Optional[list] = None) -> None:
    """
    Setup CORS middleware for FastAPI app.
    
    Args:
        app: FastAPI application instance
        allow_origins: List of allowed origins (default: ["*"])
    """
    if allow_origins is None:
        allow_origins = ["*"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_project_path(project_root: Optional[Path] = None) -> Path:
    """
    Setup project root path and add to sys.path.
    
    Args:
        project_root: Optional project root path (if None, will be detected)
    
    Returns:
        Path: Project root directory
    """
    if project_root is None:
        project_root = get_project_root()
    
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    
    return project_root


async def check_service_health(service_url: str, timeout: float = 5.0) -> Dict[str, Any]:
    """
    Check health of a microservice.
    
    Args:
        service_url: Base URL of the service
        timeout: Request timeout in seconds
    
    Returns:
        Dict with service health status
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{service_url}/health", timeout=timeout)
            if response.status_code == 200:
                return {"status": "healthy", "data": response.json()}
            else:
                return {"status": "unhealthy", "status_code": response.status_code}
    except httpx.TimeoutException:
        return {"status": "timeout", "error": "Service did not respond in time"}
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


def get_database_health_status() -> Dict[str, Any]:
    """
    Get database health status.
    
    Returns:
        Dict with database connection status
    """
    try:
        from src.utils.database_client import check_database_connection, get_database_info
        db_connected = check_database_connection()
        health_status = {
            "database": "connected" if db_connected else "disconnected"
        }
        if db_connected:
            health_status["database_info"] = get_database_info()
        return health_status
    except Exception as e:
        return {"database": f"error: {str(e)}"}


def create_health_response(
    service_name: str,
    include_database: bool = False,
    additional_status: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create standardized health check response.
    
    Args:
        service_name: Name of the service
        include_database: Whether to include database health check
        additional_status: Additional status information to include
    
    Returns:
        Dict with health check response
    """
    health_status = {
        "status": "healthy",
        "service": service_name,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if include_database:
        health_status.update(get_database_health_status())
    
    if additional_status:
        health_status.update(additional_status)
    
    return health_status


def get_service_urls() -> Dict[str, str]:
    """
    Get service URLs from environment variables.
    
    Returns:
        Dict mapping service names to URLs
    """
    return {
        "dcf": os.getenv("DCF_SERVICE_URL", "http://dcf:8001"),
        "stock": os.getenv("STOCK_SERVICE_URL", "http://stock:8002"),
        "database": os.getenv("DATABASE_SERVICE_URL", "http://database:8003"),
    }

