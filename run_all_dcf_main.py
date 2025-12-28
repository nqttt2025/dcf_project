#!/usr/bin/env python3
"""
Runner script to run all DCF analyses
Run from project root: python3 run_all_dcf_main.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.dcf_calculator import calculate_dcf_from_config
from src.utils.logger import get_logger

logger = get_logger()


async def main():
    """Run DCF analysis for all stocks"""
    logger.info("\n" + "=" * 100)
    logger.info("DCF ANALYSIS - ALL STOCKS")
    logger.info("=" * 100)
    
    # Find all config files
    config_dir = Path('config')
    config_files = sorted(config_dir.glob('*.cfg'))
    
    if not config_files:
        logger.error("No config files found in config directory!")
        sys.exit(1)
    
    logger.info(f"Found {len(config_files)} config file(s)")
    
    results = []
    for cfg_file in config_files:
        try:
            logger.info(f"\nProcessing: {cfg_file.name}")
            result = await calculate_dcf_from_config(f'config/{cfg_file.name}')
            results.append(result)
            logger.info(f"✓ {result['ticker']}: DCF Fair Value = {result['dcf_fair_value']:,.2f}")
        except Exception as e:
            logger.error(f"✗ Error analyzing {cfg_file.name}: {e}")
    
    # Print summary
    if results:
        logger.info("\n" + "=" * 120)
        logger.info("VALUATION SUMMARY - All Stocks")
        logger.info("=" * 120)
        logger.info(f"{'Ticker':<8} {'Price':<14} {'DCF Fair':<14} {'Graham Fair':<14} "
                   f"{'Avg Fair':<14} {'Upside %':<10}")
        logger.info("-" * 120)
        
        for result in results:
            ticker = result['ticker']
            price = result['price']
            dcf_fair = result['dcf_fair_value']
            graham_fair = result.get('graham_fair_value', 0) or 0
            avg_fair = result['average_fair_value']
            upside_pct = ((avg_fair - price) / price * 100) if price > 0 else 0
            
            logger.info(f"{ticker:<8} {price:>12,.0f}  {dcf_fair:>12,.2f}  {graham_fair:>12,.2f}  "
                       f"{avg_fair:>12,.2f}  {upside_pct:>8.1f}%")
        
        logger.info("=" * 120)
        logger.info(f"\n✓ Analysis completed for {len(results)} stock(s)")
    else:
        logger.error("No successful analyses!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
