"""
Unit tests for error handler.

Tests the DCFErrorHandler in src/utils/error_handler.py.

Run with:
    pytest tests/unit/utils/test_error_handler.py -v
"""

import pytest

from src.utils.error_handler import (
    DCFErrorHandler,
    DataFetchResult,
    ErrorRecord,
    ErrorSeverity,
    RecoveryStrategy,
    analyze_calculation_viability,
    with_error_recovery,
)


# ============================================================================
# Test DataFetchResult
# ============================================================================

class TestDataFetchResult:
    """Tests for DataFetchResult dataclass."""
    
    def test_live_source_not_degraded(self):
        """Test live source is not degraded."""
        result = DataFetchResult(True, 1000000, "live")
        assert result.is_degraded == False
    
    def test_cache_source_is_degraded(self):
        """Test cache source is degraded."""
        result = DataFetchResult(True, 1000000, "cache")
        assert result.is_degraded == True
    
    def test_default_source_is_degraded(self):
        """Test default source is degraded."""
        result = DataFetchResult(True, 5.0, "default")
        assert result.is_degraded == True


# ============================================================================
# Test ErrorRecord
# ============================================================================

class TestErrorRecord:
    """Tests for ErrorRecord dataclass."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        record = ErrorRecord(
            task_name="FCF",
            error_type="TimeoutError",
            error_message="API timeout after 60s",
            severity=ErrorSeverity.WARNING,
            recovery_strategy=RecoveryStrategy.USE_CACHE,
            recovered_value=1500000000000,
        )
        
        d = record.to_dict()
        
        assert d["task_name"] == "FCF"
        assert d["error_type"] == "TimeoutError"
        assert d["severity"] == "warning"
        assert d["recovery_strategy"] == "use_cache"


# ============================================================================
# Test DCFErrorHandler
# ============================================================================

class TestDCFErrorHandler:
    """Tests for DCFErrorHandler class."""
    
    def test_initialization(self):
        """Test handler initialization."""
        handler = DCFErrorHandler("FPT")
        
        assert handler.ticker == "FPT"
        assert handler.max_errors == 3
        assert len(handler.errors) == 0
    
    def test_ticker_uppercase(self):
        """Test ticker converted to uppercase."""
        handler = DCFErrorHandler("fpt")
        assert handler.ticker == "FPT"
    
    def test_handle_fetch_error_with_cache(self):
        """Test error handling with cache fallback."""
        handler = DCFErrorHandler("FPT")
        
        result = handler.handle_fetch_error(
            task_name="FCF",
            error=TimeoutError("API timeout"),
            cached_value=1500000000000,
        )
        
        assert result.success == True
        assert result.value == 1500000000000
        assert result.source == "cache"
        assert len(handler.errors) == 1
    
    def test_handle_fetch_error_with_default(self):
        """Test error handling with default fallback."""
        handler = DCFErrorHandler("FPT")
        
        result = handler.handle_fetch_error(
            task_name="Growth",
            error=ValueError("No data"),
            default_value=5.0,
        )
        
        assert result.success == True
        assert result.value == 5.0
        assert result.source == "default"
    
    def test_handle_fetch_error_system_default(self):
        """Test error handling uses system default for known fields."""
        handler = DCFErrorHandler("FPT")
        
        result = handler.handle_fetch_error(
            task_name="growth_estimate",
            error=ValueError("No growth data"),
        )
        
        assert result.success == True
        assert result.value == 5.0  # System default
        assert result.source == "fallback"
    
    def test_handle_fetch_error_no_recovery(self):
        """Test error handling when no recovery possible."""
        handler = DCFErrorHandler("FPT")
        
        result = handler.handle_fetch_error(
            task_name="FCF",  # Required field
            error=ValueError("No data"),
        )
        
        assert result.success == False
        assert result.value is None
        assert result.error is not None
    
    def test_critical_error_count(self):
        """Test critical error counting."""
        handler = DCFErrorHandler("FPT")
        
        # Cause critical errors for required fields
        handler.handle_fetch_error("FCF", ValueError("No data"))
        handler.handle_fetch_error("Shares", ValueError("No data"))
        handler.handle_fetch_error("Price", ValueError("No data"))
        
        assert handler._critical_count == 3
        assert handler.can_proceed() == False
    
    def test_can_proceed_under_limit(self):
        """Test can_proceed returns True under error limit."""
        handler = DCFErrorHandler("FPT", max_errors=3)
        
        handler.handle_fetch_error("FCF", ValueError("No data"))
        handler.handle_fetch_error("Shares", ValueError("No data"))
        
        assert handler.can_proceed() == True


class TestValidationErrorHandling:
    """Tests for validation error handling."""
    
    def test_validation_error_with_fallback(self):
        """Test validation error with fallback value."""
        handler = DCFErrorHandler("FPT")
        
        is_valid, value = handler.handle_validation_error(
            field_name="shares",
            value=-1000,
            error_message="Shares cannot be negative",
            fallback_value=1703507121,
        )
        
        assert is_valid == True
        assert value == 1703507121
        assert len(handler.errors) == 1
    
    def test_validation_error_no_fallback(self):
        """Test validation error without fallback."""
        handler = DCFErrorHandler("FPT")
        
        is_valid, value = handler.handle_validation_error(
            field_name="shares",
            value=-1000,
            error_message="Shares cannot be negative",
        )
        
        assert is_valid == False
        assert value == -1000


class TestErrorSummary:
    """Tests for error summary and reporting."""
    
    def test_get_error_summary(self):
        """Test getting error summary."""
        handler = DCFErrorHandler("FPT")
        
        handler.handle_fetch_error("FCF", TimeoutError("Timeout"), cached_value=1000)
        handler.handle_fetch_error("EPS", ValueError("No data"), default_value=1500)
        
        summary = handler.get_error_summary()
        
        assert summary["ticker"] == "FPT"
        assert summary["total_errors"] == 2
        assert len(summary["errors"]) == 2
        assert "FCF" in summary["recovered_fields"]
    
    def test_get_warnings(self):
        """Test getting warning messages."""
        handler = DCFErrorHandler("FPT")
        
        handler.handle_fetch_error("FCF", TimeoutError("Timeout"), cached_value=1000)
        
        warnings = handler.get_warnings()
        
        assert len(warnings) >= 1
        assert "FCF" in warnings[0]
    
    def test_get_missing_required(self):
        """Test getting missing required fields."""
        handler = DCFErrorHandler("FPT")
        
        data = {
            "fcf": 1500000000000,
            "shares": None,
            "price": 92500,
        }
        
        missing = handler.get_missing_required(data)
        
        assert "shares" in missing
        assert "fcf" not in missing
    
    def test_has_degraded_data(self):
        """Test checking for degraded data."""
        handler = DCFErrorHandler("FPT")
        
        assert handler.has_degraded_data() == False
        
        handler.handle_fetch_error("FCF", TimeoutError("Timeout"), cached_value=1000)
        
        assert handler.has_degraded_data() == True


# ============================================================================
# Test with_error_recovery Function
# ============================================================================

class TestWithErrorRecovery:
    """Tests for with_error_recovery helper function."""
    
    def test_successful_fetch(self):
        """Test successful fetch returns live data."""
        handler = DCFErrorHandler("FPT")
        
        result = with_error_recovery(
            handler,
            "FCF",
            lambda: 1500000000000,
        )
        
        assert result.success == True
        assert result.value == 1500000000000
        assert result.source == "live"
        assert len(handler.errors) == 0
    
    def test_failed_fetch_with_cache(self):
        """Test failed fetch falls back to cache."""
        handler = DCFErrorHandler("FPT")
        
        result = with_error_recovery(
            handler,
            "FCF",
            lambda: (_ for _ in ()).throw(TimeoutError("Timeout")),
            cached_value=1000000000000,
        )
        
        assert result.success == True
        assert result.value == 1000000000000
        assert result.source == "cache"
    
    def test_none_result_treated_as_error(self):
        """Test None result is treated as error."""
        handler = DCFErrorHandler("FPT")
        
        result = with_error_recovery(
            handler,
            "FCF",
            lambda: None,
            cached_value=1000000000000,
        )
        
        assert result.success == True
        assert result.source == "cache"


# ============================================================================
# Test analyze_calculation_viability
# ============================================================================

class TestAnalyzeCalculationViability:
    """Tests for analyze_calculation_viability function."""
    
    def test_all_data_available(self):
        """Test when all required data is available."""
        handler = DCFErrorHandler("FPT")
        data = {
            "fcf": 1500000000000,
            "shares": 1703507121,
            "price": 92500,
            "eps": 1429.31,
        }
        
        can_proceed, reason, recommendations = analyze_calculation_viability(handler, data)
        
        assert can_proceed == True
        assert "All data available" in reason
    
    def test_missing_required_data(self):
        """Test when required data is missing."""
        handler = DCFErrorHandler("FPT")
        data = {
            "fcf": None,
            "shares": 1703507121,
            "price": 92500,
        }
        
        can_proceed, reason, recommendations = analyze_calculation_viability(handler, data)
        
        assert can_proceed == False
        assert "fcf" in reason.lower()
    
    def test_degraded_data(self):
        """Test when data is degraded (from cache/default)."""
        handler = DCFErrorHandler("FPT")
        handler.handle_fetch_error("FCF", TimeoutError("Timeout"), cached_value=1000)
        
        data = {
            "fcf": 1000,
            "shares": 1703507121,
            "price": 92500,
        }
        
        can_proceed, reason, recommendations = analyze_calculation_viability(handler, data)
        
        assert can_proceed == True
        assert "degraded" in reason.lower()
        assert len(recommendations) > 0


# ============================================================================
# Test Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases."""
    
    def test_empty_error_message(self):
        """Test handling empty error message."""
        handler = DCFErrorHandler("FPT")
        
        result = handler.handle_fetch_error(
            task_name="FCF",
            error=Exception(""),
            cached_value=1000,
        )
        
        assert result.success == True
    
    def test_multiple_errors_same_field(self):
        """Test multiple errors for same field."""
        handler = DCFErrorHandler("FPT")
        
        handler.handle_fetch_error("FCF", TimeoutError("Timeout 1"), cached_value=1000)
        handler.handle_fetch_error("FCF", TimeoutError("Timeout 2"), cached_value=2000)
        
        assert len(handler.errors) == 2
    
    def test_special_characters_in_task_name(self):
        """Test task names with special characters."""
        handler = DCFErrorHandler("FPT")
        
        result = handler.handle_fetch_error(
            task_name="Market Cap (VND)",
            error=ValueError("No data"),
            cached_value=157574408692500,
        )
        
        assert result.success == True


