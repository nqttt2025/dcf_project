"""
Retry Utilities Module

Provides retry mechanism with exponential backoff for external API calls.
Uses tenacity library for robust retry handling.

Example:
    from src.utils.retry import with_retry, RetryConfig
    
    @with_retry()
    def fetch_data():
        return api_call()
    
    # With custom config
    @with_retry(config=RetryConfig(max_attempts=5, min_wait=1, max_wait=30))
    def fetch_important_data():
        return critical_api_call()
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Optional, Type, Union

try:
    from tenacity import (
        AsyncRetrying,
        RetryError,
        Retrying,
        after_log,
        before_sleep_log,
        retry_if_exception_type,
        stop_after_attempt,
        wait_exponential,
    )
    HAS_TENACITY = True
except ImportError:
    HAS_TENACITY = False
    Retrying = None
    AsyncRetrying = None
    RetryError = Exception

from .logger import get_logger

logger = get_logger()


@dataclass
class RetryConfig:
    """Configuration for retry behavior.
    
    Attributes:
        max_attempts: Maximum number of retry attempts (default: 3)
        min_wait: Minimum wait time in seconds between retries (default: 2)
        max_wait: Maximum wait time in seconds between retries (default: 10)
        retry_exceptions: Tuple of exception types to retry on
        timeout: Timeout for each individual attempt in seconds (default: 30)
    """
    max_attempts: int = 3
    min_wait: float = 2.0
    max_wait: float = 10.0
    retry_exceptions: tuple = (TimeoutError, ConnectionError, OSError)
    timeout: float = 30.0


# Default configuration
DEFAULT_RETRY_CONFIG = RetryConfig()


class RetryStats:
    """Track retry statistics for monitoring."""
    
    def __init__(self):
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.retry_counts = {}  # {attempt_number: count}
        self.total_retry_time = 0.0
    
    def record_success(self, attempts: int, duration: float):
        """Record a successful call."""
        self.total_calls += 1
        self.successful_calls += 1
        self.retry_counts[attempts] = self.retry_counts.get(attempts, 0) + 1
        self.total_retry_time += duration
    
    def record_failure(self, attempts: int, duration: float):
        """Record a failed call after max retries."""
        self.total_calls += 1
        self.failed_calls += 1
        self.retry_counts[attempts] = self.retry_counts.get(attempts, 0) + 1
        self.total_retry_time += duration
    
    def get_stats(self) -> dict:
        """Get current statistics."""
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": self.successful_calls / self.total_calls if self.total_calls > 0 else 0,
            "retry_distribution": self.retry_counts,
            "avg_time_per_call": self.total_retry_time / self.total_calls if self.total_calls > 0 else 0,
        }


# Global stats tracker
retry_stats = RetryStats()


def _log_retry_attempt(retry_state) -> None:
    """Log retry attempt with details."""
    attempt = retry_state.attempt_number
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    
    if exc:
        logger.warning(
            f"Retry attempt {attempt}: {type(exc).__name__}: {str(exc)[:100]}",
            extra={
                "attempt": attempt,
                "exception_type": type(exc).__name__,
                "exception_msg": str(exc)[:200],
            }
        )


def with_retry(
    config: Optional[RetryConfig] = None,
    func_name: Optional[str] = None,
) -> Callable:
    """
    Decorator to add retry logic with exponential backoff.
    
    Args:
        config: RetryConfig instance for custom retry behavior
        func_name: Optional name for logging (defaults to function name)
    
    Returns:
        Decorated function with retry logic
    
    Example:
        @with_retry()
        def fetch_stock_data(ticker):
            return vnstock.get_data(ticker)
        
        @with_retry(config=RetryConfig(max_attempts=5))
        async def fetch_financial_data(ticker):
            return await api.get_financials(ticker)
    """
    if config is None:
        config = DEFAULT_RETRY_CONFIG
    
    def decorator(func: Callable) -> Callable:
        name = func_name or func.__name__
        
        if not HAS_TENACITY:
            # Fallback: simple retry without tenacity
            logger.warning("tenacity not installed, using simple retry fallback")
            return _simple_retry_wrapper(func, config, name)
        
        if asyncio.iscoroutinefunction(func):
            return _async_retry_wrapper(func, config, name)
        else:
            return _sync_retry_wrapper(func, config, name)
    
    return decorator


def _sync_retry_wrapper(func: Callable, config: RetryConfig, name: str) -> Callable:
    """Wrapper for synchronous functions with tenacity."""
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        attempt_count = 0
        last_exception = None
        
        try:
            for attempt in Retrying(
                stop=stop_after_attempt(config.max_attempts),
                wait=wait_exponential(
                    multiplier=1,
                    min=config.min_wait,
                    max=config.max_wait
                ),
                retry=retry_if_exception_type(config.retry_exceptions),
                before_sleep=lambda rs: _log_retry_attempt(rs),
                reraise=True,
            ):
                with attempt:
                    attempt_count = attempt.retry_state.attempt_number
                    result = func(*args, **kwargs)
                    
                    # Log success
                    duration = time.time() - start_time
                    if attempt_count > 1:
                        logger.info(
                            f"{name} succeeded after {attempt_count} attempts ({duration:.2f}s)"
                        )
                    
                    retry_stats.record_success(attempt_count, duration)
                    return result
        
        except RetryError as e:
            duration = time.time() - start_time
            retry_stats.record_failure(config.max_attempts, duration)
            logger.error(
                f"{name} failed after {config.max_attempts} attempts ({duration:.2f}s): {e.last_attempt.exception()}"
            )
            raise e.last_attempt.exception()
        
        except config.retry_exceptions as e:
            # When reraise=True, the original exception is raised after max retries
            duration = time.time() - start_time
            retry_stats.record_failure(config.max_attempts, duration)
            logger.error(
                f"{name} failed after {config.max_attempts} attempts ({duration:.2f}s): {e}"
            )
            raise
    
    return wrapper


def _async_retry_wrapper(func: Callable, config: RetryConfig, name: str) -> Callable:
    """Wrapper for asynchronous functions with tenacity."""
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        attempt_count = 0
        
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(config.max_attempts),
                wait=wait_exponential(
                    multiplier=1,
                    min=config.min_wait,
                    max=config.max_wait
                ),
                retry=retry_if_exception_type(config.retry_exceptions),
                before_sleep=lambda rs: _log_retry_attempt(rs),
                reraise=True,
            ):
                with attempt:
                    attempt_count = attempt.retry_state.attempt_number
                    result = await func(*args, **kwargs)
                    
                    # Log success
                    duration = time.time() - start_time
                    if attempt_count > 1:
                        logger.info(
                            f"{name} succeeded after {attempt_count} attempts ({duration:.2f}s)"
                        )
                    
                    retry_stats.record_success(attempt_count, duration)
                    return result
        
        except RetryError as e:
            duration = time.time() - start_time
            retry_stats.record_failure(config.max_attempts, duration)
            logger.error(
                f"{name} failed after {config.max_attempts} attempts ({duration:.2f}s): {e.last_attempt.exception()}"
            )
            raise e.last_attempt.exception()
        
        except config.retry_exceptions as e:
            # When reraise=True, the original exception is raised after max retries
            duration = time.time() - start_time
            retry_stats.record_failure(config.max_attempts, duration)
            logger.error(
                f"{name} failed after {config.max_attempts} attempts ({duration:.2f}s): {e}"
            )
            raise
    
    return wrapper


def _simple_retry_wrapper(func: Callable, config: RetryConfig, name: str) -> Callable:
    """Simple retry fallback when tenacity is not installed."""
    
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            start_time = time.time()
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except config.retry_exceptions as e:
                    last_exception = e
                    if attempt < config.max_attempts:
                        wait_time = min(config.min_wait * (2 ** (attempt - 1)), config.max_wait)
                        logger.warning(f"{name} attempt {attempt} failed: {e}, retrying in {wait_time}s")
                        await asyncio.sleep(wait_time)
            
            duration = time.time() - start_time
            logger.error(f"{name} failed after {config.max_attempts} attempts ({duration:.2f}s)")
            raise last_exception
        
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            start_time = time.time()
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except config.retry_exceptions as e:
                    last_exception = e
                    if attempt < config.max_attempts:
                        wait_time = min(config.min_wait * (2 ** (attempt - 1)), config.max_wait)
                        logger.warning(f"{name} attempt {attempt} failed: {e}, retrying in {wait_time}s")
                        time.sleep(wait_time)
            
            duration = time.time() - start_time
            logger.error(f"{name} failed after {config.max_attempts} attempts ({duration:.2f}s)")
            raise last_exception
        
        return sync_wrapper


def get_retry_stats() -> dict:
    """Get current retry statistics.
    
    Returns:
        dict: Statistics including success rate, retry distribution, etc.
    """
    return retry_stats.get_stats()


def reset_retry_stats() -> None:
    """Reset retry statistics (useful for testing)."""
    global retry_stats
    retry_stats = RetryStats()


# Convenience function for one-off retries
def retry_call(
    func: Callable,
    args: tuple = (),
    kwargs: dict = None,
    config: Optional[RetryConfig] = None,
) -> Any:
    """
    Execute a function with retry logic.
    
    Args:
        func: Function to execute
        args: Positional arguments for the function
        kwargs: Keyword arguments for the function
        config: Optional RetryConfig
    
    Returns:
        Result from the function
    
    Example:
        result = retry_call(fetch_data, args=("FPT",), config=RetryConfig(max_attempts=5))
    """
    if kwargs is None:
        kwargs = {}
    
    wrapped = with_retry(config=config)(func)
    return wrapped(*args, **kwargs)


async def async_retry_call(
    func: Callable,
    args: tuple = (),
    kwargs: dict = None,
    config: Optional[RetryConfig] = None,
) -> Any:
    """
    Execute an async function with retry logic.
    
    Args:
        func: Async function to execute
        args: Positional arguments for the function
        kwargs: Keyword arguments for the function
        config: Optional RetryConfig
    
    Returns:
        Result from the function
    """
    if kwargs is None:
        kwargs = {}
    
    wrapped = with_retry(config=config)(func)
    return await wrapped(*args, **kwargs)

