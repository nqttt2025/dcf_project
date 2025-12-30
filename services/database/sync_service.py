"""
Sync Service - Fetch and sync data from external sources
"""
import sys
from pathlib import Path

# Setup project path
if Path('/app').exists():
    project_root = Path('/app')
else:
    project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import time

# Try to import pandas
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None

# Try to import vnstock
HAS_VNSTOCK = False
try:
    from io import StringIO
    import sys as sys_module
    old_stdout = sys_module.stdout
    old_stderr = sys_module.stderr
    sys_module.stdout = StringIO()
    sys_module.stderr = StringIO()
    try:
        from vnstock import Vnstock
        HAS_VNSTOCK = True
    finally:
        sys_module.stdout = old_stdout
        sys_module.stderr = old_stderr
except ImportError:
    HAS_VNSTOCK = False


def sync_financial_data(db: Session, ticker: Optional[str] = None) -> Dict:
    """Sync financial_data from vnstock"""
    if not HAS_VNSTOCK:
        return {
            "success": False,
            "error": "vnstock library not available",
            "processed": 0
        }
    
    try:
        # Get stocks to sync
        if ticker:
            stocks_query = text("SELECT id, ticker FROM stocks WHERE ticker = :ticker AND is_active = TRUE")
            stocks = db.execute(stocks_query, {"ticker": ticker.upper()}).fetchall()
        else:
            stocks_query = text("SELECT id, ticker FROM stocks WHERE is_active = TRUE")
            stocks = db.execute(stocks_query).fetchall()
        
        results = {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        if not stocks:
            return {
                "success": False,
                "error": "No active stocks found in database",
                "processed": 0
            }
        
        for idx, stock in enumerate(stocks):
            # Add delay between requests to avoid rate limit (except for first request)
            if idx > 0:
                time.sleep(2)  # 2 second delay between stocks
            
            try:
                stock_id = stock.id
                stock_ticker = stock.ticker
                
                # Fetch data from vnstock with error handling
                from io import StringIO
                import sys as sys_module
                old_stdout = sys_module.stdout
                old_stderr = sys_module.stderr
                sys_module.stdout = StringIO()
                sys_module.stderr = StringIO()
                
                income_df = None
                balance_df = None
                cashflow_df = None
                
                try:
                    vnstock = Vnstock()
                    stock_obj = vnstock.stock(symbol=stock_ticker.upper(), source="VCI")
                    
                    # Fetch with individual error handling
                    try:
                        income_df = stock_obj.finance.income_statement()
                    except (SystemExit, Exception) as e:
                        error_msg = str(e)
                        if "Rate limit" in error_msg or "quota" in error_msg.lower():
                            raise SystemExit(f"Rate limit exceeded: {error_msg}")
                        income_df = pd.DataFrame() if HAS_PANDAS else None
                    
                    # Small delay between API calls
                    time.sleep(1)
                    
                    try:
                        balance_df = stock_obj.finance.balance_sheet()
                    except (SystemExit, Exception) as e:
                        error_msg = str(e)
                        if "Rate limit" in error_msg or "quota" in error_msg.lower():
                            raise SystemExit(f"Rate limit exceeded: {error_msg}")
                        balance_df = pd.DataFrame() if HAS_PANDAS else None
                    
                    time.sleep(1)
                    
                    try:
                        cashflow_df = stock_obj.finance.cash_flow()
                    except (SystemExit, Exception) as e:
                        error_msg = str(e)
                        if "Rate limit" in error_msg or "quota" in error_msg.lower():
                            raise SystemExit(f"Rate limit exceeded: {error_msg}")
                        cashflow_df = pd.DataFrame() if HAS_PANDAS else None
                        
                except SystemExit as e:
                    # Re-raise SystemExit to be caught by outer handler
                    raise
                finally:
                    sys_module.stdout = old_stdout
                    sys_module.stderr = old_stderr
                
                inserted_count = 0
                
                # Process income statement data
                if income_df is not None:
                    # Check if dataframe is empty (only if pandas is available)
                    if HAS_PANDAS and income_df.empty:
                        pass  # Skip empty dataframe
                    else:
                        for idx, row in income_df.iterrows():
                            try:
                                # Extract period info
                                period_str = str(row.get('Period', '')) if 'Period' in row.index else ''
                                period_date = None
                                period_type = 'quarter'
                                
                                # Try to parse period date
                                if period_str:
                                    # Handle different date formats
                                    try:
                                        if HAS_PANDAS:
                                            period_date = pd.to_datetime(period_str).date()
                                        else:
                                            # Simple date parsing without pandas
                                            period_date = datetime.now().date()
                                    except:
                                        period_date = datetime.now().date()
                                
                                if not period_date:
                                    continue
                                
                                # Extract financial metrics
                                revenue = None
                                net_profit = None
                                operating_profit = None
                                ebit = None
                                ebitda = None
                                
                                def safe_get(row, key):
                                    if key not in row.index:
                                        return None
                                    value = row[key]
                                    if HAS_PANDAS:
                                        return float(value) if pd.notna(value) else None
                                    else:
                                        return float(value) if value is not None else None
                                
                                revenue = safe_get(row, 'Revenue')
                                net_profit = safe_get(row, 'Attributable to parent company')
                                operating_profit = safe_get(row, 'Operating Profit')
                                
                                # Insert or update
                                insert_query = text("""
                                    INSERT INTO financial_data (
                                        stock_id, period_type, period, period_date,
                                        revenue, net_profit, operating_profit, ebit, ebitda,
                                        data_source, created_at, updated_at
                                    ) VALUES (
                                        :stock_id, :period_type, :period, :period_date,
                                        :revenue, :net_profit, :operating_profit, :ebit, :ebitda,
                                        'vnstock', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                                    )
                                    ON CONFLICT (stock_id, period_type, period)
                                    DO UPDATE SET
                                        revenue = EXCLUDED.revenue,
                                        net_profit = EXCLUDED.net_profit,
                                        operating_profit = EXCLUDED.operating_profit,
                                        ebit = EXCLUDED.ebit,
                                        ebitda = EXCLUDED.ebitda,
                                        updated_at = CURRENT_TIMESTAMP
                                """)
                                
                                db.execute(insert_query, {
                                    "stock_id": stock_id,
                                    "period_type": period_type,
                                    "period": period_str,
                                    "period_date": period_date,
                                    "revenue": revenue,
                                    "net_profit": net_profit,
                                    "operating_profit": operating_profit,
                                    "ebit": ebit,
                                    "ebitda": ebitda
                                })
                                inserted_count += 1
                            except Exception as e:
                                continue
                
                db.commit()
                
                results["success"] += 1
                results["details"].append({
                    "ticker": stock_ticker,
                    "status": "success",
                    "records_inserted": inserted_count
                })
                
            except SystemExit as e:
                # Handle vnstock rate limit - stop processing
                db.rollback()
                error_msg = str(e)
                results["failed"] += 1
                results["error"] = f"Rate limit exceeded while processing {stock_ticker}. Please wait and try again later."
                results["details"].append({
                    "ticker": stock_ticker,
                    "status": "error",
                    "error": error_msg
                })
                break
            except Exception as e:
                db.rollback()
                results["failed"] += 1
                results["details"].append({
                    "ticker": stock_ticker,
                    "status": "error",
                    "error": str(e)
                })
            
            results["processed"] += 1
        
        return results
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "processed": 0
        }


