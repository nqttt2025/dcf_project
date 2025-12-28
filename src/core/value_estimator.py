from lxml import html
import requests
import json
import argparse
from collections import OrderedDict
from fcfs import get_free_cash_flow, get_shares_outstanding, get_earnings_per_share_Diluted, price_board_stock, get_market_cap
from ge import get_growth_estimate
from cache_manager import get_cache_manager
from logger import get_logger
import warnings
warnings.filterwarnings('ignore')

logger = get_logger()
# //tr[.//td[.//span[.//div[text()='Free Cash Flow']]]]
# "//tr[.//td[.//span[.//div[text()='Free Cash Flow']]]]"

fcfs_xpath = "//tr[.//td[.//span[.//div[text()='Free Cash Flow']]]]"

def parse(ticker):
    # url = "https://stockanalysis.com/stocks/{}/financials/cash-flow-statement".format(ticker)
    # url = "https://stockanalysis.com/quote/hose/{}/financials/cash-flow-statement".format(ticker)
    # response = requests.get(url, verify=False)
    # print(response)
    # parser = html.fromstring(response.content)
    # print(parser)
    # fcfs = parser.xpath('//table[contains(@id,"financial-table")]//tr[td/span/text()[contains(., "Free Cash Flow")]]')[0].xpath('.//td/span/text()')[1:]
    last_fcf = get_free_cash_flow(ticker.upper())

    # response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'})
    # parser = html.fromstring(response.content)
    # ge = parser.xpath('//table//tbody//tr')

    # for row in ge:
    #     label = row.xpath("td/span/text()")[0]
    #     if 'Next 5 Years' in label:
    #         try:
    #             ge = float(row.xpath("td/text()")[0].replace('%', ''))
    #         except:
    #             ge = []
    #         break
    ge = get_growth_estimate(ticker.upper())

    shares = get_shares_outstanding(ticker.upper())

    eps = get_earnings_per_share_Diluted(ticker.upper())
    market_price = price_board_stock(ticker.upper())

    # Fetch market cap to cache it
    market_cap, _ = get_market_cap(ticker.upper())

    return {'fcf': last_fcf, 'ge': ge, 'yr': 5, 'dr': 10, 'pr': 2.5, 'shares': shares, 'eps': eps, 'mp': market_price}

def dcf(data):
    forecast = [data['fcf']]

    if data['ge'] == []:
        raise ValueError("No growth rate available from Yahoo Finance")

    for _ in range(1, data['yr']):
        forecast.append(round(forecast[-1] + (data['ge'] / 100) * forecast[-1], 2))

    forecast.append(round(forecast[-1] * (1 + (data['pr'] / 100)) / (data['dr'] / 100 - data['pr'] / 100), 2)) #terminal value
    discount_factors = [1 / (1 + (data['dr'] / 100))**(i + 1) for i in range(len(forecast) - 1)]

    pvs = [round(f * d, 2) for f, d in zip(forecast[:-1], discount_factors)]
    pvs.append(round(discount_factors[-1] * forecast[-1], 2)) # discounted terminal value

    logger.info("Forecasted cash flows: {}".format(", ".join(map(str, forecast))))
    logger.info("PV of cash flows: {}".format(", ".join(map(str, pvs))))

    dcf = sum(pvs)
    logger.info("Fair value: {}".format(dcf / data['shares']))

def reverse_dcf(data):
    pass

def graham(data):
    if data['eps'] > 0:
        expected_value = data['eps'] * (8.5 + 2 * (data['ge']))
        ge_priced_in = (data['mp'] / data['eps'] - 8.5) / 2

        logger.info("Expected value based on growth rate: {}".format(expected_value))
        logger.info("Growth rate priced in for next 7-10 years: {}".format(ge_priced_in))
    else:
        logger.warning("Not applicable since EPS is negative.")

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    # argparser.add_argument('ticker', help='Ticker to analyse. Example: GOOG')
    # argparser.add_argument('--discount_rate', help='Discount rate in %. Default: 10', default=10)
    # argparser.add_argument('--growth_estimate', help='Estimated yoy growth rate. Default: Fetched from Yahoo Finance')
    # argparser.add_argument('--terminal_rate', help='Terminal growth rate. Default: 2.5')
    # argparser.add_argument('--period', help='Time period in years. Default: 5')
    # args = argparser.parse_args()

    # ticker = args.ticker
    ticker = "fpt"

    logger.info("Fetching data for %s..." % (ticker))
    data = parse("fpt")
    logger.info("=" * 80)
    logger.info("DCF model (basic)")
    logger.info("=" * 80)

    # if args.period is not None:
    #     data['yr'] = int(args.period)
    # if args.growth_estimate is not None:
    #     data['ge'] = float(args.growth_estimate)
    # if args.discount_rate is not None:
    #     data['dr'] = float(args.discount_rate)
    # if args.terminal_rate is not None:
    #     data['pr'] = float(args.terminal_rate)

    logger.info("Market price: {}".format(data['mp']))
    logger.info("EPS: {}".format(data['eps']))
    logger.info("Growth estimate: {}".format(data['ge']))
    logger.info("Term: {} years".format(data['yr']))
    logger.info("Discount Rate: {}%".format(data['dr']))
    logger.info("Perpetual Rate: {}%".format(data['pr']))

    dcf(data)

    logger.info("=" * 80)
    logger.info("Graham style valuation basic (Page 295, The Intelligent Investor)")
    logger.info("=" * 80)

    graham(data)

    # Save cache to file at the end
    cache_manager = get_cache_manager()
    cache_manager.save_to_file()