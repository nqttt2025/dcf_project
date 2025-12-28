"""
Unit tests for Free Cash Flow TTM calculation
"""
import unittest
import os
import sys
from unittest.mock import patch, MagicMock
import pandas as pd

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '../..')
sys.path.insert(0, project_root)

from src.core.fcfs import get_free_cash_flow, get_free_cash_flow_ttm
# Add tests to path for test_logger
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lib.test_logger import logger, border


class TestFCFTTM(unittest.TestCase):
    """Test cases for Free Cash Flow TTM calculation"""

    @border
    def setUp(self):
        """Set up before each test"""
        logger.info("Execute test case %s", self.id())

    @border
    def tearDown(self):
        """Clean up after each test"""
        logger.info("Execute test case %s completed", self.id())

    @border
    @patch('src.core.fcfs.Vnstock')
    @patch('src.core.fcfs.cache_manager')
    def test_get_free_cash_flow_ttm_success(self, mock_cache, mock_vnstock):
        """Test successful TTM calculation with 4 quarters"""
        logger.info("Test TTM calculation with 4 quarters")
        
        # Setup mock cache - no cached value
        mock_cache.exists.return_value = False
        
        # Setup mock vnstock data
        mock_stock_instance = MagicMock()
        mock_vnstock.return_value.stock.return_value = mock_stock_instance
        
        # Create mock DataFrame with 4 quarters
        cash_flow_data = {
            'yearReport': [2025, 2025, 2024, 2024],
            'lengthReport': [3, 2, 4, 3],
            'Net cash inflows/outflows from operating activities': [
                4344020060779,  # Q3 2025
                4190477000730,  # Q2 2025
                5396556198562,  # Q4 2024
                3235944796986   # Q3 2024
            ],
            'Purchase of fixed assets': [
                -830371040007,  # Q3 2025 (negative)
                -687830960368,  # Q2 2025
                -838077306200,  # Q4 2024
                -876954143250   # Q3 2024
            ]
        }
        mock_df = pd.DataFrame(cash_flow_data)
        mock_stock_instance.finance.cash_flow.return_value = mock_df
        
        # Call function
        result = get_free_cash_flow_ttm('FPT')
        
        # Verify result
        self.assertIsNotNone(result, "Should return a value")
        self.assertIsInstance(result, float, "Should return a float")
        self.assertGreater(result, 0, "FCF should be positive")
        
        # Expected: Sum of OCF - Sum of CapEx
        expected_ocf = sum(cash_flow_data['Net cash inflows/outflows from operating activities'])
        expected_capex = sum([abs(x) for x in cash_flow_data['Purchase of fixed assets']])
        expected_fcf = expected_ocf - expected_capex
        
        self.assertAlmostEqual(result, expected_fcf, delta=1.0, 
                              msg="Should calculate correct TTM FCF")
        logger.info("TTM calculation test succeeded")

    @border
    @patch('src.core.fcfs.Vnstock')
    @patch('src.core.fcfs.cache_manager')
    def test_get_free_cash_flow_ttm_with_cache(self, mock_cache, mock_vnstock):
        """Test TTM calculation using cached value"""
        logger.info("Test TTM calculation with cache")
        
        # Setup mock cache - has cached value
        cached_value = 13933764607232.0
        mock_cache.exists.return_value = True
        mock_cache.get_with_timestamp.return_value = cached_value
        
        # Call function
        result = get_free_cash_flow_ttm('FPT')
        
        # Verify result
        self.assertEqual(result, cached_value, "Should return cached value")
        mock_cache.exists.assert_called_once_with('FPT', 'fcf_ttm')
        logger.info("TTM cache test succeeded")

    @border
    @patch('src.core.fcfs.Vnstock')
    @patch('src.core.fcfs.cache_manager')
    def test_get_free_cash_flow_ttm_insufficient_quarters(self, mock_cache, mock_vnstock):
        """Test TTM calculation with insufficient quarters"""
        logger.info("Test TTM calculation with insufficient data")
        
        # Setup mock cache - no cached value
        mock_cache.exists.return_value = False
        
        # Setup mock vnstock data - only 2 quarters
        mock_stock_instance = MagicMock()
        mock_vnstock.return_value.stock.return_value = mock_stock_instance
        
        cash_flow_data = {
            'yearReport': [2025, 2025],
            'lengthReport': [3, 2],
            'Net cash inflows/outflows from operating activities': [
                4344020060779,
                4190477000730
            ],
            'Purchase of fixed assets': [
                -830371040007,
                -687830960368
            ]
        }
        mock_df = pd.DataFrame(cash_flow_data)
        mock_stock_instance.finance.cash_flow.return_value = mock_df
        
        # Call function
        result = get_free_cash_flow_ttm('FPT')
        
        # Should still return a value (sum of available quarters)
        # But log a warning about insufficient quarters
        self.assertIsNotNone(result, "Should return a value even with insufficient quarters")
        logger.info("Insufficient quarters test succeeded")

    @border
    @patch('src.core.fcfs.Vnstock')
    @patch('src.core.fcfs.cache_manager')
    def test_get_free_cash_flow_default_uses_ttm(self, mock_cache, mock_vnstock):
        """Test that get_free_cash_flow defaults to TTM"""
        logger.info("Test get_free_cash_flow defaults to TTM")
        
        # Setup mock cache - no cached value
        mock_cache.exists.return_value = False
        
        # Setup mock vnstock data
        mock_stock_instance = MagicMock()
        mock_vnstock.return_value.stock.return_value = mock_stock_instance
        
        cash_flow_data = {
            'yearReport': [2025, 2025, 2024, 2024],
            'lengthReport': [3, 2, 4, 3],
            'Net cash inflows/outflows from operating activities': [
                4344020060779,
                4190477000730,
                5396556198562,
                3235944796986
            ],
            'Purchase of fixed assets': [
                -830371040007,
                -687830960368,
                -838077306200,
                -876954143250
            ]
        }
        mock_df = pd.DataFrame(cash_flow_data)
        mock_stock_instance.finance.cash_flow.return_value = mock_df
        
        # Call function without use_ttm parameter (should default to True)
        result = get_free_cash_flow('FPT')
        
        # Verify result
        self.assertIsNotNone(result, "Should return a value")
        self.assertIsInstance(result, float, "Should return a float")
        self.assertGreater(result, 0, "FCF should be positive")
        logger.info("Default TTM test succeeded")

    @border
    @patch('src.core.fcfs.Vnstock')
    @patch('src.core.fcfs.cache_manager')
    def test_get_free_cash_flow_with_ttm_false(self, mock_cache, mock_vnstock):
        """Test get_free_cash_flow with use_ttm=False"""
        logger.info("Test get_free_cash_flow with use_ttm=False")
        
        # Setup mock cache - no cached value
        mock_cache.exists.return_value = False
        
        # Setup mock vnstock data - single quarter
        mock_stock_instance = MagicMock()
        mock_vnstock.return_value.stock.return_value = mock_stock_instance
        
        cash_flow_data = {
            'yearReport': [2025],
            'lengthReport': [3],
            'Net cash inflows/outflows from operating activities': [4344020060779],
            'Purchase of fixed assets': [-830371040007]
        }
        mock_df = pd.DataFrame(cash_flow_data)
        mock_stock_instance.finance.cash_flow.return_value = mock_df
        
        # Call function with use_ttm=False
        result = get_free_cash_flow('FPT', use_ttm=False)
        
        # Verify result
        self.assertIsNotNone(result, "Should return a value")
        self.assertIsInstance(result, float, "Should return a float")
        
        # Should be single quarter FCF
        expected_fcf = 4344020060779 - 830371040007
        self.assertAlmostEqual(result, expected_fcf, delta=1.0,
                              msg="Should calculate single quarter FCF")
        logger.info("Single quarter test succeeded")

    @border
    @patch('src.core.fcfs.Vnstock')
    @patch('src.core.fcfs.cache_manager')
    def test_get_free_cash_flow_ttm_empty_dataframe(self, mock_cache, mock_vnstock):
        """Test TTM calculation with empty DataFrame"""
        logger.info("Test TTM calculation with empty DataFrame")
        
        # Setup mock cache - no cached value
        mock_cache.exists.return_value = False
        
        # Setup mock vnstock data - empty DataFrame
        mock_stock_instance = MagicMock()
        mock_vnstock.return_value.stock.return_value = mock_stock_instance
        mock_stock_instance.finance.cash_flow.return_value = pd.DataFrame()
        
        # Call function
        result = get_free_cash_flow_ttm('FPT')
        
        # Should return None
        self.assertIsNone(result, "Should return None for empty DataFrame")
        logger.info("Empty DataFrame test succeeded")

    @border
    @patch('src.core.fcfs.Vnstock')
    @patch('src.core.fcfs.cache_manager')
    def test_get_free_cash_flow_ttm_no_valid_data(self, mock_cache, mock_vnstock):
        """Test TTM calculation with no valid data"""
        logger.info("Test TTM calculation with no valid data")
        
        # Setup mock cache - no cached value
        mock_cache.exists.return_value = False
        
        # Setup mock vnstock data - invalid data
        mock_stock_instance = MagicMock()
        mock_vnstock.return_value.stock.return_value = mock_stock_instance
        
        cash_flow_data = {
            'yearReport': [2025],
            'lengthReport': [3],
            'Net cash inflows/outflows from operating activities': [0],  # Invalid
            'Purchase of fixed assets': [0]
        }
        mock_df = pd.DataFrame(cash_flow_data)
        mock_stock_instance.finance.cash_flow.return_value = mock_df
        
        # Call function
        result = get_free_cash_flow_ttm('FPT')
        
        # Should return None
        self.assertIsNone(result, "Should return None for invalid data")
        logger.info("No valid data test succeeded")


if __name__ == '__main__':
    unittest.main()

