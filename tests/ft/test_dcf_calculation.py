"""
Function Test: DCF Calculation
Tests the DCF calculation function with various inputs
"""
import unittest
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.core.dcf_calculator import DCFCalculator
sys.path.insert(0, os.path.join(project_root, 'tests'))
from lib.test_logger import border, logger


class TestDCFCalculation(unittest.TestCase):
    """Test DCF calculation function"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary config file for testing
        self.test_config_content = """
[ticker]
ticker = TEST

[dcf]
yr = 5
dr = 10.0
pr = 2.5

[graham]
base_pe = 8.5
growth_multiplier = 2.0
"""
        self.test_config_file = os.path.join(project_root, 'tests', 'tmp', 'test_dcf.cfg')
        os.makedirs(os.path.dirname(self.test_config_file), exist_ok=True)
        with open(self.test_config_file, 'w') as f:
            f.write(self.test_config_content)

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)

    @border
    def test_dcf_calculation_basic(self):
        """Test basic DCF calculation"""
        logger.info("Testing basic DCF calculation")
        calculator = DCFCalculator(self.test_config_file)
        
        # Test data
        test_data = {
            'fcf': 1000000000,  # 1 billion VND
            'ge': 10.0,  # 10% growth
            'shares': 1000000,  # 1 million shares
        }
        
        result = calculator.calculate_dcf(test_data)
        
        # Verify result structure
        self.assertIn('forecast', result)
        self.assertIn('pvs', result)
        self.assertIn('dcf_value', result)
        self.assertIn('fair_value', result)
        
        # Verify forecast length (yr + 1 for terminal value)
        self.assertEqual(len(result['forecast']), calculator.dcf_params['yr'] + 1)
        
        # Verify fair value is positive
        self.assertGreater(result['fair_value'], 0)
        
        logger.info(f"DCF Fair Value: {result['fair_value']:,.2f} VND")
        logger.info("Basic DCF calculation test passed")

    @border
    def test_dcf_calculation_zero_growth(self):
        """Test DCF calculation with zero growth rate"""
        logger.info("Testing DCF calculation with zero growth")
        calculator = DCFCalculator(self.test_config_file)
        
        test_data = {
            'fcf': 1000000000,
            'ge': 0.0,  # Zero growth
            'shares': 1000000,
        }
        
        result = calculator.calculate_dcf(test_data)
        
        # With zero growth, all forecast values should be the same (except terminal)
        forecast = result['forecast']
        for i in range(1, len(forecast) - 1):
            self.assertEqual(forecast[i], forecast[i-1])
        
        self.assertGreater(result['fair_value'], 0)
        logger.info("Zero growth DCF calculation test passed")

    @border
    def test_dcf_calculation_negative_growth(self):
        """Test DCF calculation with negative growth rate"""
        logger.info("Testing DCF calculation with negative growth")
        calculator = DCFCalculator(self.test_config_file)
        
        test_data = {
            'fcf': 1000000000,
            'ge': -5.0,  # Negative growth
            'shares': 1000000,
        }
        
        result = calculator.calculate_dcf(test_data)
        
        # Verify forecast decreases over time
        forecast = result['forecast']
        for i in range(1, len(forecast) - 1):
            self.assertLess(forecast[i], forecast[i-1])
        
        self.assertGreater(result['fair_value'], 0)
        logger.info("Negative growth DCF calculation test passed")

    @border
    def test_dcf_calculation_missing_growth(self):
        """Test DCF calculation with missing growth rate"""
        logger.info("Testing DCF calculation with missing growth")
        calculator = DCFCalculator(self.test_config_file)
        
        test_data = {
            'fcf': 1000000000,
            'ge': None,  # Missing growth
            'shares': 1000000,
        }
        
        with self.assertRaises(ValueError):
            calculator.calculate_dcf(test_data)
        
        logger.info("Missing growth rate error handling test passed")

    @border
    def test_dcf_calculation_different_years(self):
        """Test DCF calculation with different projection years"""
        logger.info("Testing DCF calculation with different years")
        
        # Test with 3 years
        config_3yr = self.test_config_file.replace('test_dcf.cfg', 'test_dcf_3yr.cfg')
        with open(config_3yr, 'w') as f:
            f.write(self.test_config_content.replace('yr = 5', 'yr = 3'))
        
        calculator_3yr = DCFCalculator(config_3yr)
        test_data = {
            'fcf': 1000000000,
            'ge': 10.0,
            'shares': 1000000,
        }
        
        result_3yr = calculator_3yr.calculate_dcf(test_data)
        self.assertEqual(len(result_3yr['forecast']), 4)  # 3 years + terminal
        
        # Test with 10 years
        config_10yr = self.test_config_file.replace('test_dcf.cfg', 'test_dcf_10yr.cfg')
        with open(config_10yr, 'w') as f:
            f.write(self.test_config_content.replace('yr = 5', 'yr = 10'))
        
        calculator_10yr = DCFCalculator(config_10yr)
        result_10yr = calculator_10yr.calculate_dcf(test_data)
        self.assertEqual(len(result_10yr['forecast']), 11)  # 10 years + terminal
        
        # Cleanup
        os.remove(config_3yr)
        os.remove(config_10yr)
        
        logger.info("Different years DCF calculation test passed")


if __name__ == '__main__':
    unittest.main()

