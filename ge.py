import requests
from lxml import html

def get_growth_estimate(ticker):    
    return "16"
    url = "https://valueinvesting.io/{}/estimates".format(ticker)
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data for {ticker}. HTTP Status Code: {response.status_code}")
    
    parser = html.fromstring(response.content)
    
    try:
        # Locate the "Next 5 Years (per annum)" growth estimate
        rows = parser.xpath('//table//tbody//tr')
        for row in rows:
            label = row.xpath("td/span/text()")
            if label and 'Next 5 Years' in label[0]:
                growth_estimate = row.xpath("td/text()")[0].replace('%', '').strip()
                return float(growth_estimate)
    except Exception as e:
        raise Exception(f"Error parsing growth estimate: {e}")
    
    return None

if __name__ == "__main__":
    ticker = "FPT.VN"
    try:
        ge = get_growth_estimate(ticker)
        print(f"Growth Estimate for {ticker}: {ge}%")
    except Exception as e:
        print(f"Error: {e}")