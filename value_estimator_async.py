from lxml import html
import requests
import json
import argparse
import asyncio
from collections import OrderedDict
from fcfs import (
    get_free_cash_flow, 
    get_shares_outstanding, 
    get_earnings_per_share_Diluted, 
    price_board_stock, 
    get_market_cap
)
from ge import get_growth_estimate
from cache_manager import get_cache_manager
from config_manager import get_config_manager
from logger import get_logger
import warnings
warnings.filterwarnings('ignore')

logger = get_logger()
config_manager = get_config_manager()


async def async_parse(ticker, config):
    """
    Fetch financial data asynchronously for faster execution.
    Runs multiple data fetching operations in parallel.
    """
    logger.info(f"Starting async data fetch for {ticker}...")
    
    # Create tasks for concurrent execution
    tasks = [
        asyncio.to_thread(get_free_cash_flow, ticker.upper()),
        asyncio.to_thread(get_growth_estimate, ticker.upper()),
        asyncio.to_thread(get_shares_outstanding, ticker.upper()),
        asyncio.to_thread(get_earnings_per_share_Diluted, ticker.upper()),
        asyncio.to_thread(price_board_stock, ticker.upper()),
        asyncio.to_thread(lambda: get_market_cap(ticker.upper())[0]),  # Get market cap, discard price
    ]
    
    # Execute all tasks concurrently
    logger.info("Fetching: FCF, Growth Estimate, Shares, EPS, Price, Market Cap (in parallel)...")
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle results
    last_fcf = results[0]
    ge = results[1]
    shares = results[2]
    eps = results[3]
    market_price = results[4]
    market_cap = results[5]
    
    # Check for errors
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Error in task {i}: {result}")
    
    logger.info("Data fetch completed")
    
    return {
        'fcf': last_fcf,
        'ge': ge,
        'yr': config['yr'],
        'dr': config['dr'],
        'pr': config['pr'],
        'shares': shares,
        'eps': eps,
        'mp': market_price,
        'market_cap': market_cap,
    }


def dcf(data):
    """Calculate DCF valuation"""
    forecast = [data['fcf']]

    if data['ge'] == [] or data['ge'] is None:
        raise ValueError("No growth rate available")

    for _ in range(1, data['yr']):
        forecast.append(round(forecast[-1] + (data['ge'] / 100) * forecast[-1], 2))

    forecast.append(round(forecast[-1] * (1 + (data['pr'] / 100)) / (data['dr'] / 100 - data['pr'] / 100), 2))
    discount_factors = [1 / (1 + (data['dr'] / 100))**(i + 1) for i in range(len(forecast) - 1)]

    pvs = [round(f * d, 2) for f, d in zip(forecast[:-1], discount_factors)]
    pvs.append(round(discount_factors[-1] * forecast[-1], 2))

    logger.info("Forecasted cash flows: {}".format(", ".join(map(str, forecast))))
    logger.info("PV of cash flows: {}".format(", ".join(map(str, pvs))))

    dcf_value = sum(pvs)
    fair_value = dcf_value / data['shares']
    logger.info("Fair value: {:.2f}".format(fair_value))
    
    return fair_value


def graham(data):
    """Calculate Graham valuation"""
    base_pe = config_manager.get_graham_params()['base_pe']
    growth_multiplier = config_manager.get_graham_params()['growth_multiplier']
    
    if data['eps'] > 0:
        expected_value = data['eps'] * (base_pe + growth_multiplier * (data['ge']))
        ge_priced_in = (data['mp'] / data['eps'] - base_pe) / growth_multiplier

        logger.info("Expected value based on growth rate: {:.2f}".format(expected_value))
        logger.info("Growth rate priced in for next 7-10 years: {:.2f}%".format(ge_priced_in))
        
        return expected_value
    else:
        logger.warning("Not applicable since EPS is negative.")
        return None


async def main():
    """Main async function"""
    # Get configuration
    config = config_manager.get_dcf_params()
    ticker = config_manager.get_ticker()
    
    logger.info("=" * 80)
    logger.info("DCF Valuation Analysis")
    logger.info("=" * 80)
    
    # Log configuration
    config_manager.log_config()
    
    logger.info(f"Fetching data for {ticker}...")
    
    # Fetch data asynchronously
    data = await async_parse(ticker, config)
    
    logger.info("=" * 80)
    logger.info("DCF model (basic)")
    logger.info("=" * 80)

    logger.info("Market price: {:.2f}".format(data['mp']))
    logger.info("EPS: {:.2f}".format(data['eps']))
    logger.info("Growth estimate: {:.2f}%".format(data['ge']))
    logger.info("Market Cap: {:.0f}".format(data['market_cap']))
    logger.info("Term: {} years".format(data['yr']))
    logger.info("Discount Rate: {}%".format(data['dr']))
    logger.info("Perpetual Rate: {}%".format(data['pr']))

    # Calculate DCF
    dcf_fair_value = dcf(data)

    logger.info("=" * 80)
    logger.info("Graham style valuation basic (Page 295, The Intelligent Investor)")
    logger.info("=" * 80)

    graham_fair_value = graham(data)
    
    # Summary
    logger.info("=" * 80)
    logger.info("Valuation Summary")
    logger.info("=" * 80)
    logger.info("Current Price: {:.2f}".format(data['mp']))
    logger.info("DCF Fair Value: {:.2f}".format(dcf_fair_value))
    logger.info("Graham Fair Value: {:.2f}".format(graham_fair_value if graham_fair_value else 0))
    
    if graham_fair_value:
        avg_fair_value = (dcf_fair_value + graham_fair_value) / 2
        logger.info("Average Fair Value: {:.2f}".format(avg_fair_value))
    
    logger.info("=" * 80)
    
    # Save cache
    cache_manager = get_cache_manager()
    cache_manager.save_to_file()


if __name__ == "__main__":
    asyncio.run(main())
