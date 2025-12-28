"""
System Test: Web Service
Tests the web service endpoints (if available)
"""
import unittest
import sys
import os
import requests
import time

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

sys.path.insert(0, os.path.join(project_root, 'tests'))
from lib.test_logger import border, logger


class TestWebService(unittest.TestCase):
    """Test web service endpoints"""

    def setUp(self):
        """Set up test fixtures"""
        self.gateway_url = "http://localhost:8000"
        self.dcf_service_url = "http://localhost:8001"
        self.stock_service_url = "http://localhost:8002"
        self.frontend_url = "http://localhost:8080"
        
        # Timeout for requests
        self.timeout = 5

    def _check_service_available(self, url):
        """Check if service is available"""
        try:
            response = requests.get(f"{url}/health", timeout=self.timeout)
            return response.status_code == 200
        except:
            return False

    @border
    def test_gateway_health(self):
        """Test gateway health endpoint"""
        logger.info("Testing gateway health endpoint")
        
        if not self._check_service_available(self.gateway_url):
            self.skipTest("Gateway service not available")
        
        try:
            response = requests.get(f"{self.gateway_url}/health", timeout=self.timeout)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn('status', data)
            logger.info(f"Gateway health: {data}")
        except requests.exceptions.RequestException as e:
            self.skipTest(f"Gateway not available: {e}")
        
        logger.info("Gateway health test passed")

    @border
    def test_dcf_service_health(self):
        """Test DCF service health endpoint"""
        logger.info("Testing DCF service health endpoint")
        
        if not self._check_service_available(self.dcf_service_url):
            self.skipTest("DCF service not available")
        
        try:
            response = requests.get(f"{self.dcf_service_url}/health", timeout=self.timeout)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn('status', data)
            logger.info(f"DCF service health: {data}")
        except requests.exceptions.RequestException as e:
            self.skipTest(f"DCF service not available: {e}")
        
        logger.info("DCF service health test passed")

    @border
    def test_stock_service_health(self):
        """Test stock service health endpoint"""
        logger.info("Testing stock service health endpoint")
        
        if not self._check_service_available(self.stock_service_url):
            self.skipTest("Stock service not available")
        
        try:
            response = requests.get(f"{self.stock_service_url}/health", timeout=self.timeout)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn('status', data)
            logger.info(f"Stock service health: {data}")
        except requests.exceptions.RequestException as e:
            self.skipTest(f"Stock service not available: {e}")
        
        logger.info("Stock service health test passed")

    @border
    def test_gateway_stocks_endpoint(self):
        """Test gateway stocks list endpoint"""
        logger.info("Testing gateway stocks endpoint")
        
        if not self._check_service_available(self.gateway_url):
            self.skipTest("Gateway service not available")
        
        try:
            response = requests.get(f"{self.gateway_url}/api/stocks", timeout=self.timeout)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIsInstance(data, (list, dict))
            logger.info(f"Stocks endpoint returned {len(data) if isinstance(data, list) else 'data'}")
        except requests.exceptions.RequestException as e:
            self.skipTest(f"Gateway not available: {e}")
        
        logger.info("Gateway stocks endpoint test passed")

    @border
    def test_frontend_availability(self):
        """Test frontend availability"""
        logger.info("Testing frontend availability")
        
        try:
            response = requests.get(self.frontend_url, timeout=self.timeout)
            self.assertIn(response.status_code, [200, 301, 302])
            logger.info(f"Frontend available at {self.frontend_url}")
        except requests.exceptions.RequestException as e:
            self.skipTest(f"Frontend not available: {e}")
        
        logger.info("Frontend availability test passed")


if __name__ == '__main__':
    unittest.main()

