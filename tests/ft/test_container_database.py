"""
Function Test: Database Container
Tests the Database service container functionality using Docker API
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


class TestDatabaseContainer(unittest.TestCase):
    """Test Database container functionality"""
    
    CONTAINER_NAME = "dcf-database"
    SERVICE_URL = "http://localhost:8003"
    POSTGRES_CONTAINER = "dcf-postgres"
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.container_manager = get_container_manager()
        if not cls.container_manager.is_available():
            raise unittest.SkipTest("Docker not available")
        
        # Build containers before testing to ensure latest code
        logger.info("Building database container with latest code...")
        builder = get_container_builder(project_root)
        build_success = builder.build_containers(services=['database'])
        if not build_success:
            logger.warning("Container build failed, but continuing with existing images")
        
        # Note: Containers need to be started separately with 'make docker-up' or 'docker-compose up'
    
    @border
    def test_container_exists(self):
        """Test that Database container exists"""
        logger.info("Testing Database container existence")
        
        container = self.container_manager.get_container(self.CONTAINER_NAME)
        self.assertIsNotNone(container, f"Container {self.CONTAINER_NAME} should exist")
        
        logger.info(f"Container found: {container.name}")
    
    @border
    def test_container_running(self):
        """Test that Database container is running"""
        logger.info("Testing Database container status")
        
        is_running = self.container_manager.is_container_running(self.CONTAINER_NAME)
        if not is_running:
            self.skipTest(f"Container {self.CONTAINER_NAME} is not running")
        
        status = self.container_manager.get_container_status(self.CONTAINER_NAME)
        self.assertEqual(status, 'running', f"Container should be running, got: {status}")
        
        logger.info(f"Container status: {status}")
    
    @border
    def test_postgres_container(self):
        """Test PostgreSQL container"""
        logger.info("Testing PostgreSQL container")
        
        is_running = self.container_manager.is_container_running(self.POSTGRES_CONTAINER)
        if not is_running:
            self.skipTest(f"PostgreSQL container {self.POSTGRES_CONTAINER} is not running")
        
        # Check PostgreSQL health
        exit_code, output = self.container_manager.exec_command(
            self.POSTGRES_CONTAINER,
            "pg_isready -U dcf_user -d dcf_db"
        )
        
        self.assertEqual(exit_code, 0, f"PostgreSQL should be ready, got: {output}")
        logger.info("PostgreSQL is ready")
    
    @border
    def test_service_health_endpoint(self):
        """Test Database service health endpoint"""
        logger.info("Testing Database service health endpoint")
        
        is_available = self.container_manager.check_service_health(self.SERVICE_URL)
        if not is_available:
            self.skipTest("Database service not available")
        
        service_info = self.container_manager.get_service_info(self.SERVICE_URL)
        self.assertIsNotNone(service_info, "Should get service info")
        self.assertIn('status', service_info)
        
        logger.info(f"Service health: {service_info}")


if __name__ == '__main__':
    unittest.main()

