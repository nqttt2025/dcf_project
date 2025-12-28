"""
Unit tests for ResultManager module
"""
import unittest
import os
import json
import tempfile
import sys
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from utils.result_manager import ResultManager, get_result_manager
# Add tests to path for test_logger
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lib.test_logger import logger, border


class TestResultManager(unittest.TestCase):
    """Test cases for ResultManager"""

    @classmethod
    @border
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_results_dir = os.path.join(cls.temp_dir, 'results')

    @border
    def setUp(self):
        """Set up before each test"""
        logger.info("Execute test case %s", self.id())
        # Create test result manager with custom results directory
        self.manager = ResultManager()
        self.manager.results_dir = self.__class__.test_results_dir
        os.makedirs(self.manager.results_dir, exist_ok=True)

    @border
    def tearDown(self):
        """Clean up after each test"""
        logger.info("Execute test case %s completed", self.id())
        # Clean up test files
        if os.path.exists(self.manager.results_dir):
            for file in os.listdir(self.manager.results_dir):
                os.remove(os.path.join(self.manager.results_dir, file))

    @border
    def test_save_result(self):
        """Test saving result to file"""
        logger.info("Test save result to file")
        test_result = {
            'ticker': 'FPT',
            'price': 92500.0,
            'dcf_fair_value': 44206.13,
            'graham_fair_value': 42674.55,
            'average_fair_value': 43440.34,
            'eps': 1429.31,
            'shares': 1703507121,
            'growth_estimate': 10.68
        }
        
        result_file, log_file = self.manager.save_result('FPT', test_result)
        
        self.assertTrue(os.path.exists(result_file), "Result JSON file should be created")
        self.assertTrue(os.path.exists(log_file), "Result log file should be created")
        
        # Verify JSON content
        with open(result_file, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data['ticker'], 'FPT', "Should save correct ticker")
        self.assertEqual(saved_data['price'], 92500.0, "Should save correct price")
        self.assertIn('saved_at', saved_data, "Should include timestamp")
        self.assertIn('stock_name', saved_data, "Should include stock name")
        logger.info("Save result test succeeded")

    @border
    def test_load_result(self):
        """Test loading result from file"""
        logger.info("Test load result from file")
        test_result = {
            'ticker': 'VNM',
            'price': 61500.0,
            'dcf_fair_value': 19435.99
        }
        
        self.manager.save_result('VNM', test_result)
        loaded_result = self.manager.load_result('VNM')
        
        self.assertIsNotNone(loaded_result, "Should load result from file")
        self.assertEqual(loaded_result['ticker'], 'VNM', "Should load correct ticker")
        self.assertEqual(loaded_result['price'], 61500.0, "Should load correct price")
        logger.info("Load result test succeeded")

    @border
    def test_load_nonexistent_result(self):
        """Test loading result that doesn't exist"""
        logger.info("Test load nonexistent result")
        loaded_result = self.manager.load_result('NONEXISTENT')
        
        self.assertIsNone(loaded_result, "Should return None for nonexistent result")
        logger.info("Load nonexistent result test succeeded")

    @border
    def test_list_results(self):
        """Test listing all results"""
        logger.info("Test list all results")
        # Save multiple results
        self.manager.save_result('FPT', {'ticker': 'FPT', 'price': 92500.0})
        self.manager.save_result('VNM', {'ticker': 'VNM', 'price': 61500.0})
        self.manager.save_result('BID', {'ticker': 'BID', 'price': 50000.0})
        
        results = self.manager.list_results()
        
        self.assertIsInstance(results, list, "Should return a list")
        self.assertEqual(len(results), 3, "Should list all result files")
        
        # Check that all results have required keys
        for result in results:
            self.assertIn('file', result, "Should have 'file' key")
            self.assertIn('path', result, "Should have 'path' key")
            self.assertIn('size', result, "Should have 'size' key")
            self.assertTrue(result['file'].endswith('_result.json'), "Should be a result JSON file")
        logger.info("List results test succeeded")

    @border
    def test_delete_result(self):
        """Test deleting a result"""
        logger.info("Test delete result")
        test_result = {'ticker': 'TEST', 'price': 10000.0}
        
        self.manager.save_result('TEST', test_result)
        self.assertTrue(os.path.exists(
            os.path.join(self.manager.results_dir, 'test_result.json')
        ), "Result file should exist")
        
        deleted = self.manager.delete_result('TEST')
        
        self.assertTrue(deleted, "Should return True when deleting existing result")
        self.assertFalse(os.path.exists(
            os.path.join(self.manager.results_dir, 'test_result.json')
        ), "Result file should be deleted")
        logger.info("Delete result test succeeded")

    @border
    def test_delete_nonexistent_result(self):
        """Test deleting a result that doesn't exist"""
        logger.info("Test delete nonexistent result")
        deleted = self.manager.delete_result('NONEXISTENT')
        
        self.assertFalse(deleted, "Should return False when deleting nonexistent result")
        logger.info("Delete nonexistent result test succeeded")

    @border
    def test_clear_all_results(self):
        """Test clearing all results"""
        logger.info("Test clear all results")
        # Save multiple results
        self.manager.save_result('FPT', {'ticker': 'FPT'})
        self.manager.save_result('VNM', {'ticker': 'VNM'})
        
        self.manager.clear_all_results()
        
        results = self.manager.list_results()
        self.assertEqual(len(results), 0, "Should clear all results")
        logger.info("Clear all results test succeeded")

    @border
    def test_get_results_dir(self):
        """Test getting results directory"""
        logger.info("Test get results directory")
        results_dir = self.manager.get_results_dir()
        
        self.assertIsInstance(results_dir, str, "Should return a string")
        self.assertTrue(os.path.isdir(results_dir), "Should return a valid directory")
        logger.info("Get results directory test succeeded")

    @border
    def test_serialize_result(self):
        """Test serializing result with non-serializable types"""
        logger.info("Test serialize result")
        test_result = {
            'ticker': 'FPT',
            'price': 92500.0,
            'nested_dict': {'key': 'value'},
            'list': [1, 2, 3]
        }
        
        serialized = self.manager._serialize_result(test_result)
        
        # Should be able to convert to JSON
        json_str = json.dumps(serialized)
        self.assertIsInstance(json_str, str, "Should be JSON serializable")
        logger.info("Serialize result test succeeded")

    @border
    def test_get_result_manager_factory(self):
        """Test factory function get_result_manager"""
        logger.info("Test factory function get_result_manager")
        manager1 = get_result_manager()
        manager2 = get_result_manager()
        
        self.assertIs(manager1, manager2, "Factory should return same singleton instance")
        self.assertIsInstance(manager1, ResultManager, "Should return ResultManager instance")
        logger.info("Factory function test succeeded")


if __name__ == '__main__':
    unittest.main()

