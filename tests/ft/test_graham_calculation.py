"""
Function Test: Graham Valuation Calculation
Tests the Graham valuation calculation function
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


class TestGrahamCalculation(unittest.TestCase):
    """Test Graham valuation calculation function"""

    def setUp(self):
        """Set up test fixtures"""
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
        self.test_config_file = os.path.join(project_root, 'tests', 'tmp', 'test_graham.cfg')
        os.makedirs(os.path.dirname(self.test_config_file), exist_ok=True)
        with open(self.test_config_file, 'w') as f:
            f.write(self.test_config_content)

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)

    @border
    def test_graham_calculation_basic(self):
        """Test basic Graham valuation calculation"""
        logger.info("Testing basic Graham calculation")
        calculator = DCFCalculator(self.test_config_file)
        
        test_data = {
            'eps': 5000,  # Earnings per share
            'ge': 10.0,  # 10% growth
        }
        
        result = calculator.calculate_graham(test_data)
        
        # Verify result structure
        self.assertIn('fair_value', result)
        self.assertGreater(result['fair_value'], 0)
        
        # Graham formula: EPS * (base_pe + growth_multiplier * growth_rate)
        expected_value = test_data['eps'] * (
            calculator.graham_params['base_pe'] + 
            calculator.graham_params['growth_multiplier'] * test_data['ge']
        )
        
        self.assertAlmostEqual(result['fair_value'], expected_value, places=2)
        logger.info(f"Graham Fair Value: {result['fair_value']:,.2f} VND")
        logger.info("Basic Graham calculation test passed")

    @border
    def test_graham_calculation_zero_growth(self):
        """Test Graham calculation with zero growth"""
        logger.info("Testing Graham calculation with zero growth")
        calculator = DCFCalculator(self.test_config_file)
        
        test_data = {
            'eps': 5000,
            'ge': 0.0,
        }
        
        result = calculator.calculate_graham(test_data)
        
        # With zero growth, should use base PE only
        expected_value = test_data['eps'] * calculator.graham_params['base_pe']
        self.assertAlmostEqual(result['fair_value'], expected_value, places=2)
        
        logger.info("Zero growth Graham calculation test passed")

    @border
    def test_graham_calculation_high_growth(self):
        """Test Graham calculation with high growth rate"""
        logger.info("Testing Graham calculation with high growth")
        calculator = DCFCalculator(self.test_config_file)
        
        test_data = {
            'eps': 5000,
            'ge': 25.0,  # 25% growth
        }
        
        result = calculator.calculate_graham(test_data)
        
        # High growth should result in higher fair value
        expected_value = test_data['eps'] * (
            calculator.graham_params['base_pe'] + 
            calculator.graham_params['growth_multiplier'] * test_data['ge']
        )
        self.assertAlmostEqual(result['fair_value'], expected_value, places=2)
        self.assertGreater(result['fair_value'], test_data['eps'] * calculator.graham_params['base_pe'])
        
        logger.info("High growth Graham calculation test passed")

    @border
    def test_graham_calculation_different_base_pe(self):
        """Test Graham calculation with different base PE"""
        logger.info("Testing Graham calculation with different base PE")
        
        # Test with base PE = 10
        config_pe10 = self.test_config_file.replace('test_graham.cfg', 'test_graham_pe10.cfg')
        with open(config_pe10, 'w') as f:
            f.write(self.test_config_content.replace('base_pe = 8.5', 'base_pe = 10.0'))
        
        calculator_pe10 = DCFCalculator(config_pe10)
        test_data = {
            'eps': 5000,
            'ge': 10.0,
        }
        
        result_pe10 = calculator_pe10.calculate_graham(test_data)
        
        # Test with base PE = 15
        config_pe15 = self.test_config_file.replace('test_graham.cfg', 'test_graham_pe15.cfg')
        with open(config_pe15, 'w') as f:
            f.write(self.test_config_content.replace('base_pe = 8.5', 'base_pe = 15.0'))
        
        calculator_pe15 = DCFCalculator(config_pe15)
        result_pe15 = calculator_pe15.calculate_graham(test_data)
        
        # Higher base PE should result in higher fair value
        self.assertGreater(result_pe15['fair_value'], result_pe10['fair_value'])
        
        # Cleanup
        os.remove(config_pe10)
        os.remove(config_pe15)
        
        logger.info("Different base PE Graham calculation test passed")


if __name__ == '__main__':
    unittest.main()

