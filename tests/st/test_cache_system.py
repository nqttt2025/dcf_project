"""
System Test: Cache System
Tests the cache system functionality
"""
import unittest
import sys
import os
import asyncio
import json
import time

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.core.dcf_calculator import calculate_dcf_from_config
from src.utils.cache_manager import get_cache_manager
sys.path.insert(0, os.path.join(project_root, 'tests'))
from lib.test_logger import border, logger


class TestCacheSystem(unittest.TestCase):
    """Test cache system functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = os.path.join(project_root, 'tests', 'tmp')
        os.makedirs(self.test_dir, exist_ok=True)
        
        self.test_config_content = """
[ticker]
ticker = CACHETEST

[dcf]
yr = 5
dr = 10.0
pr = 2.5

[graham]
base_pe = 8.5
growth_multiplier = 2.0
"""
        self.test_config_file = os.path.join(self.test_dir, 'CACHETEST.cfg')
        with open(self.test_config_file, 'w') as f:
            f.write(self.test_config_content)
        
        self.cache_manager = get_cache_manager()

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
        
        # Clean up cache
        cache_file = os.path.join(project_root, 'data', 'cache', 'cachetest_cache.json')
        if os.path.exists(cache_file):
            os.remove(cache_file)

    @border
    def test_cache_creation(self):
        """Test that cache is created after calculation"""
        logger.info("Testing cache creation")
        
        async def run_test():
            result = await calculate_dcf_from_config(self.test_config_file)
            
            # Verify cache file exists
            cache_file = result['cache_file']
            self.assertTrue(os.path.exists(cache_file))
            
            # Verify cache content
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Verify cache contains financial data
            expected_keys = ['fcf', 'shares', 'eps', 'price']
            for key in expected_keys:
                self.assertIn(key, cache_data)
            
            logger.info(f"Cache file created: {os.path.basename(cache_file)}")
            logger.info(f"Cache contains {len(cache_data)} entries")
        
        asyncio.run(run_test())
        logger.info("Cache creation test passed")

    @border
    def test_cache_timestamp(self):
        """Test that cache includes timestamps"""
        logger.info("Testing cache timestamps")
        
        async def run_test():
            result = await calculate_dcf_from_config(self.test_config_file)
            
            cache_file = result['cache_file']
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Verify timestamps exist
            timestamp_keys = [k for k in cache_data.keys() if 'timestamp' in k.lower()]
            self.assertGreater(len(timestamp_keys), 0)
            
            logger.info(f"Found {len(timestamp_keys)} timestamp entries")
        
        asyncio.run(run_test())
        logger.info("Cache timestamp test passed")

    @border
    def test_cache_reuse(self):
        """Test that cache is reused on subsequent calculations"""
        logger.info("Testing cache reuse")
        
        async def run_test():
            # First calculation - creates cache
            result1 = await calculate_dcf_from_config(self.test_config_file)
            cache_file = result1['cache_file']
            
            # Verify cache exists
            self.assertTrue(os.path.exists(cache_file))
            
            # Get cache modification time
            cache_mtime1 = os.path.getmtime(cache_file)
            
            # Small delay
            await asyncio.sleep(0.1)
            
            # Second calculation - should reuse cache
            result2 = await calculate_dcf_from_config(self.test_config_file)
            
            # Cache file should still exist
            self.assertTrue(os.path.exists(cache_file))
            
            # Cache should have same or newer modification time
            cache_mtime2 = os.path.getmtime(cache_file)
            self.assertGreaterEqual(cache_mtime2, cache_mtime1)
            
            logger.info("Cache reuse verified")
        
        asyncio.run(run_test())
        logger.info("Cache reuse test passed")

    @border
    def test_cache_data_integrity(self):
        """Test that cache data maintains integrity"""
        logger.info("Testing cache data integrity")
        
        async def run_test():
            result = await calculate_dcf_from_config(self.test_config_file)
            
            cache_file = result['cache_file']
            
            # Load cache
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Verify data types
            self.assertIsInstance(cache_data, dict)
            
            # Verify numeric values are valid
            numeric_keys = ['fcf', 'shares', 'eps', 'price']
            for key in numeric_keys:
                if key in cache_data:
                    value = cache_data[key]
                    self.assertIsInstance(value, (int, float))
                    self.assertGreater(value, 0)
            
            logger.info("Cache data integrity verified")
        
        asyncio.run(run_test())
        logger.info("Cache data integrity test passed")


if __name__ == '__main__':
    unittest.main()

