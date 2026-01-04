"""
Unit tests for shares validator.

Tests the SharesValidator in src/utils/shares_validator.py.

Run with:
    pytest tests/unit/utils/test_shares_validator.py -v
"""

import pytest

from src.utils.shares_validator import (
    SharesValidator,
    ValidationConfidence,
    ValidationResult,
    validate_shares,
    validate_shares_from_sources,
    cross_validate_shares_with_market_cap,
    validate_and_cross_check,
)


# ============================================================================
# Test SharesValidator Class
# ============================================================================

class TestSharesValidator:
    """Tests for SharesValidator class."""
    
    def test_add_single_source(self):
        """Test adding a single source."""
        validator = SharesValidator("FPT")
        validator.add_source("balance_sheet", 1703507121)
        
        assert len(validator.sources) == 1
        assert validator.sources[0].name == "balance_sheet"
        assert validator.sources[0].value == 1703507121
    
    def test_add_multiple_sources(self):
        """Test adding multiple sources."""
        validator = SharesValidator("FPT")
        validator.add_source("balance_sheet", 1703507121, priority=3)
        validator.add_source("market_cap_calc", 1700000000, priority=2)
        validator.add_source("api_vnstock", 1705000000, priority=1)
        
        assert len(validator.sources) == 3
    
    def test_chaining(self):
        """Test method chaining."""
        validator = (
            SharesValidator("FPT")
            .add_source("source1", 1000000000)
            .add_source("source2", 1010000000)
        )
        
        assert len(validator.sources) == 2
    
    def test_add_invalid_source_skipped(self):
        """Test that invalid sources are skipped."""
        validator = SharesValidator("FPT")
        validator.add_source("valid", 1000000000)
        validator.add_source("invalid_none", None)
        validator.add_source("invalid_zero", 0)
        validator.add_source("invalid_negative", -1000)
        
        assert len(validator.sources) == 1
    
    def test_add_from_balance_sheet(self):
        """Test adding from balance sheet."""
        validator = SharesValidator("FPT")
        validator.add_from_balance_sheet(
            charter_capital=17035071210000,  # 17 trillion VND
            par_value=10000
        )
        
        assert len(validator.sources) == 1
        assert validator.sources[0].name == "balance_sheet"
        assert validator.sources[0].value == 1703507121
    
    def test_add_from_market_cap(self):
        """Test adding from market cap calculation."""
        validator = SharesValidator("FPT")
        validator.add_from_market_cap(
            market_cap=157574408692500,
            price=92500
        )
        
        assert len(validator.sources) == 1
        assert validator.sources[0].name == "market_cap_calc"
        # 157574408692500 / 92500 ≈ 1703507121
        assert abs(validator.sources[0].value - 1703507121) < 100


