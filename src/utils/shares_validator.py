"""
Shares Outstanding Validator

Provides validation and cross-validation functions for shares outstanding data.
Supports multiple sources and discrepancy detection.

Example:
    from src.utils.shares_validator import SharesValidator
    
    validator = SharesValidator("FPT")
    validator.add_source("balance_sheet", 1703507121)
    validator.add_source("market_cap_calc", 1700000000)
    
    result = validator.validate()
    print(f"Best estimate: {result.value}")
    print(f"Confidence: {result.confidence}")
"""

import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .logger import get_logger

logger = get_logger()


class ValidationConfidence(Enum):
    """Confidence level for validation result."""
    HIGH = "high"        # Multiple sources agree
    MEDIUM = "medium"    # Single source or minor discrepancy
    LOW = "low"          # Significant discrepancy or fallback
    UNKNOWN = "unknown"  # No valid sources


@dataclass
class ValidationResult:
    """Result of shares validation."""
    value: Optional[float]  # Best estimate of shares outstanding
    confidence: ValidationConfidence
    sources_used: List[str]
    discrepancies: List[str]
    warnings: List[str]
    
    @property
    def is_valid(self) -> bool:
        return self.value is not None and self.value > 0


@dataclass
class SharesSource:
    """A source for shares outstanding data."""
    name: str
    value: float
    priority: int = 1  # Higher = more trusted
    metadata: Dict = field(default_factory=dict)


