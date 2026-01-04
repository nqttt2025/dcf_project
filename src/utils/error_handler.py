"""
Error Handler Module

Provides error recovery strategies for DCF calculations.
Handles partial failures, fallbacks to cached data, and error reporting.

Example:
    from src.utils.error_handler import DCFErrorHandler, RecoveryStrategy
    
    handler = DCFErrorHandler("FPT")
    
    # Handle data fetch failure
    result = handler.handle_fetch_error(
        task_name="FCF",
        error=TimeoutError("API timeout"),
        cached_value=1500000000000
    )
    
    # Check if calculation can proceed
    if handler.can_proceed():
        # Continue with calculation
        pass
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from .logger import get_logger

logger = get_logger()


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    INFO = "info"           # Informational, no action needed
    WARNING = "warning"     # Degraded but can continue
    ERROR = "error"         # Significant, may affect results
    CRITICAL = "critical"   # Cannot proceed


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types."""
    USE_CACHE = "use_cache"           # Use cached value
    USE_DEFAULT = "use_default"        # Use default value
    RETRY = "retry"                    # Retry the operation
    SKIP = "skip"                      # Skip this data point
    ABORT = "abort"                    # Abort the calculation


@dataclass
class ErrorRecord:
    """Record of an error occurrence."""
    task_name: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    recovery_strategy: RecoveryStrategy
    recovered_value: Optional[Any] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "task_name": self.task_name,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "severity": self.severity.value,
            "recovery_strategy": self.recovery_strategy.value,
            "recovered_value": str(self.recovered_value) if self.recovered_value else None,
            "timestamp": self.timestamp,
        }


@dataclass
class DataFetchResult:
    """Result of a data fetch operation with error handling."""
    success: bool
    value: Optional[Any]
    source: str  # "live", "cache", "default", "fallback"
    error: Optional[ErrorRecord] = None
    
    @property
    def is_degraded(self) -> bool:
        """Check if result is degraded (not from live data)."""
        return self.source != "live"


class DCFErrorHandler:
    """
    Error handler for DCF calculations.
    
    Provides:
    - Error classification and recovery strategies
    - Fallback to cached data
    - Error aggregation and reporting
    - Decision support for proceeding with degraded data
    """
    
    # Default values for critical fields
    DEFAULT_VALUES = {
        "growth_estimate": 5.0,  # Conservative 5% growth
    }
    
    # Required fields for calculation
    REQUIRED_FIELDS = ["fcf", "shares", "price"]
    OPTIONAL_FIELDS = ["eps", "market_cap", "industry_pe", "growth_estimate"]
    
    def __init__(self, ticker: str, max_errors: int = 3):
        """
        Initialize error handler.
        
        Args:
            ticker: Stock ticker symbol
            max_errors: Maximum critical errors before aborting
        """
        self.ticker = ticker.upper()
        self.max_errors = max_errors
        self.errors: List[ErrorRecord] = []
        self.recovered_data: Dict[str, Any] = {}
        self._critical_count = 0
    
    def handle_fetch_error(
        self,
        task_name: str,
        error: Exception,
        cached_value: Optional[Any] = None,
        default_value: Optional[Any] = None,
    ) -> DataFetchResult:
        """
        Handle a data fetch error with recovery.
        
        Args:
            task_name: Name of the fetch task (e.g., "FCF", "Price")
            error: The exception that occurred
            cached_value: Previously cached value to use as fallback
            default_value: Default value if no cache available
            
        Returns:
            DataFetchResult with recovered value or None
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Determine severity based on field importance
        is_required = task_name.lower().replace(" ", "_") in [
            f.lower() for f in self.REQUIRED_FIELDS
        ]
        
        # Try recovery strategies in order
        if cached_value is not None:
            # Use cached value
            self._record_error(
                task_name, error_type, error_msg,
                ErrorSeverity.WARNING if is_required else ErrorSeverity.INFO,
                RecoveryStrategy.USE_CACHE,
                cached_value
            )
            self.recovered_data[task_name] = cached_value
            logger.info(f"{self.ticker}: Using cached {task_name}: {cached_value}")
            return DataFetchResult(True, cached_value, "cache")
        
        if default_value is not None:
            # Use default value
            self._record_error(
                task_name, error_type, error_msg,
                ErrorSeverity.WARNING,
                RecoveryStrategy.USE_DEFAULT,
                default_value
            )
            self.recovered_data[task_name] = default_value
            logger.warning(f"{self.ticker}: Using default {task_name}: {default_value}")
            return DataFetchResult(True, default_value, "default")
        
        # Check if we have a predefined default
        task_key = task_name.lower().replace(" ", "_")
        if task_key in self.DEFAULT_VALUES:
            default = self.DEFAULT_VALUES[task_key]
            self._record_error(
                task_name, error_type, error_msg,
                ErrorSeverity.WARNING,
                RecoveryStrategy.USE_DEFAULT,
                default
            )
            self.recovered_data[task_name] = default
            logger.warning(f"{self.ticker}: Using system default {task_name}: {default}")
            return DataFetchResult(True, default, "fallback")
        
        # No recovery possible
        severity = ErrorSeverity.CRITICAL if is_required else ErrorSeverity.ERROR
        strategy = RecoveryStrategy.ABORT if is_required else RecoveryStrategy.SKIP
        
        self._record_error(
            task_name, error_type, error_msg,
            severity, strategy
        )
        
        if severity == ErrorSeverity.CRITICAL:
            self._critical_count += 1
            logger.error(f"{self.ticker}: Critical error - no {task_name} available")
        
        return DataFetchResult(False, None, "none", self.errors[-1])
    
    def handle_validation_error(
        self,
        field_name: str,
        value: Any,
        error_message: str,
        fallback_value: Optional[Any] = None,
    ) -> Tuple[bool, Any]:
        """
        Handle a validation error.
        
        Args:
            field_name: Name of the field being validated
            value: The invalid value
            error_message: Description of the validation failure
            fallback_value: Value to use if validation fails
            
        Returns:
            Tuple of (is_valid, value_to_use)
        """
        if fallback_value is not None:
            self._record_error(
                field_name, "ValidationError", error_message,
                ErrorSeverity.WARNING,
                RecoveryStrategy.USE_DEFAULT,
                fallback_value
            )
            logger.warning(
                f"{self.ticker}: Validation failed for {field_name}: {error_message}. "
                f"Using fallback: {fallback_value}"
            )
            return True, fallback_value
        
        self._record_error(
            field_name, "ValidationError", error_message,
            ErrorSeverity.ERROR,
            RecoveryStrategy.ABORT
        )
        logger.error(f"{self.ticker}: Validation failed for {field_name}: {error_message}")
        return False, value
    
    def _record_error(
        self,
        task_name: str,
        error_type: str,
        error_message: str,
        severity: ErrorSeverity,
        strategy: RecoveryStrategy,
        recovered_value: Any = None,
    ) -> None:
        """Record an error."""
        record = ErrorRecord(
            task_name=task_name,
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            recovery_strategy=strategy,
            recovered_value=recovered_value,
        )
        self.errors.append(record)
    
    def can_proceed(self) -> bool:
        """
        Check if calculation can proceed.
        
        Returns:
            True if calculation should proceed, False if too many critical errors
        """
        return self._critical_count < self.max_errors
    
    def get_missing_required(self, data: Dict[str, Any]) -> List[str]:
        """
        Get list of missing required fields.
        
        Args:
            data: Data dictionary to check
            
        Returns:
            List of missing required field names
        """
        missing = []
        for field in self.REQUIRED_FIELDS:
            if data.get(field) is None:
                missing.append(field)
        return missing
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors."""
        return {
            "ticker": self.ticker,
            "total_errors": len(self.errors),
            "critical_errors": self._critical_count,
            "can_proceed": self.can_proceed(),
            "recovered_fields": list(self.recovered_data.keys()),
            "errors": [e.to_dict() for e in self.errors],
        }
    
    def get_warnings(self) -> List[str]:
        """Get list of warning messages for user display."""
        warnings = []
        for error in self.errors:
            if error.severity in [ErrorSeverity.WARNING, ErrorSeverity.INFO]:
                if error.recovered_value:
                    warnings.append(
                        f"{error.task_name}: Using {error.recovery_strategy.value} "
                        f"due to {error.error_type}"
                    )
                else:
                    warnings.append(f"{error.task_name}: {error.error_message}")
        return warnings
    
    def has_degraded_data(self) -> bool:
        """Check if any data is from fallback sources."""
        return len(self.recovered_data) > 0


