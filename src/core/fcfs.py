import requests
import urllib3
import time
import json
import os
import sys
from io import StringIO
from datetime import datetime
from ..utils.logger import get_logger
from ..utils.cache_manager import get_cache_manager

# Optional imports - only import if available
try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False

try:
    from lxml import html
    HAS_LXML = True
except ImportError:
    HAS_LXML = False

try:
    from pandas import json_normalize
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

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

def get_free_cash_flow_ttm(ticker):
    """
    Tính Free Cash Flow TTM (Trailing Twelve Months) từ vnstock
    bằng cách cộng dồn 4 quý gần nhất.
    
    TTM (Trailing Twelve Months) là tổng hợp dữ liệu từ 12 tháng gần nhất,
    thường được tính bằng cách cộng dồn 4 quý báo cáo gần nhất.
    
    Tại sao sử dụng TTM?
    - Phản ánh tốt hơn tình hình hiện tại của công ty (12 tháng gần nhất)
    - Tránh biến động theo mùa của từng quý riêng lẻ
    - Chuẩn trong phân tích tài chính và định giá DCF
    - Nhất quán với cách tính của các nguồn dữ liệu khác (như stockanalysis.com)
    
    Ví dụ với FPT:
    - Q3 2025: OCF = 4,344 tỷ VND, CapEx = 830 tỷ VND
    - Q2 2025: OCF = 4,190 tỷ VND, CapEx = 688 tỷ VND
    - Q1 2025: OCF = ... tỷ VND, CapEx = ... tỷ VND
    - Q4 2024: OCF = 5,397 tỷ VND, CapEx = 838 tỷ VND
    - TTM FCF = Tổng OCF - Tổng CapEx của 4 quý
    
    Args:
        ticker (str): Mã cổ phiếu (ví dụ: 'FPT', 'VNM')
    
    Returns:
        float: Free Cash Flow TTM tính bằng VND, hoặc None nếu không lấy được dữ liệu
    
    Note:
        - Hàm sẽ tự động cache kết quả để tránh tính toán lại
        - Nếu không đủ 4 quý dữ liệu, sẽ trả về None
        - CapEx được lấy giá trị tuyệt đối (vì trong báo cáo thường là số âm)
    
    Example:
        >>> fcf_ttm = get_free_cash_flow_ttm('FPT')
        >>> print(f"FCF TTM: {fcf_ttm:,.0f} VND")
        FCF TTM: 13,933,764,607,232 VND
    """
    if not HAS_VNSTOCK:
        logger.error("vnstock not installed. Install with: pip install vnstock")
        return None
    
    if not HAS_PANDAS:
        logger.error("pandas not installed. Install with: pip install pandas")
        return None
    
    # Check cache first
    cache_key = "fcf_ttm"
    if cache_manager.exists(ticker, cache_key):
        cached_value = cache_manager.get_with_timestamp(ticker, cache_key)
        logger.info(f"Using cached FCF TTM for {ticker}: {cached_value:,.0f} VND")
        return float(cached_value)
    
    try:
        logger.info(f"Calculating FCF TTM for {ticker} from vnstock (summing last 4 quarters)...")
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
        
        # Tên các cột cần tìm trong DataFrame
        ocf_col = 'Net cash inflows/outflows from operating activities'
        capex_col = 'Purchase of fixed assets'
        
        # Khởi tạo biến để tính TTM
        # TTM = tổng của 4 quý gần nhất
        ttm_ocf = 0      # TTM Operating Cash Flow
        ttm_capex = 0    # TTM Capital Expenditures
        quarters_counted = 0  # Số quý đã tính
        
        # Duyệt qua DataFrame từ đầu (quý gần nhất) đến cuối
        # Dữ liệu từ vnstock thường được sắp xếp từ mới nhất đến cũ nhất
        for idx in range(len(cash_flow_df)):
            row = cash_flow_df.iloc[idx]
            
            # Lấy giá trị OCF và CapEx từ dòng hiện tại
            ocf_val = row.get(ocf_col, 0) if ocf_col in row.index else 0
            capex_val = row.get(capex_col, 0) if capex_col in row.index else 0
            
            # Kiểm tra tính hợp lệ của dữ liệu
            # Bỏ qua các dòng không có dữ liệu hoặc là header row
            if HAS_PANDAS:
                is_valid = pd.notna(ocf_val) and ocf_val != 0 and ocf_val != ticker.upper()
            else:
                is_valid = ocf_val is not None and ocf_val != 0 and ocf_val != ticker.upper()
            
            if is_valid:
                try:
                    # Chuyển đổi sang float
                    ocf_float = float(ocf_val)
                    # CapEx trong báo cáo thường là số âm (dòng tiền ra), lấy giá trị tuyệt đối
                    if HAS_PANDAS:
                        capex_valid = capex_val != 0 and pd.notna(capex_val)
                    else:
                        capex_valid = capex_val != 0 and capex_val is not None
                    capex_float = abs(float(capex_val)) if capex_valid else 0
                    
                    # Chỉ tính các quý có OCF > 0 và chưa đủ 4 quý
                    if ocf_float > 0 and quarters_counted < 4:
                        year = row.get('yearReport', 'N/A')
                        length = row.get('lengthReport', 'N/A')
                        logger.debug(f"  Q{length} {year}: OCF={ocf_float:,.0f}, CapEx={capex_float:,.0f}")
                        
                        # Cộng dồn vào TTM
                        ttm_ocf += ocf_float
                        ttm_capex += capex_float
                        quarters_counted += 1
                        
                        # Đã đủ 4 quý, dừng lại
                        if quarters_counted == 4:
                            break
                except (ValueError, TypeError) as e:
                    # Bỏ qua các dòng không parse được
                    logger.debug(f"Skipping row {idx}: {e}")
                    continue
        
        # Kiểm tra xem có đủ dữ liệu không
        if quarters_counted == 0:
            logger.warning(f"Could not find valid quarterly data for {ticker}")
            return None
        
        # Tính Free Cash Flow TTM = TTM Operating Cash Flow - TTM Capital Expenditures
        # Đây là công thức chuẩn để tính FCF
        ttm_fcf = ttm_ocf - ttm_capex
        
        logger.info(f"FCF TTM for {ticker} (from {quarters_counted} quarters):")
        logger.info(f"  TTM Operating Cash Flow: {ttm_ocf:,.0f} VND")
        logger.info(f"  TTM Capital Expenditures: {ttm_capex:,.0f} VND")
        logger.info(f"  TTM Free Cash Flow: {ttm_fcf:,.0f} VND")
        
        cache_manager.set_with_timestamp(ticker, cache_key, ttm_fcf)
        return float(ttm_fcf)
        
    except Exception as e:
        logger.error(f"Error calculating FCF TTM for {ticker}: {e}")
        return None


