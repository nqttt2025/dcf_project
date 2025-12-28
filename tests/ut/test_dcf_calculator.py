"""
Unit tests for DCFCalculator module
"""
import unittest
import os
import tempfile
import configparser
import sys
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

# Add project root to path so src becomes a package
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, project_root)

from src.core.dcf_calculator import DCFCalculator, calculate_dcf_from_config
# Add tests to path for test_logger
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lib.test_logger import logger, border


class TestDCFCalculator(unittest.TestCase):
    """Test cases for DCFCalculator"""

    @classmethod
    @border
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_config_file = os.path.join(cls.temp_dir, 'TEST.cfg')
        
        # Create test config file
        config = configparser.ConfigParser()
        config['ticker'] = {'ticker': 'TEST'}
        config['dcf'] = {
            'yr': '5',
            'dr': '10.0',
            'pr': '2.5'
        }
        config['graham'] = {
            'base_pe': '8.5',
            'growth_multiplier': '2.0'
        }
        
        with open(cls.test_config_file, 'w') as f:
            config.write(f)

    @border
    def setUp(self):
        """Set up before each test"""
        logger.info("Execute test case %s", self.id())

    @border
    def tearDown(self):
        """Clean up after each test"""
        logger.info("Execute test case %s completed", self.id())

    @border
    def test_init_with_config_file(self):
        """Test initializing DCFCalculator with config file"""
        logger.info("Test initialize DCFCalculator")
        calculator = DCFCalculator(self.test_config_file)
        
        self.assertEqual(calculator.ticker, 'TEST', "Should load ticker from config")
        self.assertEqual(calculator.dcf_params['yr'], 5, "Should load DCF year parameter")
        self.assertEqual(calculator.dcf_params['dr'], 10.0, "Should load discount rate")
        self.assertEqual(calculator.dcf_params['pr'], 2.5, "Should load perpetual rate")
        logger.info("Initialize test succeeded")

    @border
    def test_init_with_nonexistent_config(self):
        """Test initializing with nonexistent config file"""
        logger.info("Test initialize with nonexistent config")
        with self.assertRaises(FileNotFoundError, msg="Should raise FileNotFoundError"):
            DCFCalculator('NONEXISTENT.cfg')
        logger.info("Nonexistent config test succeeded")

    @border
    def test_calculate_dcf(self):
        """Test DCF calculation"""
        logger.info("Test DCF calculation")
        calculator = DCFCalculator(self.test_config_file)
        
        # Mock data
        data = {
            'fcf': 1000000,
            'ge': 10.0,  # 10% growth
            'shares': 1000000
        }
        
        result = calculator.calculate_dcf(data)
        
        self.assertIn('forecast', result, "Should have forecast")
        self.assertIn('pvs', result, "Should have present values")
        self.assertIn('dcf_value', result, "Should have DCF value")
        self.assertIn('fair_value', result, "Should have fair value")
        self.assertIsInstance(result['fair_value'], float, "Fair value should be a float")
        self.assertGreater(result['fair_value'], 0, "Fair value should be positive")
        logger.info("DCF calculation test succeeded")

    @border
    def test_calculate_dcf_with_zero_growth(self):
        """Test DCF calculation with zero growth"""
        logger.info("Test DCF calculation with zero growth")
        calculator = DCFCalculator(self.test_config_file)
        
        data = {
            'fcf': 1000000,
            'ge': 0.0,
            'shares': 1000000
        }
        
        result = calculator.calculate_dcf(data)
        
        # With zero growth, all forecast values should be the same
        self.assertEqual(len(result['forecast']), 6, "Should have 5 years + terminal value")
        self.assertGreater(result['fair_value'], 0, "Fair value should be positive")
        logger.info("Zero growth DCF test succeeded")

    @border
    def test_calculate_dcf_with_no_growth(self):
        """Test DCF calculation with None growth"""
        logger.info("Test DCF calculation with None growth")
        calculator = DCFCalculator(self.test_config_file)
        
        data = {
            'fcf': 1000000,
            'ge': None,
            'shares': 1000000
        }
        
        with self.assertRaises(ValueError, msg="Should raise ValueError for None growth"):
            calculator.calculate_dcf(data)
        logger.info("None growth DCF test succeeded")

    @border
    def test_calculate_graham(self):
        """Test Graham valuation calculation"""
        logger.info("Test Graham valuation calculation")
        calculator = DCFCalculator(self.test_config_file)
        
        data = {
            'eps': 1000.0,
            'ge': 10.0,
            'price': 50000.0
        }
        
        result = calculator.calculate_graham(data)
        
        self.assertIsNotNone(result, "Should return a result")
        self.assertIn('fair_value', result, "Should have fair value")
        self.assertIn('ge_priced_in', result, "Should have growth estimate priced in")
        self.assertIsInstance(result['fair_value'], float, "Fair value should be a float")
        self.assertGreater(result['fair_value'], 0, "Fair value should be positive")
        logger.info("Graham calculation test succeeded")

    @border
    def test_calculate_graham_with_zero_eps(self):
        """Test Graham valuation with zero EPS"""
        logger.info("Test Graham valuation with zero EPS")
        calculator = DCFCalculator(self.test_config_file)
        
        data = {
            'eps': 0.0,
            'ge': 10.0,
            'price': 50000.0
        }
        
        result = calculator.calculate_graham(data)
        
        self.assertIsNone(result, "Should return None for zero EPS")
        logger.info("Zero EPS Graham test succeeded")

    @border
    def test_calculate_graham_with_negative_eps(self):
        """Test Graham valuation with negative EPS"""
        logger.info("Test Graham valuation with negative EPS")
        calculator = DCFCalculator(self.test_config_file)
        
        data = {
            'eps': -100.0,
            'ge': 10.0,
            'price': 50000.0
        }
        
        result = calculator.calculate_graham(data)
        
        self.assertIsNone(result, "Should return None for negative EPS")
        logger.info("Negative EPS Graham test succeeded")

    @border
    @patch('src.core.dcf_calculator.get_free_cash_flow')
    @patch('src.core.dcf_calculator.get_growth_estimate')
    @patch('src.core.dcf_calculator.get_shares_outstanding')
    @patch('src.core.dcf_calculator.get_earnings_per_share_Diluted')
    @patch('src.core.dcf_calculator.price_board_stock')
    @patch('src.core.dcf_calculator.get_market_cap')
    def test_fetch_data_async(self, mock_market_cap, mock_price, mock_eps, 
                               mock_shares, mock_growth, mock_fcf):
        """Test async data fetching"""
        logger.info("Test async data fetching")
        # Setup mocks
        mock_fcf.return_value = 1000000
        mock_growth.return_value = 10.0
        mock_shares.return_value = 1000000
        mock_eps.return_value = 1000.0
        mock_price.return_value = 50000.0
        mock_market_cap.return_value = (500000000000.0, None)
        
        calculator = DCFCalculator(self.test_config_file)
        
        async def run_test():
            data = await calculator.fetch_data_async()
            return data
        
        data = asyncio.run(run_test())
        
        self.assertIn('fcf', data, "Should have FCF")
        self.assertIn('ge', data, "Should have growth estimate")
        self.assertIn('shares', data, "Should have shares")
        self.assertIn('eps', data, "Should have EPS")
        self.assertIn('price', data, "Should have price")
        self.assertIn('market_cap', data, "Should have market cap")
        self.assertEqual(data['fcf'], 1000000, "Should have correct FCF")
        logger.info("Async data fetching test succeeded")

    @border
    @patch('src.core.dcf_calculator.get_free_cash_flow')
    @patch('src.core.dcf_calculator.get_growth_estimate')
    @patch('src.core.dcf_calculator.get_shares_outstanding')
    @patch('src.core.dcf_calculator.get_earnings_per_share_Diluted')
    @patch('src.core.dcf_calculator.price_board_stock')
    @patch('src.core.dcf_calculator.get_market_cap')
    def test_calculate_full_flow(self, mock_market_cap, mock_price, mock_eps,
                                   mock_shares, mock_growth, mock_fcf):
        """Test full calculation flow"""
        logger.info("Test full calculation flow")
        # Setup mocks
        mock_fcf.return_value = 1000000
        mock_growth.return_value = 10.0
        mock_shares.return_value = 1000000
        mock_eps.return_value = 1000.0
        mock_price.return_value = 50000.0
        mock_market_cap.return_value = (500000000000.0, None)
        
        calculator = DCFCalculator(self.test_config_file)
        
        async def run_test():
            result = await calculator.calculate()
            return result
        
        result = asyncio.run(run_test())
        
        self.assertIn('ticker', result, "Should have ticker")
        self.assertIn('dcf_fair_value', result, "Should have DCF fair value")
        self.assertIn('graham_fair_value', result, "Should have Graham fair value")
        self.assertIn('average_fair_value', result, "Should have average fair value")
        self.assertEqual(result['ticker'], 'TEST', "Should have correct ticker")
        self.assertGreater(result['dcf_fair_value'], 0, "DCF fair value should be positive")
        logger.info("Full calculation flow test succeeded")

    @border
    @patch('src.core.dcf_calculator.get_free_cash_flow')
    @patch('src.core.dcf_calculator.get_growth_estimate')
    @patch('src.core.dcf_calculator.get_shares_outstanding')
    @patch('src.core.dcf_calculator.get_earnings_per_share_Diluted')
    @patch('src.core.dcf_calculator.price_board_stock')
    @patch('src.core.dcf_calculator.get_market_cap')
    def test_calculate_dcf_from_config_function(self, mock_market_cap, mock_price, 
                                                  mock_eps, mock_shares, mock_growth, mock_fcf):
        """Test calculate_dcf_from_config function"""
        logger.info("Test calculate_dcf_from_config function")
        # Setup mocks
        mock_fcf.return_value = 1000000
        mock_growth.return_value = 10.0
        mock_shares.return_value = 1000000
        mock_eps.return_value = 1000.0
        mock_price.return_value = 50000.0
        mock_market_cap.return_value = (500000000000.0, None)
        
        async def run_test():
            result = await calculate_dcf_from_config(self.test_config_file)
            return result
        
        result = asyncio.run(run_test())
        
        self.assertIn('ticker', result, "Should have ticker")
        self.assertIn('dcf_fair_value', result, "Should have DCF fair value")
        self.assertEqual(result['ticker'], 'TEST', "Should have correct ticker")
        logger.info("calculate_dcf_from_config function test succeeded")


if __name__ == '__main__':
    unittest.main()

