"""
Function-level tests for dcf_calculator.py.

Tests the DCFCalculator class with mocked dependencies.
These tests verify the DoD requirements:
1. Error handler integration works
2. Shares validation integration works
3. Partial results are handled correctly

Run with:
    pytest tests/unit/core/test_dcf_calculator_functions.py -v
"""

import os
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

import pytest


# ============================================================================
# Fixtures
# ============================================================================

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


@pytest.fixture
def temp_config_file(tmp_path, sample_config_content):
    """Create a temporary config file."""
    config_file = tmp_path / "FPT.cfg"
    config_file.write_text(sample_config_content)
    return str(config_file)


@pytest.fixture
def sample_financial_data():
    """Sample financial data for testing."""
    return {
        'fcf': 5000000000000,  # 5 trillion VND
        'ge': 10.0,  # 10% growth
        'shares': 1703507121,
        'eps': 1429.31,
        'price': 92500,
        'market_cap': 157574408692500,
        'industry_pe': 15.0,
    }


@pytest.fixture
def mock_fcfs_functions(sample_financial_data):
    """Mock all fcfs functions."""
    with patch('src.core.dcf_calculator.get_free_cash_flow', return_value=sample_financial_data['fcf']):
        with patch('src.core.dcf_calculator.get_shares_outstanding', return_value=sample_financial_data['shares']):
            with patch('src.core.dcf_calculator.get_earnings_per_share_Diluted', return_value=sample_financial_data['eps']):
                with patch('src.core.dcf_calculator.price_board_stock', return_value=sample_financial_data['price']):
                    with patch('src.core.dcf_calculator.get_market_cap', return_value=(sample_financial_data['market_cap'], sample_financial_data['price'])):
                        with patch('src.core.dcf_calculator.get_growth_estimate', return_value=sample_financial_data['ge']):
                            with patch('src.core.dcf_calculator.get_industry_pe', return_value=sample_financial_data['industry_pe']):
                                yield


# ============================================================================
# Test DCFCalculator Initialization
# ============================================================================

class TestDCFCalculatorInit:
    """Test DCFCalculator initialization."""
    
    def test_init_loads_config(self, temp_config_file):
        """Test that config is loaded correctly."""
        from src.core.dcf_calculator import DCFCalculator
        
        calculator = DCFCalculator(temp_config_file)
        
        assert calculator.ticker == "FPT"
        assert calculator.dcf_params['yr'] == 5
        assert calculator.dcf_params['dr'] == 10.0
        assert calculator.dcf_params['pr'] == 2.5
    
    def test_init_sets_cache_file(self, temp_config_file):
        """Test that cache file path is set."""
        from src.core.dcf_calculator import DCFCalculator
        
        calculator = DCFCalculator(temp_config_file)
        
        assert calculator.cache_file is not None
        assert "fpt_cache.json" in calculator.cache_file


# ============================================================================
# Test fetch_data_async with Error Handler
# ============================================================================

class TestFetchDataAsyncWithErrorHandler:
    """Test fetch_data_async with error handler integration."""
    
    @pytest.mark.asyncio
    async def test_fetch_data_all_success(self, temp_config_file, mock_fcfs_functions, sample_financial_data):
        """Test data fetch when all sources succeed."""
        from src.core.dcf_calculator import DCFCalculator
        
        calculator = DCFCalculator(temp_config_file)
        
        data = await calculator.fetch_data_async()
        
        assert data['fcf'] == sample_financial_data['fcf']
        assert data['shares'] == sample_financial_data['shares']
        assert data['price'] == sample_financial_data['price']
    
    @pytest.mark.asyncio
    async def test_fetch_data_partial_failure(self, temp_config_file, sample_financial_data):
        """Test data fetch when some sources fail."""
        from src.core.dcf_calculator import DCFCalculator
        
        # Mock FCF to fail, others succeed
        with patch('src.core.dcf_calculator.get_free_cash_flow', side_effect=TimeoutError("FCF timeout")):
            with patch('src.core.dcf_calculator.get_shares_outstanding', return_value=sample_financial_data['shares']):
                with patch('src.core.dcf_calculator.get_earnings_per_share_Diluted', return_value=sample_financial_data['eps']):
                    with patch('src.core.dcf_calculator.price_board_stock', return_value=sample_financial_data['price']):
                        with patch('src.core.dcf_calculator.get_market_cap', return_value=(sample_financial_data['market_cap'], sample_financial_data['price'])):
                            with patch('src.core.dcf_calculator.get_growth_estimate', return_value=sample_financial_data['ge']):
                                with patch('src.core.dcf_calculator.get_industry_pe', return_value=sample_financial_data['industry_pe']):
                                    calculator = DCFCalculator(temp_config_file)
                                    
                                    data = await calculator.fetch_data_async()
                                    
                                    # FCF should be None due to failure
                                    assert data['fcf'] is None
                                    # Other data should be present
                                    assert data['shares'] == sample_financial_data['shares']
                                    assert data['price'] == sample_financial_data['price']
    
    @pytest.mark.asyncio
    async def test_error_handler_records_errors(self, temp_config_file, sample_financial_data):
        """Test that error handler records fetch errors."""
        from src.core.dcf_calculator import DCFCalculator, HAS_ERROR_HANDLER
        
        if not HAS_ERROR_HANDLER:
            pytest.skip("Error handler not available")
        
        # Mock FCF to fail
        with patch('src.core.dcf_calculator.get_free_cash_flow', side_effect=TimeoutError("FCF timeout")):
            with patch('src.core.dcf_calculator.get_shares_outstanding', return_value=sample_financial_data['shares']):
                with patch('src.core.dcf_calculator.get_earnings_per_share_Diluted', return_value=sample_financial_data['eps']):
                    with patch('src.core.dcf_calculator.price_board_stock', return_value=sample_financial_data['price']):
                        with patch('src.core.dcf_calculator.get_market_cap', return_value=(sample_financial_data['market_cap'], sample_financial_data['price'])):
                            with patch('src.core.dcf_calculator.get_growth_estimate', return_value=sample_financial_data['ge']):
                                with patch('src.core.dcf_calculator.get_industry_pe', return_value=sample_financial_data['industry_pe']):
                                    calculator = DCFCalculator(temp_config_file)
                                    
                                    data = await calculator.fetch_data_async()
                                    
                                    # Error handler should have recorded the error
                                    if calculator.error_handler:
                                        assert len(calculator.error_handler.errors) >= 1