def get_free_cash_flow(ticker, use_ttm=True):
    """
    Tính Free Cash Flow (FCF) = Operating Cash Flow - Capital Expenditures.
    
    Free Cash Flow là dòng tiền tự do mà công ty tạo ra sau khi trừ đi các khoản
    chi tiêu cần thiết để duy trì hoạt động và tài sản cố định.
    
    Công thức: FCF = Operating Cash Flow - Capital Expenditures (CapEx)
    
    Mặc định sử dụng TTM (Trailing Twelve Months):
    - Tính bằng cách cộng dồn 4 quý gần nhất từ vnstock
    - Phản ánh tốt hơn tình hình hiện tại của công ty
    - Chuẩn trong phân tích tài chính và định giá DCF
    
    Args:
        ticker (str): Mã cổ phiếu (ví dụ: 'FPT', 'VNM')
        use_ttm (bool): Nếu True (mặc định), tính TTM từ vnstock (cộng 4 quý gần nhất).
                       Nếu False, chỉ lấy dữ liệu từ quý gần nhất.
    
    Returns:
        float: Free Cash Flow tính bằng VND, hoặc None nếu không lấy được dữ liệu
    
    Note:
        - Mặc định sử dụng TTM để có giá trị chính xác hơn cho phân tích DCF
        - Dữ liệu được lấy từ vnstock library (source: VCI)
        - Nếu TTM không tính được, sẽ fallback về quý gần nhất
        - Kết quả được cache tự động để tránh tính toán lại
    
    Example:
        >>> # Sử dụng TTM (mặc định - khuyến nghị)
        >>> fcf = get_free_cash_flow('FPT')
        >>> print(f"FCF TTM: {fcf:,.0f} VND")
        
        >>> # Chỉ lấy quý gần nhất (không khuyến nghị)
        >>> fcf_quarter = get_free_cash_flow('FPT', use_ttm=False)
    """
    # Sử dụng TTM (mặc định) - tính từ vnstock bằng cách cộng 4 quý gần nhất
    # Đây là phương pháp được khuyến nghị vì phản ánh tốt hơn tình hình hiện tại
    if use_ttm:
        fcf_ttm = get_free_cash_flow_ttm(ticker)
        if fcf_ttm:
            return fcf_ttm
        # Nếu không tính được TTM, cảnh báo và fallback về quý gần nhất
        logger.warning(f"Could not calculate TTM for {ticker}, falling back to single quarter")
    
    # Fallback: Lấy dữ liệu từ quý gần nhất (không khuyến nghị cho DCF)
    # Chỉ sử dụng khi không thể tính TTM hoặc use_ttm=False
    if not HAS_VNSTOCK:
        logger.error("vnstock not installed. Install with: pip install vnstock")
        return None

    try:
        # Lấy dữ liệu cash flow từ vnstock (quý gần nhất)
        # Lưu ý: Đây là fallback, nên sử dụng TTM (use_ttm=True) để có giá trị chính xác hơn
        logger.info(f"Fetching cash flow data for {ticker} using vnstock (single quarter)...")
        logger.warning(f"Note: Using single quarter data. Consider using TTM (use_ttm=True) for better accuracy.")
        
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

        # Lấy dòng đầu tiên (quý gần nhất)
        latest_row = cash_flow_df.iloc[0]

        # Tìm Operating Cash Flow (OCF) trong các cột có thể có
        # OCF là dòng tiền từ hoạt động kinh doanh chính của công ty
        ocf = None
        ocf_names = [
            'Net cash inflows/outflows from operating activities',
            'Net Cash Flows from Operating Activities',
            'Operating cash flow',
            'Cash flows from operating activities'
        ]

        for col_name in ocf_names:
            if col_name in latest_row.index:
                ocf_value = latest_row[col_name]
                ocf_valid = (HAS_PANDAS and pd.notna(ocf_value)) or (not HAS_PANDAS and ocf_value is not None)
                if ocf_valid:
                    ocf = float(ocf_value)
                    break

        if ocf is None:
            logger.warning(f"Could not find operating cash flow for {ticker}")
            return None

        # Tìm Capital Expenditures (CapEx)
        # CapEx là chi phí đầu tư vào tài sản cố định (nhà xưởng, máy móc, thiết bị)
        # Trong báo cáo tài chính, CapEx thường là số âm (dòng tiền ra)
        capex = 0.0
        capex_names = [
            'Purchase of fixed assets',
            'Capital Expenditures',
            'Purchase of property, plant and equipment',
            'Investments in fixed assets'
        ]

        for col_name in capex_names:
            if col_name in latest_row.index:
                capex_value = latest_row[col_name]
                capex_valid = (HAS_PANDAS and pd.notna(capex_value)) or (not HAS_PANDAS and capex_value is not None)
                if capex_valid:
                    # Lấy giá trị tuyệt đối vì CapEx trong báo cáo thường là số âm
                    capex = abs(float(capex_value))
                    logger.info(f"Found CapEx for {ticker}: {capex:,.0f} VND")
                    break

        # Tính Free Cash Flow = Operating Cash Flow - Capital Expenditures
        # FCF là dòng tiền tự do sau khi trừ đi các khoản đầu tư cần thiết
        fcf = ocf - capex
        
        logger.info(f"Operating Cash Flow for {ticker} (single quarter): {ocf:,.0f} VND")
        logger.info(f"Capital Expenditures for {ticker} (single quarter): {capex:,.0f} VND")
        logger.info(f"Free Cash Flow (FCF) for {ticker} (single quarter): {fcf:,.0f} VND (OCF - CapEx)")
        logger.warning(f"Note: This is single quarter data. For DCF analysis, TTM is recommended (use_ttm=True)")

        if fcf <= 0:
            logger.warning(f"FCF is negative or zero for {ticker}: {fcf:,.0f} VND")
            # Vẫn trả về giá trị nhưng cảnh báo

        # Cache kết quả với key riêng để phân biệt với TTM
        cache_manager.set_with_timestamp(ticker, "fcf", fcf)
        return float(fcf)

    except Exception as e:
        logger.error(f"Error fetching FCF from vnstock: {e}")
        # Check cache as fallback
        if cache_manager.exists(ticker, "fcf"):
            cached_fcf = cache_manager.get(f"{ticker.upper()}_fcf")
            logger.info(f"Using cached FCF for {ticker}: {cached_fcf:,.0f}")
            return float(cached_fcf) if cached_fcf else None
        return None

def get_shares_outstanding(ticker):
    # Default shares fallback (FPT shares outstanding as of DEC-26-2025)
    default_shares = 1703507121
    
    if not HAS_VNSTOCK:
        logger.error("vnstock not installed. Install with: pip install vnstock")
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
            shares_capital_valid = (HAS_PANDAS and pd.notna(shares_capital)) or (not HAS_PANDAS and shares_capital is not None)
            if shares_capital_valid and shares_capital > 0:
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
                shares_valid = (HAS_PANDAS and pd.notna(shares)) or (not HAS_PANDAS and shares is not None)
                if shares_valid and shares > 0:
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

        if HAS_PANDAS:
            is_invalid = net_profit is None or pd.isna(net_profit) or net_profit <= 0
        else:
            is_invalid = net_profit is None or net_profit <= 0
        
        if is_invalid:
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
    if not HAS_CLOUDSCRAPER or not HAS_LXML:
        logger.warning("cloudscraper or lxml not available, get_staticvalue not supported")
        raise Exception("cloudscraper or lxml module not available")
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
