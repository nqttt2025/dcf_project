#!/usr/bin/env python3
"""
Script chạy DCF cho tất cả mã với retry và delay để tránh quá tải API
"""
import asyncio
import sys
import os
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.dcf_calculator import calculate_dcf_from_config
from src.utils.logger import get_logger

logger = get_logger()

# Delay giữa các request (giây)
DELAY_BETWEEN_REQUESTS = 2
MAX_RETRIES = 3

async def run_dcf_with_retry(config_file, retry_count=0):
    """Chạy DCF với retry logic"""
    try:
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing: {config_file.name} (Attempt {retry_count + 1}/{MAX_RETRIES})")
        logger.info(f"{'='*80}")
        
        result = await calculate_dcf_from_config(f'config/{config_file.name}')
        logger.info(f"✓ {result['ticker']}: DCF Fair Value = {result['dcf_fair_value']:,.2f}")
        return result
    except Exception as e:
        if retry_count < MAX_RETRIES - 1:
            wait_time = (retry_count + 1) * 5  # Exponential backoff: 5s, 10s, 15s
            logger.warning(f"✗ Error analyzing {config_file.name}: {e}")
            logger.info(f"Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            return await run_dcf_with_retry(config_file, retry_count + 1)
        else:
            logger.error(f"✗ Failed to analyze {config_file.name} after {MAX_RETRIES} attempts: {e}")
            return None

async def main():
    """Run DCF analysis for all stocks with retry and delay"""
    logger.info("\n" + "=" * 100)
    logger.info("DCF ANALYSIS - ALL STOCKS (WITH RETRY & DELAY)")
    logger.info("=" * 100)
    
    # Find all config files
    config_dir = Path('config')
    config_files = sorted(config_dir.glob('*.cfg'))
    
    # Filter out test configs
    config_files = [f for f in config_files if f.stem.upper() != 'TEST']
    
    if not config_files:
        logger.error("No config files found in config directory!")
        sys.exit(1)
    
    logger.info(f"Found {len(config_files)} config file(s)")
    
    # Check which ones are already done
    results_dir = Path('data/results')
    completed_tickers = set()
    if results_dir.exists():
        completed_files = list(results_dir.glob('*.text'))
        completed_tickers = {f.stem.replace('_result', '').upper() for f in completed_files}
        logger.info(f"Already completed: {len(completed_tickers)} ticker(s)")
    
    # Filter out already completed
    remaining_configs = [f for f in config_files if f.stem.upper() not in completed_tickers]
    
    if not remaining_configs:
        logger.info("All stocks have been analyzed!")
        return
    
    logger.info(f"Remaining to process: {len(remaining_configs)} ticker(s)")
    logger.info(f"Tickers: {', '.join([f.stem.upper() for f in remaining_configs])}")
    
    results = []
    total = len(remaining_configs)
    
    for idx, cfg_file in enumerate(remaining_configs, 1):
        logger.info(f"\n[{idx}/{total}] Processing {cfg_file.stem.upper()}...")
        
        result = await run_dcf_with_retry(cfg_file)
        if result:
            results.append(result)
        
        # Delay between requests (except for the last one)
        if idx < total:
            logger.info(f"Waiting {DELAY_BETWEEN_REQUESTS} seconds before next request...")
            await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
    
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

