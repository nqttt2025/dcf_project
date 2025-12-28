#!/usr/bin/env python3
"""
Script to run DCF analysis for all stocks
Automatically discovers all .cfg files in the database folder and runs analysis
"""

import asyncio
import os
import sys
from pathlib import Path
from dcf_calculator import calculate_dcf_from_config
from logger import get_logger

logger = get_logger()


def discover_config_files(database_dir='database'):
    """
    Discover all .cfg files in database directory
    
    Args:
        database_dir: Path to database directory
    
    Returns:
        List of config file paths
    """
    config_files = []
    db_path = Path(database_dir)
    
    if not db_path.exists():
        logger.warning(f"Database directory not found: {database_dir}")
        return config_files
    
    # Find all .cfg files
    for cfg_file in sorted(db_path.glob('*.cfg')):
        config_files.append(cfg_file.name)
    
    return config_files


async def analyze_all_stocks(config_files):
    """
    Analyze all stocks from config files
    
    Args:
        config_files: List of config file names
    
    Returns:
        List of results
    """
    if not config_files:
        logger.warning("No config files found!")
        return []
    
    logger.info(f"Analyzing {len(config_files)} stocks...")
    logger.info("=" * 100)
    
    results = []
    for config_file in config_files:
        try:
            logger.info(f"\nProcessing: {config_file}")
            result = await calculate_dcf_from_config(f'database/{config_file}')
            results.append(result)
            logger.info(f"✓ {result['ticker']}: DCF Fair Value = {result['dcf_fair_value']:,.2f}")
        except Exception as e:
            logger.error(f"✗ Error analyzing {config_file}: {e}")
            import traceback
            traceback.print_exc()
    
    return results


def print_summary_table(results):
    """
    Print summary comparison table of all stocks
    
    Args:
        results: List of valuation results
    """
    if not results:
        logger.warning("No results to display")
        return
    
    logger.info("\n" + "=" * 120)
    logger.info("DCF VALUATION SUMMARY - All Stocks")
    logger.info("=" * 120)
    
    # Header
    logger.info(f"{'Ticker':<8} {'Price':<14} {'DCF Fair':<14} {'Graham Fair':<14} "
                f"{'Avg Fair':<14} {'Upside %':<10}")
    logger.info("-" * 120)
    
    # Data rows
    for result in results:
        ticker = result['ticker']
        price = result['price']
        dcf_fair = result['dcf_fair_value']
        graham_fair = result.get('graham_fair_value', 0) or 0
        avg_fair = result['average_fair_value']
        
        # Calculate upside percentage
        if price > 0:
            upside_pct = ((avg_fair - price) / price * 100)
        else:
            upside_pct = 0
        
        logger.info(f"{ticker:<8} {price:>12,.0f}  {dcf_fair:>12,.2f}  {graham_fair:>12,.2f}  "
                    f"{avg_fair:>12,.2f}  {upside_pct:>8.1f}%")
    
    logger.info("=" * 120)


async def main():
    """Main function"""
    logger.info("\n" + "=" * 100)
    logger.info("DCF ANALYSIS - ALL STOCKS")
    logger.info("=" * 100)

    # Discover config files
    config_files = discover_config_files('database')
    
    if not config_files:
        logger.error("No config files found in database directory!")
        sys.exit(1)
    
    logger.info(f"Found {len(config_files)} config file(s): {', '.join(config_files)}")
    
    # Analyze all stocks
    results = await analyze_all_stocks(config_files)
    
    # Print summary
    if results:
        print_summary_table(results)
        logger.info(f"\n✓ Analysis completed for {len(results)} stock(s)")
        logger.info("=" * 100)
    else:
        logger.error("No successful analyses!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