def sync_market_data(db: Session, ticker: Optional[str] = None, days: int = 30) -> Dict:
    """Sync market_data from vnstock"""
    if not HAS_VNSTOCK:
        return {
            "success": False,
            "error": "vnstock library not available",
            "processed": 0
        }
    
    try:
        # Get stocks to sync
        if ticker:
            stocks_query = text("SELECT id, ticker FROM stocks WHERE ticker = :ticker AND is_active = TRUE")
            stocks = db.execute(stocks_query, {"ticker": ticker.upper()}).fetchall()
        else:
            stocks_query = text("SELECT id, ticker FROM stocks WHERE is_active = TRUE")
            stocks = db.execute(stocks_query).fetchall()
        
        results = {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        if not stocks:
            return {
                "success": False,
                "error": "No active stocks found in database",
                "processed": 0
            }
        
        for idx, stock in enumerate(stocks):
            # Add delay between requests to avoid rate limit
            if idx > 0:
                time.sleep(2)
            
            try:
                stock_id = stock.id
                stock_ticker = stock.ticker
                
                # Fetch historical price data
                from io import StringIO
                import sys as sys_module
                old_stdout = sys_module.stdout
                old_stderr = sys_module.stderr
                sys_module.stdout = StringIO()
                sys_module.stderr = StringIO()
                
                price_df = None
                
                try:
                    vnstock = Vnstock()
                    stock_obj = vnstock.stock(symbol=stock_ticker.upper(), source="VCI")
                    # Get historical price data
                    end_date = datetime.now().date()
                    start_date = end_date - timedelta(days=days)
                    try:
                        price_df = stock_obj.historical_data(start_date=start_date.strftime('%Y-%m-%d'), 
                                                             end_date=end_date.strftime('%Y-%m-%d'))
                    except (SystemExit, Exception) as e:
                        error_msg = str(e)
                        if "Rate limit" in error_msg or "quota" in error_msg.lower():
                            raise SystemExit(f"Rate limit exceeded: {error_msg}")
                        price_df = pd.DataFrame() if HAS_PANDAS else None
                except SystemExit as e:
                    raise
                finally:
                    sys_module.stdout = old_stdout
                    sys_module.stderr = old_stderr
                
                inserted_count = 0
                
                if price_df is not None and (not HAS_PANDAS or (not price_df.empty and len(price_df) > 0)):
                    for idx, row in price_df.iterrows():
                        try:
                            def safe_get_date(row, key, default_idx):
                                if HAS_PANDAS:
                                    return pd.to_datetime(row.get(key, default_idx)).date() if key in row.index else None
                                else:
                                    value = row.get(key) if key in row.index else None
                                    if value:
                                        try:
                                            return datetime.fromisoformat(str(value)).date()
                                        except:
                                            return datetime.now().date()
                                    return None
                            
                            trade_date = safe_get_date(row, 'time', idx)
                            if not trade_date:
                                continue
                            
                            def safe_get_float(row, key):
                                if key not in row.index:
                                    return None
                                value = row.get(key)
                                if HAS_PANDAS:
                                    return float(value) if pd.notna(value) else None
                                else:
                                    return float(value) if value is not None else None
                            
                            def safe_get_int(row, key):
                                if key not in row.index:
                                    return None
                                value = row.get(key)
                                if HAS_PANDAS:
                                    return int(value) if pd.notna(value) else None
                                else:
                                    return int(value) if value is not None else None
                            
                            open_price = safe_get_float(row, 'open')
                            high_price = safe_get_float(row, 'high')
                            low_price = safe_get_float(row, 'low')
                            close_price = safe_get_float(row, 'close')
                            volume = safe_get_int(row, 'volume')
                            
                            # Insert or update
                            insert_query = text("""
                                INSERT INTO market_data (
                                    stock_id, trade_date,
                                    open_price, high_price, low_price, close_price, adjusted_close,
                                    volume, data_source, created_at, updated_at
                                ) VALUES (
                                    :stock_id, :trade_date,
                                    :open_price, :high_price, :low_price, :close_price, :close_price,
                                    :volume, 'vnstock', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                                )
                                ON CONFLICT (stock_id, trade_date)
                                DO UPDATE SET
                                    open_price = EXCLUDED.open_price,
                                    high_price = EXCLUDED.high_price,
                                    low_price = EXCLUDED.low_price,
                                    close_price = EXCLUDED.close_price,
                                    adjusted_close = EXCLUDED.adjusted_close,
                                    volume = EXCLUDED.volume,
                                    updated_at = CURRENT_TIMESTAMP
                            """)
                            
                            db.execute(insert_query, {
                                "stock_id": stock_id,
                                "trade_date": trade_date,
                                "open_price": open_price,
                                "high_price": high_price,
                                "low_price": low_price,
                                "close_price": close_price,
                                "volume": volume
                            })
                            inserted_count += 1
                        except Exception as e:
                            continue
                
                db.commit()
                
                results["success"] += 1
                results["details"].append({
                    "ticker": stock_ticker,
                    "status": "success",
                    "records_inserted": inserted_count
                })
                
            except SystemExit as e:
                # Handle vnstock rate limit - stop processing
                db.rollback()
                error_msg = str(e)
                results["failed"] += 1
                results["error"] = f"Rate limit exceeded while processing {stock_ticker}. Please wait and try again later."
                results["details"].append({
                    "ticker": stock_ticker,
                    "status": "error",
                    "error": error_msg
                })
                break
            except Exception as e:
                db.rollback()
                results["failed"] += 1
                results["details"].append({
                    "ticker": stock_ticker,
                    "status": "error",
                    "error": str(e)
                })
            
            results["processed"] += 1
        
        return results
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "processed": 0
        }


