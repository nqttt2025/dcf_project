#!/usr/bin/env python3
"""
Main runner script for DCF Analysis
Run from project root: python3 run_dcf.py
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.dcf_calculator import calculate_dcf_from_config
from src.utils.logger import get_logger

logger = get_logger()


async def main():
    """Run DCF analysis for a single stock"""
    if len(sys.argv) < 2:
        print("Usage: python3 run_dcf.py <config_file>")
        print("Example: python3 run_dcf.py FPT.cfg")
        sys.exit(1)

    config_file = sys.argv[1]
    
    try:
        result = await calculate_dcf_from_config(f'config/{config_file}')
        print(f"\n✓ Analysis completed for {result['ticker']}")
        print(f"  DCF Fair Value: {result['dcf_fair_value']:,.2f}")
        print(f"  Cache saved to: {result['cache_file']}")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
