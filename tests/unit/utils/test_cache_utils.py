"""
Unit tests for cache utilities.

Tests the cache service in src/utils/cache_utils.py.

Run with:
    pytest tests/unit/utils/test_cache_utils.py -v
"""

import json
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from src.utils.cache_utils import (
    CacheKey,
    CacheService,
    CacheStats,
    CacheTTL,
    cached,
    get_cache_service,
    reset_cache_service,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def clean_cache_service():
    """Reset cache service before each test."""
    reset_cache_service()
    yield
    reset_cache_service()


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock = MagicMock()
    mock._client = MagicMock()
    mock._client.ping.return_value = True
    
    # In-memory storage for testing
    storage = {}
    ttls = {}
    
    def mock_get(key):
        return storage.get(key)
    
    def mock_setex(key, ttl, value):
        storage[key] = value
        ttls[key] = ttl
        return True
    
    def mock_delete(*keys):
        deleted = 0
        for key in keys:
            if key in storage:
                del storage[key]
                deleted += 1
        return deleted
    
    def mock_keys(pattern):
        # Simple pattern matching (only supports *)
        prefix = pattern.replace("*", "")
        return [k for k in storage.keys() if k.startswith(prefix)]
    
    def mock_ttl(key):
        return ttls.get(key, -1)
    
    mock._client.get.side_effect = mock_get
    mock._client.setex.side_effect = mock_setex
    mock._client.delete.side_effect = mock_delete
    mock._client.keys.side_effect = mock_keys
    mock._client.ttl.side_effect = mock_ttl
    mock._storage = storage  # Expose for testing
    mock._ttls = ttls
    
    return mock


@pytest.fixture
def cache_service_with_mock_redis(mock_redis):
    """Create cache service with mocked Redis."""
    with patch('src.utils.cache_utils.get_redis_client', return_value=mock_redis):
        with patch('src.utils.cache_utils.HAS_REDIS', True):
            with patch('src.utils.cache_utils.HAS_FILE_CACHE', False):
                reset_cache_service()
                service = get_cache_service()
                service._redis = mock_redis
                service.stats.redis_available = True
                yield service


# ============================================================================
# Test CacheKey
# ============================================================================

class TestCacheKey:
    """Tests for CacheKey builder."""
    
    def test_price_key(self):
        """Test price key format."""
        key = CacheKey.price("FPT")
        assert key == "dcf:price:FPT:current"
    
    def test_price_key_uppercase(self):
        """Test ticker is converted to uppercase."""
        key = CacheKey.price("fpt")
        assert key == "dcf:price:FPT:current"
    
    def test_dcf_result_key(self):
        """Test DCF result key format."""
        key = CacheKey.dcf_result("VNM")
        assert key == "dcf:analysis:VNM:dcf"
    
    def test_graham_result_key(self):
        """Test Graham result key format."""
        key = CacheKey.graham_result("VNM")
        assert key == "dcf:analysis:VNM:graham"
    
    def test_financial_ttm_key(self):
        """Test financial TTM key format."""
        key = CacheKey.financial_ttm("FPT")
        assert key == "dcf:financial:FPT:ttm"
    
    def test_shares_key(self):
        """Test shares key format."""
        key = CacheKey.shares("FPT")
        assert key == "dcf:shares:FPT"
    
    def test_growth_estimate_key(self):
        """Test growth estimate key format."""
        key = CacheKey.growth_estimate("FPT")
        assert key == "dcf:growth:FPT:estimate"
    
    def test_fcf_key(self):
        """Test FCF key format."""
        key = CacheKey.fcf("FPT")
        assert key == "dcf:fcf:FPT:ttm"
    
    def test_custom_key(self):
        """Test custom key builder."""
        key = CacheKey.custom("custom", "FPT", "data")
        assert key == "dcf:custom:FPT:data"
    
    def test_custom_key_no_suffix(self):
        """Test custom key without suffix."""
        key = CacheKey.custom("category", "ABC")
        assert key == "dcf:category:ABC"


# ============================================================================
# Test CacheTTL
# ============================================================================

class TestCacheTTL:
    """Tests for CacheTTL constants."""
    
    def test_price_ttl(self):
        """Test price TTL is 5 minutes."""
        assert CacheTTL.PRICE == 300
    
    def test_dcf_result_ttl(self):
        """Test DCF result TTL is 1 hour."""
        assert CacheTTL.DCF_RESULT == 3600
    
    def test_shares_ttl(self):
        """Test shares TTL is 24 hours."""
        assert CacheTTL.SHARES == 86400
    
    def test_financial_ttm_ttl(self):
        """Test financial TTM TTL is 6 hours."""
        assert CacheTTL.FINANCIAL_TTM == 21600


# ============================================================================
# Test CacheStats
# ============================================================================

class TestCacheStats:
    """Tests for CacheStats class."""
    
    def test_initial_stats(self):
        """Test initial stats are zero."""
        stats = CacheStats()
        
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.sets == 0
        assert stats.hit_rate == 0.0
    
    def test_record_hit(self):
        """Test recording cache hit."""
        stats = CacheStats()
        stats.record_hit("dcf:price:FPT:current")
        
        assert stats.hits == 1
        assert stats.misses == 0
    
    def test_record_miss(self):
        """Test recording cache miss."""
        stats = CacheStats()
        stats.record_miss("dcf:price:FPT:current")
        
        assert stats.hits == 0
        assert stats.misses == 1
    
    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats()
        stats.record_hit()
        stats.record_hit()
        stats.record_hit()
        stats.record_miss()
        
        assert stats.hit_rate == 0.75
    
    def test_hit_rate_zero_requests(self):
        """Test hit rate with no requests."""
        stats = CacheStats()
        assert stats.hit_rate == 0.0
    
    def test_key_stats_tracking(self):
        """Test per-key-type statistics."""
        stats = CacheStats()
        stats.record_hit("dcf:price:FPT:current")
        stats.record_hit("dcf:price:VNM:current")
        stats.record_miss("dcf:analysis:FPT:dcf")
        
        assert "price" in stats.key_stats
        assert stats.key_stats["price"]["hits"] == 2
        assert "analysis" in stats.key_stats
        assert stats.key_stats["analysis"]["misses"] == 1
    
    def test_reset(self):
        """Test stats reset."""
        stats = CacheStats()
        stats.record_hit()
        stats.record_miss()
        stats.reset()
        
        assert stats.hits == 0
        assert stats.misses == 0
    
    def test_get_stats(self):
        """Test get_stats returns all data."""
        stats = CacheStats()
        stats.record_hit()
        stats.redis_available = True
        
        result = stats.get_stats()
        
        assert "hits" in result
        assert "hit_rate" in result
        assert "redis_available" in result
        assert result["hits"] == 1
        assert result["redis_available"] == True


# ============================================================================
# Test CacheService
# ============================================================================

class TestCacheService:
    """Tests for CacheService class."""
    
    def test_get_returns_none_when_not_cached(self, cache_service_with_mock_redis):
        """Test get returns None for missing key."""
        service = cache_service_with_mock_redis
        
        result = service.get("dcf:price:FPT:current")
        
        assert result is None
        assert service.stats.misses == 1
    
    def test_set_and_get(self, cache_service_with_mock_redis):
        """Test basic set and get operations."""
        service = cache_service_with_mock_redis
        key = "dcf:price:FPT:current"
        
        service.set(key, 92500, ttl=300)
        result = service.get(key)
        
        # JSON deserializes int correctly
        assert result == 92500
        assert service.stats.sets == 1
        assert service.stats.hits == 1
    
    def test_set_dict_value(self, cache_service_with_mock_redis):
        """Test caching dict value."""
        service = cache_service_with_mock_redis
        key = "dcf:analysis:FPT:dcf"
        value = {"dcf_value": 85000, "graham_value": 92000}
        
        service.set(key, value, ttl=3600)
        result = service.get(key)
        
        assert result == value
    
    def test_delete(self, cache_service_with_mock_redis):
        """Test delete operation."""
        service = cache_service_with_mock_redis
        key = "dcf:price:FPT:current"
        
        service.set(key, 92500)
        service.delete(key)
        result = service.get(key)
        
        assert result is None
        assert service.stats.deletes == 1
    
    def test_ttl_is_set(self, cache_service_with_mock_redis, mock_redis):
        """Test TTL is properly set."""
        service = cache_service_with_mock_redis
        key = "dcf:price:FPT:current"
        
        service.set(key, 92500, ttl=300)
        
        assert mock_redis._ttls[key] == 300
    
    def test_get_ttl(self, cache_service_with_mock_redis):
        """Test getting remaining TTL."""
        service = cache_service_with_mock_redis
        key = "dcf:price:FPT:current"
        
        service.set(key, 92500, ttl=300)
        ttl = service.get_ttl(key)
        
        assert ttl == 300


# ============================================================================
# Test Cache-Aside Pattern
# ============================================================================

class TestCacheAsidePattern:
    """Tests for get_or_fetch cache-aside pattern."""
    
    def test_get_or_fetch_cache_miss(self, cache_service_with_mock_redis):
        """Test get_or_fetch fetches on cache miss."""
        service = cache_service_with_mock_redis
        key = "dcf:price:FPT:current"
        fetch_called = False
        
        def fetch_fn():
            nonlocal fetch_called
            fetch_called = True
            return 92500
        
        result = service.get_or_fetch(key, fetch_fn, ttl=300)
        
        assert result == 92500
        assert fetch_called == True
        assert service.stats.misses == 1
        assert service.stats.sets == 1
    
    def test_get_or_fetch_cache_hit(self, cache_service_with_mock_redis):
        """Test get_or_fetch uses cache on hit."""
        service = cache_service_with_mock_redis
        key = "dcf:price:FPT:current"
        
        # Pre-populate cache
        service.set(key, 92500)
        
        fetch_called = False
        def fetch_fn():
            nonlocal fetch_called
            fetch_called = True
            return 99999  # Different value
        
        result = service.get_or_fetch(key, fetch_fn)
        
        # Should return cached value, not fetch
        assert result == 92500  # From cache (JSON deserializes correctly)
        assert fetch_called == False
        assert service.stats.hits == 1
    
    def test_get_or_fetch_force_refresh(self, cache_service_with_mock_redis):
        """Test get_or_fetch with force_refresh."""
        service = cache_service_with_mock_redis
        key = "dcf:price:FPT:current"
        
        # Pre-populate cache with old value
        service.set(key, 90000)
        
        def fetch_fn():
            return 92500  # New value
        
        result = service.get_or_fetch(key, fetch_fn, force_refresh=True)
        
        # Should return fresh value
        assert result == 92500
    
    def test_get_or_fetch_none_result_not_cached(self, cache_service_with_mock_redis):
        """Test None results are not cached."""
        service = cache_service_with_mock_redis
        key = "dcf:price:FPT:current"
        
        def fetch_fn():
            return None
        
        result = service.get_or_fetch(key, fetch_fn)
        
        assert result is None
        # Check cache is still empty
        cached = service.get(key)
        assert cached is None


# ============================================================================
# Test Async Cache-Aside Pattern
# ============================================================================

class TestAsyncCacheAsidePattern:
    """Tests for async get_or_fetch."""
    
    @pytest.mark.asyncio
    async def test_get_or_fetch_async(self, cache_service_with_mock_redis):
        """Test async get_or_fetch."""
        service = cache_service_with_mock_redis
        key = "dcf:price:FPT:current"
        
        async def async_fetch():
            return 92500
        
        result = await service.get_or_fetch_async(key, async_fetch)
        
        assert result == 92500
        assert service.stats.sets == 1
    
    @pytest.mark.asyncio
    async def test_get_or_fetch_async_cache_hit(self, cache_service_with_mock_redis):
        """Test async get_or_fetch cache hit."""
        service = cache_service_with_mock_redis
        key = "dcf:price:FPT:current"
        
        # Pre-populate
        service.set(key, 92500)
        
        fetch_called = False
        async def async_fetch():
            nonlocal fetch_called
            fetch_called = True
            return 99999
        
        result = await service.get_or_fetch_async(key, async_fetch)
        
        assert fetch_called == False
        assert service.stats.hits == 1


# ============================================================================
# Test Cache Invalidation
# ============================================================================

class TestCacheInvalidation:
    """Tests for cache invalidation."""
    
    def test_invalidate_ticker(self, cache_service_with_mock_redis, mock_redis):
        """Test invalidating all cache for a ticker."""
        service = cache_service_with_mock_redis
        
        # Set multiple keys for same ticker
        service.set("dcf:price:FPT:current", 92500)
        service.set("dcf:analysis:FPT:dcf", {"value": 85000})
        
        # Also set key for different ticker
        service.set("dcf:price:VNM:current", 78000)
        
        # Manually fix the mock keys function for this test
        def mock_keys(pattern):
            # Match keys containing "FPT"
            return [k for k in mock_redis._storage.keys() if "FPT" in k]
        
        mock_redis._client.keys.side_effect = mock_keys
        
        deleted = service.invalidate_ticker("FPT")
        
        # FPT keys should be deleted
        assert service.get("dcf:price:FPT:current") is None
        assert service.get("dcf:analysis:FPT:dcf") is None
        
        # VNM should still exist
        assert service.get("dcf:price:VNM:current") is not None


# ============================================================================
# Test @cached Decorator
# ============================================================================

class TestCachedDecorator:
    """Tests for @cached decorator."""
    
    def test_cached_decorator(self, cache_service_with_mock_redis):
        """Test @cached decorator caches result."""
        call_count = 0
        
        @cached(key_fn=lambda ticker: CacheKey.dcf_result(ticker), ttl=CacheTTL.DCF_RESULT)
        def calculate_dcf(ticker: str) -> dict:
            nonlocal call_count
            call_count += 1
            return {"dcf_value": 85000, "ticker": ticker}
        
        # First call - should calculate
        result1 = calculate_dcf("FPT")
        assert call_count == 1
        assert result1["dcf_value"] == 85000
        
        # Second call - should use cache
        result2 = calculate_dcf("FPT")
        assert call_count == 1  # Not incremented
    
    def test_cached_decorator_different_args(self, cache_service_with_mock_redis):
        """Test @cached decorator with different arguments."""
        call_count = 0
        
        @cached(key_fn=lambda ticker: CacheKey.price(ticker), ttl=300)
        def get_price(ticker: str) -> int:
            nonlocal call_count
            call_count += 1
            return 92500 if ticker == "FPT" else 78000
        
        # Different tickers should have different cache entries
        price_fpt = get_price("FPT")
        price_vnm = get_price("VNM")
        
        assert call_count == 2
        assert price_fpt == 92500
        assert price_vnm == 78000


# ============================================================================
# Test Service Availability
# ============================================================================

class TestServiceAvailability:
    """Tests for cache service availability checks."""
    
    def test_is_available_with_redis(self, cache_service_with_mock_redis):
        """Test is_available returns True with Redis."""
        service = cache_service_with_mock_redis
        assert service.is_available() == True
    
    def test_is_available_without_backends(self):
        """Test is_available returns False without backends."""
        with patch('src.utils.cache_utils.HAS_REDIS', False):
            with patch('src.utils.cache_utils.HAS_FILE_CACHE', False):
                reset_cache_service()
                service = get_cache_service()
                assert service.is_available() == False


# ============================================================================
# Test Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_get_with_redis_error(self, cache_service_with_mock_redis):
        """Test get handles Redis errors gracefully."""
        service = cache_service_with_mock_redis
        service._redis._client.get.side_effect = Exception("Redis error")
        
        result = service.get("dcf:price:FPT:current")
        
        assert result is None
        assert service.stats.errors == 1
    
    def test_empty_key(self, cache_service_with_mock_redis):
        """Test handling empty key."""
        service = cache_service_with_mock_redis
        
        result = service.get("")
        assert result is None
    
    def test_stats_preserve_after_errors(self, cache_service_with_mock_redis):
        """Test stats are preserved after errors."""
        service = cache_service_with_mock_redis
        
        # Successful operation
        service.set("dcf:price:FPT:current", 92500)
        
        # Error
        service._redis._client.get.side_effect = Exception("Redis error")
        service.get("dcf:price:FPT:current")
        
        stats = service.get_stats()
        assert stats["sets"] == 1
        assert stats["errors"] == 1

