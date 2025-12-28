"""
Module để scrape dữ liệu từ stockanalysis.com
Sử dụng cloudscraper để bypass anti-bot protection
"""
import requests
import cloudscraper
from lxml import html
import re
import json
import urllib3
from ..utils.logger import get_logger
from ..utils.cache_manager import get_cache_manager

logger = get_logger()
cache_manager = get_cache_manager()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

stock_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0',
    'Referer': 'https://stockanalysis.com/',
}


def parse_number(value_str):
    """
    Parse số từ string, xử lý format như "6,460,442" hoặc "6.46M"
    """
    if not value_str or value_str == '-':
        return None
    
    # Remove commas
    value_str = value_str.replace(',', '').strip()
    
    # Handle millions (M), billions (B), thousands (K)
    multiplier = 1
    if value_str.endswith('M'):
        multiplier = 1_000_000
        value_str = value_str[:-1]
    elif value_str.endswith('B'):
        multiplier = 1_000_000_000
        value_str = value_str[:-1]
    elif value_str.endswith('K'):
        multiplier = 1_000
        value_str = value_str[:-1]
    
    try:
        return float(value_str) * multiplier
    except ValueError:
        return None


def get_free_cash_flow_from_stockanalysis(ticker):
    """
    Lấy Free Cash Flow từ stockanalysis.com (TTM)
    
    Args:
        ticker: Mã cổ phiếu (ví dụ: 'FPT')
    
    Returns:
        float: Free Cash Flow (VND) hoặc None nếu không lấy được
    """
    # Check cache first
    cache_key = f"{ticker.upper()}_fcf_stockanalysis"
    if cache_manager.exists(ticker, cache_key):
        cached_value = cache_manager.get_with_timestamp(ticker, cache_key)
        logger.info(f"Using cached FCF from stockanalysis.com for {ticker}: {cached_value:,.0f} VND")
        return float(cached_value)
    
    url = f"https://stockanalysis.com/quote/hose/{ticker.upper()}/financials/cash-flow-statement/"
    
    try:
        logger.info(f"Fetching FCF from stockanalysis.com for {ticker}...")
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, headers=stock_headers, timeout=15)
        
        if response.status_code != 200:
            logger.warning(f"Failed to fetch from stockanalysis.com. Status: {response.status_code}")
            return None
        
        parser = html.fromstring(response.content)
        
        # Method 1: Tìm trong bảng financial
        # Tìm dòng có chứa "Free Cash Flow"
        fcf_xpaths = [
            "//tr[td//text()[contains(.,'Free Cash Flow')]]",
            "//tr[td//span[contains(text(),'Free Cash Flow')]]",
            "//table//tr[.//td[contains(text(),'Free Cash Flow')]]",
        ]
        
        fcf_value = None
        
        for xpath in fcf_xpaths:
            rows = parser.xpath(xpath)
            if rows:
                row = rows[0]
                # Lấy tất cả các cell trong dòng
                cells = row.xpath('.//td')
                
                # TTM thường là cột thứ 2 (sau header)
                if len(cells) >= 2:
                    # Thử lấy từ cell thứ 2 (TTM column)
                    ttm_cell = cells[1]
                    text = ttm_cell.text_content().strip()
                    
                    # Parse số
                    value = parse_number(text)
                    if value:
                        # Convert từ triệu VND sang VND
                        fcf_value = value * 1_000_000
                        logger.info(f"Found FCF TTM from stockanalysis.com for {ticker}: {fcf_value:,.0f} VND")
                        break
        
        # Method 2: Tìm trong JSON data nếu có
        if fcf_value is None:
            content = response.text
            # Tìm JSON data trong script tags
            json_patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                r'window\.__DATA__\s*=\s*({.+?});',
                r'"freeCashFlow":\s*([0-9,]+)',
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                if matches:
                    try:
                        if pattern.startswith('"freeCashFlow"'):
                            # Direct match
                            value = parse_number(matches[0])
                            if value:
                                fcf_value = value * 1_000_000
                                break
                        else:
                            # JSON object
                            json_str = matches[0]
                            data = json.loads(json_str)
                            # Tìm FCF trong data structure
                            # (cần điều chỉnh dựa trên cấu trúc thực tế)
                            if isinstance(data, dict):
                                # Thử các key có thể có
                                for key in ['freeCashFlow', 'fcf', 'cashFlow', 'financials']:
                                    if key in data:
                                        val = data[key]
                                        if isinstance(val, (int, float)):
                                            fcf_value = val * 1_000_000
                                            break
                                        elif isinstance(val, dict) and 'ttm' in val:
                                            fcf_value = val['ttm'] * 1_000_000
                                            break
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
        
        if fcf_value:
            cache_manager.set_with_timestamp(ticker, cache_key, fcf_value)
            logger.info(f"✓ FCF from stockanalysis.com for {ticker}: {fcf_value:,.0f} VND (TTM)")
            return float(fcf_value)
        else:
            logger.warning(f"Could not find FCF from stockanalysis.com for {ticker}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching FCF from stockanalysis.com for {ticker}: {e}")
        return None


