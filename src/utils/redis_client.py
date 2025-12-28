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

# Singleton instance
_redis_client = None

def get_redis_client() -> RedisClient:
    """Get Redis client instance"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client

