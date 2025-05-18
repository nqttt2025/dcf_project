import requests
from lxml import html
from pandas import json_normalize
import urllib3

stock_headers = {
        'Connection': 'keep-alive',
        'sec-ch-ua': '"Not A;Brand";v="99", "Chromium";v="98", "Google Chrome";v="98"',
        'DNT': '1',
        'sec-ch-ua-mobile': '?0',
        'X-Fiin-Key': 'KEY',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Fiin-User-ID': 'ID',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36',
        'X-Fiin-Seed': 'SEED',
        'sec-ch-ua-platform': 'Windows',
        'Origin': 'https://iboard.ssi.com.vn',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://iboard.ssi.com.vn/',
        'Accept-Language': 'en-US,en;q=0.9,vi-VN;q=0.8,vi;q=0.7'
        }

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

def get_free_cash_flow(ticker):
    url = f"https://stockanalysis.com/quote/hose/{ticker}/financials/cash-flow-statement/"
    response = requests.get(url, verify=False)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data for {ticker}. HTTP Status Code: {response.status_code}")
    parser = html.fromstring(response.content)
    try:
        # Extract Free Cash Flow values from the table
        fcfs_xpath = "//tr[.//td[.//span[.//div[text()='Free Cash Flow']]]]"
        fcfs = parser.xpath(fcfs_xpath)[0]
        for fcf in fcfs:
            if is_float(fcf.text_content().replace(',', '')):
                fcf_value = float(fcf.text_content().replace(',', ''))
                return fcf_value
        return 0
    except IndexError:
        raise Exception("Unable to locate Free Cash Flow data on the page.")

def get_shares_outstanding(ticker):
    
    url = f"https://stockanalysis.com/quote/hose/{ticker}/"
    response = requests.get(url, verify=False)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data for {ticker}. HTTP Status Code: {response.status_code}")
    parser = html.fromstring(response.content)
    try:
        shares_xpath = "//tr[.//td[text()='Shares Out']]/td[2]"
        shares = str(parser.xpath(shares_xpath)[0].text_content())
        factor = 1000000000 if 'B' in shares else 1 
        shares = float(shares.replace('B', '').replace('M', '')) * factor
        return shares
    except IndexError:
        raise Exception("Unable to locate Shares Outstanding data on the page.")

def get_earnings_per_share_Diluted(ticker):
    
    url = "https://stockanalysis.com/quote/hose/{}/financials/".format(ticker)
    response = requests.get(url, verify=False)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data for {ticker}. HTTP Status Code: {response.status_code}")
    parser = html.fromstring(response.content)
    try:
        eps_xpath = "//tr[.//td[.//span[.//div[text()='EPS (Diluted)']]]]"
        epss = parser.xpath(eps_xpath)[0]
        for eps in epss:
            if is_float(eps.text_content().replace(',', '')):
                eps_value = float(eps.text_content().replace(',', ''))
                return eps_value
        return 0
    except IndexError:
        raise Exception("Unable to locate EPS data on the page.")
    except ValueError:  
        raise Exception("Unable to convert EPS data to float.")
    except TypeError:   
        raise Exception("EPS data is not in the expected format.")
    except Exception as e:  
        raise Exception(f"An unexpected error occurred: {e}")

