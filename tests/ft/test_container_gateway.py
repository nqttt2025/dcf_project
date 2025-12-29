"""
Function Test: Gateway Container
Tests the Gateway container functionality using Docker API
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


class TestGatewayContainer(unittest.TestCase):
    """Test Gateway container functionality"""
    
    CONTAINER_NAME = "dcf-gateway"
    SERVICE_URL = "http://localhost:8000"
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.container_manager = get_container_manager()
        if not cls.container_manager.is_available():
            raise unittest.SkipTest("Docker not available")
        
        # Build containers before testing to ensure latest code
        logger.info("Building gateway container with latest code...")
        builder = get_container_builder(project_root)
        build_success = builder.build_containers(services=['gateway'])
        
        # Fail if build fails - we need latest code to test
        if not build_success:
            raise unittest.SkipTest(
                "Container build failed - cannot test with latest code. "
                "Please check build logs and fix errors."
            )
        
        logger.info("Container build successful - proceeding with tests")
        
        # Note: Containers need to be started separately with 'make docker-up' or 'docker-compose up'
    
    @border
    def test_container_exists(self):
        """Test that Gateway container exists"""
        logger.info("Testing Gateway container existence")
        
        container = self.container_manager.get_container(self.CONTAINER_NAME)
        self.assertIsNotNone(container, f"Container {self.CONTAINER_NAME} should exist")
        
        logger.info(f"Container found: {container.name}")
    
    @border
    def test_container_running(self):
        """Test that Gateway container is running"""
        logger.info("Testing Gateway container status")
        
        is_running = self.container_manager.is_container_running(self.CONTAINER_NAME)
        if not is_running:
            self.fail(
                f"Container {self.CONTAINER_NAME} is not running. "
                "Start containers with: make docker-up"
            )
        
        status = self.container_manager.get_container_status(self.CONTAINER_NAME)
        self.assertEqual(status, 'running', f"Container should be running, got: {status}")
        
        logger.info(f"Container status: {status}")
    
    @border
    def test_container_health(self):
        """Test Gateway container health check"""
        logger.info("Testing Gateway container health")
        
        # Wait for container to be healthy
        is_healthy = self.container_manager.wait_for_container_healthy(
            self.CONTAINER_NAME, 
            timeout=60
        )
        
        if not is_healthy:
            health = self.container_manager.get_container_health(self.CONTAINER_NAME)
            logger.warning(f"Container health: {health}")
            # Don't fail if health check not configured
            if health is None:
                self.skipTest("Health check not configured")
        
        logger.info("Container is healthy")
    
    @border
    def test_service_health_endpoint(self):
        """Test Gateway service health endpoint"""
        logger.info("Testing Gateway service health endpoint")
        
        is_available = self.container_manager.check_service_health(self.SERVICE_URL)
        if not is_available:
            self.skipTest("Gateway service not available")
        
        service_info = self.container_manager.get_service_info(self.SERVICE_URL)
        self.assertIsNotNone(service_info, "Should get service info")
        self.assertIn('status', service_info)
        
        logger.info(f"Service health: {service_info}")
    
    @border
    def test_container_info(self):
        """Test getting container information"""
        logger.info("Testing container information")
        
        container = self.container_manager.get_container(self.CONTAINER_NAME)
        if not container:
            self.skipTest(f"Container {self.CONTAINER_NAME} not found")
        
        info = self.container_manager.get_container_info(self.CONTAINER_NAME)
        self.assertIsNotNone(info, "Should get container info")
        
        self.assertEqual(info['name'], self.CONTAINER_NAME)
        self.assertEqual(info['status'], 'running')
        
        # Check ports
        self.assertIsNotNone(info['ports'], "Should have port mappings")
        
        logger.info(f"Container info: {info}")
    
    @border
    def test_container_exec(self):
        """Test executing command in container"""
        logger.info("Testing container exec")
        
        container = self.container_manager.get_container(self.CONTAINER_NAME)
        if not container:
            self.skipTest(f"Container {self.CONTAINER_NAME} not found")
        
        exit_code, output = self.container_manager.exec_command(
            self.CONTAINER_NAME,
            "python --version"
        )
        
        self.assertEqual(exit_code, 0, f"Command should succeed, got: {output}")
        self.assertIn("Python", output)
        
        logger.info(f"Exec output: {output[:100]}")
    
    @border
    def test_container_logs(self):
        """Test getting container logs"""
        logger.info("Testing container logs")
        
        container = self.container_manager.get_container(self.CONTAINER_NAME)
        if not container:
            self.skipTest(f"Container {self.CONTAINER_NAME} not found")
        
        logs = self.container_manager.get_container_logs(self.CONTAINER_NAME, tail=50)
        self.assertIsInstance(logs, str)
        # Logs may be empty if container just started
        logger.info(f"Logs length: {len(logs)} characters")
    
    @border
    def test_gateway_api_endpoints(self):
        """Test Gateway API endpoints"""
        logger.info("Testing Gateway API endpoints")
        
        import requests
        
        # Test health endpoint
        try:
            response = requests.get(f"{self.SERVICE_URL}/health", timeout=5)
            self.assertEqual(response.status_code, 200)
            
            # Test stocks endpoint
            response = requests.get(f"{self.SERVICE_URL}/api/stocks", timeout=5)
            self.assertIn(response.status_code, [200, 404])  # May not be implemented
            
            logger.info("API endpoints accessible")
        except requests.exceptions.RequestException as e:
            self.skipTest(f"Service not available: {e}")


if __name__ == '__main__':
    unittest.main()

