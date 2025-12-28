import requests
import cloudscraper
from lxml import html
from pandas import json_normalize
import pandas as pd
import urllib3
import time
import json
import os
import sys
from io import StringIO
from datetime import datetime
from ..utils.logger import get_logger
from ..utils.cache_manager import get_cache_manager

try:
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = StringIO()
    sys.stderr = StringIO()
    try:
        from vnstock import Vnstock
        HAS_VNSTOCK = True
    except ImportError:
        HAS_VNSTOCK = False
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
except:
    HAS_VNSTOCK = False
    sys.stdout = old_stdout
    sys.stderr = old_stderr

logger = get_logger()
cache_manager = get_cache_manager()

stock_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://stockanalysis.com/'
}

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

def get_free_cash_flow(ticker):
    if not HAS_VNSTOCK:
        logger.error("vnstock not installed. Install with: pip install vnstock")
        return None

    try:
        logger.info(f"Fetching cash flow data for {ticker} using vnstock...")
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            stock = Vnstock().stock(symbol=ticker.upper(), source="VCI")
            cash_flow_df = stock.finance.cash_flow()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        if cash_flow_df.empty:
            logger.warning(f"No cash flow data available for {ticker}")
            return None

        latest_row = cash_flow_df.iloc[0]

        if 'Net cash inflows/outflows from operating activities' in latest_row.index:
            fcf = latest_row['Net cash inflows/outflows from operating activities']
            if pd.notna(fcf) and fcf > 0:
                logger.info(f"FCF for {ticker}: {fcf:,.0f} VND")
                return float(fcf)

        alt_names = [
            'Net Cash Flows from Operating Activities',
            'Operating cash flow',
            'Cash flows from operating activities'
        ]

        for col_name in alt_names:
            if col_name in latest_row.index:
                fcf = latest_row[col_name]
                if pd.notna(fcf) and fcf > 0:
                    logger.info(f"FCF for {ticker}: {fcf:,.0f} VND")
                    return float(fcf)

        logger.warning(f"Could not find operating cash flow in columns")
        return None

    except Exception as e:
        logger.error(f"Error fetching from vnstock: {e}")
        return None

def get_shares_outstanding(ticker):
    if not HAS_VNSTOCK:
        logger.error("vnstock not installed. Install with: pip install vnstock")
        default_shares = 1703507121 # FPT shares outstanding as of DEC-26-2025
        logger.info(f"Using default: {default_shares}")
        return default_shares

    try:
        logger.info(f"Fetching shares outstanding for {ticker} using vnstock...")
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            stock = Vnstock().stock(symbol=ticker.upper(), source="VCI")
            balance_sheet_df = stock.finance.balance_sheet()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        if balance_sheet_df.empty:
            logger.warning(f"No balance sheet data available for {ticker}")
            raise Exception("No balance sheet data available")

        latest_row = balance_sheet_df.iloc[0]

        # Try to find shares outstanding or common shares in the data
        if 'Common shares (Bn. VND)' in latest_row.index:
            shares_capital = latest_row['Common shares (Bn. VND)']
            if pd.notna(shares_capital) and shares_capital > 0:
                # Convert from charter capital (VND) to number of shares
                # Par value (mệnh giá) of FPT shares is 10,000 VND per share
                par_value = 10000
                shares_count = float(shares_capital) / par_value
                logger.info(f"Fetched shares for {ticker}: {shares_count:,.0f} (from charter capital {shares_capital:,.0f} VND)")
                cache_manager.set_with_timestamp(ticker, "shares", shares_count)
                return shares_count

        # Alternative column names to check
        alt_names = [
            'Paid-in capital (Bn. VND)',
            'Capital and reserves (Bn. VND)',
            'Shares Outstanding'
        ]

        for col_name in alt_names:
            if col_name in latest_row.index:
                shares = latest_row[col_name]
                if pd.notna(shares) and shares > 0:
                    logger.info(f"Fetched shares outstanding for {ticker}: {shares:,.0f}")
                    shares_value = float(shares)
                    cache_manager.set_with_timestamp(ticker, "shares", shares_value)
                    return shares_value

        logger.warning(f"Could not find shares outstanding in balance sheet data")
        raise Exception("Shares outstanding not found in data")

    except Exception as e:
        logger.debug(f"Error fetching shares: {e}")
        # Check cache as fallback
        if cache_manager.exists(ticker, "shares"):
            shares = cache_manager.get_with_timestamp(ticker, "shares")
            logger.info(f"Using cached shares for {ticker}: {shares}")
            return shares
        # Use default if cache also fails
        logger.info(f"Using default share outstanding: {default_shares}")
        return default_shares