class TestSharesValidatorValidation:
    """Tests for validation logic."""
    
    def test_validate_single_source(self):
        """Test validation with single source."""
        validator = SharesValidator("FPT")
        validator.add_source("database", 1703507121, priority=5)
        
        result = validator.validate()
        
        assert result.is_valid
        assert result.value == 1703507121
        assert result.confidence == ValidationConfidence.MEDIUM
        assert "Only single source available" in result.warnings
    
    def test_validate_multiple_agreeing_sources(self):
        """Test validation with multiple agreeing sources."""
        validator = SharesValidator("FPT")
        validator.add_source("database", 1703507121, priority=5)
        validator.add_source("balance_sheet", 1703500000, priority=3)  # ~0.0004% diff
        validator.add_source("market_cap", 1704000000, priority=2)     # ~0.03% diff
        
        result = validator.validate()
        
        assert result.is_valid
        assert result.confidence == ValidationConfidence.HIGH
        assert len(result.discrepancies) == 0
    
    def test_validate_with_discrepancy(self):
        """Test validation with significant discrepancy."""
        validator = SharesValidator("FPT")
        validator.add_source("source1", 1000000000, priority=3)
        validator.add_source("source2", 1500000000, priority=2)  # 50% diff from source1
        
        result = validator.validate()
        
        assert result.is_valid
        # With 2 values, median is (1000+1500)/2 = 1250
        # source1 diff: |1000-1250|/1250 = 20% > 10%
        # source2 diff: |1500-1250|/1250 = 20% > 10%
        assert len(result.discrepancies) >= 1
        # Should use median due to discrepancy
    
    def test_validate_uses_median_on_discrepancy(self):
        """Test that median is used when there are discrepancies."""
        validator = SharesValidator("FPT")
        validator.add_source("low", 1000000000, priority=1)
        validator.add_source("mid", 1500000000, priority=2)
        validator.add_source("high", 2000000000, priority=3)
        
        result = validator.validate()
        
        # Median should be 1500000000
        assert result.value == 1500000000
    
    def test_validate_uses_highest_priority_when_no_discrepancy(self):
        """Test highest priority source used when sources agree."""
        validator = SharesValidator("FPT")
        validator.add_source("low_priority", 1700000000, priority=1)
        validator.add_source("high_priority", 1703507121, priority=5)
        
        result = validator.validate()
        
        # Should use high priority source
        assert result.value == 1703507121
    
    def test_validate_no_sources(self):
        """Test validation with no sources."""
        validator = SharesValidator("FPT")
        
        result = validator.validate()
        
        assert not result.is_valid
        assert result.value is None
        assert result.confidence == ValidationConfidence.UNKNOWN
    
    def test_validate_rejects_too_large(self):
        """Test that too large values are rejected."""
        validator = SharesValidator("FPT")
        validator.add_source("too_large", 200_000_000_000)  # 200 billion
        
        result = validator.validate()
        
        assert not result.is_valid
        assert result.confidence == ValidationConfidence.UNKNOWN
    
    def test_validate_rejects_too_small(self):
        """Test that too small values are rejected."""
        validator = SharesValidator("FPT")
        validator.add_source("too_small", 100)  # Only 100 shares
        
        result = validator.validate()
        
        assert not result.is_valid
    
    def test_validate_caches_result(self):
        """Test that validation result is cached."""
        validator = SharesValidator("FPT")
        validator.add_source("test", 1000000000)
        
        result1 = validator.validate()
        result2 = validator.validate()
        
        assert result1 is result2


class TestSharesValidatorReport:
    """Tests for discrepancy report."""
    
    def test_get_discrepancy_report(self):
        """Test discrepancy report generation."""
        validator = SharesValidator("FPT")
        validator.add_source("source1", 1703507121, priority=3)
        validator.add_source("source2", 1800000000, priority=2)
        
        report = validator.get_discrepancy_report()
        
        assert "FPT" in report
        assert "source1" in report
        assert "source2" in report
        assert "1,703,507,121" in report or "1703507121" in report


# ============================================================================
# Test Legacy Functions
# ============================================================================

class TestLegacyValidateShares:
    """Tests for legacy validate_shares function."""
    
    def test_valid_shares(self):
        """Test with valid shares."""
        assert validate_shares(1703507121, "FPT") == True
    
    def test_none_shares_raises(self):
        """Test None shares raises error."""
        with pytest.raises(ValueError):
            validate_shares(None, "FPT")
    
    def test_none_shares_no_raise(self):
        """Test None shares returns False when raise_error=False."""
        assert validate_shares(None, "FPT", raise_error=False) == False
    
    def test_zero_shares_raises(self):
        """Test zero shares raises error."""
        with pytest.raises(ValueError):
            validate_shares(0, "FPT")
    
    def test_negative_shares_raises(self):
        """Test negative shares raises error."""
        with pytest.raises(ValueError):
            validate_shares(-1000, "FPT")
    
    def test_too_large_shares_raises(self):
        """Test too large shares raises error."""
        with pytest.raises(ValueError):
            validate_shares(2e12, "FPT")  # 2 trillion


