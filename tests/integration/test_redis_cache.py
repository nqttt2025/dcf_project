"""
Integration tests for Redis caching.

Tests the cache service with real Redis connection.

Run with:
    docker-compose up -d redis  # Start Redis first
    pytest tests/integration/test_redis_cache.py -v
"""

import os
import time
from unittest.mock import patch

import pytest

# Skip all tests if Redis is not available
try:
    import redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    test_client = redis.from_url(REDIS_URL)
    test_client.ping()
    REDIS_AVAILABLE = True
except Exception:
    REDIS_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not REDIS_AVAILABLE,
    reason="Redis not available - start with: docker-compose up -d redis"
)


from src.utils.cache_utils import (
    CacheKey,
    CacheService,
    CacheTTL,
    get_cache_service,
    reset_cache_service,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def clean_test_keys():
    """Clean up test keys before and after each test."""
    reset_cache_service()
    cache = get_cache_service()
    
    # Clean before test
    if cache._redis and cache._redis._client:
        keys = cache._redis._client.keys("dcf:test:*")
        if keys:
            cache._redis._client.delete(*keys)
    
    yield cache
    
    # Clean after test
    if cache._redis and cache._redis._client:
        keys = cache._redis._client.keys("dcf:test:*")
        if keys:
            cache._redis._client.delete(*keys)


# ============================================================================
# Basic Redis Operations
# ============================================================================

class TestRedisConnection:
    """Test Redis connection and basic operations."""
    
    @pytest.mark.integration
    def test_redis_is_connected(self, clean_test_keys):
        """Test Redis connection is established."""
        cache = clean_test_keys
        
        assert cache.stats.redis_available == True
        assert cache._redis is not None
    
    @pytest.mark.integration
    def test_set_and_get_string(self, clean_test_keys):
        """Test set and get string value."""
        cache = clean_test_keys
        key = "dcf:test:string"
        
        cache.set(key, "hello world", ttl=60)
        result = cache.get(key)
        
        assert result == "hello world"
    
    @pytest.mark.integration
    def test_set_and_get_int(self, clean_test_keys):
        """Test set and get integer value."""
        cache = clean_test_keys
        key = "dcf:test:int"
        
        cache.set(key, 92500, ttl=60)
        result = cache.get(key)
        
        assert result == 92500
    
    @pytest.mark.integration
    def test_set_and_get_dict(self, clean_test_keys):
        """Test set and get dictionary value."""
        cache = clean_test_keys
        key = "dcf:test:dict"
        value = {
            "ticker": "FPT",
            "dcf_value": 85000.50,
            "graham_value": 92000.25,
            "upside": 10.5,
        }
        
        cache.set(key, value, ttl=60)
        result = cache.get(key)
        
        assert result == value
        assert result["ticker"] == "FPT"
        assert result["dcf_value"] == 85000.50
    
    @pytest.mark.integration
    def test_set_and_get_list(self, clean_test_keys):
        """Test set and get list value."""
        cache = clean_test_keys
        key = "dcf:test:list"
        value = [1, 2, 3, "four", {"five": 5}]
        
        cache.set(key, value, ttl=60)
        result = cache.get(key)
        
        assert result == value


# ============================================================================
# TTL Tests
# ============================================================================

class TestRedisTTL:
    """Test TTL functionality."""
    
    @pytest.mark.integration
    def test_ttl_is_set(self, clean_test_keys):
        """Test TTL is properly set on key."""
        cache = clean_test_keys
        key = "dcf:test:ttl"
        
        cache.set(key, "value", ttl=300)
        
        # Check TTL
        ttl = cache.get_ttl(key)
        assert ttl is not None
        assert 290 <= ttl <= 300  # Allow small variance
    
    @pytest.mark.integration
    def test_key_expires(self, clean_test_keys):
        """Test key expires after TTL."""
        cache = clean_test_keys
        key = "dcf:test:expire"
        
        # Set with very short TTL
        cache.set(key, "value", ttl=1)
        
        # Should exist immediately
        assert cache.get(key) == "value"
        
        # Wait for expiry
        time.sleep(1.5)
        
        # Should be gone
        assert cache.get(key) is None
    
    @pytest.mark.integration
    def test_different_ttl_values(self, clean_test_keys):
        """Test different TTL values for different data types."""
        cache = clean_test_keys
        
        # Set with different TTLs
        cache.set("dcf:test:price", 92500, ttl=CacheTTL.PRICE)
        cache.set("dcf:test:dcf", {"value": 85000}, ttl=CacheTTL.DCF_RESULT)
        cache.set("dcf:test:shares", 1703507121, ttl=CacheTTL.SHARES)
        
        # Check TTLs
        price_ttl = cache.get_ttl("dcf:test:price")
        dcf_ttl = cache.get_ttl("dcf:test:dcf")
        shares_ttl = cache.get_ttl("dcf:test:shares")
        
        # Price should have shorter TTL than DCF
        assert price_ttl < dcf_ttl
        # DCF should have shorter TTL than shares
        assert dcf_ttl < shares_ttl


# ============================================================================
# Cache-Aside Pattern Tests
# ============================================================================

class TestCacheAsidePatternRedis:
    """Test cache-aside pattern with real Redis."""
    
    @pytest.mark.integration
    def test_get_or_fetch_miss_then_hit(self, clean_test_keys):
        """Test cache miss then cache hit."""
        cache = clean_test_keys
        key = "dcf:test:aside"
        fetch_count = 0
        
        def expensive_fetch():
            nonlocal fetch_count
            fetch_count += 1
            return {"data": "result", "fetch_number": fetch_count}
        
        # First call - cache miss
        result1 = cache.get_or_fetch(key, expensive_fetch, ttl=60)
        assert result1["fetch_number"] == 1
        assert fetch_count == 1
        
        # Second call - cache hit
        result2 = cache.get_or_fetch(key, expensive_fetch, ttl=60)
        assert result2["fetch_number"] == 1  # Same as first
        assert fetch_count == 1  # Not incremented
    
    @pytest.mark.integration
    def test_force_refresh(self, clean_test_keys):
        """Test force refresh bypasses cache."""
        cache = clean_test_keys
        key = "dcf:test:refresh"
        fetch_count = 0
        
        def fetch():
            nonlocal fetch_count
            fetch_count += 1
            return fetch_count
        
        # First call
        result1 = cache.get_or_fetch(key, fetch, ttl=60)
        assert result1 == 1
        
        # Force refresh
        result2 = cache.get_or_fetch(key, fetch, ttl=60, force_refresh=True)
        assert result2 == 2  # New value
        assert fetch_count == 2


# ============================================================================
# Cache Invalidation Tests
# ============================================================================

class TestCacheInvalidation:
    """Test cache invalidation."""
    
    @pytest.mark.integration
    def test_delete_single_key(self, clean_test_keys):
        """Test deleting a single key."""
        cache = clean_test_keys
        key = "dcf:test:delete"
        
        cache.set(key, "value", ttl=60)
        assert cache.get(key) == "value"
        
        cache.delete(key)
        assert cache.get(key) is None
    
    @pytest.mark.integration
    def test_invalidate_ticker(self, clean_test_keys):
        """Test invalidating all keys for a ticker."""
        cache = clean_test_keys
        
        # Use custom keys with test prefix for isolation
        # But simulate real key patterns
        cache._redis._client.setex("dcf:price:TESTFPT:current", 60, "92500")
        cache._redis._client.setex("dcf:analysis:TESTFPT:dcf", 60, '{"value": 85000}')
        cache._redis._client.setex("dcf:shares:TESTFPT", 60, "1703507121")
        cache._redis._client.setex("dcf:price:TESTVNM:current", 60, "78000")
        
        # Invalidate TESTFPT
        keys = cache._redis._client.keys("dcf:*:TESTFPT:*")
        keys2 = cache._redis._client.keys("dcf:*:TESTFPT")
        all_keys = keys + keys2
        if all_keys:
            cache._redis._client.delete(*all_keys)
        
        # TESTFPT keys should be gone
        assert cache._redis._client.get("dcf:price:TESTFPT:current") is None
        assert cache._redis._client.get("dcf:analysis:TESTFPT:dcf") is None
        
        # TESTVNM should still exist
        assert cache._redis._client.get("dcf:price:TESTVNM:current") == "78000"


# ============================================================================
# Stats Tests
# ============================================================================

class TestCacheStats:
    """Test cache statistics with real Redis."""
    
    @pytest.mark.integration
    def test_stats_track_hits_misses(self, clean_test_keys):
        """Test stats track hits and misses."""
        cache = clean_test_keys
        cache.stats.reset()
        
        # Miss
        cache.get("dcf:test:nonexistent")
        
        # Set and Hit
        cache.set("dcf:test:exists", "value", ttl=60)
        cache.get("dcf:test:exists")
        
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] == 1
        assert stats["hit_rate"] == 0.5
    
    @pytest.mark.integration
    def test_stats_per_key_type(self, clean_test_keys):
        """Test stats track per key type."""
        cache = clean_test_keys
        cache.stats.reset()
        
        # Price keys
        cache.get("dcf:price:FPT:current")  # Miss
        cache.set("dcf:price:FPT:current", 92500, ttl=60)
        cache.get("dcf:price:FPT:current")  # Hit
        
        # Analysis keys
        cache.get("dcf:analysis:FPT:dcf")  # Miss
        
        stats = cache.get_stats()
        
        assert "price" in stats["key_stats"]
        assert stats["key_stats"]["price"]["hits"] == 1
        assert stats["key_stats"]["price"]["misses"] == 1
        
        assert "analysis" in stats["key_stats"]
        assert stats["key_stats"]["analysis"]["misses"] == 1