# ============================================================================
# Recovery Functions
# ============================================================================

def with_error_recovery(
    handler: DCFErrorHandler,
    task_name: str,
    fetch_fn: Callable[[], Any],
    cached_value: Optional[Any] = None,
    default_value: Optional[Any] = None,
) -> DataFetchResult:
    """
    Execute a fetch function with error recovery.
    
    Args:
        handler: DCFErrorHandler instance
        task_name: Name of the task
        fetch_fn: Function to execute
        cached_value: Cached value for fallback
        default_value: Default value for fallback
        
    Returns:
        DataFetchResult with value or error
    """
    try:
        value = fetch_fn()
        if value is not None:
            return DataFetchResult(True, value, "live")
        # None result treated as error
        return handler.handle_fetch_error(
            task_name,
            ValueError(f"{task_name} returned None"),
            cached_value,
            default_value
        )
    except Exception as e:
        return handler.handle_fetch_error(
            task_name, e, cached_value, default_value
        )


async def with_error_recovery_async(
    handler: DCFErrorHandler,
    task_name: str,
    fetch_fn: Callable,
    cached_value: Optional[Any] = None,
    default_value: Optional[Any] = None,
) -> DataFetchResult:
    """
    Async version of with_error_recovery.
    """
    import asyncio
    
    try:
        if asyncio.iscoroutinefunction(fetch_fn):
            value = await fetch_fn()
        else:
            value = fetch_fn()
        
        if value is not None:
            return DataFetchResult(True, value, "live")
        
        return handler.handle_fetch_error(
            task_name,
            ValueError(f"{task_name} returned None"),
            cached_value,
            default_value
        )
    except Exception as e:
        return handler.handle_fetch_error(
            task_name, e, cached_value, default_value
        )


# ============================================================================
# Error Analysis
# ============================================================================

def analyze_calculation_viability(
    handler: DCFErrorHandler,
    data: Dict[str, Any]
) -> Tuple[bool, str, List[str]]:
    """
    Analyze if calculation can proceed with available data.
    
    Args:
        handler: Error handler with recorded errors
        data: Available data dictionary
        
    Returns:
        Tuple of (can_proceed, reason, recommendations)
    """
    missing = handler.get_missing_required(data)
    
    if missing:
        return (
            False,
            f"Missing required data: {', '.join(missing)}",
            [
                f"Check data source for {field}" for field in missing
            ] + ["Verify network connectivity", "Check API credentials"]
        )
    
    if not handler.can_proceed():
        return (
            False,
            f"Too many critical errors ({handler._critical_count})",
            ["Review error log", "Check data sources", "Contact support"]
        )
    
    if handler.has_degraded_data():
        return (
            True,
            "Proceeding with degraded data",
            handler.get_warnings()
        )
    
    return (True, "All data available", [])