class TestLegacyCrossValidation:
    """Tests for legacy cross_validate_shares_with_market_cap."""
    
    def test_matching_values(self):
        """Test with matching market cap."""
        shares = 1703507121
        price = 92500
        market_cap = shares * price  # Exact match
        
        is_valid, error = cross_validate_shares_with_market_cap(
            shares, price, market_cap, "FPT"
        )
        
        assert is_valid == True
        assert error is None
    
    def test_within_tolerance(self):
        """Test within 15% tolerance."""
        shares = 1703507121
        price = 92500
        market_cap = shares * price * 1.10  # 10% higher
        
        is_valid, error = cross_validate_shares_with_market_cap(
            shares, price, market_cap, "FPT"
        )
        
        assert is_valid == True
    
    def test_exceeds_tolerance(self):
        """Test exceeds 15% tolerance."""
        shares = 1703507121
        price = 92500
        market_cap = shares * price * 1.20  # 20% higher
        
        is_valid, error = cross_validate_shares_with_market_cap(
            shares, price, market_cap, "FPT"
        )
        
        assert is_valid == False
        assert error is not None
    
    def test_missing_values(self):
        """Test with missing values returns valid."""
        is_valid, error = cross_validate_shares_with_market_cap(
            None, 92500, 157574408692500, "FPT"
        )
        
        assert is_valid == True


class TestLegacyValidateAndCrossCheck:
    """Tests for legacy validate_and_cross_check."""
    
    def test_basic_validation_only(self):
        """Test basic validation without cross-check."""
        assert validate_and_cross_check(1703507121, "FPT") == True
    
    def test_with_cross_check(self):
        """Test with cross-check."""
        shares = 1703507121
        price = 92500
        market_cap = shares * price
        
        result = validate_and_cross_check(
            shares, "FPT", price=price, market_cap=market_cap
        )
        
        assert result == True


class TestValidateSharesFromSources:
    """Tests for convenience function."""
    
    def test_with_all_sources(self):
        """Test with all sources provided."""
        result = validate_shares_from_sources(
            ticker="FPT",
            database_shares=1703507121,
            balance_sheet_shares=1703500000,
            market_cap=157574408692500,
            price=92500,
        )
        
        assert result.is_valid
        assert result.confidence in [ValidationConfidence.HIGH, ValidationConfidence.MEDIUM]
    
    def test_with_single_source(self):
        """Test with single source."""
        result = validate_shares_from_sources(
            ticker="FPT",
            database_shares=1703507121,
        )
        
        assert result.is_valid
        assert result.value == 1703507121
    
    def test_with_no_sources(self):
        """Test with no sources."""
        result = validate_shares_from_sources(ticker="FPT")
        
        assert not result.is_valid


# ============================================================================
# Test Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases."""
    
    def test_ticker_uppercase(self):
        """Test ticker is converted to uppercase."""
        validator = SharesValidator("fpt")
        assert validator.ticker == "FPT"
    
    def test_float_values(self):
        """Test float values are handled."""
        validator = SharesValidator("FPT")
        validator.add_source("test", 1703507121.5)
        
        result = validator.validate()
        assert result.is_valid
    
    def test_very_close_values(self):
        """Test very close values don't trigger discrepancy."""
        validator = SharesValidator("FPT")
        validator.add_source("s1", 1000000000)
        validator.add_source("s2", 1000000001)  # 0.0000001% diff
        
        result = validator.validate()
        
        assert len(result.discrepancies) == 0
    
    def test_warning_for_large_but_valid(self):
        """Test warning for large but valid shares."""
        validator = SharesValidator("FPT")
        validator.add_source("test", 60_000_000_000)  # 60 billion
        
        result = validator.validate()
        
        assert result.is_valid
        assert any("exceeds" in w for w in result.warnings)

