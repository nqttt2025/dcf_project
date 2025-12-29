"""
Function Test: Stock Container
Tests the Stock service container functionality using Docker API
"""
import unittest
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

sys.path.insert(0, os.path.join(project_root, 'tests'))
from lib.docker_utils import get_container_manager
from lib.container_builder import get_container_builder
from lib.test_logger import border, logger


class TestStockContainer(unittest.TestCase):
    """Test Stock container functionality"""
    
    CONTAINER_NAME = "dcf-stock"
    SERVICE_URL = "http://localhost:8002"
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.container_manager = get_container_manager()
        if not cls.container_manager.is_available():
            raise unittest.SkipTest("Docker not available")
        
        # Build containers before testing to ensure latest code
        logger.info("Building stock container with latest code...")
        builder = get_container_builder(project_root)
        build_success = builder.build_containers(services=['stock'])
        if not build_success:
            logger.warning("Container build failed, but continuing with existing images")
        
        # Note: Containers need to be started separately with 'make docker-up' or 'docker-compose up'
    
    @border
    def test_container_exists(self):
        """Test that Stock container exists"""
        logger.info("Testing Stock container existence")
        
        container = self.container_manager.get_container(self.CONTAINER_NAME)
        if not container:
            self.skipTest(f"Container {self.CONTAINER_NAME} not found (may not be built)")
        
        logger.info(f"Container found: {container.name}")
    
    @border
    def test_container_running(self):
        """Test that Stock container is running"""
        logger.info("Testing Stock container status")
        
        is_running = self.container_manager.is_container_running(self.CONTAINER_NAME)
        if not is_running:
            self.skipTest(f"Container {self.CONTAINER_NAME} is not running")
        
        status = self.container_manager.get_container_status(self.CONTAINER_NAME)
        self.assertEqual(status, 'running', f"Container should be running, got: {status}")
        
        logger.info(f"Container status: {status}")
    
    @border
    def test_service_health_endpoint(self):
        """Test Stock service health endpoint"""
        logger.info("Testing Stock service health endpoint")
        
        is_available = self.container_manager.check_service_health(self.SERVICE_URL)
        if not is_available:
            self.skipTest("Stock service not available")
        
        service_info = self.container_manager.get_service_info(self.SERVICE_URL)
        self.assertIsNotNone(service_info, "Should get service info")
        self.assertIn('status', service_info)
        
        logger.info(f"Service health: {service_info}")


if __name__ == '__main__':
    unittest.main()

