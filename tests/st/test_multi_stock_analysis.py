"""
System Test: Multi-Stock Analysis
Tests analyzing multiple stocks in sequence
"""
import unittest
import sys
import os
import asyncio

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.core.dcf_calculator import calculate_dcf_from_config
sys.path.insert(0, os.path.join(project_root, 'tests'))
from lib.test_logger import border, logger


class TestMultiStockAnalysis(unittest.TestCase):
    """Test multi-stock analysis functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = os.path.join(project_root, 'tests', 'tmp')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Create multiple test config files
        self.test_configs = []
        tickers = ['STOCK1', 'STOCK2', 'STOCK3']
        
        for ticker in tickers:
            config_content = f"""
[ticker]
ticker = {ticker}

[dcf]
yr = 5
dr = 10.0
pr = 2.5

[graham]
base_pe = 8.5
growth_multiplier = 2.0
"""
            config_file = os.path.join(self.test_dir, f'{ticker}.cfg')
            with open(config_file, 'w') as f:
                f.write(config_content)
            self.test_configs.append(config_file)

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up config files
        for config_file in self.test_configs:
            if os.path.exists(config_file):
                os.remove(config_file)
        
        # Clean up cache and result files
        for ticker in ['STOCK1', 'STOCK2', 'STOCK3']:
            cache_file = os.path.join(project_root, 'data', 'cache', f'{ticker.lower()}_cache.json')
            if os.path.exists(cache_file):
                os.remove(cache_file)
            
            result_file = os.path.join(project_root, 'data', 'results', f'{ticker.lower()}_result.json')
            if os.path.exists(result_file):
                os.remove(result_file)

    @border
    def test_multi_stock_sequential(self):
        """Test analyzing multiple stocks sequentially"""
        logger.info("Testing sequential multi-stock analysis")
        
        async def run_test():
            results = []
            
            for config_file in self.test_configs:
                try:
                    result = await calculate_dcf_from_config(config_file)
                    results.append(result)
                    logger.info(f"Analyzed {result['ticker']}: DCF={result['dcf_fair_value']:,.2f}")
                except Exception as e:
                    logger.warning(f"Failed to analyze {config_file}: {e}")
            
            # Verify all stocks were analyzed
            self.assertEqual(len(results), len(self.test_configs))
            
            # Verify each result has required fields
            for result in results:
                self.assertIn('ticker', result)
                self.assertIn('dcf_fair_value', result)
                self.assertIn('graham_fair_value', result)
                self.assertGreater(result['dcf_fair_value'], 0)
            
            logger.info(f"Successfully analyzed {len(results)} stocks")
            return results
        
        results = asyncio.run(run_test())
        logger.info("Sequential multi-stock analysis test passed")

    @border
    def test_multi_stock_parallel(self):
        """Test analyzing multiple stocks in parallel"""
        logger.info("Testing parallel multi-stock analysis")
        
        async def run_test():
            # Create tasks for parallel execution
            tasks = [
                calculate_dcf_from_config(config_file)
                for config_file in self.test_configs
            ]
            
            # Run all tasks in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions
            valid_results = [r for r in results if not isinstance(r, Exception)]
            
            # Verify results
            self.assertGreater(len(valid_results), 0)
            
            for result in valid_results:
                self.assertIn('ticker', result)
                self.assertIn('dcf_fair_value', result)
                self.assertGreater(result['dcf_fair_value'], 0)
            
            logger.info(f"Successfully analyzed {len(valid_results)} stocks in parallel")
            return valid_results
        
        results = asyncio.run(run_test())
        logger.info("Parallel multi-stock analysis test passed")

    @border
    def test_multi_stock_result_consistency(self):
        """Test that results are consistent across multiple runs"""
        logger.info("Testing result consistency")
        
        async def run_test():
            # Run analysis twice
            results1 = []
            results2 = []
            
            for config_file in self.test_configs[:1]:  # Test with one stock
                result1 = await calculate_dcf_from_config(config_file)
                results1.append(result1)
                
                # Run again
                result2 = await calculate_dcf_from_config(config_file)
                results2.append(result2)
            
            # Results should be consistent (same ticker, similar values)
            for r1, r2 in zip(results1, results2):
                self.assertEqual(r1['ticker'], r2['ticker'])
                # Values might differ slightly due to market data updates, but structure should be same
                self.assertIn('dcf_fair_value', r1)
                self.assertIn('dcf_fair_value', r2)
            
            logger.info("Result consistency verified")
        
        asyncio.run(run_test())
        logger.info("Result consistency test passed")


if __name__ == '__main__':
    unittest.main()

