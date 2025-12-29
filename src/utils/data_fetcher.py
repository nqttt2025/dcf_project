"""
Data Fetcher with Priority: Database → Redis → File → vnstock API
"""
from typing import Optional, Dict, Any, Callable
from ..utils.logger import get_logger
from ..utils.database_client import check_database_connection, get_db
from ..utils.redis_client import get_redis_client
from ..utils.cache_manager import get_cache_manager
from sqlalchemy import text

logger = get_logger()
redis_client = get_redis_client()
cache_manager = get_cache_manager()


def get_financial_ttm(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Get financial TTM data with priority: Database → Redis → File → vnstock API
    
    Args:
        ticker: Stock ticker
        
    Returns:
        Dict with ttm_ocf, ttm_capex, ttm_fcf, or None
    """
    ticker = ticker.upper()
    
    # 1. Try Database first
    if check_database_connection():
        try:
            with get_db() as db:
                # Query financial_data for TTM calculation
                # This is a simplified query - actual implementation depends on schema
                result = db.execute(text("""
                    SELECT 
                        SUM(operating_cash_flow) FILTER (
                            WHERE period_type = 'quarter' 
                            AND period_date >= CURRENT_DATE - INTERVAL '1 year'
                        ) as ttm_ocf,
                        SUM(capital_expenditures) FILTER (
                            WHERE period_type = 'quarter' 
                            AND period_date >= CURRENT_DATE - INTERVAL '1 year'
                        ) as ttm_capex
                    FROM financial_data fd
                    JOIN stocks s ON fd.stock_id = s.id
                    WHERE s.ticker = :ticker
                """), {"ticker": ticker})
                
                row = result.fetchone()
                if row and row[0] is not None:
                    ttm_ocf = float(row[0]) if row[0] else 0
                    ttm_capex = float(row[1]) if row[1] else 0
                    ttm_fcf = ttm_ocf - ttm_capex
                    
                    data = {
                        'ttm_ocf': ttm_ocf,
                        'ttm_capex': ttm_capex,
                        'ttm_fcf': ttm_fcf,
                        'source': 'database'
                    }
                    
                    # Cache to Redis
                    redis_client.cache_financial_ttm(ticker, data)
                    logger.info(f"Got financial TTM from database for {ticker}")
                    return data
        except Exception as e:
            logger.debug(f"Database query failed for {ticker}: {e}")
    
    # 2. Try Redis
    data = redis_client.get_financial_ttm(ticker)
    if data:
        logger.info(f"Got financial TTM from Redis for {ticker}")
        return data
    
    # 3. Try File cache
    # Note: File cache format is different, need to reconstruct TTM
    # For now, skip file cache for TTM (requires aggregation)
    
    # 4. Return None - caller should fetch from vnstock API
    return None


def get_market_data(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Get market data with priority: Database → Redis → File → vnstock API
    
    Args:
        ticker: Stock ticker
        
    Returns:
        Dict with current_price, market_cap, pe_ratio, etc., or None
    """
    ticker = ticker.upper()
    
    # 1. Try Database first
    if check_database_connection():
        try:
            with get_db() as db:
                result = db.execute(text("""
                    SELECT 
                        md.close_price,
                        md.market_cap,
                        md.pe_ratio,
                        md.pb_ratio,
                        md.ps_ratio,
                        md.volume,
                        md.trade_date
                    FROM market_data md
                    JOIN stocks s ON md.stock_id = s.id
                    WHERE s.ticker = :ticker
                    ORDER BY md.trade_date DESC
                    LIMIT 1
                """), {"ticker": ticker})
                
                row = result.fetchone()
                if row:
                    data = {
                        'current_price': float(row[0]) if row[0] else None,
                        'market_cap': int(row[1]) if row[1] else None,
                        'pe_ratio': float(row[2]) if row[2] else None,
                        'pb_ratio': float(row[3]) if row[3] else None,
                        'ps_ratio': float(row[4]) if row[4] else None,
                        'volume': int(row[5]) if row[5] else None,
                        'trade_date': str(row[6]) if row[6] else None,
                        'source': 'database'
                    }
                    
                    # Cache to Redis
                    redis_client.cache_market_data(ticker, data)
                    logger.info(f"Got market data from database for {ticker}")
                    return data
        except Exception as e:
            logger.debug(f"Database query failed for {ticker}: {e}")
    
    # 2. Try Redis
    data = redis_client.get_market_data(ticker)
    if data:
        logger.info(f"Got market data from Redis for {ticker}")
        return data
    
    # 3. Try File cache
    price = cache_manager.get_with_timestamp(ticker, "price")
    market_cap = cache_manager.get_with_timestamp(ticker, "market_cap")
    if price:
        data = {
            'current_price': float(price),
            'market_cap': float(market_cap) if market_cap else None,
            'source': 'file_cache'
        }
        # Cache to Redis
        redis_client.cache_market_data(ticker, data)
        logger.info(f"Got market data from file cache for {ticker}")
        return data
    
    # 4. Return None - caller should fetch from vnstock API
    return None


def get_shares_outstanding(ticker: str) -> Optional[float]:
    """
    Get shares outstanding with priority: Database → Redis → File → vnstock API
    
    Args:
        ticker: Stock ticker
        
    Returns:
        Shares outstanding as float, or None
    """
    ticker = ticker.upper()
    
    # 1. Try Database first
    if check_database_connection():
        try:
            with get_db() as db:
                result = db.execute(text("""
                    SELECT 
                        so.shares_outstanding,
                        so.par_value,
                        so.calculation_method
                    FROM shares_outstanding so
                    JOIN stocks s ON so.stock_id = s.id
                    WHERE s.ticker = :ticker
                    ORDER BY so.period_date DESC
                    LIMIT 1
                """), {"ticker": ticker})
                
                row = result.fetchone()
                if row and row[0]:
                    shares = float(row[0])
                    par_value = float(row[1]) if row[1] else 10000
                    
                    # Cache to Redis
                    redis_client.cache_shares(
                        ticker, 
                        shares, 
                        par_value=par_value,
                        calculation_method=str(row[2]) if row[2] else "from_database"
                    )
                    logger.info(f"Got shares from database for {ticker}: {shares:,.0f}")
                    return shares
        except Exception as e:
            logger.debug(f"Database query failed for {ticker}: {e}")
    
    # 2. Try Redis
    data = redis_client.get_shares(ticker)
    if data:
        shares = data.get('shares_outstanding')
        if shares:
            logger.info(f"Got shares from Redis for {ticker}: {shares:,.0f}")
            return float(shares)
    
    # 3. Try File cache
    shares = cache_manager.get_with_timestamp(ticker, "shares")
    if shares:
        # Cache to Redis
        redis_client.cache_shares(ticker, float(shares))
        logger.info(f"Got shares from file cache for {ticker}: {shares:,.0f}")
        return float(shares)
    
    # 4. Return None - caller should fetch from vnstock API
    return None


def save_to_all_caches(ticker: str, data_type: str, value: Any, 
                       db_save_func: Optional[Callable] = None,
                       additional_data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Save data to all caches: Database → Redis → File
    
    Args:
        ticker: Stock ticker
        data_type: Type of data ('financial_ttm', 'market_data', 'shares', etc.)
        value: Value to cache
        db_save_func: Optional function to save to database
        additional_data: Additional data for caching
        
    Returns:
        True if saved successfully
    """
    ticker = ticker.upper()
    saved = False
    
    # 1. Save to Database
    if db_save_func and check_database_connection():
        try:
            db_save_func(ticker, value, additional_data or {})
            saved = True
        except Exception as e:
            logger.debug(f"Failed to save to database: {e}")
    
    # 2. Save to Redis
    try:
        if data_type == 'financial_ttm':
            redis_client.cache_financial_ttm(ticker, value)
        elif data_type == 'market_data':
            redis_client.cache_market_data(ticker, value)
        elif data_type == 'shares':
            redis_client.cache_shares(
                ticker, 
                value,
                par_value=additional_data.get('par_value', 10000) if additional_data else 10000
            )
        saved = True
    except Exception as e:
        logger.debug(f"Failed to save to Redis: {e}")
    
    # 3. Save to File cache
    try:
        cache_manager.set_with_timestamp(ticker, data_type, value)
        saved = True
    except Exception as e:
        logger.debug(f"Failed to save to file cache: {e}")
    
    return saved

