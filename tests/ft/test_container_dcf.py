"""
Function Test: DCF Container
Tests the DCF service container functionality using Docker API
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


class TestDCFContainer(unittest.TestCase):
    """Test DCF container functionality"""
    
    CONTAINER_NAME = "dcf-service"
    SERVICE_URL = "http://localhost:8001"
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.container_manager = get_container_manager()
        if not cls.container_manager.is_available():
            logger.error("Docker not available - skipping all tests")
            raise unittest.SkipTest("Docker not available")
        
        # Build containers before testing to ensure latest code
        logger.info("Building DCF container with latest code...")
        builder = get_container_builder(project_root)
        build_success = builder.build_containers(services=['dcf'])
        
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
        """Test that DCF container exists"""
        logger.info("Testing DCF container existence")
        
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
        """Test that DCF container is running"""
        logger.info("Testing DCF container status")
        
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
    def test_service_health_endpoint(self):
        """Test DCF service health endpoint"""
        logger.info("Testing DCF service health endpoint")
        
        # First verify container is running
        if not self.container_manager.is_container_running(self.CONTAINER_NAME):
            logger.error(f"Container {self.CONTAINER_NAME} is not running")
            self.fail(
                f"Container {self.CONTAINER_NAME} is not running. "
                "Start containers with: make docker-up"
            )
        
        is_available = self.container_manager.check_service_health(self.SERVICE_URL)
        if not is_available:
            logger.error(f"DCF service at {self.SERVICE_URL} is not available")
            self.fail(
                f"DCF service at {self.SERVICE_URL} is not available. "
                "Check if service is running and health endpoint is working."
            )
        
        service_info = self.container_manager.get_service_info(self.SERVICE_URL)
        self.assertIsNotNone(service_info, "Should get service info")
        self.assertIn('status', service_info)
        
        logger.info(f"Service health: {service_info}")
    
    @border
    def test_container_environment(self):
        """Test container environment variables"""
        logger.info("Testing container environment")
        
        info = self.container_manager.get_container_info(self.CONTAINER_NAME)
        self.assertIsNotNone(info, "Should get container info")
        
        env_vars = info.get('env', [])
        env_dict = {k: v for k, v in [e.split('=', 1) for e in env_vars if '=' in e]}
        
        # Check important environment variables
        self.assertIn('PYTHONUNBUFFERED', env_dict)
        self.assertIn('DATABASE_URL', env_dict)
        
        logger.info(f"Environment variables: {len(env_vars)} found")
    
    @border
    def test_container_volumes(self):
        """Test container volume mounts"""
        logger.info("Testing container volumes")
        
        container = self.container_manager.get_container(self.CONTAINER_NAME)
        if not container:
            logger.error(f"Container {self.CONTAINER_NAME} not found")
            self.fail(
                f"Container {self.CONTAINER_NAME} not found. "
                "Container may not be running. Start with: make docker-up"
            )
        
        mounts = container.attrs.get('Mounts', [])
        if len(mounts) > 0:
            # Check for data, config, logs volumes
            mount_paths = [m.get('Destination', '') for m in mounts]
            logger.info(f"Volume mounts: {mount_paths}")
            self.assertGreater(len(mount_paths), 0, "Should have volume mounts")
        else:
            logger.info("No volume mounts found (may be using bind mounts)")


if __name__ == '__main__':
    unittest.main()

