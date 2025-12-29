"""
Edge case tests for DCF calculation
Tests boundary conditions and error handling
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


class TestDCFEdgeCases(unittest.TestCase):
    """Edge case tests for DCF calculation"""

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
        self.test_config_file = os.path.join(project_root, 'tests', 'tmp', 'test_dcf_edge.cfg')
        os.makedirs(os.path.dirname(self.test_config_file), exist_ok=True)
        with open(self.test_config_file, 'w') as f:
            f.write(self.test_config_content)

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)

    @border
    def test_dcf_with_very_high_growth(self):
        """Test DCF calculation with very high growth rate"""
        logger.info("Testing DCF with very high growth")
        calculator = DCFCalculator(self.test_config_file)
        
        # Very high growth (50%)
        test_data = {
            'fcf': 1000000,
            'ge': 50.0,
            'shares': 1000000,
            'eps': 1000,
            'price': 50000,
            'market_cap': 50000000000
        }
        
        result = calculator.calculate_dcf(test_data)
        
        self.assertIsNotNone(result)
        self.assertIn('fair_value', result)
        self.assertGreater(result['fair_value'], 0)
        logger.info("Very high growth test passed")

    @border
    def test_dcf_with_negative_fcf(self):
        """Test DCF calculation with negative FCF"""
        logger.info("Testing DCF with negative FCF")
        calculator = DCFCalculator(self.test_config_file)
        
        test_data = {
            'fcf': -1000000,  # Negative FCF
            'ge': 5.0,
            'shares': 1000000,
            'eps': 1000,
            'price': 50000,
            'market_cap': 50000000000
        }
        
        result = calculator.calculate_dcf(test_data)
        
        # Should handle negative FCF gracefully
        self.assertIsNotNone(result)
        logger.info("Negative FCF test passed")

    @border
    def test_dcf_with_zero_shares(self):
        """Test DCF calculation with zero shares"""
        logger.info("Testing DCF with zero shares")
        calculator = DCFCalculator(self.test_config_file)
        
        test_data = {
            'fcf': 1000000,
            'ge': 10.0,
            'shares': 0,  # Zero shares
            'eps': 1000,
            'price': 50000,
            'market_cap': 0
        }
        
        # Should handle zero shares without crashing
        try:
            result = calculator.calculate_dcf(test_data)
            self.assertIsNotNone(result)
        except (ZeroDivisionError, ValueError):
            # Expected behavior - zero shares is invalid
            pass
        logger.info("Zero shares test passed")

    @border
    def test_graham_with_negative_eps(self):
        """Test Graham calculation with negative EPS"""
        logger.info("Testing Graham with negative EPS")
        calculator = DCFCalculator(self.test_config_file)
        
        test_data = {
            'eps': -1000,  # Negative EPS
            'ge': 10.0,
            'price': 50000
        }
        
        result = calculator.calculate_graham(test_data)
        
        # Should return None for negative EPS
        self.assertIsNone(result)
        logger.info("Negative EPS test passed")

    @border
    def test_graham_with_zero_price(self):
        """Test Graham calculation with zero price"""
        logger.info("Testing Graham with zero price")
        calculator = DCFCalculator(self.test_config_file)
        
        test_data = {
            'eps': 1000,
            'ge': 10.0,
            'price': 0  # Zero price
        }
        
        result = calculator.calculate_graham(test_data)
        
        # Should handle zero price
        self.assertIsNotNone(result)
        logger.info("Zero price test passed")


if __name__ == '__main__':
    unittest.main()