def get_earnings_per_share_Diluted(ticker):
    if not HAS_VNSTOCK:
        logger.error("vnstock not installed. Install with: pip install vnstock")
        default_eps = 5000
        logger.info(f"Using default: {default_eps}")
        return default_eps

    try:
        logger.info(f"Fetching EPS for {ticker} using vnstock...")
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            stock = Vnstock().stock(symbol=ticker.upper(), source="VCI")
            income_df = stock.finance.income_statement()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        if income_df.empty:
            logger.warning(f"No income statement data available for {ticker}")
            raise Exception("No income statement data available")

        latest_row = income_df.iloc[0]

        # Get net profit and shares outstanding to calculate EPS
        net_profit = None
        if 'Attributable to parent company' in latest_row.index:
            net_profit = latest_row['Attributable to parent company']
        elif 'Net Profit For the Year' in latest_row.index:
            net_profit = latest_row['Net Profit For the Year']

        if net_profit is None or pd.isna(net_profit) or net_profit <= 0:
            logger.warning(f"Could not find net profit in income statement for {ticker}")
            raise Exception("Net profit not found in data")

        # Get shares outstanding
        shares = get_shares_outstanding(ticker)

        if shares is None or shares <= 0:
            logger.warning(f"Could not get shares outstanding for {ticker}")
            raise Exception("Shares outstanding not available")

        # Calculate EPS = Net Profit / Shares Outstanding
        logger.info(f"Net Profit for {ticker}: {net_profit:,.0f}")
        logger.info(f"Shares Outstanding for {ticker}: {shares:,.0f}")
        eps = float(net_profit) / float(shares)

        logger.info(f"Calculated EPS for {ticker}: {eps:,.2f}")
        cache_manager.set_with_timestamp(ticker, "eps", eps)
        return eps

    except Exception as e:
        logger.debug(f"Error fetching EPS: {e}")
        # Check cache as fallback
        if cache_manager.exists(ticker, "eps"):
            eps = cache_manager.get_with_timestamp(ticker, "eps")
            logger.info(f"Using cached EPS for {ticker}: {eps}")
            return eps
        # Use default if cache also fails
        default_eps = 5000
        logger.info(f"Using default: {default_eps}")
        return default_eps

def price_board_stock(ticker):
    if not HAS_VNSTOCK:
        logger.error("vnstock not installed. Install with: pip install vnstock")
        default_price = 50000
        logger.info(f"Using default: {default_price}")
        return default_price

    try:
        logger.info(f"Fetching price for {ticker} using vnstock...")
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            stock = Vnstock().stock(symbol=ticker.upper(), source="VCI")
            # Get price board data
            price_board_df = stock.trading.price_board([stock.symbol])
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        if price_board_df is not None and not price_board_df.empty:
            # Get the match price from the price board
            price = float(price_board_df.iloc[0][('match', 'match_price')])
            if price > 0:
                logger.info(f"Fetched price for {ticker}: {price}")
                cache_manager.set_with_timestamp(ticker, "price", price)
                return price

        logger.warning(f"No valid price data in response for {ticker}")
        raise Exception("No valid price data in response")
    except Exception as e:
        logger.debug(f"Error fetching price: {e}")
        # Check cache as fallback
        if cache_manager.exists(ticker, "price"):
            price = cache_manager.get_with_timestamp(ticker, "price")
            logger.info(f"Using cached price for {ticker}: {price}")
            return price
        # Use default if cache also fails
        default_price = 50000
        logger.info(f"Using default: {default_price}")
        return default_price


