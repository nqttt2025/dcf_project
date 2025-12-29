"""
Redis Client Wrapper for Status Tracking
"""
import os
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import redis
from .logger import get_logger

logger = get_logger()

class RedisClient:
    """Singleton Redis client for status tracking"""
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._connect()

    def _connect(self):
        """Connect to Redis"""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            self._client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self._client.ping()
            logger.info(f"Connected to Redis: {redis_url}")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using fallback mode.")
            self._client = None

    def _ensure_connected(self):
        """Ensure Redis connection is active"""
        if self._client is None:
            self._connect()
        if self._client is None:
            return False
        try:
            self._client.ping()
            return True
        except:
            try:
                self._connect()
                return self._client is not None
            except:
                return False

    def set_analysis_status(self, ticker: str, status: str, progress: Optional[str] = None, 
                           progress_percent: Optional[float] = None, **kwargs) -> bool:
        """
        Set analysis status for a ticker
        
        Args:
            ticker: Stock ticker
            status: Status ('pending', 'running', 'processing', 'completed', 'failed')
            progress: Progress message
            progress_percent: Progress percentage (0-100)
            **kwargs: Additional data to store
        """
        if not self._ensure_connected():
            return False
        
        try:
            ticker = ticker.upper()
            key = f"analysis:{ticker}"
            
            data = {
                'ticker': ticker,
                'status': status,
                'updated_at': datetime.now().isoformat(),
            }
            
            if progress:
                data['progress'] = progress
            if progress_percent is not None:
                data['progress_percent'] = progress_percent
            
            # Add any additional kwargs
            data.update(kwargs)
            
            # Set with 1 hour expiration
            self._client.setex(key, 3600, json.dumps(data))
            
            # Also add to set of running analyses
            if status in ['running', 'processing']:
                self._client.sadd('running_analyses', ticker)
            else:
                self._client.srem('running_analyses', ticker)
            
            return True
        except Exception as e:
            logger.error(f"Error setting analysis status: {e}")
            return False

    def get_analysis_status(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get analysis status for a ticker"""
        if not self._ensure_connected():
            return None
        
        try:
            ticker = ticker.upper()
            key = f"analysis:{ticker}"
            data = self._client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting analysis status: {e}")
            return None

    def get_all_running_analyses(self) -> Dict[str, Dict[str, Any]]:
        """Get all running analyses"""
        if not self._ensure_connected():
            return {}
        
        try:
            running_tickers = self._client.smembers('running_analyses')
            result = {}
            for ticker in running_tickers:
                status = self.get_analysis_status(ticker)
                if status:
                    result[ticker] = status
            return result
        except Exception as e:
            logger.error(f"Error getting running analyses: {e}")
            return {}

    def delete_analysis_status(self, ticker: str) -> bool:
        """Delete analysis status"""
        if not self._ensure_connected():
            return False
        
        try:
            ticker = ticker.upper()
            key = f"analysis:{ticker}"
            self._client.delete(key)
            self._client.srem('running_analyses', ticker)
            return True
        except Exception as e:
            logger.error(f"Error deleting analysis status: {e}")
            return False

    def update_progress(self, ticker: str, progress: str, progress_percent: Optional[float] = None) -> bool:
        """Update progress for an analysis"""
        status = self.get_analysis_status(ticker)
        if status:
            return self.set_analysis_status(
                ticker,
                status.get('status', 'running'),
                progress=progress,
                progress_percent=progress_percent,
                started_at=status.get('started_at')
            )
        return False

    # ============================================================================
    # Data Caching Methods
    # ============================================================================

    def cache_financial_ttm(self, ticker: str, data: Dict[str, Any], ttl: int = 21600) -> bool:
        """Cache financial TTM data (TTL: 6 hours)"""
        if not self._ensure_connected():
            return False
        try:
            ticker = ticker.upper()
            key = f"stock:{ticker}:financial:ttm"
            data['ticker'] = ticker
            data['cached_at'] = datetime.now().isoformat()
            self._client.setex(key, ttl, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error caching financial TTM: {e}")
            return False

    def get_financial_ttm(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get cached financial TTM data"""
        if not self._ensure_connected():
            return None
        try:
            ticker = ticker.upper()
            key = f"stock:{ticker}:financial:ttm"
            data = self._client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting financial TTM: {e}")
            return None

    def cache_market_data(self, ticker: str, data: Dict[str, Any], ttl: int = 300) -> bool:
        """Cache market data (TTL: 5 minutes)"""
        if not self._ensure_connected():
            return False
        try:
            ticker = ticker.upper()
            key = f"stock:{ticker}:market:latest"
            data['ticker'] = ticker
            data['cached_at'] = datetime.now().isoformat()
            self._client.setex(key, ttl, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error caching market data: {e}")
            return False

    def get_market_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get cached market data"""
        if not self._ensure_connected():
            return None
        try:
            ticker = ticker.upper()
            key = f"stock:{ticker}:market:latest"
            data = self._client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return None

    def cache_shares(self, ticker: str, shares: float, par_value: float = 10000, 
                     calculation_method: str = "from_balance_sheet", ttl: int = 86400) -> bool:
        """Cache shares outstanding (TTL: 1 day)"""
        if not self._ensure_connected():
            return False
        try:
            ticker = ticker.upper()
            key = f"stock:{ticker}:shares:latest"
            data = {
                'ticker': ticker,
                'shares_outstanding': shares,
                'par_value': par_value,
                'calculation_method': calculation_method,
                'period_date': datetime.now().strftime('%Y-%m-%d'),
                'cached_at': datetime.now().isoformat()
            }
            self._client.setex(key, ttl, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error caching shares: {e}")
            return False

    def get_shares(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get cached shares outstanding"""
        if not self._ensure_connected():
            return None
        try:
            ticker = ticker.upper()
            key = f"stock:{ticker}:shares:latest"
            data = self._client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting shares: {e}")
            return None

    def cache_stock_info(self, ticker: str, data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Cache stock info (TTL: 1 hour)"""
        if not self._ensure_connected():
            return False
        try:
            ticker = ticker.upper()
            key = f"stock:{ticker}:info"
            data['ticker'] = ticker
            data['cached_at'] = datetime.now().isoformat()
            self._client.setex(key, ttl, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error caching stock info: {e}")
            return False

    def get_stock_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get cached stock info"""
        if not self._ensure_connected():
            return None
        try:
            ticker = ticker.upper()
            key = f"stock:{ticker}:info"
            data = self._client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting stock info: {e}")
            return None

    def cache_dcf_config(self, ticker: str, config: Dict[str, Any], ttl: int = 86400) -> bool:
        """Cache DCF config (TTL: 1 day)"""
        if not self._ensure_connected():
            return False
        try:
            ticker = ticker.upper()
            key = f"stock:{ticker}:config"
            config['ticker'] = ticker
            config['cached_at'] = datetime.now().isoformat()
            self._client.setex(key, ttl, json.dumps(config))
            return True
        except Exception as e:
            logger.error(f"Error caching DCF config: {e}")
            return False

    def get_dcf_config(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get cached DCF config"""
        if not self._ensure_connected():
            return None
        try:
            ticker = ticker.upper()
            key = f"stock:{ticker}:config"
            data = self._client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting DCF config: {e}")
            return None

    def cache_dcf_result(self, ticker: str, result: Dict[str, Any], ttl: int = 3600) -> bool:
        """Cache latest DCF result (TTL: 1 hour)"""
        if not self._ensure_connected():
            return False
        try:
            ticker = ticker.upper()
            key = f"stock:{ticker}:result:latest"
            result['ticker'] = ticker
            result['cached_at'] = datetime.now().isoformat()
            self._client.setex(key, ttl, json.dumps(result))
            return True
        except Exception as e:
            logger.error(f"Error caching DCF result: {e}")
            return False

    def get_dcf_result(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get cached DCF result"""
        if not self._ensure_connected():
            return None
        try:
            ticker = ticker.upper()
            key = f"stock:{ticker}:result:latest"
            data = self._client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting DCF result: {e}")
            return None

    def invalidate_cache(self, ticker: str, cache_type: Optional[str] = None) -> bool:
        """Invalidate cache for a ticker"""
        if not self._ensure_connected():
            return False
        try:
            ticker = ticker.upper()
            if cache_type:
                # Invalidate specific cache type
                key = f"stock:{ticker}:{cache_type}"
                self._client.delete(key)
            else:
                # Invalidate all caches for this ticker
                pattern = f"stock:{ticker}:*"
                keys = self._client.keys(pattern)
                if keys:
                    self._client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return False

# Singleton instance
_redis_client = None

def get_redis_client() -> RedisClient:
    """Get Redis client instance"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client

