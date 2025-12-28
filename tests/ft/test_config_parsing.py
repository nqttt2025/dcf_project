"""
Function Test: Config File Parsing
Tests the configuration file parsing functionality
"""
import unittest
import sys
import os
import configparser

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.core.dcf_calculator import DCFCalculator
sys.path.insert(0, os.path.join(project_root, 'tests'))
from lib.test_logger import border, logger


class TestConfigParsing(unittest.TestCase):
    """Test configuration file parsing"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = os.path.join(project_root, 'tests', 'tmp')
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures"""
        # Cleanup handled per test

    @border
    def test_config_parsing_full_config(self):
        """Test parsing a complete config file"""
        logger.info("Testing parsing complete config file")
        
        config_content = """
[ticker]
ticker = FPT

[dcf]
yr = 5
dr = 10.0
pr = 2.5

[graham]
base_pe = 8.5
growth_multiplier = 2.0

[data_source]
source = vnstock
note = Data sourced from vnstock library

[fcf_calculation]
method = TTM
note = Using Trailing Twelve Months for FCF calculation

[report]
language = vi
"""
        config_file = os.path.join(self.test_dir, 'test_full.cfg')
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        calculator = DCFCalculator(config_file)
        
        # Verify ticker
        self.assertEqual(calculator.ticker, 'FPT')
        
        # Verify DCF parameters
        self.assertEqual(calculator.dcf_params['yr'], 5)
        self.assertEqual(calculator.dcf_params['dr'], 10.0)
        self.assertEqual(calculator.dcf_params['pr'], 2.5)
        
        # Verify Graham parameters
        self.assertEqual(calculator.graham_params['base_pe'], 8.5)
        self.assertEqual(calculator.graham_params['growth_multiplier'], 2.0)
        
        os.remove(config_file)
        logger.info("Complete config parsing test passed")

    @border
    def test_config_parsing_minimal_config(self):
        """Test parsing a minimal config file with defaults"""
        logger.info("Testing parsing minimal config file")
        
        config_content = """
[ticker]
ticker = TEST
"""
        config_file = os.path.join(self.test_dir, 'test_minimal.cfg')
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        calculator = DCFCalculator(config_file)
        
        # Verify ticker
        self.assertEqual(calculator.ticker, 'TEST')
        
        # Verify default DCF parameters
        self.assertEqual(calculator.dcf_params['yr'], 5)  # Default
        self.assertEqual(calculator.dcf_params['dr'], 10.0)  # Default
        self.assertEqual(calculator.dcf_params['pr'], 2.5)  # Default
        
        # Verify default Graham parameters
        self.assertEqual(calculator.graham_params['base_pe'], 8.5)  # Default
        self.assertEqual(calculator.graham_params['growth_multiplier'], 2.0)  # Default
        
        os.remove(config_file)
        logger.info("Minimal config parsing test passed")

    @border
    def test_config_parsing_ticker_from_filename(self):
        """Test extracting ticker from filename when not in config"""
        logger.info("Testing ticker extraction from filename")
        
        config_content = """
[dcf]
yr = 5
dr = 10.0
pr = 2.5
"""
        config_file = os.path.join(self.test_dir, 'VNM.cfg')
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        calculator = DCFCalculator(config_file)
        
        # Ticker should be extracted from filename
        self.assertEqual(calculator.ticker, 'VNM')
        
        os.remove(config_file)
        logger.info("Ticker from filename test passed")

    @border
    def test_config_parsing_custom_parameters(self):
        """Test parsing config with custom parameters"""
        logger.info("Testing parsing custom parameters")
        
        config_content = """
[ticker]
ticker = CUSTOM

[dcf]
yr = 10
dr = 12.5
pr = 3.0

[graham]
base_pe = 15.0
growth_multiplier = 2.5
"""
        config_file = os.path.join(self.test_dir, 'test_custom.cfg')
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        calculator = DCFCalculator(config_file)
        
        # Verify custom DCF parameters
        self.assertEqual(calculator.dcf_params['yr'], 10)
        self.assertEqual(calculator.dcf_params['dr'], 12.5)
        self.assertEqual(calculator.dcf_params['pr'], 3.0)
        
        # Verify custom Graham parameters
        self.assertEqual(calculator.graham_params['base_pe'], 15.0)
        self.assertEqual(calculator.graham_params['growth_multiplier'], 2.5)
        
        os.remove(config_file)
        logger.info("Custom parameters parsing test passed")

    @border
    def test_config_parsing_missing_file(self):
        """Test error handling for missing config file"""
        logger.info("Testing error handling for missing config file")
        
        with self.assertRaises(FileNotFoundError):
            DCFCalculator('nonexistent.cfg')
        
        logger.info("Missing file error handling test passed")


if __name__ == '__main__':
    unittest.main()

