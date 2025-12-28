"""
System Test: DCF Pipeline
Tests the complete DCF calculation pipeline from config to result
"""
import unittest
import sys
import os
import asyncio
import json

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.core.dcf_calculator import calculate_dcf_from_config, DCFCalculator
sys.path.insert(0, os.path.join(project_root, 'tests'))
from lib.test_logger import border, logger


class TestDCFPipeline(unittest.TestCase):
    """Test complete DCF calculation pipeline"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = os.path.join(project_root, 'tests', 'tmp')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Create test config file
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

[report]
language = en
"""
        self.test_config_file = os.path.join(self.test_dir, 'TEST.cfg')
        with open(self.test_config_file, 'w') as f:
            f.write(self.test_config_content)

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)
        
        # Clean up cache and result files
        cache_file = os.path.join(project_root, 'data', 'cache', 'test_cache.json')
        if os.path.exists(cache_file):
            os.remove(cache_file)
        
        result_file = os.path.join(project_root, 'data', 'results', 'test_result.json')
        if os.path.exists(result_file):
            os.remove(result_file)
        
        result_text = os.path.join(project_root, 'data', 'results', 'test_result.text')
        if os.path.exists(result_text):
            os.remove(result_text)

    @border
    def test_dcf_pipeline_complete(self):
        """Test complete DCF pipeline from config to result"""
        logger.info("Testing complete DCF pipeline")
        
        async def run_test():
            # Run DCF calculation
            result = await calculate_dcf_from_config(self.test_config_file)
            
            # Verify result structure
            self.assertIn('ticker', result)
            self.assertIn('price', result)
            self.assertIn('dcf_fair_value', result)
            self.assertIn('graham_fair_value', result)
            self.assertIn('average_fair_value', result)
            self.assertIn('cache_file', result)
            self.assertIn('result_file', result)
            
            # Verify ticker
            self.assertEqual(result['ticker'], 'TEST')
            
            # Verify values are positive
            self.assertGreater(result['price'], 0)
            self.assertGreater(result['dcf_fair_value'], 0)
            self.assertGreater(result['graham_fair_value'], 0)
            self.assertGreater(result['average_fair_value'], 0)
            
            # Verify cache file exists
            self.assertTrue(os.path.exists(result['cache_file']))
            
            # Verify result file exists
            self.assertTrue(os.path.exists(result['result_file']))
            
            logger.info(f"Pipeline completed successfully")
            logger.info(f"  Ticker: {result['ticker']}")
            logger.info(f"  Price: {result['price']:,.0f} VND")
            logger.info(f"  DCF Fair Value: {result['dcf_fair_value']:,.2f} VND")
            logger.info(f"  Graham Fair Value: {result['graham_fair_value']:,.2f} VND")
            logger.info(f"  Average Fair Value: {result['average_fair_value']:,.2f} VND")
            
            return result
        
        result = asyncio.run(run_test())
        logger.info("Complete DCF pipeline test passed")

    @border
    def test_dcf_pipeline_cache_creation(self):
        """Test that cache file is created correctly"""
        logger.info("Testing cache file creation")
        
        async def run_test():
            result = await calculate_dcf_from_config(self.test_config_file)
            
            # Verify cache file exists
            cache_file = result['cache_file']
            self.assertTrue(os.path.exists(cache_file))
            
            # Load and verify cache content
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Verify cache contains expected keys
            expected_keys = ['fcf', 'shares', 'eps', 'price', 'market_cap']
            for key in expected_keys:
                self.assertIn(key, cache_data)
            
            logger.info(f"Cache file created: {os.path.basename(cache_file)}")
            logger.info(f"Cache entries: {len(cache_data)}")
            
        asyncio.run(run_test())
        logger.info("Cache creation test passed")

    @border
    def test_dcf_pipeline_result_files(self):
        """Test that result files (JSON and text) are created"""
        logger.info("Testing result file creation")
        
        async def run_test():
            result = await calculate_dcf_from_config(self.test_config_file)
            
            # Verify JSON result file
            json_file = result['result_file']
            self.assertTrue(os.path.exists(json_file))
            
            with open(json_file, 'r') as f:
                result_data = json.load(f)
            
            # Verify result data structure
            self.assertIn('ticker', result_data)
            self.assertIn('dcf_fair_value', result_data)
            
            # Verify text result file (should have same name with .text extension)
            text_file = json_file.replace('.json', '.text')
            self.assertTrue(os.path.exists(text_file))
            
            # Verify text file is not empty
            with open(text_file, 'r') as f:
                text_content = f.read()
                self.assertGreater(len(text_content), 0)
            
            logger.info(f"Result files created:")
            logger.info(f"  JSON: {os.path.basename(json_file)}")
            logger.info(f"  Text: {os.path.basename(text_file)}")
            
        asyncio.run(run_test())
        logger.info("Result files creation test passed")

    @border
    def test_dcf_pipeline_error_handling(self):
        """Test error handling in pipeline"""
        logger.info("Testing error handling")
        
        # Test with invalid config file
        invalid_config = os.path.join(self.test_dir, 'INVALID.cfg')
        with open(invalid_config, 'w') as f:
            f.write("invalid config content")
        
        async def run_test():
            with self.assertRaises(Exception):
                await calculate_dcf_from_config(invalid_config)
        
        asyncio.run(run_test())
        os.remove(invalid_config)
        logger.info("Error handling test passed")


if __name__ == '__main__':
    unittest.main()

