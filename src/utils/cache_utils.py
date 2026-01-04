"""
Enhanced Cache Utilities Module

Provides unified caching interface with:
- Redis (primary) with automatic TTL
- File cache (fallback)
- Cache-aside pattern helpers
- Cache statistics tracking

Example:
    from src.utils.cache_utils import CacheService, CacheKey
    
    cache = get_cache_service()
    
    # Get or fetch pattern
    result = await cache.get_or_fetch(
        key=CacheKey.dcf_result("FPT"),
        fetch_fn=lambda: calculate_dcf("FPT"),
        ttl=CacheTTL.DCF_RESULT
    )
    
    # Manual cache operations
    cache.set(CacheKey.price("FPT"), 92500, ttl=CacheTTL.PRICE)
    price = cache.get(CacheKey.price("FPT"))
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, Union
import asyncio

from .logger import get_logger

# Try to import Redis client
try:
    from .redis_client import get_redis_client
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    get_redis_client = None

# Try to import file cache manager
try:
    from .cache_manager import get_cache_manager
    HAS_FILE_CACHE = True
except ImportError:
    HAS_FILE_CACHE = False
    get_cache_manager = None


logger = get_logger()
T = TypeVar('T')


# ============================================================================
# Cache TTL Constants (in seconds)
# ============================================================================

class CacheTTL(IntEnum):
    """Standard TTL values for different data types."""
    PRICE = 300           # 5 minutes - volatile data
    MARKET_DATA = 300     # 5 minutes
    DCF_RESULT = 3600     # 1 hour - calculated result
    GRAHAM_RESULT = 3600  # 1 hour
    FINANCIAL_TTM = 21600 # 6 hours - quarterly data
    SHARES = 86400        # 24 hours - rarely changes
    GROWTH_ESTIMATE = 86400  # 24 hours
    STOCK_INFO = 86400    # 24 hours - company info
    DEFAULT = 3600        # 1 hour default


# ============================================================================
# Cache Key Builder
# ============================================================================

class CacheKey:
    """Builder for consistent cache keys."""
    
    PREFIX = "dcf"
    
    @classmethod
    def _build(cls, category: str, ticker: str, suffix: str = "") -> str:
        """Build a cache key."""
        ticker = ticker.upper()
        if suffix:
            return f"{cls.PREFIX}:{category}:{ticker}:{suffix}"
        return f"{cls.PREFIX}:{category}:{ticker}"
    
    @classmethod
    def price(cls, ticker: str) -> str:
        """Key for current price."""
        return cls._build("price", ticker, "current")
    
    @classmethod
    def dcf_result(cls, ticker: str) -> str:
        """Key for DCF calculation result."""
        return cls._build("analysis", ticker, "dcf")
    
    @classmethod
    def graham_result(cls, ticker: str) -> str:
        """Key for Graham valuation result."""
        return cls._build("analysis", ticker, "graham")
    
    @classmethod
    def financial_ttm(cls, ticker: str) -> str:
        """Key for financial TTM data."""
        return cls._build("financial", ticker, "ttm")
    
    @classmethod
    def shares(cls, ticker: str) -> str:
        """Key for shares outstanding."""
        return cls._build("shares", ticker)
    
    @classmethod
    def growth_estimate(cls, ticker: str) -> str:
        """Key for growth estimate."""
        return cls._build("growth", ticker, "estimate")
    
    @classmethod
    def market_data(cls, ticker: str) -> str:
        """Key for market data."""
        return cls._build("market", ticker, "data")
    
    @classmethod
    def eps(cls, ticker: str) -> str:
        """Key for EPS."""
        return cls._build("eps", ticker)
    
    @classmethod
    def fcf(cls, ticker: str) -> str:
        """Key for Free Cash Flow."""
        return cls._build("fcf", ticker, "ttm")
    
    @classmethod
    def custom(cls, category: str, ticker: str, suffix: str = "") -> str:
        """Build a custom cache key."""
        return cls._build(category, ticker, suffix)


# ============================================================================
# Cache Statistics
# ============================================================================

@dataclass
class CacheStats:
    """Track cache performance statistics."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    redis_available: bool = False
    file_cache_available: bool = False
    
    # Per-key type stats
    key_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    def record_hit(self, key: str = "") -> None:
        """Record a cache hit."""
        self.hits += 1
        self._record_key_stat(key, "hits")
    
    def record_miss(self, key: str = "") -> None:
        """Record a cache miss."""
        self.misses += 1
        self._record_key_stat(key, "misses")
    
    def record_set(self, key: str = "") -> None:
        """Record a cache set operation."""
        self.sets += 1
        self._record_key_stat(key, "sets")
    
    def record_delete(self, key: str = "") -> None:
        """Record a cache delete operation."""
        self.deletes += 1
        self._record_key_stat(key, "deletes")
    
    def record_error(self, key: str = "") -> None:
        """Record a cache error."""
        self.errors += 1
        self._record_key_stat(key, "errors")
    
    def _record_key_stat(self, key: str, stat_type: str) -> None:
        """Record stat for a specific key pattern."""
        if not key:
            return
        # Extract key type (e.g., "dcf:price:FPT:current" -> "price")
        parts = key.split(":")
        key_type = parts[1] if len(parts) > 1 else "unknown"
        
        if key_type not in self.key_stats:
            self.key_stats[key_type] = {"hits": 0, "misses": 0, "sets": 0}
        
        if stat_type in self.key_stats[key_type]:
            self.key_stats[key_type][stat_type] += 1
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get all statistics as a dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "errors": self.errors,
            "hit_rate": round(self.hit_rate, 4),
            "redis_available": self.redis_available,
            "file_cache_available": self.file_cache_available,
            "key_stats": self.key_stats,
        }
    
    def reset(self) -> None:
        """Reset all statistics."""
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.errors = 0
        self.key_stats = {}