def get_market_cap(ticker):
    if not HAS_VNSTOCK:
        logger.error("vnstock not installed. Install with: pip install vnstock")
        raise Exception("vnstock not installed")

    try:
        logger.info(f"Fetching market cap for {ticker} using vnstock...")
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            stock = Vnstock().stock(symbol=ticker.upper(), source="VCI")
            # Get ratio summary which contains EV (Enterprise Value / Market Cap)
            ratio_df = stock.company.ratio_summary()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        if ratio_df is not None and not ratio_df.empty:
            # Get the EV (Enterprise Value) which equals Market Cap
            market_cap_vnstock = float(ratio_df['ev'].iloc[0])

            # Get price for verification
            price = price_board_stock(ticker)

            # Get shares for verification
            shares = get_shares_outstanding(ticker)

            # Calculate market cap = price × shares for verification
            market_cap_calculated = price * shares

            if market_cap_vnstock > 0:
                logger.info(f"Fetched market cap for {ticker}: {market_cap_vnstock:,.0f} (vnstock EV)")
                logger.info(f"Verification - price: {price}, shares: {shares:,.0f}, calculated: {market_cap_calculated:,.0f}")
                logger.info(f"Match verification: vnstock={market_cap_vnstock:,.0f}, calculated={market_cap_calculated:,.0f}, diff={abs(market_cap_vnstock-market_cap_calculated):,.0f}")
                cache_manager.set_with_timestamp(ticker, "market_cap", market_cap_vnstock)
                return market_cap_vnstock, price

        logger.warning(f"No valid market cap data in response for {ticker}")
        raise Exception("No valid market cap data in response")
    except Exception as e:
        logger.debug(f"Error fetching market cap: {e}")
        # Check cache as fallback
        if cache_manager.exists(ticker, "market_cap"):
            market_cap = cache_manager.get_with_timestamp(ticker, "market_cap")
            # Get cached price or use price_board_stock
            price = price_board_stock(ticker)
            logger.info(f"Using cached market cap for {ticker}: {market_cap:,.0f}")
            return market_cap, price
        # Raise exception if cache also fails
        raise Exception(f"Could not fetch market cap for {ticker}")

def get_equity(ticker):
    try:
        url = "https://stockanalysis.com/quote/hose/{}/statistics/".format(ticker)
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, headers=stock_headers)

        if response.status_code != 200:
            logger.error(f"Failed to fetch data for {ticker}. HTTP Status Code: {response.status_code}")
            raise Exception(f"Failed to fetch data for {ticker}. HTTP Status Code: {response.status_code}")
        parser = html.fromstring(response.content)
        try:
            equity_xpath = "//tr[.//td[.//span[contains(text(),'Equity (Book Value)')]]]/td[2]"
            equity = parser.xpath(equity_xpath)[0]
            Equity_value = float(equity.attrib.get('title').replace(',', ''))
            return Equity_value

        except IndexError as ie:
            logger.error(f"Unable to locate Total Equity data on the page: {ie}")
            raise Exception("Unable to locate Total Equity data on the page.")
        except ValueError as ve:
            logger.error(f"Unable to convert Total Equity data to float: {ve}")
            raise Exception("Unable to convert Total Equity data to float.")
        except TypeError as te:
            logger.error(f"Total Equity data is not in the expected format: {te}")
            raise Exception("Total Equity data is not in the expected format.")
    except Exception as e:
        logger.error(f"An unexpected error in get_equity: {e}")
        raise Exception(f"An unexpected error occurred: {e}")

def get_staticvalue(ticker):
    try:
        url = "https://stockanalysis.com/quote/hose/{}/statistics/".format(ticker)
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, headers=stock_headers)

        if response.status_code != 200:
            logger.error(f"Failed to fetch data for {ticker}. HTTP Status Code: {response.status_code}")
            raise Exception(f"Failed to fetch data for {ticker}. HTTP Status Code: {response.status_code}")
        parser = html.fromstring(response.content)
        try:
            equity_xpath = "//tr[.//td[.//span[contains(text(),'Equity (Book Value)')]]]/td[2]"
            debt_xpath = "//tr[.//td[.//span[contains(text(),'Total Debt')]]]/td[2]"
            equity = parser.xpath(equity_xpath)[0]
            Equity_value = float(equity.attrib.get('title').replace(',', ''))
            debt = parser.xpath(debt_xpath)[0]
            Debt_value = float(debt.attrib.get('title').replace(',', ''))
            return Equity_value, Debt_value

        except IndexError as ie:
            logger.error(f"Unable to locate Total Equity data on the page: {ie}")
            raise Exception("Unable to locate Total Equity data on the page.")
        except ValueError as ve:
            logger.error(f"Unable to convert Total Equity data to float: {ve}")
            raise Exception("Unable to convert Total Equity data to float.")
        except TypeError as te:
            logger.error(f"Total Equity data is not in the expected format: {te}")
            raise Exception("Total Equity data is not in the expected format.")
    except Exception as e:
        logger.error(f"An unexpected error in get_staticvalue: {e}")
        raise Exception(f"An unexpected error occurred: {e}")

def calculate_wacc(E, D, Re, Rd, Tc):
    V = E + D
    wacc = (E/V) * Re + (D/V) * Rd * (1 - Tc)
    return wacc

if __name__ == "__main__":
    ticker = "FPT"
    try:
        last_fcf = get_free_cash_flow(ticker.upper())
        logger.info(f"Free Cash Flow for {ticker}: {last_fcf}")
    except Exception as e:
        logger.error(f"Error: {e}")
