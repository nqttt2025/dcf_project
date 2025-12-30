"""
Shares Outstanding Validator
Provides validation and cross-validation functions for shares outstanding data
"""
from typing import Optional, Tuple
from ..utils.logger import get_logger

logger = get_logger()


def validate_shares(shares: float, ticker: str, raise_error: bool = True) -> bool:
    """
    Validate shares outstanding value
    
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
            f"This value is unreasonably large (>1 trillion shares) and likely indicates a unit error. "
            f"Please check the shares calculation logic."
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
    Cross-validate shares using market cap
    
    Formula: shares * price ≈ market_cap
    
    Args:
        shares: Shares outstanding
        price: Current stock price
        market_cap: Market capitalization from source
        ticker: Stock ticker for logging
        tolerance: Maximum allowed difference (default 15%)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not all([shares, price, market_cap]):
        return True, None  # Skip validation if any value is missing
    
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
                f"source market cap ({market_cap:,.0f}) by {diff*100:.1f}%. "
                f"Shares: {shares:,.0f}, Price: {price:,.2f}"
            )
            logger.error(error_msg)
            return False, error_msg
        
        logger.debug(
            f"Shares cross-validation passed for {ticker}: "
            f"difference {diff*100:.2f}%"
        )
        return True, None
        
    except Exception as e:
        logger.warning(f"Error in cross-validation for {ticker}: {e}")
        return True, None  # Don't fail on validation errors


def validate_and_cross_check(
    shares: float,
    ticker: str,
    price: Optional[float] = None,
    market_cap: Optional[float] = None,
    raise_error: bool = True
) -> bool:
    """
    Comprehensive validation: basic validation + cross-validation with market cap
    
    Args:
        shares: Shares outstanding
        ticker: Stock ticker
        price: Current stock price (optional)
        market_cap: Market capitalization (optional)
        raise_error: If True, raise ValueError on validation failure
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If validation fails and raise_error=True
    """
    # Basic validation
    if not validate_shares(shares, ticker, raise_error=raise_error):
        return False
    
    # Cross-validation if price and market_cap are available
    if price and market_cap:
        is_valid, error_msg = cross_validate_shares_with_market_cap(
            shares, price, market_cap, ticker
        )
        if not is_valid and raise_error:
            raise ValueError(error_msg)
        return is_valid
    
    return True