class SharesValidator:
    """
    Cross-validates shares outstanding from multiple sources.
    
    Sources (in order of priority):
    1. Database (synced data) - most reliable
    2. Balance sheet (charter capital / par value)
    3. Market cap calculation (market_cap / price)
    4. Company profile / API response
    """
    
    # Maximum allowed deviation before flagging as discrepancy
    MAX_DEVIATION_PERCENT = 10.0
    
    # Absolute limits for validation
    MIN_SHARES = 1_000_000  # 1 million shares minimum
    MAX_SHARES = 100_000_000_000  # 100 billion shares maximum
    WARNING_THRESHOLD = 50_000_000_000  # 50 billion - warn if larger
    
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.sources: List[SharesSource] = []
        self._validated = False
        self._result: Optional[ValidationResult] = None
    
    def add_source(
        self,
        name: str,
        value: float,
        priority: int = 1,
        **metadata
    ) -> "SharesValidator":
        """
        Add a source for shares outstanding.
        
        Args:
            name: Source identifier (e.g., "balance_sheet", "market_cap_calc")
            value: Shares outstanding value from this source
            priority: Trust level (higher = more trusted)
            **metadata: Additional info about this source
            
        Returns:
            self for chaining
        """
        if value is None or value <= 0:
            logger.debug(f"Skipping invalid source {name} for {self.ticker}: {value}")
            return self
        
        source = SharesSource(
            name=name,
            value=float(value),
            priority=priority,
            metadata=metadata or {}
        )
        self.sources.append(source)
        self._validated = False
        return self
    
    def add_from_balance_sheet(
        self,
        charter_capital: float,
        par_value: float = 10000
    ) -> "SharesValidator":
        """Add source from balance sheet calculation."""
        if charter_capital and par_value > 0:
            shares = charter_capital / par_value
            self.add_source(
                "balance_sheet",
                shares,
                priority=3,
                charter_capital=charter_capital,
                par_value=par_value
            )
        return self
    
    def add_from_market_cap(
        self,
        market_cap: float,
        price: float
    ) -> "SharesValidator":
        """Add source from market cap / price calculation."""
        if market_cap and price > 0:
            shares = market_cap / price
            self.add_source(
                "market_cap_calc",
                shares,
                priority=2,
                market_cap=market_cap,
                price=price
            )
        return self
    
    def add_from_database(self, shares: float) -> "SharesValidator":
        """Add source from database (highest priority)."""
        if shares:
            self.add_source("database", shares, priority=5)
        return self
    
    def add_from_api(self, shares: float, api_name: str = "vnstock") -> "SharesValidator":
        """Add source from API response."""
        if shares:
            self.add_source(f"api_{api_name}", shares, priority=1)
        return self
    
    def validate(self) -> ValidationResult:
        """
        Validate shares from all sources.
        
        Returns:
            ValidationResult with best estimate and confidence level
        """
        if self._validated and self._result:
            return self._result
        
        discrepancies = []
        warnings = []
        
        # Filter valid sources
        valid_sources = [s for s in self.sources if self._is_value_valid(s.value)]
        
        if not valid_sources:
            self._result = ValidationResult(
                value=None,
                confidence=ValidationConfidence.UNKNOWN,
                sources_used=[],
                discrepancies=["No valid sources available"],
                warnings=[]
            )
            self._validated = True
            return self._result
        
        # Sort by priority (highest first)
        valid_sources.sort(key=lambda s: s.priority, reverse=True)
        
        # Get all values for analysis
        values = [s.value for s in valid_sources]
        
        # Calculate statistics
        if len(values) >= 2:
            median_value = statistics.median(values)
            
            # Check for discrepancies
            for source in valid_sources:
                deviation = abs(source.value - median_value) / median_value * 100
                if deviation > self.MAX_DEVIATION_PERCENT:
                    discrepancy_msg = (
                        f"Source '{source.name}' ({source.value:,.0f}) "
                        f"deviates {deviation:.1f}% from median ({median_value:,.0f})"
                    )
                    discrepancies.append(discrepancy_msg)
                    logger.warning(f"{self.ticker}: {discrepancy_msg}")
        else:
            median_value = values[0]
        
        # Determine best value
        # Use highest priority source if no major discrepancies, otherwise use median
        if discrepancies:
            best_value = median_value
            logger.info(f"{self.ticker}: Using median value due to discrepancies: {best_value:,.0f}")
        else:
            best_value = valid_sources[0].value  # Highest priority
        
        # Additional validation
        if best_value > self.WARNING_THRESHOLD:
            warnings.append(
                f"Shares outstanding ({best_value:,.0f}) exceeds {self.WARNING_THRESHOLD:,.0f}"
            )
        
        # Determine confidence
        if len(valid_sources) >= 3 and not discrepancies:
            confidence = ValidationConfidence.HIGH
        elif len(valid_sources) >= 2 and len(discrepancies) <= 1:
            confidence = ValidationConfidence.MEDIUM
        elif len(valid_sources) == 1:
            confidence = ValidationConfidence.MEDIUM
            warnings.append("Only single source available")
        else:
            confidence = ValidationConfidence.LOW
        
        self._result = ValidationResult(
            value=best_value,
            confidence=confidence,
            sources_used=[s.name for s in valid_sources],
            discrepancies=discrepancies,
            warnings=warnings
        )
        self._validated = True
        
        # Log result
        logger.info(
            f"{self.ticker} shares validation: {best_value:,.0f} "
            f"(confidence: {confidence.value}, sources: {len(valid_sources)})"
        )
        if discrepancies:
            logger.warning(f"{self.ticker} discrepancies: {discrepancies}")
        
        return self._result
    
    def _is_value_valid(self, value: float) -> bool:
        """Check if a value is within valid range."""
        if value is None:
            return False
        if value <= 0:
            return False
        if value > self.MAX_SHARES:
            logger.warning(f"{self.ticker}: Rejecting value {value:,.0f} (exceeds max)")
            return False
        if value < self.MIN_SHARES:
            logger.warning(f"{self.ticker}: Rejecting value {value:,.0f} (below min)")
            return False
        return True
    
    def get_discrepancy_report(self) -> str:
        """Get detailed discrepancy report."""
        if not self._validated:
            self.validate()
        
        lines = [f"=== Shares Validation Report: {self.ticker} ==="]
        lines.append(f"Sources: {len(self.sources)}")
        
        for source in self.sources:
            lines.append(f"  - {source.name}: {source.value:,.0f} (priority: {source.priority})")
        
        if self._result:
            lines.append(f"Best Estimate: {self._result.value:,.0f}")
            lines.append(f"Confidence: {self._result.confidence.value}")
            
            if self._result.discrepancies:
                lines.append("Discrepancies:")
                for d in self._result.discrepancies:
                    lines.append(f"  ⚠ {d}")
            
            if self._result.warnings:
                lines.append("Warnings:")
                for w in self._result.warnings:
                    lines.append(f"  ℹ {w}")
        
        return "\n".join(lines)


