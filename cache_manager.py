import json
import os
from datetime import datetime, timezone
from logger import get_logger

logger = get_logger()

class CacheManager:
    """Singleton class for managing cache operations"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.cache = {}
        self.cache_file = os.path.join(os.path.dirname(__file__), "data", "fcf_cache.json")
        self._load_cache()

    def _load_cache(self):
        """Load cache from file into memory"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
                logger.debug(f"Loaded cache from file: {len(self.cache)} items")
        except Exception as e:
            logger.debug(f"Error loading cache: {e}")
            self.cache = {}

    def get(self, key):
        """Get value from cache"""
        return self.cache.get(key)

    def set(self, key, value):
        """Set value in cache (in-memory only, not persisted immediately)"""
        self.cache[key] = value
        logger.debug(f"Cache set: {key} = {value}")

    def set_with_timestamp(self, ticker, data_type, value):
        """Set value with timestamp in cache"""
        key = f"{ticker.upper()}_{data_type}"
        timestamp_key = f"{ticker.upper()}_{data_type}_timestamp"

        self.cache[key] = value
        self.cache[timestamp_key] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        if key in self.cache:
            value = self.cache[key]
            timestamp = self.cache.get(timestamp_key, "Unknown")
            logger.debug(f"Cache hit: {key} (updated: {timestamp})")
            return value
        return None

    def exists(self, ticker, data_type):
        """Check if data exists in cache"""
        key = f"{ticker.upper()}_{data_type}"
        return key in self.cache

    def save_to_file(self):
        """Save cache to file"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            logger.info(f"Cache saved to file with {len(self.cache)} items")
        except Exception as e:
            logger.error(f"Error saving cache to file: {e}")

    def clear(self):
        """Clear cache from memory"""
        self.cache = {}
        logger.debug("Cache cleared from memory")

    def get_all(self):
        """Get all cache data"""
        return self.cache.copy()


def get_cache_manager():
    """Get or create singleton instance"""
    return CacheManager()
