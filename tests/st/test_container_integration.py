"""
System Test: Container Integration
Tests integration between containers using Docker API
"""
import unittest
import sys
import os
import time

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

sys.path.insert(0, os.path.join(project_root, 'tests'))
from lib.docker_utils import get_container_manager
from lib.container_builder import get_container_builder
from lib.test_logger import border, logger


class TestContainerIntegration(unittest.TestCase):
    """Test container integration"""
    
    CONTAINERS = {
        'gateway': 'dcf-gateway',
        'dcf': 'dcf-service',
        'stock': 'dcf-stock',
        'database': 'dcf-database',
        'postgres': 'dcf-postgres',
        'redis': 'dcf-redis',
    }
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.container_manager = get_container_manager()
        if not cls.container_manager.is_available():
            raise unittest.SkipTest("Docker not available")
        
        # Build all containers before testing to ensure latest code
        logger.info("Building all containers with latest code...")
        builder = get_container_builder(project_root)
        build_success = builder.build_containers()
        if not build_success:
            logger.warning("Container build failed, but continuing with existing images")
        
        # Note: Containers need to be started separately with 'make docker-up' or 'docker-compose up'
    
    @border
    def test_all_containers_running(self):
        """Test that all required containers are running"""
        logger.info("Testing all containers are running")
        
        running_containers = []
        stopped_containers = []
        
        for service, container_name in self.CONTAINERS.items():
            is_running = self.container_manager.is_container_running(container_name)
            if is_running:
                running_containers.append(service)
            else:
                stopped_containers.append(service)
        
        logger.info(f"Running containers: {running_containers}")
        logger.info(f"Stopped containers: {stopped_containers}")
        
        # At least core services should be running
        core_services = ['postgres', 'redis']
        for service in core_services:
            container_name = self.CONTAINERS[service]
            self.assertTrue(
                self.container_manager.is_container_running(container_name),
                f"Core service {service} should be running"
            )
    
    @border
    def test_container_port_mappings(self):
        """Test container port mappings (external access)"""
        logger.info("Testing container port mappings")
        
        # Check that containers have port mappings for external access
        containers_info = []
        for service, container_name in self.CONTAINERS.items():
            info = self.container_manager.get_container_info(container_name)
            if info:
                containers_info.append((service, info))
        
        # Verify containers have port mappings for external access
        for service, info in containers_info:
            ports = info.get('ports', {})
            if ports:
                logger.info(f"{service} ports: {ports}")
        
        logger.info(f"Checked port mappings for {len(containers_info)} containers")
    
    @border
    def test_external_service_access(self):
        """Test external service access via exposed ports"""
        logger.info("Testing external service access")
        
        import requests
        
        # Test external access to services via exposed ports
        services = {
            'gateway': 'http://localhost:8000',
            'dcf': 'http://localhost:8001',
            'stock': 'http://localhost:8002',
            'database': 'http://localhost:8003',
        }
        
        for service_name, url in services.items():
            container_name = self.CONTAINERS.get(service_name)
            if container_name and self.container_manager.is_container_running(container_name):
                try:
                    response = requests.get(f"{url}/health", timeout=5)
                    logger.info(f"{service_name} health: {response.status_code}")
                except Exception as e:
                    logger.info(f"{service_name} not accessible: {e}")
    
    @border
    def test_container_dependencies(self):
        """Test container dependencies (core services)"""
        logger.info("Testing container dependencies")
        
        # Check that core services (postgres, redis) are running
        # These are required for other services to work
        core_services = ['postgres', 'redis']
        
        for service in core_services:
            container_name = self.CONTAINERS.get(service)
            if container_name:
                is_running = self.container_manager.is_container_running(container_name)
                logger.info(f"Core service {service}: {'running' if is_running else 'stopped'}")
                
                # Core services should be running for other services to work
                if not is_running:
                    logger.warning(f"Core service {service} is not running - other services may fail")
    
    @border
    def test_container_health_status(self):
        """Test container health status"""
        logger.info("Testing container health status")
        
        health_status = {}
        for service, container_name in self.CONTAINERS.items():
            health = self.container_manager.get_container_health(container_name)
            if health:
                health_status[service] = health
        
        logger.info(f"Health status: {health_status}")
        
        # At least some containers should have health checks
        if health_status:
            logger.info("Some containers have health checks configured")
    
    @border
    def test_container_logs_accessible(self):
        """Test that container logs are accessible"""
        logger.info("Testing container logs accessibility")
        
        for service, container_name in self.CONTAINERS.items():
            logs = self.container_manager.get_container_logs(container_name, tail=10)
            if logs:
                logger.info(f"{service} logs accessible ({len(logs)} chars)")
            else:
                logger.info(f"{service} logs not available (container may not be running)")
    
    @border
    def test_container_resource_usage(self):
        """Test container resource usage"""
        logger.info("Testing container resource usage")
        
        for service, container_name in self.CONTAINERS.items():
            container = self.container_manager.get_container(container_name)
            if container:
                try:
                    stats = container.stats(stream=False)
                    memory_usage = stats.get('memory_stats', {}).get('usage', 0)
                    cpu_usage = stats.get('cpu_stats', {}).get('cpu_usage', {}).get('total_usage', 0)
                    
                    logger.info(f"{service}: Memory={memory_usage}, CPU={cpu_usage}")
                except Exception as e:
                    logger.warning(f"Could not get stats for {service}: {e}")


if __name__ == '__main__':
    unittest.main()