def sync_shares_outstanding(db: Session, ticker: Optional[str] = None) -> Dict:
    """Sync shares_outstanding from vnstock"""
    if not HAS_VNSTOCK:
        return {
            "success": False,
            "error": "vnstock library not available",
            "processed": 0
        }
    
    try:
        # Get stocks to sync
        if ticker:
            stocks_query = text("SELECT id, ticker FROM stocks WHERE ticker = :ticker AND is_active = TRUE")
            stocks = db.execute(stocks_query, {"ticker": ticker.upper()}).fetchall()
        else:
            stocks_query = text("SELECT id, ticker FROM stocks WHERE is_active = TRUE")
            stocks = db.execute(stocks_query).fetchall()
        
        results = {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        if not stocks:
            return {
                "success": False,
                "error": "No active stocks found in database",
                "processed": 0
            }
        
        for idx, stock in enumerate(stocks):
            # Add delay between requests
            if idx > 0:
                time.sleep(2)
            
            try:
                stock_id = stock.id
                stock_ticker = stock.ticker
                
                # Fetch data from vnstock
                from io import StringIO
                import sys as sys_module
                old_stdout = sys_module.stdout
                old_stderr = sys_module.stderr
                sys_module.stdout = StringIO()
                sys_module.stderr = StringIO()
                
                balance_df = None
                
                try:
                    vnstock = Vnstock()
                    stock_obj = vnstock.stock(symbol=stock_ticker.upper(), source="VCI")
                    try:
                        balance_df = stock_obj.finance.balance_sheet()
                    except (SystemExit, Exception) as e:
                        error_msg = str(e)
                        if "Rate limit" in error_msg or "quota" in error_msg.lower():
                            raise SystemExit(f"Rate limit exceeded: {error_msg}")
                        balance_df = pd.DataFrame() if HAS_PANDAS else None
                except SystemExit as e:
                    raise
                finally:
                    sys_module.stdout = old_stdout
                    sys_module.stderr = old_stderr
                
                inserted_count = 0
                
                if balance_df is not None and (not HAS_PANDAS or not balance_df.empty):
                    # Get latest balance sheet row
                    latest_row = balance_df.iloc[0]
                    
                    # Try to get shares outstanding
                    shares_outstanding = None
                    par_value = 10000  # Default par value
                    calculation_method = 'direct'
                    source_column = None
                    
                    # Check various column names
                    def safe_get_value(row, key):
                        if key not in row.index:
                            return None
                        value = row[key]
                        if HAS_PANDAS:
                            return float(value) if pd.notna(value) else None
                        else:
                            return float(value) if value is not None else None
                    
                    if 'Common shares' in latest_row.index:
                        capital = safe_get_value(latest_row, 'Common shares')
                        if capital and capital > 0:
                            shares_outstanding = capital / par_value
                            calculation_method = 'charter_capital'
                            source_column = 'Common shares'
                    elif 'Paid-in capital (Bn. VND)' in latest_row.index:
                        capital = safe_get_value(latest_row, 'Paid-in capital (Bn. VND)')
                        if capital and capital > 0:
                            # Note: Despite the name "(Bn. VND)", the value is actually in VND (not billions)
                            # So we only divide by par_value, not multiply by 1,000,000
                            shares_outstanding = capital / par_value
                            
                            # Validation using shares_validator
                            try:
                                from src.utils.shares_validator import validate_shares
                                validate_shares(shares_outstanding, stock_ticker, raise_error=True)
                            except ImportError:
                                # Fallback validation if validator not available
                                if shares_outstanding > 1e12:  # More than 1 trillion shares
                                    error_msg = (
                                        f"Shares outstanding too large for {stock_ticker}: {shares_outstanding:,.0f}. "
                                        f"This is likely a unit error. Capital value: {capital:,.0f} VND, "
                                        f"par_value: {par_value}. Please check the calculation logic."
                                    )
                                    raise ValueError(error_msg)
                            
                            calculation_method = 'paid_in_capital'
                            source_column = 'Paid-in capital (Bn. VND)'
                    
                    if shares_outstanding and shares_outstanding > 0:
                        # Final validation before saving to database
                        try:
                            from src.utils.shares_validator import validate_shares
                            validate_shares(shares_outstanding, stock_ticker, raise_error=True)
                        except ImportError:
                            # Fallback validation if validator not available
                            if shares_outstanding > 1e12:  # More than 1 trillion shares
                                error_msg = (
                                    f"Shares outstanding validation failed for {stock_ticker}: {shares_outstanding:,.0f}. "
                                    f"This value is unreasonably large and likely incorrect."
                                )
                                raise ValueError(error_msg)
                        period_date = datetime.now().date()
                        
                        insert_query = text("""
                            INSERT INTO shares_outstanding (
                                stock_id, period_date, shares_outstanding, par_value,
                                calculation_method, source_column, data_source,
                                created_at, updated_at
                            ) VALUES (
                                :stock_id, :period_date, :shares_outstanding, :par_value,
                                :calculation_method, :source_column, 'vnstock',
                                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                            )
                            ON CONFLICT (stock_id, period_date)
                            DO UPDATE SET
                                shares_outstanding = EXCLUDED.shares_outstanding,
                                par_value = EXCLUDED.par_value,
                                calculation_method = EXCLUDED.calculation_method,
                                source_column = EXCLUDED.source_column,
                                updated_at = CURRENT_TIMESTAMP
                        """)
                        
                        db.execute(insert_query, {
                            "stock_id": stock_id,
                            "period_date": period_date,
                            "shares_outstanding": int(shares_outstanding),
                            "par_value": par_value,
                            "calculation_method": calculation_method,
                            "source_column": source_column
                        })
                        inserted_count = 1
                        db.commit()
                
                results["success"] += 1
                results["details"].append({
                    "ticker": stock_ticker,
                    "status": "success",
                    "records_inserted": inserted_count
                })
                
            except SystemExit as e:
                # Handle vnstock rate limit - stop processing
                db.rollback()
                error_msg = str(e)
                results["failed"] += 1
                results["error"] = f"Rate limit exceeded while processing {stock_ticker}. Please wait and try again later."
                results["details"].append({
                    "ticker": stock_ticker,
                    "status": "error",
                    "error": error_msg
                })
                break
            except Exception as e:
                db.rollback()
                results["failed"] += 1
                results["details"].append({
                    "ticker": stock_ticker,
                    "status": "error",
                    "error": str(e)
                })
            
            results["processed"] += 1
        
        return results
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "processed": 0
        }

