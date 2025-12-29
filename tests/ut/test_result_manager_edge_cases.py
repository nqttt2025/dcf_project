"""
Additional edge case tests for ResultManager
Ensures robust behavior in various scenarios
"""
import unittest
import os
import json
import tempfile
import sys

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, project_root)

from src.utils.result_manager import ResultManager
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lib.test_logger import logger, border


class TestResultManagerEdgeCases(unittest.TestCase):
    """Edge case tests for ResultManager"""

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
        self.manager = ResultManager()
        self.manager.results_dir = self.__class__.test_results_dir
        os.makedirs(self.manager.results_dir, exist_ok=True)

    @border
    def tearDown(self):
        """Clean up after each test"""
        logger.info("Execute test case %s completed", self.id())
        if os.path.exists(self.manager.results_dir):
            for file in os.listdir(self.manager.results_dir):
                os.remove(os.path.join(self.manager.results_dir, file))

    @border
    def test_save_result_with_missing_values(self):
        """Test saving result with missing optional values"""
        logger.info("Test save result with missing values")
        minimal_result = {'ticker': 'TEST'}
        
        result_file, log_file = self.manager.save_result('TEST', minimal_result)
        
        self.assertTrue(os.path.exists(result_file))
        self.assertTrue(os.path.exists(log_file))
        
        with open(result_file, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data['ticker'], 'TEST')
        logger.info("Save result with missing values test succeeded")

    @border
    def test_save_result_with_none_values(self):
        """Test saving result with None values"""
        logger.info("Test save result with None values")
        result_with_none = {
            'ticker': 'TEST',
            'price': None,
            'dcf_fair_value': None,
            'graham_fair_value': None
        }
        
        result_file, log_file = self.manager.save_result('TEST', result_with_none)
        
        self.assertTrue(os.path.exists(result_file))
        logger.info("Save result with None values test succeeded")

    @border
    def test_save_result_with_special_characters(self):
        """Test saving result with special characters in ticker"""
        logger.info("Test save result with special characters")
        result = {'ticker': 'TEST-123', 'price': 10000.0}
        
        result_file, log_file = self.manager.save_result('TEST-123', result)
        
        self.assertTrue(os.path.exists(result_file))
        # Verify file name is sanitized
        self.assertIn('test-123', result_file.lower())
        logger.info("Save result with special characters test succeeded")

    @border
    def test_list_results_empty_directory(self):
        """Test listing results when directory is empty"""
        logger.info("Test list results empty directory")
        results = self.manager.list_results()
        
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)
        logger.info("List results empty directory test succeeded")

    @border
    def test_delete_result_case_insensitive(self):
        """Test deleting result is case insensitive"""
        logger.info("Test delete result case insensitive")
        test_result = {'ticker': 'TEST', 'price': 10000.0}
        
        self.manager.save_result('TEST', test_result)
        
        # Try deleting with different case
        deleted = self.manager.delete_result('test')
        
        self.assertTrue(deleted)
        self.assertFalse(os.path.exists(
            os.path.join(self.manager.results_dir, 'test_result.json')
        ))
        logger.info("Delete result case insensitive test succeeded")

    @border
    def test_load_result_case_insensitive(self):
        """Test loading result is case insensitive"""
        logger.info("Test load result case insensitive")
        test_result = {'ticker': 'TEST', 'price': 10000.0}
        
        self.manager.save_result('TEST', test_result)
        
        # Try loading with different case
        loaded = self.manager.load_result('test')
        
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded['ticker'], 'TEST')
        logger.info("Load result case insensitive test succeeded")

    @border
    def test_save_result_unicode_characters(self):
        """Test saving result with unicode characters"""
        logger.info("Test save result with unicode")
        result = {
            'ticker': 'TEST',
            'price': 10000.0,
            'description': 'Công ty TEST với ký tự đặc biệt'
        }
        
        result_file, log_file = self.manager.save_result('TEST', result)
        
        self.assertTrue(os.path.exists(result_file))
        
        with open(result_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        # stock_name is set from ticker parameter, not from result dict
        self.assertEqual(saved_data['stock_name'], 'TEST')
        # But custom fields with unicode should be preserved
        self.assertEqual(saved_data['description'], 'Công ty TEST với ký tự đặc biệt')
        logger.info("Save result with unicode test succeeded")

    @border
    def test_serialize_result_with_datetime(self):
        """Test serializing result with datetime objects"""
        logger.info("Test serialize result with datetime")
        from datetime import datetime, timezone
        
        result = {
            'ticker': 'TEST',
            'timestamp': datetime.now(timezone.utc)
        }
        
        serialized = self.manager._serialize_result(result)
        
        # Should convert datetime to string
        self.assertIsInstance(serialized['timestamp'], str)
        logger.info("Serialize result with datetime test succeeded")


if __name__ == '__main__':
    unittest.main()

