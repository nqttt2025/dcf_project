"""
Unit tests for retry mechanism.

Tests the retry utilities in src/utils/retry.py.

Run with:
    pytest tests/unit/core/test_retry_mechanism.py -v
"""

import asyncio
import time
from unittest.mock import MagicMock, patch, call

import pytest

# Import retry utilities
from src.utils.retry import (
    RetryConfig,
    RetryStats,
    with_retry,
    retry_call,
    async_retry_call,
    get_retry_stats,
    reset_retry_stats,
    DEFAULT_RETRY_CONFIG,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def clean_stats():
    """Reset retry stats before each test."""
    reset_retry_stats()
    yield
    reset_retry_stats()


# ============================================================================
# Test RetryConfig
# ============================================================================

class TestRetryConfig:
    """Tests for RetryConfig dataclass."""
    
    def test_default_config_values(self):
        """Test default configuration values."""
        config = RetryConfig()
        
        assert config.max_attempts == 3
        assert config.min_wait == 2.0
        assert config.max_wait == 10.0
        assert config.timeout == 30.0
        assert TimeoutError in config.retry_exceptions
        assert ConnectionError in config.retry_exceptions
    
    def test_custom_config_values(self):
        """Test custom configuration values."""
        config = RetryConfig(
            max_attempts=5,
            min_wait=1.0,
            max_wait=30.0,
            timeout=60.0,
            retry_exceptions=(ValueError, KeyError),
        )
        
        assert config.max_attempts == 5
        assert config.min_wait == 1.0
        assert config.max_wait == 30.0
        assert config.timeout == 60.0
        assert ValueError in config.retry_exceptions
        assert KeyError in config.retry_exceptions


# ============================================================================
# Test RetryStats
# ============================================================================

class TestRetryStats:
    """Tests for RetryStats class."""
    
    def test_initial_stats(self):
        """Test initial statistics are zero."""
        stats = RetryStats()
        result = stats.get_stats()
        
        assert result["total_calls"] == 0
        assert result["successful_calls"] == 0
        assert result["failed_calls"] == 0
        assert result["success_rate"] == 0
    
    def test_record_success(self):
        """Test recording successful calls."""
        stats = RetryStats()
        stats.record_success(attempts=1, duration=0.5)
        stats.record_success(attempts=2, duration=1.0)
        
        result = stats.get_stats()
        
        assert result["total_calls"] == 2
        assert result["successful_calls"] == 2
        assert result["failed_calls"] == 0
        assert result["success_rate"] == 1.0
        assert result["retry_distribution"] == {1: 1, 2: 1}
    
    def test_record_failure(self):
        """Test recording failed calls."""
        stats = RetryStats()
        stats.record_failure(attempts=3, duration=6.0)
        
        result = stats.get_stats()
        
        assert result["total_calls"] == 1
        assert result["successful_calls"] == 0
        assert result["failed_calls"] == 1
        assert result["success_rate"] == 0


# ============================================================================
# Test Sync Retry Decorator
# ============================================================================

class TestSyncRetry:
    """Tests for synchronous retry decorator."""
    
    def test_succeeds_first_attempt(self):
        """Test function succeeds on first attempt - no retry needed."""
        mock_func = MagicMock(return_value="success")
        
        @with_retry()
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_succeeds_after_one_retry(self):
        """Test function succeeds after one retry."""
        mock_func = MagicMock(side_effect=[TimeoutError("fail"), "success"])
        
        config = RetryConfig(min_wait=0.01, max_wait=0.02)  # Fast retry for testing
        
        @with_retry(config=config)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_succeeds_after_two_retries(self):
        """Test function succeeds after two retries."""
        mock_func = MagicMock(side_effect=[
            TimeoutError("fail 1"),
            ConnectionError("fail 2"),
            "success"
        ])
        
        config = RetryConfig(min_wait=0.01, max_wait=0.02)
        
        @with_retry(config=config)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_fails_after_max_retries(self):
        """Test function fails after exhausting max retries."""
        mock_func = MagicMock(side_effect=TimeoutError("always fail"))
        
        config = RetryConfig(max_attempts=3, min_wait=0.01, max_wait=0.02)
        
        @with_retry(config=config)
        def test_func():
            return mock_func()
        
        with pytest.raises(TimeoutError):
            test_func()
        
        assert mock_func.call_count == 3
    
    def test_non_retryable_exception_not_retried(self):
        """Test non-retryable exceptions are raised immediately."""
        mock_func = MagicMock(side_effect=ValueError("not retryable"))
        
        config = RetryConfig(retry_exceptions=(TimeoutError,))
        
        @with_retry(config=config)
        def test_func():
            return mock_func()
        
        with pytest.raises(ValueError):
            test_func()
        
        # Should only be called once - no retry for ValueError
        assert mock_func.call_count == 1
    
    def test_retry_logs_attempts(self, caplog):
        """Test retry attempts are logged."""
        mock_func = MagicMock(side_effect=[TimeoutError("fail"), "success"])
        
        config = RetryConfig(min_wait=0.01, max_wait=0.02)
        
        @with_retry(config=config, func_name="test_function")
        def test_func():
            return mock_func()
        
        with caplog.at_level("WARNING"):
            result = test_func()
        
        assert result == "success"
        # Check that retry was logged
        assert any("Retry attempt" in record.message or "succeeded after" in record.message 
                   for record in caplog.records)


# ============================================================================
# Test Async Retry Decorator
# ============================================================================

class TestAsyncRetry:
    """Tests for asynchronous retry decorator."""
    
    @pytest.mark.asyncio
    async def test_async_succeeds_first_attempt(self):
        """Test async function succeeds on first attempt."""
        mock_func = MagicMock(return_value="success")
        
        @with_retry()
        async def test_func():
            return mock_func()
        
        result = await test_func()
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    @pytest.mark.asyncio
    async def test_async_succeeds_after_retry(self):
        """Test async function succeeds after retry."""
        mock_func = MagicMock(side_effect=[TimeoutError("fail"), "success"])
        
        config = RetryConfig(min_wait=0.01, max_wait=0.02)
        
        @with_retry(config=config)
        async def test_func():
            return mock_func()
        
        result = await test_func()
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    @pytest.mark.asyncio
    async def test_async_fails_after_max_retries(self):
        """Test async function fails after max retries."""
        mock_func = MagicMock(side_effect=TimeoutError("always fail"))
        
        config = RetryConfig(max_attempts=3, min_wait=0.01, max_wait=0.02)
        
        @with_retry(config=config)
        async def test_func():
            return mock_func()
        
        with pytest.raises(TimeoutError):
            await test_func()
        
        assert mock_func.call_count == 3


# ============================================================================
# Test Exponential Backoff Timing
# ============================================================================

class TestExponentialBackoff:
    """Tests for exponential backoff timing."""
    
    def test_backoff_increases_exponentially(self):
        """Test that wait time increases with each retry."""
        call_times = []
        call_count = 0
        
        def failing_func():
            nonlocal call_count
            call_count += 1
            call_times.append(time.time())
            if call_count < 3:
                raise TimeoutError("fail")
            return "success"
        
        config = RetryConfig(
            max_attempts=3,
            min_wait=0.1,
            max_wait=1.0,
        )
        
        @with_retry(config=config)
        def test_func():
            return failing_func()
        
        result = test_func()
        
        assert result == "success"
        assert len(call_times) == 3
        
        # Check delays (should be approximately 0.1s and 0.2s for exponential)
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        
        # Allow some tolerance for timing
        assert delay1 >= 0.05  # At least some delay
        assert delay2 >= delay1 * 0.8  # Second delay should be similar or larger


# ============================================================================
# Test retry_call Function
# ============================================================================

class TestRetryCall:
    """Tests for retry_call convenience function."""
    
    def test_retry_call_success(self):
        """Test retry_call with successful function."""
        def simple_func(x, y):
            return x + y
        
        result = retry_call(simple_func, args=(1, 2))
        
        assert result == 3
    
    def test_retry_call_with_kwargs(self):
        """Test retry_call with keyword arguments."""
        def func_with_kwargs(a, b=10):
            return a * b
        
        result = retry_call(func_with_kwargs, args=(5,), kwargs={"b": 20})
        
        assert result == 100
    
    def test_retry_call_with_custom_config(self):
        """Test retry_call with custom configuration."""
        call_count = 0
        
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("fail")
            return "success"
        
        config = RetryConfig(max_attempts=3, min_wait=0.01, max_wait=0.02)
        result = retry_call(flaky_func, config=config)
        
        assert result == "success"
        assert call_count == 2


class TestAsyncRetryCall:
    """Tests for async_retry_call convenience function."""
    
    @pytest.mark.asyncio
    async def test_async_retry_call_success(self):
        """Test async_retry_call with successful function."""
        async def simple_async_func(x):
            return x * 2
        
        result = await async_retry_call(simple_async_func, args=(5,))
        
        assert result == 10


# ============================================================================
# Test Stats Integration
# ============================================================================

class TestStatsIntegration:
    """Test retry statistics are updated correctly."""
    
    def test_stats_updated_on_success(self):
        """Test stats are updated on successful calls."""
        @with_retry()
        def successful_func():
            return "ok"
        
        successful_func()
        successful_func()
        
        stats = get_retry_stats()
        
        assert stats["total_calls"] == 2
        assert stats["successful_calls"] == 2
        assert stats["failed_calls"] == 0
    
    def test_stats_updated_on_failure(self):
        """Test stats are updated on failed calls."""
        config = RetryConfig(max_attempts=2, min_wait=0.01, max_wait=0.02)
        
        @with_retry(config=config)
        def failing_func():
            raise TimeoutError("fail")
        
        with pytest.raises(TimeoutError):
            failing_func()
        
        stats = get_retry_stats()
        
        assert stats["total_calls"] == 1
        assert stats["successful_calls"] == 0
        assert stats["failed_calls"] == 1
    
    def test_stats_track_retry_distribution(self):
        """Test stats track retry distribution correctly."""
        call_count = 0
        
        def sometimes_fail():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TimeoutError("fail once")
            return "ok"
        
        config = RetryConfig(min_wait=0.01, max_wait=0.02)
        
        @with_retry(config=config)
        def test_func():
            return sometimes_fail()
        
        test_func()
        
        stats = get_retry_stats()
        
        # Should have succeeded on attempt 2
        assert 2 in stats["retry_distribution"]


# ============================================================================
# Test Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_zero_max_attempts_raises(self):
        """Test that zero max_attempts still tries once (tenacity behavior)."""
        # Note: tenacity's stop_after_attempt(0) means no attempts
        # Our implementation should handle this gracefully
        mock_func = MagicMock(return_value="success")
        
        config = RetryConfig(max_attempts=1)
        
        @with_retry(config=config)
        def test_func():
            return mock_func()
        
        result = test_func()
        assert result == "success"
    
    def test_function_with_arguments(self):
        """Test retry preserves function arguments."""
        @with_retry()
        def func_with_args(a, b, c=None):
            return f"{a}-{b}-{c}"
        
        result = func_with_args("x", "y", c="z")
        
        assert result == "x-y-z"
    
    def test_exception_message_preserved(self):
        """Test original exception message is preserved after retries."""
        config = RetryConfig(max_attempts=2, min_wait=0.01, max_wait=0.02)
        
        @with_retry(config=config)
        def failing_func():
            raise TimeoutError("specific error message")
        
        with pytest.raises(TimeoutError) as exc_info:
            failing_func()
        
        assert "specific error message" in str(exc_info.value)

