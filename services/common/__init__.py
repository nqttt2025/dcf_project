"""
Common utilities for microservices
"""
from .service_utils import (
    get_project_root,
    setup_cors,
    setup_project_path,
    check_service_health,
    get_database_health_status,
    create_health_response,
    get_service_urls,
)

__all__ = [
    "get_project_root",
    "setup_cors",
    "setup_project_path",
    "check_service_health",
    "get_database_health_status",
    "create_health_response",
    "get_service_urls",
]

