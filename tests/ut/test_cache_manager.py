"""
Unit tests for CacheManager module
"""
import unittest
import os
import json
import tempfile
import sys
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from utils.cache_manager import CacheManager, get_cache_manager
# Add tests to path for test_logger
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lib.test_logger import logger, border


class TestCacheManager(unittest.TestCase):
    """Test cases for CacheManager"""

    @classmethod
    @border
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_cache_file = os.path.join(cls.temp_dir, 'test_cache.json')

    @border
    def setUp(self):
        """Set up before each test"""
        logger.info("Execute test case %s", self.id())
        # Reset singleton instance
        CacheManager._instance = None
        CacheManager._initialized = False
        # Set custom cache file for testing
        if os.path.exists(self.test_cache_file):
            os.remove(self.test_cache_file)

    @border
    def tearDown(self):
        """Clean up after each test"""
        logger.info("Execute test case %s completed", self.id())
        # Reset singleton instance
        CacheManager._instance = None
        CacheManager._initialized = False
        # Clean up test cache file
        if os.path.exists(self.test_cache_file):
            os.remove(self.test_cache_file)

    def _create_test_cache_manager(self):
        """Helper to create CacheManager with test cache file"""
        manager = CacheManager()
        manager.cache_file = self.test_cache_file
        manager.cache = {}
        return manager

    @border
    def test_singleton_pattern(self):
        """Test that CacheManager is a singleton"""
        logger.info("Test singleton pattern")
        manager1 = CacheManager()
        manager2 = CacheManager()
        self.assertIs(manager1, manager2, "CacheManager should be a singleton")
        logger.info("Singleton pattern test succeeded")

    @border
    def test_set_and_get(self):
        """Test setting and getting cache values"""
        logger.info("Test set and get cache values")
        manager = self._create_test_cache_manager()
        
        manager.set('test_key', 'test_value')
        value = manager.get('test_key')
        
        self.assertEqual(value, 'test_value', "Should retrieve the same value that was set")
        logger.info("Set and get test succeeded")

    @border
    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist"""
        logger.info("Test get nonexistent key")
        manager = self._create_test_cache_manager()
        
        value = manager.get('nonexistent_key')
        
        self.assertIsNone(value, "Should return None for nonexistent key")
        logger.info("Nonexistent key test succeeded")

    @border
    def test_set_with_timestamp(self):
        """Test setting value with timestamp"""
        logger.info("Test set value with timestamp")
        manager = self._create_test_cache_manager()
        
        result = manager.set_with_timestamp('FPT', 'fcf', 1000000)
        
        self.assertIsNotNone(result, "Should return the value")
        self.assertEqual(manager.get('FPT_fcf'), 1000000, "Should store the value")
        self.assertIn('FPT_fcf_timestamp', manager.cache, "Should store timestamp")
        timestamp = manager.cache['FPT_fcf_timestamp']
        self.assertIsInstance(timestamp, str, "Timestamp should be a string")
        logger.info("Set with timestamp test succeeded")

    @border
    def test_exists(self):
        """Test checking if data exists in cache"""
        logger.info("Test check if data exists in cache")
        manager = self._create_test_cache_manager()
        
        self.assertFalse(manager.exists('FPT', 'fcf'), "Should return False for nonexistent data")
        
        manager.set_with_timestamp('FPT', 'fcf', 1000000)
        self.assertTrue(manager.exists('FPT', 'fcf'), "Should return True for existing data")
        logger.info("Exists check test succeeded")

    @border
    def test_save_to_file(self):
        """Test saving cache to file"""
        logger.info("Test save cache to file")
        manager = self._create_test_cache_manager()
        
        manager.set('test_key', 'test_value')
        manager.set('test_key2', 12345)
        manager.save_to_file()
        
        self.assertTrue(os.path.exists(self.test_cache_file), "Cache file should be created")
        
        with open(self.test_cache_file, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data['test_key'], 'test_value', "Should save correct value")
        self.assertEqual(saved_data['test_key2'], 12345, "Should save correct value")
        logger.info("Save to file test succeeded")

    @border
    def test_load_cache_from_file(self):
        """Test loading cache from existing file"""
        logger.info("Test load cache from file")
        # Create a cache file first
        test_data = {
            'FPT_fcf': 1000000,
            'FPT_fcf_timestamp': '2024-01-01 00:00:00 UTC',
            'VNM_price': 50000
        }
        with open(self.test_cache_file, 'w') as f:
            json.dump(test_data, f)
        
        manager = self._create_test_cache_manager()
        manager._load_cache()
        
        self.assertEqual(manager.get('FPT_fcf'), 1000000, "Should load value from file")
        self.assertEqual(manager.get('VNM_price'), 50000, "Should load value from file")
        logger.info("Load from file test succeeded")

    @border
    def test_clear(self):
        """Test clearing cache"""
        logger.info("Test clear cache")
        manager = self._create_test_cache_manager()
        
        manager.set('test_key', 'test_value')
        manager.set('test_key2', 12345)
        self.assertEqual(len(manager.cache), 2, "Cache should have 2 items")
        
        manager.clear()
        
        self.assertEqual(len(manager.cache), 0, "Cache should be empty after clear")
        logger.info("Clear cache test succeeded")

    @border
    def test_get_all(self):
        """Test getting all cache data"""
        logger.info("Test get all cache data")
        manager = self._create_test_cache_manager()
        
        manager.set('key1', 'value1')
        manager.set('key2', 'value2')
        
        all_data = manager.get_all()
        
        self.assertIsInstance(all_data, dict, "Should return a dictionary")
        self.assertEqual(len(all_data), 2, "Should return all cache items")
        self.assertEqual(all_data['key1'], 'value1', "Should contain correct values")
        self.assertEqual(all_data['key2'], 'value2', "Should contain correct values")
        # Should be a copy, not the same object
        self.assertIsNot(all_data, manager.cache, "Should return a copy, not the original")
        logger.info("Get all test succeeded")

    @border
    def test_get_cache_manager_factory(self):
        """Test factory function get_cache_manager"""
        logger.info("Test factory function get_cache_manager")
        manager1 = get_cache_manager()
        manager2 = get_cache_manager()
        
        self.assertIs(manager1, manager2, "Factory should return same singleton instance")
        self.assertIsInstance(manager1, CacheManager, "Should return CacheManager instance")
        logger.info("Factory function test succeeded")


if __name__ == '__main__':
    unittest.main()