# ============================================================================
# Cache Service
# ============================================================================

class CacheService:
    """
    Unified cache service with Redis primary and file fallback.
    
    Implements cache-aside pattern:
    1. Check cache first
    2. If miss, fetch from source
    3. Store in cache
    4. Return result
    """
    
    def __init__(self):
        self._redis = None
        self._file_cache = None
        self.stats = CacheStats()
        self._init_backends()
    
    def _init_backends(self) -> None:
        """Initialize cache backends."""
        # Try Redis
        if HAS_REDIS:
            try:
                self._redis = get_redis_client()
                if self._redis and self._redis._client:
                    self._redis._client.ping()
                    self.stats.redis_available = True
                    logger.debug("Cache: Redis backend available")
            except Exception as e:
                logger.debug(f"Cache: Redis not available: {e}")
                self._redis = None
        
        # Try file cache
        if HAS_FILE_CACHE:
            try:
                self._file_cache = get_cache_manager()
                self.stats.file_cache_available = True
                logger.debug("Cache: File backend available")
            except Exception as e:
                logger.debug(f"Cache: File cache not available: {e}")
                self._file_cache = None
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        # Try Redis first
        if self._redis and self.stats.redis_available:
            try:
                value = self._redis._client.get(key)
                if value is not None:
                    self.stats.record_hit(key)
                    logger.debug(f"Cache HIT (Redis): {key}")
                    # Try to deserialize JSON
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        return value
            except Exception as e:
                logger.debug(f"Redis get error: {e}")
                self.stats.record_error(key)
        
        # Try file cache fallback
        if self._file_cache:
            try:
                # Extract ticker and data type from key
                parts = key.split(":")
                if len(parts) >= 3:
                    ticker = parts[2]
                    data_type = ":".join(parts[1:])
                    value = self._file_cache.get_with_timestamp(ticker, data_type)
                    if value is not None:
                        self.stats.record_hit(key)
                        logger.debug(f"Cache HIT (File): {key}")
                        return value
            except Exception as e:
                logger.debug(f"File cache get error: {e}")
        
        self.stats.record_miss(key)
        logger.debug(f"Cache MISS: {key}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = CacheTTL.DEFAULT) -> bool:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successfully cached
        """
        success = False
        
        # Serialize value
        if isinstance(value, (dict, list)):
            serialized = json.dumps(value)
        else:
            serialized = str(value)
        
        # Try Redis
        if self._redis and self.stats.redis_available:
            try:
                self._redis._client.setex(key, ttl, serialized)
                success = True
                logger.debug(f"Cache SET (Redis): {key} [TTL: {ttl}s]")
            except Exception as e:
                logger.debug(f"Redis set error: {e}")
                self.stats.record_error(key)
        
        # Also set in file cache (as backup)
        if self._file_cache:
            try:
                parts = key.split(":")
                if len(parts) >= 3:
                    ticker = parts[2]
                    data_type = ":".join(parts[1:])
                    self._file_cache.set_with_timestamp(ticker, data_type, value)
                    if not success:
                        success = True
                        logger.debug(f"Cache SET (File): {key}")
            except Exception as e:
                logger.debug(f"File cache set error: {e}")
        
        if success:
            self.stats.record_set(key)
        
        return success
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted
        """
        success = False
        
        if self._redis and self.stats.redis_available:
            try:
                self._redis._client.delete(key)
                success = True
            except Exception as e:
                logger.debug(f"Redis delete error: {e}")
        
        if success:
            self.stats.record_delete(key)
            logger.debug(f"Cache DELETE: {key}")
        
        return success
    
    def invalidate_ticker(self, ticker: str) -> int:
        """
        Invalidate all cache entries for a ticker.
        
        Args:
            ticker: Stock ticker
            
        Returns:
            Number of keys deleted
        """
        ticker = ticker.upper()
        pattern = f"{CacheKey.PREFIX}:*:{ticker}:*"
        deleted = 0
        
        if self._redis and self.stats.redis_available:
            try:
                keys = self._redis._client.keys(pattern)
                if keys:
                    deleted = self._redis._client.delete(*keys)
                    logger.info(f"Cache INVALIDATE: {ticker} ({deleted} keys)")
            except Exception as e:
                logger.debug(f"Redis invalidate error: {e}")
        
        return deleted
    
    def get_or_fetch(
        self,
        key: str,
        fetch_fn: Callable[[], T],
        ttl: int = CacheTTL.DEFAULT,
        force_refresh: bool = False,
    ) -> T:
        """
        Cache-aside pattern: Get from cache or fetch and cache.
        
        Args:
            key: Cache key
            fetch_fn: Function to fetch data if not in cache
            ttl: Time to live for cached data
            force_refresh: If True, skip cache and fetch fresh data
            
        Returns:
            Cached or freshly fetched value
        """
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached = self.get(key)
            if cached is not None:
                return cached
        
        # Fetch fresh data
        logger.debug(f"Cache FETCH: {key}")
        result = fetch_fn()
        
        # Cache the result
        if result is not None:
            self.set(key, result, ttl)
        
        return result
    
    async def get_or_fetch_async(
        self,
        key: str,
        fetch_fn: Callable[[], T],
        ttl: int = CacheTTL.DEFAULT,
        force_refresh: bool = False,
    ) -> T:
        """
        Async version of get_or_fetch for async fetch functions.
        
        Args:
            key: Cache key
            fetch_fn: Async function to fetch data if not in cache
            ttl: Time to live for cached data
            force_refresh: If True, skip cache and fetch fresh data
            
        Returns:
            Cached or freshly fetched value
        """
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached = self.get(key)
            if cached is not None:
                return cached
        
        # Fetch fresh data
        logger.debug(f"Cache FETCH (async): {key}")
        if asyncio.iscoroutinefunction(fetch_fn):
            result = await fetch_fn()
        else:
            result = fetch_fn()
        
        # Cache the result
        if result is not None:
            self.set(key, result, ttl)
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.stats.get_stats()
    
    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self.stats.reset()
    
    def is_available(self) -> bool:
        """Check if any cache backend is available."""
        return self.stats.redis_available or self.stats.file_cache_available
    
    def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for a key (Redis only)."""
        if self._redis and self.stats.redis_available:
            try:
                ttl = self._redis._client.ttl(key)
                return ttl if ttl > 0 else None
            except Exception:
                pass
        return None


# ============================================================================
# Singleton Instance
# ============================================================================

_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get or create singleton cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def reset_cache_service() -> None:
    """Reset cache service (for testing)."""
    global _cache_service
    _cache_service = None


# ============================================================================
# Decorator for Caching Function Results
# ============================================================================

def cached(
    key_fn: Callable[..., str],
    ttl: int = CacheTTL.DEFAULT,
) -> Callable:
    """
    Decorator to cache function results.
    
    Args:
        key_fn: Function to generate cache key from function arguments
        ttl: Time to live in seconds
    
    Example:
        @cached(key_fn=lambda ticker: CacheKey.dcf_result(ticker), ttl=CacheTTL.DCF_RESULT)
        def calculate_dcf(ticker: str) -> dict:
            # expensive calculation
            return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_service()
            key = key_fn(*args, **kwargs)
            
            # Check cache
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # Calculate and cache
            result = func(*args, **kwargs)
            if result is not None:
                cache.set(key, result, ttl)
            
            return result
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_cache_service()
            key = key_fn(*args, **kwargs)
            
            # Check cache
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # Calculate and cache
            result = await func(*args, **kwargs)
            if result is not None:
                cache.set(key, result, ttl)
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator


