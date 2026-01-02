"""
Shared pytest fixtures for all tests.

This module provides common fixtures used across unit, integration, and e2e tests.
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, no external deps)")
    config.addinivalue_line("markers", "integration: Integration tests (requires Docker)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (slow)")
    config.addinivalue_line("markers", "slow: Slow running tests")


# ============================================================================
# Event Loop Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Mock Fixtures - VNStock
# ============================================================================

@pytest.fixture
def mock_vnstock():
    """Mock vnstock library responses."""
    with patch("src.core.fcfs.Vnstock") as mock:
        stock_instance = MagicMock()
        mock.return_value.stock.return_value = stock_instance
        
        # Mock finance methods
        stock_instance.finance.cash_flow.return_value = MagicMock(
            empty=False,
            iloc=[{
                'Net cash inflows/outflows from operating activities': 5000000000000,
                'Purchase of fixed assets': 500000000000,
                'yearReport': 2025,
                'lengthReport': 4,
            }]
        )
        
        stock_instance.finance.balance_sheet.return_value = MagicMock(
            empty=False,
            iloc=[{
                'Common shares (Bn. VND)': 17035071210000,
            }]
        )
        
        stock_instance.finance.income_statement.return_value = MagicMock(
            empty=False,
            iloc=[{
                'Attributable to parent company': 8000000000000,
            }]
        )
        
        # Mock trading methods
        stock_instance.trading.price_board.return_value = MagicMock(
            empty=False,
            iloc=[{('match', 'match_price'): 92500}]
        )
        
        yield mock


@pytest.fixture
def mock_vnstock_timeout():
    """Mock vnstock that always times out."""
    with patch("src.core.fcfs.Vnstock") as mock:
        mock.return_value.stock.side_effect = TimeoutError("API timeout")
        yield mock


@pytest.fixture
def mock_vnstock_intermittent():
    """Mock vnstock that fails twice then succeeds."""
    call_count = 0
    
    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise TimeoutError(f"API timeout (attempt {call_count})")
        return MagicMock()
    
    with patch("src.core.fcfs.Vnstock") as mock:
        mock.return_value.stock.side_effect = side_effect
        yield mock, lambda: call_count


# ============================================================================
# Mock Fixtures - Redis
# ============================================================================

@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch("src.utils.redis_client.get_redis_client") as mock:
        redis_instance = MagicMock()
        mock.return_value = redis_instance
        
        # Setup basic operations
        cache_data = {}
        
        def mock_get(key):
            return cache_data.get(key)
        
        def mock_set(key, value, ex=None):
            cache_data[key] = value
            return True
        
        def mock_delete(key):
            if key in cache_data:
                del cache_data[key]
                return 1
            return 0
        
        redis_instance.get.side_effect = mock_get
        redis_instance.set.side_effect = mock_set
        redis_instance.delete.side_effect = mock_delete
        redis_instance._cache_data = cache_data  # Expose for inspection
        
        yield redis_instance


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_financial_data():
    """Sample financial data for testing."""
    return {
        'ticker': 'FPT',
        'fcf': 5000000000000,  # 5 trillion VND
        'ge': 15.0,  # 15% growth
        'shares': 1703507121,
        'eps': 4696.5,
        'price': 92500,
        'market_cap': 157574408692500,
        'industry_pe': 15.0,
    }


@pytest.fixture
def sample_dcf_result(sample_financial_data):
    """Sample DCF calculation result."""
    return {
        'ticker': 'FPT',
        'dcf_fair_value': 85000.0,
        'graham_fair_value': 92000.0,
        'average_fair_value': 88500.0,
        'price': sample_financial_data['price'],
        'upside': -4.3,  # Current price above fair value
    }


@pytest.fixture
def sample_config_content():
    """Sample config file content."""
    return """
[ticker]
ticker = FPT

[dcf]
yr = 5
dr = 10.0
pr = 2.5

[graham]
base_pe = 8.5
growth_multiplier = 2.0

[report]
language = vi
"""


# ============================================================================
# Temporary Files Fixtures
# ============================================================================

@pytest.fixture
def temp_config_file(tmp_path, sample_config_content):
    """Create a temporary config file for testing."""
    config_file = tmp_path / "TEST.cfg"
    config_file.write_text(sample_config_content)
    return config_file


# ============================================================================
# Retry Testing Fixtures
# ============================================================================

@pytest.fixture
def reset_retry_stats():
    """Reset retry statistics before and after test."""
    from src.utils.retry import reset_retry_stats
    reset_retry_stats()
    yield
    reset_retry_stats()


# ============================================================================
# Environment Fixtures
# ============================================================================

@pytest.fixture
def clean_env():
    """Provide a clean environment for testing."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)

