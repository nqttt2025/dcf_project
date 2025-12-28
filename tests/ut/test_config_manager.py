"""
Unit tests for ConfigManager module
"""
import unittest
import os
import tempfile
import configparser
import sys

# Add project root to path so src becomes a package
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, project_root)

from src.utils.config_manager import ConfigManager, get_config_manager
# Add tests to path for test_logger
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lib.test_logger import logger, border


class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager"""

    @classmethod
    @border
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.test_config_content = """
[ticker]
ticker = TEST

[dcf]
yr = 5
dr = 10.0
pr = 2.5

[graham]
base_pe = 8.5
growth_multiplier = 2.0

[data_source]
source = VCI
"""
        # Create temporary config file
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_config_file = os.path.join(cls.temp_dir, 'DCF.cfg')
        with open(cls.test_config_file, 'w') as f:
            f.write(cls.test_config_content)

    @border
    def setUp(self):
        """Set up before each test"""
        logger.info("Execute test case %s", self.id())
        # Reset singleton instance
        ConfigManager._instance = None
        ConfigManager._initialized = False

    @border
    def tearDown(self):
        """Clean up after each test"""
        logger.info("Execute test case %s completed", self.id())
        # Reset singleton instance
        ConfigManager._instance = None
        ConfigManager._initialized = False

    @border
    def test_singleton_pattern(self):
        """Test that ConfigManager is a singleton"""
        logger.info("Test singleton pattern")
        manager1 = ConfigManager()
        manager2 = ConfigManager()
        self.assertIs(manager1, manager2, "ConfigManager should be a singleton")
        logger.info("Singleton pattern test succeeded")

    @border
    def test_get_dcf_params_default(self):
        """Test getting DCF parameters with defaults"""
        logger.info("Test get DCF parameters with defaults")
        manager = ConfigManager()
        params = manager.get_dcf_params()
        
        self.assertIsInstance(params, dict, "DCF params should be a dictionary")
        self.assertIn('yr', params, "Should have 'yr' key")
        self.assertIn('dr', params, "Should have 'dr' key")
        self.assertIn('pr', params, "Should have 'pr' key")
        self.assertIsInstance(params['yr'], int, "'yr' should be an integer")
        self.assertIsInstance(params['dr'], float, "'dr' should be a float")
        self.assertIsInstance(params['pr'], float, "'pr' should be a float")
        logger.info("DCF parameters test succeeded")

    @border
    def test_get_graham_params_default(self):
        """Test getting Graham parameters with defaults"""
        logger.info("Test get Graham parameters with defaults")
        manager = ConfigManager()
        params = manager.get_graham_params()
        
        self.assertIsInstance(params, dict, "Graham params should be a dictionary")
        self.assertIn('base_pe', params, "Should have 'base_pe' key")
        self.assertIn('growth_multiplier', params, "Should have 'growth_multiplier' key")
        self.assertIsInstance(params['base_pe'], float, "'base_pe' should be a float")
        self.assertIsInstance(params['growth_multiplier'], float, "'growth_multiplier' should be a float")
        logger.info("Graham parameters test succeeded")

    @border
    def test_get_ticker_default(self):
        """Test getting ticker with default"""
        logger.info("Test get ticker with default")
        manager = ConfigManager()
        ticker = manager.get_ticker()
        
        self.assertIsInstance(ticker, str, "Ticker should be a string")
        self.assertGreater(len(ticker), 0, "Ticker should not be empty")
        logger.info("Ticker test succeeded")

    @border
    def test_get_data_source_default(self):
        """Test getting data source with default"""
        logger.info("Test get data source with default")
        manager = ConfigManager()
        source = manager.get_data_source()
        
        self.assertIsInstance(source, str, "Data source should be a string")
        self.assertGreater(len(source), 0, "Data source should not be empty")
        logger.info("Data source test succeeded")

    @border
    def test_get_all_params(self):
        """Test getting all parameters"""
        logger.info("Test get all parameters")
        manager = ConfigManager()
        all_params = manager.get_all_params()
        
        self.assertIsInstance(all_params, dict, "All params should be a dictionary")
        self.assertIn('yr', all_params, "Should have 'yr' key")
        self.assertIn('dr', all_params, "Should have 'dr' key")
        self.assertIn('pr', all_params, "Should have 'pr' key")
        self.assertIn('base_pe', all_params, "Should have 'base_pe' key")
        self.assertIn('growth_multiplier', all_params, "Should have 'growth_multiplier' key")
        self.assertIn('ticker', all_params, "Should have 'ticker' key")
        self.assertIn('source', all_params, "Should have 'source' key")
        logger.info("All parameters test succeeded")

    @border
    def test_get_config_manager_factory(self):
        """Test factory function get_config_manager"""
        logger.info("Test factory function get_config_manager")
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        
        self.assertIs(manager1, manager2, "Factory should return same singleton instance")
        self.assertIsInstance(manager1, ConfigManager, "Should return ConfigManager instance")
        logger.info("Factory function test succeeded")


if __name__ == '__main__':
    unittest.main()