def price_board_stock(ticker):
    """
    This function returns the trading price board of a target stocks list.
    Args:
        ticker (:obj:`str`, required): STRING list of symbols separated by "," without any space. Ex: "TCB,SSI,BID"
    """
    data = requests.get(
        'https://apipubaws.tcbs.com.vn/stock-insight/v1/stock/second-tc-price?tickers={}'.format(ticker)).json()

    df = json_normalize(data['data'])
    # drop columns named seq
    print(df)
    df.drop(columns=['seq'], inplace=True)
    df = df[['t', 'cp', 'fv', 'mav', 'nstv', 'nstp', 'rsi', 'macdv', 'macdsignal',
             'tsignal', 'avgsignal', 'ma20', 'ma50', 'ma100', 'session', 'mw3d',
             'mw1m', 'mw3m', 'mw1y', 'rs3d', 'rs1m', 'rs3m', 'rs1y', 'rsavg', 'hp1m',
             'hp3m', 'hp1y', 'lp1m', 'lp3m', 'lp1y', 'hp1yp', 'lp1yp', 'pe', 'pb',
             'roe', 'oscore', 'av', 'bv', 'ev', 'hmp', 'mscore', 'delta1m',
             'delta1y', 'vnipe', 'vnipb', 'vnid3d', 'vnid1m', 'vnid3m', 'vnid1y']]

    # df = df.rename(columns={'t': 'Ticket', 'cp': 'Price', 'fv': 'KLBD/TB5D', 'mav': 'T.độ GD', 'nstv': 'KLGD ròng(CM)',
    #                         'nstp': '%KLGD ròng (CM)', 'rsi': 'RSI', 'macdv': 'MACD Hist', 'macdsignal': 'MACD Signal',
    #                         'tsignal': 'Tín hiệu KT', 'avgsignal': 'Tín hiệu TB động', 'ma20': 'MA20', 'ma50': 'MA50',
    #                         'ma100': 'MA100', 'session': 'Session +/- ', 'mscore': 'Đ.góp VNINDEX', 'pe': 'P/E', 'pb': 'P/B',
    #                         'roe': 'ROE', 'oscore': 'TCRating', 'ev': 'TCBS định giá', 'mw3d': '% thay đổi giá 3D',
    #                         'mw1m': '% thay đổi giá 1M', 'mw3m': '% thay đổi giá 3M', 'mw1y': '% thay đổi giá 1Y',
    #                         'rs3d': 'RS 3D', 'rs1m': 'RS 1M', 'rs3m': 'RS 3M', 'rs1y': 'RS 1Y', 'rsavg': 'RS TB',
    #                         'hp1m': 'Đỉnh 1M', 'hp3m': 'Đỉnh 3M', 'hp1y': 'Đỉnh 1Y', 'lp1m': 'Đáy 1M', 'lp3m': 'Đáy 3M',
    #                         'lp1y': 'Đáy 1Y', 'hp1yp': '%Đỉnh 1Y', 'lp1yp': 'Low-Price-1Y', 'delta1m': 'Price-VNI-1M',
    #                         'delta1y': 'Price-VNI-1Y', 'bv': 'Khối lượng Dư mua', 'av': 'Khối lượng Dư bán',
    #                         'hmp': 'Khớp nhiều nhất', 'vnipe': 'VNINDEX P/E', 'vnipb': 'VNINDEX P/B'})

    # df = df.rename(columns={'t': 'Mã CP', 'cp': 'Giá', 'fv': 'KLBD/TB5D', 'mav': 'T.độ GD', 'nstv': 'KLGD ròng(CM)',
    #                         'nstp': '%KLGD ròng (CM)', 'rsi': 'RSI', 'macdv': 'MACD Hist', 'macdsignal': 'MACD Signal',
    #                         'tsignal': 'Tín hiệu KT', 'avgsignal': 'Tín hiệu TB động', 'ma20': 'MA20', 'ma50': 'MA50',
    #                         'ma100': 'MA100', 'session': 'Phiên +/- ', 'mscore': 'Đ.góp VNINDEX', 'pe': 'P/E', 'pb': 'P/B',
    #                         'roe': 'ROE', 'oscore': 'TCRating', 'ev': 'TCBS định giá', 'mw3d': '% thay đổi giá 3D',
    #                         'mw1m': '% thay đổi giá 1M', 'mw3m': '% thay đổi giá 3M', 'mw1y': '% thay đổi giá 1Y',
    #                         'rs3d': 'RS 3D', 'rs1m': 'RS 1M', 'rs3m': 'RS 3M', 'rs1y': 'RS 1Y', 'rsavg': 'RS TB',
    #                         'hp1m': 'Đỉnh 1M', 'hp3m': 'Đỉnh 3M', 'hp1y': 'Đỉnh 1Y', 'lp1m': 'Đáy 1M', 'lp3m': 'Đáy 3M',
    #                         'lp1y': 'Đáy 1Y', 'hp1yp': '%Đỉnh 1Y', 'lp1yp': '%Đáy 1Y', 'delta1m': '%Giá - %VNI (1M)',
    #                         'delta1y': '%Giá - %VNI (1Y)', 'bv': 'Khối lượng Dư mua', 'av': 'Khối lượng Dư bán',
    #                         'hmp': 'Khớp nhiều nhất', 'vnipe': 'VNINDEX P/E', 'vnipb': 'VNINDEX P/B'})
    # return 118000.0
    print(df.cp.values[0])
    return float(df.cp.values[0])