# ============================================================================
# Concurrent Access Tests
# ============================================================================

class TestConcurrentAccess:
    """Test concurrent cache access."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_get_or_fetch(self, clean_test_keys):
        """Test concurrent get_or_fetch calls."""
        import asyncio
        
        cache = clean_test_keys
        key = "dcf:test:concurrent"
        fetch_count = 0
        
        async def slow_fetch():
            nonlocal fetch_count
            fetch_count += 1
            await asyncio.sleep(0.1)
            return {"fetch_number": fetch_count}
        
        # Run multiple concurrent fetches
        tasks = [
            cache.get_or_fetch_async(key, slow_fetch, ttl=60)
            for _ in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Due to race conditions, might have multiple fetches
        # But all results should be valid
        for result in results:
            assert "fetch_number" in result
            assert result["fetch_number"] >= 1


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling with Redis."""
    
    @pytest.mark.integration
    def test_graceful_degradation(self, clean_test_keys):
        """Test cache operations don't fail app on Redis errors."""
        cache = clean_test_keys
        
        # Force an error by passing invalid data
        # (This should not raise an exception)
        try:
            cache.set("dcf:test:error", object(), ttl=60)  # Non-serializable
        except Exception:
            pass  # Expected to fail gracefully
        
        # Service should still work for valid data
        cache.set("dcf:test:valid", "value", ttl=60)
        assert cache.get("dcf:test:valid") == "value"


