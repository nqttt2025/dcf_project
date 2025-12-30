"""
Redis Jobs Store - Persistent storage for sync jobs and executions

This module replaces in-memory storage (jobs_store, executions_store, logs_store)
with Redis-backed persistent storage.
"""
import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import redis
from .logger import get_logger

logger = get_logger()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Key prefixes
JOBS_PREFIX = "sync:jobs:"
EXECUTIONS_PREFIX = "sync:executions:"
LOGS_PREFIX = "sync:logs:"
JOB_LIST_KEY = "sync:job_ids"
STATS_KEY = "sync:stats"


class RedisJobsStore:
    """Redis-backed storage for sync jobs"""
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisJobsStore, cls).__new__(cls)
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
            self._client = redis.from_url(REDIS_URL, decode_responses=True)
            self._client.ping()
            logger.info(f"RedisJobsStore connected to: {REDIS_URL}")
        except Exception as e:
            logger.warning(f"RedisJobsStore failed to connect: {e}")
            self._client = None
    
    def _ensure_connected(self) -> bool:
        """Ensure Redis connection is active"""
        if self._client is None:
            self._connect()
        if self._client is None:
            return False
        try:
            self._client.ping()
            return True
        except:
            self._connect()
            return self._client is not None
    
    # ==========================================================================
    # JOBS Methods
    # ==========================================================================
    
    def save_job(self, job_id: str, job_data: Dict[str, Any]) -> bool:
        """Save a job to Redis"""
        if not self._ensure_connected():
            return False
        try:
            key = f"{JOBS_PREFIX}{job_id}"
            self._client.set(key, json.dumps(job_data))
            self._client.sadd(JOB_LIST_KEY, job_id)
            return True
        except Exception as e:
            logger.error(f"Error saving job {job_id}: {e}")
            return False
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a job from Redis"""
        if not self._ensure_connected():
            return None
        try:
            key = f"{JOBS_PREFIX}{job_id}"
            data = self._client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            return None
    
    def get_all_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Get all jobs from Redis"""
        if not self._ensure_connected():
            return {}
        try:
            job_ids = self._client.smembers(JOB_LIST_KEY)
            jobs = {}
            for job_id in job_ids:
                job = self.get_job(job_id)
                if job:
                    jobs[job_id] = job
            return jobs
        except Exception as e:
            logger.error(f"Error getting all jobs: {e}")
            return {}
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job from Redis"""
        if not self._ensure_connected():
            return False
        try:
            key = f"{JOBS_PREFIX}{job_id}"
            self._client.delete(key)
            self._client.srem(JOB_LIST_KEY, job_id)
            # Also delete associated executions
            exec_key = f"{EXECUTIONS_PREFIX}{job_id}"
            self._client.delete(exec_key)
            return True
        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {e}")
            return False
    
    def job_exists(self, job_id: str) -> bool:
        """Check if a job exists"""
        if not self._ensure_connected():
            return False
        try:
            return self._client.sismember(JOB_LIST_KEY, job_id)
        except:
            return False
    
    # ==========================================================================
    # EXECUTIONS Methods
    # ==========================================================================
    
    def add_execution(self, job_id: str, execution: Dict[str, Any]) -> bool:
        """Add an execution to a job"""
        if not self._ensure_connected():
            return False
        try:
            key = f"{EXECUTIONS_PREFIX}{job_id}"
            execution_id = execution.get('execution_id')
            # Store individual execution
            exec_key = f"{EXECUTIONS_PREFIX}exec:{execution_id}"
            self._client.setex(exec_key, 86400, json.dumps(execution))  # 24h TTL
            # Add to job's execution list
            self._client.rpush(key, execution_id)
            # Keep only last 100 executions
            self._client.ltrim(key, -100, -1)
            return True
        except Exception as e:
            logger.error(f"Error adding execution: {e}")
            return False
    
    def update_execution(self, execution_id: str, updates: Dict[str, Any]) -> bool:
        """Update an execution"""
        if not self._ensure_connected():
            return False
        try:
            exec_key = f"{EXECUTIONS_PREFIX}exec:{execution_id}"
            data = self._client.get(exec_key)
            if data:
                execution = json.loads(data)
                execution.update(updates)
                self._client.setex(exec_key, 86400, json.dumps(execution))
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating execution {execution_id}: {e}")
            return False
    
    def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get an execution by ID"""
        if not self._ensure_connected():
            return None
        try:
            exec_key = f"{EXECUTIONS_PREFIX}exec:{execution_id}"
            data = self._client.get(exec_key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting execution {execution_id}: {e}")
            return None
    
    def get_job_executions(self, job_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent executions for a job"""
        if not self._ensure_connected():
            return []
        try:
            key = f"{EXECUTIONS_PREFIX}{job_id}"
            execution_ids = self._client.lrange(key, -limit, -1)
            executions = []
            for exec_id in reversed(execution_ids):
                execution = self.get_execution(exec_id)
                if execution:
                    executions.append(execution)
            return executions
        except Exception as e:
            logger.error(f"Error getting job executions: {e}")
            return []
    
    def get_running_executions(self) -> List[Dict[str, Any]]:
        """Get all running executions"""
        if not self._ensure_connected():
            return []
        try:
            # Scan for all execution keys
            running = []
            cursor = 0
            while True:
                cursor, keys = self._client.scan(cursor, match=f"{EXECUTIONS_PREFIX}exec:*", count=100)
                for key in keys:
                    data = self._client.get(key)
                    if data:
                        execution = json.loads(data)
                        if execution.get('status') in ['running', 'pending']:
                            running.append(execution)
                if cursor == 0:
                    break
            return running
        except Exception as e:
            logger.error(f"Error getting running executions: {e}")
            return []
    
    # ==========================================================================
    # LOGS Methods
    # ==========================================================================
    
    def add_log(self, execution_id: str, level: str, message: str) -> bool:
        """Add a log entry for an execution"""
        if not self._ensure_connected():
            return False
        try:
            key = f"{LOGS_PREFIX}{execution_id}"
            log_entry = {
                "level": level,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self._client.rpush(key, json.dumps(log_entry))
            # Set TTL of 24 hours for logs
            self._client.expire(key, 86400)
            # Keep only last 1000 log entries
            self._client.ltrim(key, -1000, -1)
            return True
        except Exception as e:
            logger.error(f"Error adding log: {e}")
            return False
    
    def get_logs(self, execution_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs for an execution"""
        if not self._ensure_connected():
            return []
        try:
            key = f"{LOGS_PREFIX}{execution_id}"
            log_entries = self._client.lrange(key, -limit, -1)
            logs = []
            for entry in log_entries:
                try:
                    logs.append(json.loads(entry))
                except:
                    pass
            return logs
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return []
    
    # ==========================================================================
    # STATS Methods
    # ==========================================================================
    
    def increment_stats(self, stat_name: str, amount: int = 1) -> bool:
        """Increment a stats counter"""
        if not self._ensure_connected():
            return False
        try:
            self._client.hincrby(STATS_KEY, stat_name, amount)
            return True
        except Exception as e:
            logger.error(f"Error incrementing stats: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get all stats"""
        if not self._ensure_connected():
            return {}
        try:
            stats = self._client.hgetall(STATS_KEY)
            return {k: int(v) for k, v in stats.items()}
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    # ==========================================================================
    # Redis Info Methods (for monitoring)
    # ==========================================================================
    
    def get_redis_info(self) -> Dict[str, Any]:
        """Get Redis server info for monitoring"""
        if not self._ensure_connected():
            return {"status": "disconnected"}
        try:
            info = self._client.info()
            memory_info = self._client.info('memory')
            clients_info = self._client.info('clients')
            
            # Get key counts
            db_info = self._client.info('keyspace')
            total_keys = 0
            for db, data in db_info.items():
                if db.startswith('db'):
                    total_keys += data.get('keys', 0)
            
            # Count sync-related keys
            sync_keys = {
                'jobs': self._client.scard(JOB_LIST_KEY),
                'running_executions': len(self.get_running_executions()),
            }
            
            return {
                "status": "connected",
                "version": info.get('redis_version'),
                "uptime_seconds": info.get('uptime_in_seconds'),
                "uptime_days": info.get('uptime_in_days'),
                "connected_clients": clients_info.get('connected_clients'),
                "memory": {
                    "used_memory": info.get('used_memory'),
                    "used_memory_human": info.get('used_memory_human'),
                    "used_memory_peak_human": info.get('used_memory_peak_human'),
                    "memory_fragmentation_ratio": memory_info.get('mem_fragmentation_ratio'),
                },
                "persistence": {
                    "aof_enabled": info.get('aof_enabled'),
                    "rdb_last_save_time": info.get('rdb_last_save_time'),
                    "rdb_changes_since_last_save": info.get('rdb_changes_since_last_save'),
                },
                "stats": {
                    "total_connections_received": info.get('total_connections_received'),
                    "total_commands_processed": info.get('total_commands_processed'),
                    "ops_per_sec": info.get('instantaneous_ops_per_sec'),
                },
                "keys": {
                    "total_keys": total_keys,
                    "sync_jobs": sync_keys['jobs'],
                    "running_executions": sync_keys['running_executions'],
                },
                "sync_stats": self.get_stats(),
            }
        except Exception as e:
            logger.error(f"Error getting Redis info: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_all_keys_by_pattern(self, pattern: str) -> List[str]:
        """Get all keys matching a pattern"""
        if not self._ensure_connected():
            return []
        try:
            keys = []
            cursor = 0
            while True:
                cursor, found_keys = self._client.scan(cursor, match=pattern, count=100)
                keys.extend(found_keys)
                if cursor == 0:
                    break
            return keys
        except Exception as e:
            logger.error(f"Error scanning keys: {e}")
            return []
    
    def get_cached_data_summary(self) -> Dict[str, Any]:
        """Get summary of cached data"""
        if not self._ensure_connected():
            return {}
        try:
            summary = {
                "analysis_status": [],
                "cached_stocks": [],
                "sync_jobs": [],
            }
            
            # Analysis status keys
            analysis_keys = self.get_all_keys_by_pattern("analysis:*")
            for key in analysis_keys[:20]:  # Limit to 20
                data = self._client.get(key)
                if data:
                    try:
                        parsed = json.loads(data)
                        summary["analysis_status"].append({
                            "key": key,
                            "ticker": parsed.get('ticker'),
                            "status": parsed.get('status'),
                            "progress": parsed.get('progress_percent'),
                        })
                    except:
                        pass
            
            # Stock cache keys
            stock_keys = self.get_all_keys_by_pattern("stock:*")
            stock_tickers = set()
            for key in stock_keys:
                parts = key.split(':')
                if len(parts) >= 2:
                    stock_tickers.add(parts[1])
            
            for ticker in list(stock_tickers)[:20]:  # Limit to 20
                cache_types = []
                for key in stock_keys:
                    if f"stock:{ticker}:" in key:
                        cache_type = key.replace(f"stock:{ticker}:", "")
                        ttl = self._client.ttl(key)
                        cache_types.append({"type": cache_type, "ttl": ttl})
                summary["cached_stocks"].append({
                    "ticker": ticker,
                    "caches": cache_types
                })
            
            # Sync jobs
            job_ids = self._client.smembers(JOB_LIST_KEY)
            for job_id in list(job_ids)[:20]:
                job = self.get_job(job_id)
                if job:
                    summary["sync_jobs"].append({
                        "job_id": job_id,
                        "name": job.get('name'),
                        "job_type": job.get('job_type'),
                        "enabled": job.get('enabled'),
                    })
            
            return summary
        except Exception as e:
            logger.error(f"Error getting cached data summary: {e}")
            return {}


# Singleton instance
_redis_jobs_store = None


def get_redis_jobs_store() -> RedisJobsStore:
    """Get Redis jobs store instance"""
    global _redis_jobs_store
    if _redis_jobs_store is None:
        _redis_jobs_store = RedisJobsStore()
    return _redis_jobs_store

