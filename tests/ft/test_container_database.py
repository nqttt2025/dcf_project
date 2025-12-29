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
            logger.error("Docker not available - skipping all tests")
            raise unittest.SkipTest("Docker not available")
        
        # Build containers before testing to ensure latest code
        logger.info("Building database container with latest code...")
        builder = get_container_builder(project_root)
        build_success = builder.build_containers(services=['database'])
        
        # Fail if build fails - we need latest code to test
        if not build_success:
            logger.error("Container build failed - cannot test with latest code")
            raise unittest.SkipTest(
                "Container build failed - cannot test with latest code. "
                "Please check build logs and fix errors."
            )
        
        logger.info("Container build successful - proceeding with tests")
        
        # Note: Containers need to be started separately with 'make docker-up' or 'docker-compose up'
    
    @border
    def test_container_exists(self):
        """Test that Database container exists"""
        logger.info("Testing Database container existence")
        
        container = self.container_manager.get_container(self.CONTAINER_NAME)
        if not container:
            logger.error(f"Container {self.CONTAINER_NAME} not found")
            self.fail(
                f"Container {self.CONTAINER_NAME} not found. "
                "Container may not be running. Start with: make docker-up"
            )
        
        self.assertIsNotNone(container, f"Container {self.CONTAINER_NAME} should exist")
        logger.info(f"Container found: {container.name}")
    
    @border
    def test_container_running(self):
        """Test that Database container is running"""
        logger.info("Testing Database container status")
        
        is_running = self.container_manager.is_container_running(self.CONTAINER_NAME)
        if not is_running:
            logger.error(f"Container {self.CONTAINER_NAME} is not running")
            self.fail(
                f"Container {self.CONTAINER_NAME} is not running. "
                "Start containers with: make docker-up"
            )
        
        status = self.container_manager.get_container_status(self.CONTAINER_NAME)
        self.assertEqual(status, 'running', f"Container should be running, got: {status}")
        logger.info(f"Container status: {status}")
    
    @border
    def test_postgres_container(self):
        """Test PostgreSQL container"""
        logger.info("Testing PostgreSQL container")
        
        is_running = self.container_manager.is_container_running(self.POSTGRES_CONTAINER)
        if not is_running:
            logger.error(f"PostgreSQL container {self.POSTGRES_CONTAINER} is not running")
            self.fail(
                f"PostgreSQL container {self.POSTGRES_CONTAINER} is not running. "
                "Start containers with: make docker-up"
            )
        
        # Check PostgreSQL health
        logger.info("Checking PostgreSQL health...")
        exit_code, output = self.container_manager.exec_command(
            self.POSTGRES_CONTAINER,
            "pg_isready -U dcf_user -d dcf_db"
        )
        
        if exit_code != 0:
            logger.error(f"PostgreSQL health check failed: {output}")
            self.fail(f"PostgreSQL should be ready, got exit code {exit_code}: {output}")
        
        logger.info("PostgreSQL is ready")
    
    @border
    def test_service_health_endpoint(self):
        """Test Database service health endpoint"""
        logger.info("Testing Database service health endpoint")
        
        # First verify container is running
        if not self.container_manager.is_container_running(self.CONTAINER_NAME):
            logger.error(f"Container {self.CONTAINER_NAME} is not running")
            self.fail(
                f"Container {self.CONTAINER_NAME} is not running. "
                "Start containers with: make docker-up"
            )
        
        is_available = self.container_manager.check_service_health(self.SERVICE_URL)
        if not is_available:
            logger.error(f"Database service at {self.SERVICE_URL} is not available")
            self.fail(
                f"Database service at {self.SERVICE_URL} is not available. "
                "Check if service is running and health endpoint is working."
            )
        
        service_info = self.container_manager.get_service_info(self.SERVICE_URL)
        self.assertIsNotNone(service_info, "Should get service info")
        self.assertIn('status', service_info)
        
        logger.info(f"Service health: {service_info}")


if __name__ == '__main__':
    unittest.main()

