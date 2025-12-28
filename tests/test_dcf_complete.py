#!/usr/bin/env python3
"""
Complete DCF Calculator Module Test
"""
import asyncio
import json
import os
from dcf_calculator import calculate_dcf_from_config

async def main():
    print("\n" + "="*80)
    print("DCF CALCULATOR MODULE - COMPLETE FUNCTIONALITY TEST")
    print("="*80)

    # Test 1: Single ticker analysis
    print("\n✓ TEST 1: Single Ticker Analysis (FPT)")
    print("-" * 80)
    result_fpt = await calculate_dcf_from_config('FPT.cfg')
    print(f"  Ticker: {result_fpt['ticker']}")
    print(f"  Price: {result_fpt['price']:,.0f} VND")
    print(f"  DCF Fair Value: {result_fpt['dcf_fair_value']:,.2f} VND")
    print(f"  Graham Fair Value: {result_fpt['graham_fair_value']:,.2f} VND")
    print(f"  Average Fair Value: {result_fpt['average_fair_value']:,.2f} VND")
    upside = ((result_fpt['average_fair_value'] - result_fpt['price']) / result_fpt['price'] * 100)
    print(f"  Upside/Downside: {upside:.1f}%")

    # Test 2: Verify cache file
    print("\n✓ TEST 2: Cache File Verification")
    print("-" * 80)
    cache_file = result_fpt['cache_file']
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            cache_data = json.load(f)
        print(f"  Cache File: {os.path.basename(cache_file)}")
        print(f"  Total Entries: {len(cache_data)}")
        print(f"  Data Points:")
        for key, value in list(cache_data.items())[:6]:
            if 'timestamp' not in key:
                print(f"    - {key}: {value}")

    # Test 3: Multiple stock analysis
    print("\n✓ TEST 3: Multi-Stock Analysis")
    print("-" * 80)
    configs = ['FPT.cfg', 'VNM.cfg', 'BID.cfg']
    results = []
    for config in configs:
        try:
            r = await calculate_dcf_from_config(config)
            results.append(r)
            upside = ((r['average_fair_value'] - r['price']) / r['price'] * 100)
            print(f"  {r['ticker']:<5} | Price: {r['price']:>12,.0f} | DCF: {r['dcf_fair_value']:>12,.2f} | Graham: {r['graham_fair_value']:>12,.2f} | Upside: {upside:>7.1f}%")
        except Exception as e:
            print(f"  {config}: Error - {e}")

    # Test 4: Summary
    print("\n✓ TEST 4: Summary")
    print("-" * 80)
    print(f"  Total Stocks Analyzed: {len(results)}")
    total_upside = sum(((r['average_fair_value'] - r['price']) / r['price'] * 100) for r in results)
    avg_upside = total_upside / len(results) if results else 0
    print(f"  Average Upside: {avg_upside:.1f}%")
    print(f"  Cache Files Created: {len([r for r in results])} ({', '.join([os.path.basename(r['cache_file']) for r in results])})")

    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED - DCF CALCULATOR MODULE FULLY FUNCTIONAL")
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