# ============================================================================
# Legacy Functions (for backward compatibility)
# ============================================================================

def validate_shares(shares: float, ticker: str, raise_error: bool = True) -> bool:
    """
    Validate shares outstanding value (legacy function).
    
    Args:
        shares: Shares outstanding value to validate
        ticker: Stock ticker for logging
        raise_error: If True, raise ValueError on validation failure
        
    Returns:
        True if valid, False if invalid (only if raise_error=False)
        
    Raises:
        ValueError: If shares is invalid and raise_error=True
    """
    if shares is None:
        error_msg = f"Shares outstanding is None for {ticker}"
        logger.error(error_msg)
        if raise_error:
            raise ValueError(error_msg)
        return False
    
    if shares <= 0:
        error_msg = f"Shares outstanding must be positive for {ticker}: {shares}"
        logger.error(error_msg)
        if raise_error:
            raise ValueError(error_msg)
        return False
    
    # Check for suspiciously large shares (likely unit error)
    if shares > 1e12:  # More than 1 trillion shares
        error_msg = (
            f"Shares outstanding validation failed for {ticker}: {shares:,.0f}. "
            f"This value is unreasonably large (>1 trillion shares) and likely indicates a unit error."
        )
        logger.error(error_msg)
        if raise_error:
            raise ValueError(error_msg)
        return False
    
    # Warning for large but potentially valid shares
    if shares > 5e10:  # More than 50 billion shares
        logger.warning(
            f"Shares outstanding seems large for {ticker}: {shares:,.0f}. "
            f"Please verify this value is correct."
        )
    
    return True


def cross_validate_shares_with_market_cap(
    shares: float,
    price: float,
    market_cap: float,
    ticker: str,
    tolerance: float = 0.15  # 15% tolerance
) -> Tuple[bool, Optional[str]]:
    """
    Cross-validate shares using market cap (legacy function).
    """
    if not all([shares, price, market_cap]):
        return True, None
    
    try:
        calculated_market_cap = shares * price
        
        if market_cap == 0:
            logger.warning(f"Market cap is zero for {ticker}, skipping cross-validation")
            return True, None
        
        diff = abs(calculated_market_cap - market_cap) / market_cap
        
        if diff > tolerance:
            error_msg = (
                f"Shares cross-validation failed for {ticker}: "
                f"calculated market cap ({calculated_market_cap:,.0f}) differs from "
                f"source market cap ({market_cap:,.0f}) by {diff*100:.1f}%."
            )
            logger.error(error_msg)
            return False, error_msg
        
        return True, None
        
    except Exception as e:
        logger.warning(f"Error in cross-validation for {ticker}: {e}")
        return True, None


def validate_and_cross_check(
    shares: float,
    ticker: str,
    price: Optional[float] = None,
    market_cap: Optional[float] = None,
    raise_error: bool = True
) -> bool:
    """
    Comprehensive validation (legacy function).
    """
    if not validate_shares(shares, ticker, raise_error=raise_error):
        return False
    
    if price and market_cap:
        is_valid, error_msg = cross_validate_shares_with_market_cap(
            shares, price, market_cap, ticker
        )
        if not is_valid and raise_error:
            raise ValueError(error_msg)
        return is_valid
    
    return True


def validate_shares_from_sources(
    ticker: str,
    balance_sheet_shares: Optional[float] = None,
    market_cap: Optional[float] = None,
    price: Optional[float] = None,
    database_shares: Optional[float] = None,
    api_shares: Optional[float] = None,
) -> ValidationResult:
    """
    Convenience function to validate shares from multiple sources.
    
    Args:
        ticker: Stock ticker
        balance_sheet_shares: Shares from balance sheet
        market_cap: Market capitalization
        price: Current stock price
        database_shares: Shares from database
        api_shares: Shares from API
        
    Returns:
        ValidationResult with best estimate
    """
    validator = SharesValidator(ticker)
    
    if database_shares:
        validator.add_from_database(database_shares)
    
    if balance_sheet_shares:
        validator.add_source("balance_sheet", balance_sheet_shares, priority=3)
    
    if market_cap and price:
        validator.add_from_market_cap(market_cap, price)
    
    if api_shares:
        validator.add_from_api(api_shares)
    
    return validator.validate()
