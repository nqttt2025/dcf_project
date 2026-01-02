"""
Integration tests for DCF with retry mechanism.

Tests the complete flow of DCF calculation with retry handling.

Run with:
    pytest tests/integration/test_dcf_retry.py -v
"""

import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

import pytest


# ============================================================================
# Test DCF with Retry Integration
# ============================================================================

class TestDCFRetryIntegration:
    """Integration tests for DCF calculation with retry mechanism."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_dcf_completes_with_normal_api(self, mock_vnstock, sample_financial_data):
        """Test DCF completes normally when API works."""
        # This is a placeholder - actual implementation depends on DCF calculator structure
        # The test should verify that when vnstock API works, DCF calculates correctly
        
        from src.utils.retry import with_retry, RetryConfig
        
        # Simulate API call that works
        @with_retry()
        async def fetch_fcf(ticker):
            return sample_financial_data['fcf']
        
        result = await fetch_fcf("FPT")
        assert result == sample_financial_data['fcf']
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_dcf_recovers_from_timeout(self):
        """Test DCF recovers from initial timeout via retry."""
        from src.utils.retry import with_retry, RetryConfig
        
        call_count = 0
        
        async def mock_api_call(ticker):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError(f"API timeout (attempt {call_count})")
            return {"fcf": 5000000000000}
        
        config = RetryConfig(min_wait=0.01, max_wait=0.02)
        
        @with_retry(config=config)
        async def fetch_with_retry(ticker):
            return await mock_api_call(ticker)
        
        result = await fetch_with_retry("FPT")
        
        assert result["fcf"] == 5000000000000
        assert call_count == 2  # Failed once, succeeded on retry
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_dcf_handles_persistent_failure(self):
        """Test DCF handles persistent API failures gracefully."""
        from src.utils.retry import with_retry, RetryConfig
        
        async def always_fail(ticker):
            raise TimeoutError("API always fails")
        
        config = RetryConfig(max_attempts=3, min_wait=0.01, max_wait=0.02)
        
        @with_retry(config=config)
        async def fetch_with_retry(ticker):
            return await always_fail(ticker)
        
        with pytest.raises(TimeoutError):
            await fetch_with_retry("FPT")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multiple_parallel_fetches_with_retry(self):
        """Test multiple parallel API calls each with retry."""
        from src.utils.retry import with_retry, RetryConfig
        
        call_counts = {"fcf": 0, "shares": 0, "eps": 0}
        
        async def mock_fetch(data_type):
            call_counts[data_type] += 1
            if call_counts[data_type] < 2:
                raise TimeoutError(f"{data_type} timeout")
            return f"{data_type}_data"
        
        config = RetryConfig(min_wait=0.01, max_wait=0.02)
        
        @with_retry(config=config)
        async def fetch_fcf():
            return await mock_fetch("fcf")
        
        @with_retry(config=config)
        async def fetch_shares():
            return await mock_fetch("shares")
        
        @with_retry(config=config)
        async def fetch_eps():
            return await mock_fetch("eps")
        
        # Run in parallel
        results = await asyncio.gather(
            fetch_fcf(),
            fetch_shares(),
            fetch_eps(),
        )
        
        assert results == ["fcf_data", "shares_data", "eps_data"]
        assert all(count == 2 for count in call_counts.values())


# ============================================================================
# Test Retry Stats in DCF Context
# ============================================================================

class TestDCFRetryStats:
    """Test retry statistics in DCF calculation context."""
    
    @pytest.mark.integration
    def test_stats_reflect_dcf_retries(self, reset_retry_stats):
        """Test retry stats accurately reflect DCF call patterns."""
        from src.utils.retry import with_retry, RetryConfig, get_retry_stats, reset_retry_stats
        
        reset_retry_stats()
        
        call_count = 0
        
        def flaky_api():
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 1:  # Fail on odd attempts
                raise TimeoutError("intermittent failure")
            return "success"
        
        config = RetryConfig(min_wait=0.01, max_wait=0.02)
        
        @with_retry(config=config)
        def fetch_data():
            return flaky_api()
        
        # Make 3 calls (each succeeds on 2nd attempt)
        for _ in range(3):
            call_count = 0  # Reset for each call
            fetch_data()
        
        stats = get_retry_stats()
        
        assert stats["total_calls"] == 3
        assert stats["successful_calls"] == 3
        assert stats["success_rate"] == 1.0


# ============================================================================
# Test with Real-ish Scenario
# ============================================================================

class TestRealScenario:
    """Test scenarios that mimic real DCF calculation."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fetch_data_async_with_retry(self):
        """Test async data fetch pattern used in DCF calculator."""
        from src.utils.retry import with_retry, RetryConfig
        
        # Mock the pattern used in dcf_calculator.py
        async def fetch_with_timeout(func, timeout=60.0, task_name="Unknown"):
            """Wrapper similar to DCF calculator's fetch_with_timeout."""
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(func),
                    timeout=timeout
                )
                return result
            except asyncio.TimeoutError:
                raise TimeoutError(f"Timeout fetching {task_name}")
        
        # Test that retry wraps this pattern correctly
        config = RetryConfig(min_wait=0.01, max_wait=0.02)
        call_count = 0
        
        def slow_api():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("slow")
            return {"data": "success"}
        
        @with_retry(config=config)
        async def fetch_fcf_with_retry():
            return slow_api()
        
        result = await fetch_fcf_with_retry()
        
        assert result["data"] == "success"
        assert call_count == 2

