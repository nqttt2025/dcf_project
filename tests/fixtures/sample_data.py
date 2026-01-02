"""Sample data for testing."""


# Sample financial data for FPT
SAMPLE_FPT_DATA = {
    'ticker': 'FPT',
    'fcf': 5000000000000,  # 5 trillion VND TTM FCF
    'ge': 15.0,  # 15% growth estimate
    'shares': 1703507121,  # ~1.7 billion shares
    'eps': 4696.5,  # EPS in VND
    'price': 92500,  # Current price in VND
    'market_cap': 157574408692500,  # Market cap in VND
    'industry_pe': 15.0,
}


# Sample DCF parameters
SAMPLE_DCF_PARAMS = {
    'yr': 5,  # 5 years projection
    'dr': 10.0,  # 10% discount rate
    'pr': 2.5,  # 2.5% perpetual growth rate
}


# Sample Graham parameters
SAMPLE_GRAHAM_PARAMS = {
    'base_pe': 8.5,
    'growth_multiplier': 2.0,
}


# Expected DCF calculation results (pre-calculated)
EXPECTED_DCF_RESULT = {
    'dcf_fair_value': 85000.0,  # Approximate
    'graham_fair_value': 92000.0,  # Approximate
    'average_fair_value': 88500.0,  # Approximate
}


# Multiple ticker samples for testing
SAMPLE_TICKERS = {
    'FPT': SAMPLE_FPT_DATA,
    'VNM': {
        'ticker': 'VNM',
        'fcf': 8000000000000,
        'ge': 8.0,
        'shares': 2089956680,
        'eps': 3800,
        'price': 78000,
        'market_cap': 163016621040000,
        'industry_pe': 18.0,
    },
    'VIC': {
        'ticker': 'VIC',
        'fcf': -2000000000000,  # Negative FCF
        'ge': 12.0,
        'shares': 3891067094,
        'eps': 1200,
        'price': 42000,
        'market_cap': 163424817948000,
        'industry_pe': 25.0,
    },
}


# Config file content templates
CONFIG_TEMPLATE = """
[ticker]
ticker = {ticker}

[dcf]
yr = {yr}
dr = {dr}
pr = {pr}

[graham]
base_pe = {base_pe}
growth_multiplier = {growth_multiplier}

[report]
language = vi
"""


def get_sample_config(ticker='FPT', **kwargs):
    """Generate sample config content."""
    params = {
        'ticker': ticker,
        'yr': 5,
        'dr': 10.0,
        'pr': 2.5,
        'base_pe': 8.5,
        'growth_multiplier': 2.0,
        **kwargs
    }
    return CONFIG_TEMPLATE.format(**params)

