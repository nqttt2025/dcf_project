"""
Example script - Sử dụng DCF Calculator module
"""

import asyncio
from dcf_calculator import calculate_dcf_from_config
from logger import get_logger

logger = get_logger()


async def analyze_multiple_stocks(config_files):
    """
    Analyze multiple stocks từ multiple config files
    
    Args:
        config_files: List of config files (ví dụ: ['FPT.cfg', 'VNM.cfg', 'BID.cfg'])
    
    Returns:
        List of results
    """
    logger.info(f"Analyzing {len(config_files)} stocks...")
    
    results = []
    for config_file in config_files:
        try:
            result = await calculate_dcf_from_config(config_file)
            results.append(result)
            logger.info(f"✓ {result['ticker']}: DCF={result['dcf_fair_value']:,.2f}")
        except Exception as e:
            logger.error(f"✗ Error analyzing {config_file}: {e}")
    
    return results


def print_comparison_table(results):
    """Print comparison table of all stocks"""
    logger.info("\n" + "=" * 120)
    logger.info("Stock Comparison Table")
    logger.info("=" * 120)
    logger.info(f"{'Ticker':<10} {'Price':<12} {'DCF Fair':<12} {'Graham Fair':<12} {'Avg Fair':<12} {'Upside':<10} {'Cache':<30}")
    logger.info("-" * 120)
    
    for result in results:
        upside_pct = ((result['average_fair_value'] - result['price']) / result['price'] * 100) if result['price'] > 0 else 0
        cache_file = result['cache_file'].split('/')[-1]
        
        line = f"{result['ticker']:<10} {result['price']:>10,.0f}  {result['dcf_fair_value']:>10,.0f}  " + \
               f"{result['graham_fair_value']:>10,.0f}  {result['average_fair_value']:>10,.0f}  " + \
               f"{upside_pct:>8.1f}%  {cache_file:<30}"
        logger.info(line)
    
    logger.info("=" * 120)


async def main():
    """Main function"""
    logger.info("Starting multi-stock DCF analysis...")
    
    # Analyze 3 stocks from database folder
    config_files = ['database/FPT.cfg', 'database/VNM.cfg', 'database/BID.cfg']
    
    results = await analyze_multiple_stocks(config_files)
    
    # Print comparison
    if results:
        print_comparison_table(results)
        
        logger.info(f"Analysis completed for {len(results)} stocks")
        logger.info("Cache files created:")
        for result in results:
            logger.info(f"  - {result['cache_file']}")


if __name__ == "__main__":
    asyncio.run(main())