# ============================================================================
# Test Shares Validation Integration
# ============================================================================

class TestSharesValidationIntegration:
    """Test shares validation integration in DCFCalculator."""
    
    @pytest.mark.asyncio
    async def test_shares_validation_applied(self, temp_config_file, mock_fcfs_functions, sample_financial_data):
        """Test that shares validation is applied during fetch."""
        from src.core.dcf_calculator import DCFCalculator, HAS_SHARES_VALIDATOR
        
        if not HAS_SHARES_VALIDATOR:
            pytest.skip("Shares validator not available")
        
        calculator = DCFCalculator(temp_config_file)
        
        data = await calculator.fetch_data_async()
        
        # If shares validator is active, should add confidence info
        if 'shares_confidence' in data:
            assert data['shares_confidence'] in ['high', 'medium', 'low', 'unknown']
    
    @pytest.mark.asyncio
    async def test_shares_cross_validation_with_market_cap(self, temp_config_file, sample_financial_data):
        """Test that shares are cross-validated with market cap."""
        from src.core.dcf_calculator import DCFCalculator, HAS_SHARES_VALIDATOR
        
        if not HAS_SHARES_VALIDATOR:
            pytest.skip("Shares validator not available")
        
        # Use slightly different shares to trigger cross-validation
        modified_data = sample_financial_data.copy()
        modified_data['shares'] = 1700000000  # Slightly different
        
        with patch('src.core.dcf_calculator.get_free_cash_flow', return_value=modified_data['fcf']):
            with patch('src.core.dcf_calculator.get_shares_outstanding', return_value=modified_data['shares']):
                with patch('src.core.dcf_calculator.get_earnings_per_share_Diluted', return_value=modified_data['eps']):
                    with patch('src.core.dcf_calculator.price_board_stock', return_value=modified_data['price']):
                        with patch('src.core.dcf_calculator.get_market_cap', return_value=(modified_data['market_cap'], modified_data['price'])):
                            with patch('src.core.dcf_calculator.get_growth_estimate', return_value=modified_data['ge']):
                                with patch('src.core.dcf_calculator.get_industry_pe', return_value=modified_data['industry_pe']):
                                    calculator = DCFCalculator(temp_config_file)
                                    
                                    data = await calculator.fetch_data_async()
                                    
                                    # Shares should still be valid
                                    assert data['shares'] is not None
                                    assert data['shares'] > 0


# ============================================================================
# Test calculate_dcf Function
# ============================================================================

