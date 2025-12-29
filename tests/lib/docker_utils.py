"""
Docker Container Test Utilities
Provides helper functions for testing Docker containers using Docker API
"""
import docker
import time
import requests
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class DockerContainerManager:
    """Manages Docker containers for testing"""
    
    def __init__(self):
        """Initialize Docker client"""
        try:
            self.client = docker.from_env()
            self.client.ping()  # Test connection
        except Exception as e:
            logger.warning(f"Docker not available: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Docker is available"""
        return self.client is not None
    
    def get_container(self, container_name: str) -> Optional[docker.models.containers.Container]:
        """Get container by name"""
        if not self.is_available():
            return None
        
        try:
            containers = self.client.containers.list(all=True, filters={"name": container_name})
            return containers[0] if containers else None
        except Exception as e:
            logger.error(f"Error getting container {container_name}: {e}")
            return None
    
    def is_container_running(self, container_name: str) -> bool:
        """Check if container is running"""
        container = self.get_container(container_name)
        if not container:
            return False
        return container.status == 'running'
    
    def get_container_status(self, container_name: str) -> Optional[str]:
        """Get container status"""
        container = self.get_container(container_name)
        return container.status if container else None
    
    def get_container_health(self, container_name: str) -> Optional[str]:
        """Get container health status"""
        container = self.get_container(container_name)
        if not container:
            return None
        
        try:
            health = container.attrs.get('State', {}).get('Health', {})
            return health.get('Status') if health else None
        except Exception:
            return None
    
    def wait_for_container_healthy(self, container_name: str, timeout: int = 60) -> bool:
        """Wait for container to become healthy"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            health = self.get_container_health(container_name)
            if health == 'healthy':
                return True
            elif health == 'unhealthy':
                return False
            time.sleep(2)
        return False
    
    def exec_command(self, container_name: str, command: str, user: str = None) -> Tuple[int, str]:
        """Execute command in container"""
        container = self.get_container(container_name)
        if not container:
            return 1, f"Container {container_name} not found"
        
        try:
            if user:
                exec_result = container.exec_run(command, user=user)
            else:
                exec_result = container.exec_run(command)
            return exec_result.exit_code, exec_result.output.decode('utf-8')
        except Exception as e:
            return 1, str(e)
    
    def get_container_logs(self, container_name: str, tail: int = 100) -> str:
        """Get container logs"""
        container = self.get_container(container_name)
        if not container:
            return ""
        
        try:
            logs = container.logs(tail=tail).decode('utf-8')
            return logs
        except Exception as e:
            logger.error(f"Error getting logs for {container_name}: {e}")
            return ""
    
    def get_container_info(self, container_name: str) -> Optional[Dict]:
        """Get container information"""
        container = self.get_container(container_name)
        if not container:
            return None
        
        try:
            attrs = container.attrs
            return {
                'name': attrs.get('Name', '').lstrip('/'),
                'status': attrs.get('State', {}).get('Status'),
                'health': attrs.get('State', {}).get('Health', {}).get('Status'),
                'image': attrs.get('Config', {}).get('Image'),
                'ports': attrs.get('NetworkSettings', {}).get('Ports', {}),
                'env': attrs.get('Config', {}).get('Env', []),
            }
        except Exception as e:
            logger.error(f"Error getting container info: {e}")
            return None
    
    def list_containers(self, filters: Dict = None) -> List[Dict]:
        """List containers matching filters"""
        if not self.is_available():
            return []
        
        try:
            containers = self.client.containers.list(all=True, filters=filters or {})
            return [self.get_container_info(c.name.lstrip('/')) for c in containers]
        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            return []
    
    def check_service_health(self, service_url: str, timeout: int = 5) -> bool:
        """Check service health via HTTP"""
        try:
            response = requests.get(f"{service_url}/health", timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_service_info(self, service_url: str) -> Optional[Dict]:
        """Get service information via HTTP"""
        try:
            response = requests.get(f"{service_url}/health", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None


# Singleton instance
_container_manager = None


def get_container_manager() -> DockerContainerManager:
    """Get singleton instance of DockerContainerManager"""
    global _container_manager
    if _container_manager is None:
        _container_manager = DockerContainerManager()
    return _container_manager

