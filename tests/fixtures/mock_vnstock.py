"""Mock responses for vnstock API."""

import pandas as pd
from unittest.mock import MagicMock


def create_mock_cash_flow_df():
    """Create mock cash flow DataFrame."""
    return pd.DataFrame([
        {
            'yearReport': 2025,
            'lengthReport': 4,
            'Net cash inflows/outflows from operating activities': 1500000000000,
            'Purchase of fixed assets': 150000000000,
        },
        {
            'yearReport': 2025,
            'lengthReport': 3,
            'Net cash inflows/outflows from operating activities': 1200000000000,
            'Purchase of fixed assets': 120000000000,
        },
        {
            'yearReport': 2025,
            'lengthReport': 2,
            'Net cash inflows/outflows from operating activities': 1100000000000,
            'Purchase of fixed assets': 110000000000,
        },
        {
            'yearReport': 2025,
            'lengthReport': 1,
            'Net cash inflows/outflows from operating activities': 1200000000000,
            'Purchase of fixed assets': 120000000000,
        },
    ])


def create_mock_balance_sheet_df():
    """Create mock balance sheet DataFrame."""
    return pd.DataFrame([
        {
            'yearReport': 2025,
            'lengthReport': 4,
            'Common shares (Bn. VND)': 17035071210000,
            'Paid-in capital (Bn. VND)': 17035071210000,
        },
    ])


def create_mock_income_statement_df():
    """Create mock income statement DataFrame."""
    return pd.DataFrame([
        {
            'yearReport': 2025,
            'lengthReport': 4,
            'Attributable to parent company': 8000000000000,
            'Net Profit For the Year': 8500000000000,
        },
    ])


def create_mock_price_board_df():
    """Create mock price board DataFrame."""
    df = pd.DataFrame([
        {
            'match_price': 92500,
        }
    ])
    # Create multi-level columns like vnstock returns
    df.columns = pd.MultiIndex.from_tuples([('match', 'match_price')])
    return df


def create_mock_ratio_df():
    """Create mock ratio summary DataFrame."""
    return pd.DataFrame([
        {
            'ev': 157574408692500,
            'pe': 15.5,
            'pb': 3.2,
        }
    ])


class MockVnstock:
    """Mock Vnstock class for testing."""
    
    def __init__(self, fail_count=0, fail_exception=TimeoutError):
        self.fail_count = fail_count
        self.fail_exception = fail_exception
        self.call_count = 0
    
    def stock(self, symbol, source="VCI"):
        self.call_count += 1
        
        if self.call_count <= self.fail_count:
            raise self.fail_exception(f"Mock failure {self.call_count}")
        
        return MockStockInstance(symbol)


class MockStockInstance:
    """Mock stock instance returned by Vnstock().stock()."""
    
    def __init__(self, symbol):
        self.symbol = symbol
        self.finance = MockFinance()
        self.trading = MockTrading()
        self.company = MockCompany()


class MockFinance:
    """Mock finance methods."""
    
    def cash_flow(self):
        return create_mock_cash_flow_df()
    
    def balance_sheet(self):
        return create_mock_balance_sheet_df()
    
    def income_statement(self):
        return create_mock_income_statement_df()


class MockTrading:
    """Mock trading methods."""
    
    def price_board(self, symbols):
        return create_mock_price_board_df()


class MockCompany:
    """Mock company methods."""
    
    def ratio_summary(self):
        return create_mock_ratio_df()