def get_market_cap(ticker):
    """_summary_

    Args:
        ticker (_type_): _description_

    Raises:
        Exception: _description_
        Exception: _description_
        Exception: _description_
        Exception: _description_
        Exception: _description_

    Returns:
        _type_: _description_
    """    
    url="https://stockanalysis.com/quote/hose/{}/market-cap/".format(ticker)
    response = requests.get(url, verify=False)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data for {ticker}. HTTP Status Code: {response.status_code}")
    parser = html.fromstring(response.content)
    try:
        price_xpath = "//div[contains(text(),'Stock Price')]/div"
        price = float(parser.xpath(price_xpath)[0].text_content().replace(',', ''))        
        market_cap_xpath = "//div[contains(text(),'Market Cap')]/div"
        market_cap = str(parser.xpath(market_cap_xpath)[0].text_content().replace(',', ''))
        factor_mapping = {
            'T': 1000000000000,
            'B': 1000000000,
            'M': 1000000,
            'K': 1000
        }
        # Determine the factor based on the suffix
        # 'T' for trillion, 'B' for billion, 'M' for million, 'K' for thousand
        # Default factor is 1 (no suffix)
        # Check if the market_cap string contains any of the suffixes
        factor = 1
        if 'T' in market_cap:
            factor = factor_mapping['T']
        elif 'B' in market_cap:
            factor = factor_mapping['B']
        elif 'M' in market_cap:
            factor = factor_mapping['M']
        elif 'K' in market_cap:
            factor = factor_mapping['K']

        market_cap = float(market_cap.replace('B', '').replace('M', '').replace('K', '').replace('T', '')) * factor
        return market_cap, price

    except IndexError:
        raise Exception("Unable to locate Market Cap data on the page.")
    except ValueError:
        raise Exception("Unable to convert Market Cap data to float.")
    except TypeError:
        raise Exception("Market Cap data is not in the expected format.")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")

def get_equity(ticker):
    """
    This function returns the equity of a target stocks list.
    Args:
        ticker (:obj:`str`, required): STRING list of symbols separated by "," without any space. Ex: "TCB,SSI,BID"
    """
    url = "https://stockanalysis.com/quote/hose/{}/statistics/".format(ticker)
    response = requests.get(url, verify=False)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch data for {ticker}. HTTP Status Code: {response.status_code}")
    parser = html.fromstring(response.content)
    try:
        equity_xpath = "//tr[.//td[.//span[contains(text(),'Equity (Book Value)')]]]/td[2]"
        equity = parser.xpath(equity_xpath)[0]
        Equity_value = float(equity.attrib.get('title').replace(',', ''))
        return Equity_value

    except IndexError:
        raise Exception("Unable to locate Total Equity data on the page.")
    except ValueError:
        raise Exception("Unable to convert Total Equity data to float.")
    except TypeError:
        raise Exception("Total Equity data is not in the expected format.")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")

def get_staticvalue(ticker):
    """
    This function returns the static of a target stocks list.
    Args:
        ticker (:obj:`str`, required): STRING list of symbols separated by "," without any space. Ex: "TCB,SSI,BID"
    """
    url = "https://stockanalysis.com/quote/hose/{}/statistics/".format(ticker)
    response = requests.get(url, verify=False)

    if response.status_code != 200:
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

    except IndexError:
        raise Exception("Unable to locate Total Equity data on the page.")
    except ValueError:
        raise Exception("Unable to convert Total Equity data to float.")
    except TypeError:
        raise Exception("Total Equity data is not in the expected format.")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")

def calculate_wacc(E, D, Re, Rd, Tc):
    """
    E: Giá trị vốn chủ sở hữu (Equity)
    D: Giá trị nợ (Debt)
    Re: Chi phí vốn chủ sở hữu (Cost of Equity, %)
    Rd: Chi phí nợ (Cost of Debt, %)
    Tc: Thuế suất thu nhập doanh nghiệp (%)
    """
    V = E + D
    wacc = (E/V) * Re + (D/V) * Rd * (1 - Tc)
    return wacc

# Ví dụ số liệu cho FPT (bạn cần cập nhật số liệu thực tế)
# E = 7.5e12   # Vốn hóa thị trường (VND)
# D = 3.0e12   # Tổng nợ vay (VND)
# Re = 0.15    # Chi phí vốn chủ sở hữu (15%)
# Rd = 0.08    # Chi phí nợ (8%)
# Tc = 0.20    # Thuế suất thu nhập doanh nghiệp (20%)

# wacc = calculate_wacc(E, D, Re, Rd, Tc)
# print(f"WACC của FPT: {wacc*100:.2f}%")

if __name__ == "__main__":
    ticker = "FPT"
    try:
        market_cap = get_equity(ticker)
        print(f"Market cap for {ticker}: {market_cap}")
    except Exception as e:
        print(f"Error: {e}")