"""
Function Test: Frontend Container
Tests the Frontend container functionality using Docker API
"""
import unittest
import sys
import os
import requests

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

sys.path.insert(0, os.path.join(project_root, 'tests'))
from lib.docker_utils import get_container_manager
from lib.container_builder import get_container_builder
from lib.test_logger import border, logger


class TestFrontendContainer(unittest.TestCase):
    """Test Frontend container functionality"""
    
    CONTAINER_NAME = "dcf-frontend"
    SERVICE_URL = "http://localhost:8080"
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.container_manager = get_container_manager()
        if not cls.container_manager.is_available():
            logger.error("Docker not available - skipping all tests")
            raise unittest.SkipTest("Docker not available")
        
        # Build containers before testing to ensure latest code
        logger.info("Building frontend container with latest code...")
        builder = get_container_builder(project_root)
        build_success = builder.build_containers(services=['frontend'])
        
        # Fail if build fails - we need latest code to test
        if not build_success:
            logger.error("Container build failed - cannot test with latest code")
            raise unittest.SkipTest(
                "Container build failed - cannot test with latest code. "
                "Please check build logs and fix errors."
            )
        
        logger.info("Container build successful - proceeding with tests")
    
    @border
    def test_container_exists(self):
        """Test that Frontend container exists"""
        logger.info("Testing Frontend container existence")
        
        container = self.container_manager.get_container(self.CONTAINER_NAME)
        if not container:
            logger.error(f"Container {self.CONTAINER_NAME} not found")
            self.fail(
                f"Container {self.CONTAINER_NAME} not found. "
                "Container may not be running. Start with: make docker-up"
            )
        
        logger.info(f"Container found: {container.name}")
    
    @border
    def test_container_running(self):
        """Test that Frontend container is running"""
        logger.info("Testing Frontend container status")
        
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
    def test_frontend_accessible(self):
        """Test that Frontend is accessible"""
        logger.info("Testing Frontend accessibility")
        
        # First verify container is running
        if not self.container_manager.is_container_running(self.CONTAINER_NAME):
            logger.error(f"Container {self.CONTAINER_NAME} is not running")
            self.fail(
                f"Container {self.CONTAINER_NAME} is not running. "
                "Start containers with: make docker-up"
            )
        
        try:
            logger.info(f"Attempting to access frontend at {self.SERVICE_URL}...")
            response = requests.get(self.SERVICE_URL, timeout=5)
            self.assertIn(response.status_code, [200, 301, 302, 404])
            logger.info(f"Frontend responded with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Frontend not accessible: {e}")
            self.fail(
                f"Frontend at {self.SERVICE_URL} is not accessible: {e}. "
                "Check if frontend service is running and port 8080 is exposed."
            )
    
    @border
    def test_container_info(self):
        """Test getting container information"""
        logger.info("Testing container information")
        
        container = self.container_manager.get_container(self.CONTAINER_NAME)
        if not container:
            logger.error(f"Container {self.CONTAINER_NAME} not found")
            self.fail(
                f"Container {self.CONTAINER_NAME} not found. "
                "Container may not be running. Start with: make docker-up"
            )
        
        info = self.container_manager.get_container_info(self.CONTAINER_NAME)
        if not info:
            logger.error("Failed to get container info")
            self.fail("Failed to get container information")
        
        self.assertEqual(info['name'], self.CONTAINER_NAME)
        self.assertEqual(info['status'], 'running')
        
        # Frontend should have port 8080:80 mapping
        ports = info.get('ports', {})
        logger.info(f"Container ports: {ports}")
        self.assertIsNotNone(ports, "Should have port mappings")


if __name__ == '__main__':
    unittest.main()