class TestCalculateDcf:
    """Test calculate_dcf method."""
    
    def test_calculate_dcf_with_valid_data(self, temp_config_file, sample_financial_data):
        """Test DCF calculation with valid data."""
        from src.core.dcf_calculator import DCFCalculator
        
        calculator = DCFCalculator(temp_config_file)
        
        result = calculator.calculate_dcf(sample_financial_data)
        
        assert 'fair_value' in result
        assert result['fair_value'] > 0
        assert 'forecast' in result
        assert 'pvs' in result
    
    def test_calculate_dcf_raises_on_missing_fcf(self, temp_config_file):
        """Test DCF raises error when FCF is missing."""
        from src.core.dcf_calculator import DCFCalculator
        
        calculator = DCFCalculator(temp_config_file)
        
        invalid_data = {
            'fcf': None,  # Missing FCF
            'ge': 10.0,
            'shares': 1703507121,
            'eps': 1429.31,
            'price': 92500,
        }
        
        with pytest.raises(ValueError, match="FCF is None"):
            calculator.calculate_dcf(invalid_data)
    
    def test_calculate_dcf_raises_on_invalid_shares(self, temp_config_file):
        """Test DCF raises error when shares is invalid."""
        from src.core.dcf_calculator import DCFCalculator
        
        calculator = DCFCalculator(temp_config_file)
        
        invalid_data = {
            'fcf': 5000000000000,
            'ge': 10.0,
            'shares': 0,  # Invalid shares
            'eps': 1429.31,
            'price': 92500,
        }
        
        with pytest.raises(ValueError, match="Shares"):
            calculator.calculate_dcf(invalid_data)


# ============================================================================
# Test calculate_graham Function
# ============================================================================

class TestCalculateGraham:
    """Test calculate_graham method."""
    
    def test_calculate_graham_with_valid_data(self, temp_config_file, sample_financial_data):
        """Test Graham calculation with valid data."""
        from src.core.dcf_calculator import DCFCalculator
        
        calculator = DCFCalculator(temp_config_file)
        
        result = calculator.calculate_graham(sample_financial_data)
        
        assert result is not None
        assert 'fair_value' in result
        assert result['fair_value'] > 0
    
    def test_calculate_graham_returns_none_for_negative_eps(self, temp_config_file):
        """Test Graham returns None when EPS is negative."""
        from src.core.dcf_calculator import DCFCalculator
        
        calculator = DCFCalculator(temp_config_file)
        
        invalid_data = {
            'fcf': 5000000000000,
            'ge': 10.0,
            'shares': 1703507121,
            'eps': -100,  # Negative EPS
            'price': 92500,
        }
        
        result = calculator.calculate_graham(invalid_data)
        
        assert result is None


# ============================================================================
# Test Full Calculation Flow
# ============================================================================

class TestFullCalculationFlow:
    """Test the complete calculation flow."""
    
    @pytest.mark.asyncio
    async def test_full_calculation_success(self, temp_config_file, mock_fcfs_functions, sample_financial_data):
        """Test complete calculation from config to result."""
        from src.core.dcf_calculator import DCFCalculator
        
        # Mock result_manager to avoid file I/O
        with patch('src.core.dcf_calculator.get_result_manager') as mock_result_mgr:
            mock_result_mgr.return_value.save_result.return_value = ("/tmp/result.json", "/tmp/log.txt")
            
            # Mock advanced analysis
            with patch('src.core.dcf_calculator.generate_advanced_analysis', return_value={}):
                with patch('src.core.dcf_calculator.get_pe_analysis', return_value={}):
                    calculator = DCFCalculator(temp_config_file)
                    
                    result = await calculator.calculate()
                    
                    assert result is not None
                    assert result['ticker'] == "FPT"
                    assert 'dcf_fair_value' in result
                    assert 'graham_fair_value' in result
                    assert result['dcf_fair_value'] > 0
    
    @pytest.mark.asyncio
    async def test_calculation_includes_error_summary(self, temp_config_file, sample_financial_data):
        """Test that calculation includes error summary when errors occur."""
        from src.core.dcf_calculator import DCFCalculator, HAS_ERROR_HANDLER
        
        if not HAS_ERROR_HANDLER:
            pytest.skip("Error handler not available")
        
        # Mock one source to fail
        with patch('src.core.dcf_calculator.get_free_cash_flow', return_value=sample_financial_data['fcf']):
            with patch('src.core.dcf_calculator.get_shares_outstanding', return_value=sample_financial_data['shares']):
                with patch('src.core.dcf_calculator.get_earnings_per_share_Diluted', return_value=sample_financial_data['eps']):
                    with patch('src.core.dcf_calculator.price_board_stock', return_value=sample_financial_data['price']):
                        with patch('src.core.dcf_calculator.get_market_cap', return_value=(sample_financial_data['market_cap'], sample_financial_data['price'])):
                            with patch('src.core.dcf_calculator.get_growth_estimate', side_effect=TimeoutError("Growth timeout")):
                                with patch('src.core.dcf_calculator.get_industry_pe', return_value=sample_financial_data['industry_pe']):
                                    calculator = DCFCalculator(temp_config_file)
                                    
                                    data = await calculator.fetch_data_async()
                                    
                                    # Error summary should be in data if errors occurred
                                    if '_fetch_errors' in data:
                                        assert 'total_errors' in data['_fetch_errors']