def get_operating_cash_flow_from_stockanalysis(ticker):
    """
    Lấy Operating Cash Flow từ stockanalysis.com (TTM)
    """
    url = f"https://stockanalysis.com/quote/hose/{ticker.upper()}/financials/cash-flow-statement/"
    
    try:
        logger.info(f"Fetching OCF from stockanalysis.com for {ticker}...")
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, headers=stock_headers, timeout=15)
        
        if response.status_code != 200:
            return None
        
        parser = html.fromstring(response.content)
        
        # Tìm Operating Cash Flow
        ocf_xpaths = [
            "//tr[td//text()[contains(.,'Operating Cash Flow')]]",
            "//tr[td//text()[contains(.,'Operating cash flow')]]",
        ]
        
        for xpath in ocf_xpaths:
            rows = parser.xpath(xpath)
            if rows:
                row = rows[0]
                cells = row.xpath('.//td')
                if len(cells) >= 2:
                    ttm_cell = cells[1]
                    text = ttm_cell.text_content().strip()
                    value = parse_number(text)
                    if value:
                        ocf_value = value * 1_000_000
                        logger.info(f"Found OCF TTM from stockanalysis.com for {ticker}: {ocf_value:,.0f} VND")
                        return float(ocf_value)
        
        return None
        
    except Exception as e:
        logger.error(f"Error fetching OCF from stockanalysis.com for {ticker}: {e}")
        return None


def get_capex_from_stockanalysis(ticker):
    """
    Lấy Capital Expenditures từ stockanalysis.com (TTM)
    """
    url = f"https://stockanalysis.com/quote/hose/{ticker.upper()}/financials/cash-flow-statement/"
    
    try:
        logger.info(f"Fetching CapEx from stockanalysis.com for {ticker}...")
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, headers=stock_headers, timeout=15)
        
        if response.status_code != 200:
            return None
        
        parser = html.fromstring(response.content)
        
        # Tìm Capital Expenditures
        capex_xpaths = [
            "//tr[td//text()[contains(.,'Capital Expenditures')]]",
            "//tr[td//text()[contains(.,'Capital expenditures')]]",
        ]
        
        for xpath in capex_xpaths:
            rows = parser.xpath(xpath)
            if rows:
                row = rows[0]
                cells = row.xpath('.//td')
                if len(cells) >= 2:
                    ttm_cell = cells[1]
                    text = ttm_cell.text_content().strip()
                    # CapEx thường là số âm trong báo cáo, lấy absolute value
                    value = parse_number(text)
                    if value:
                        capex_value = abs(value) * 1_000_000
                        logger.info(f"Found CapEx TTM from stockanalysis.com for {ticker}: {capex_value:,.0f} VND")
                        return float(capex_value)
        
        return None
        
    except Exception as e:
        logger.error(f"Error fetching CapEx from stockanalysis.com for {ticker}: {e}")
        return None

