"""
Data Fetcher - Fetch and sync data from external sources (vnstock)

This module contains functions to fetch stock data from vnstock API and save to database.
Used directly by sync-service for all data synchronization operations.
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
from datetime import datetime, timedelta, date
import time
import logging

# Setup logger
try:
    from src.utils.service_logger import setup_service_logger
    logger = setup_service_logger('sync-service', level=logging.INFO)
except Exception:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

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
                
                # Helper function to safely get values with multiple possible column names
                def safe_get_value(row, *keys):
                    """Try to get value from row using multiple possible column names"""
                    for key in keys:
                        if key in row.index:
                            value = row[key]
                            if HAS_PANDAS:
                                if pd.notna(value):
                                    try:
                                        return float(value)
                                    except (ValueError, TypeError):
                                        pass
                            elif value is not None:
                                try:
                                    return float(value)
                                except (ValueError, TypeError):
                                    pass
                    return None
                
                # Helper to extract period info from vnstock format
                def extract_period_info(row):
                    """Extract period type, period string and date from vnstock row"""
                    year_report = row.get('yearReport') if 'yearReport' in row.index else None
                    length_report = row.get('lengthReport') if 'lengthReport' in row.index else None
                    
                    if year_report is None:
                        return None, None, None
                    
                    # Determine period type
                    period_type = 'annual'
                    if length_report and str(length_report) in ['1', '2', '3', '4', 'Q1', 'Q2', 'Q3', 'Q4']:
                        period_type = 'quarter'
                    
                    # Build period string (e.g., "2024-Q1" or "2024")
                    if period_type == 'quarter':
                        quarter = str(length_report).replace('Q', '')
                        period_str = f"{int(year_report)}-Q{quarter}"
                        # Set period date to end of quarter
                        quarter_month = {1: 3, 2: 6, 3: 9, 4: 12}.get(int(quarter), 12)
                        period_date = date(int(year_report), quarter_month, 28)
                    else:
                        period_str = str(int(year_report))
                        period_date = date(int(year_report), 12, 31)
                    
                    return period_type, period_str, period_date
                
                # Store financial data by period for merging income and cashflow
                financial_records = {}
                
                # Process income statement data
                if income_df is not None:
                    if not (HAS_PANDAS and income_df.empty):
                        for idx, row in income_df.iterrows():
                            try:
                                period_type, period_str, period_date = extract_period_info(row)
                                if not period_str:
                                    continue
                                
                                # Extract financial metrics with multiple possible column names
                                revenue = safe_get_value(row, 
                                    'Revenue (Bn. VND)', 'Revenue', 'Net Sales', 'Net Revenue')
                                net_profit = safe_get_value(row, 
                                    'Attributable to parent company', 'Attributable to parent company (Bn. VND)',
                                    'Net Profit For the Year', 'Net Income')
                                operating_profit = safe_get_value(row, 
                                    'Operating Profit/Loss', 'Operating Profit', 'Operating Income')
                                
                                key = (period_type, period_str)
                                if key not in financial_records:
                                    financial_records[key] = {
                                        'period_type': period_type,
                                        'period': period_str,
                                        'period_date': period_date
                                    }
                                
                                financial_records[key].update({
                                    'revenue': revenue,
                                    'net_profit': net_profit,
                                    'operating_profit': operating_profit
                                })
                            except Exception as e:
                                continue
                
                # Process cash flow data
                if cashflow_df is not None:
                    if not (HAS_PANDAS and cashflow_df.empty):
                        for idx, row in cashflow_df.iterrows():
                            try:
                                period_type, period_str, period_date = extract_period_info(row)
                                if not period_str:
                                    continue
                                
                                # Extract cash flow metrics
                                operating_cash_flow = safe_get_value(row,
                                    'Net cash inflows/outflows from operating activities',
                                    'Net Cash Flows from Operating Activities',
                                    'Cash flow from operating activities')
                                capital_expenditures = safe_get_value(row,
                                    'Purchase of fixed assets',
                                    'Payments for purchase of fixed assets',
                                    'Capital Expenditure')
                                # Capital expenditures is usually negative, we store as positive
                                if capital_expenditures is not None and capital_expenditures < 0:
                                    capital_expenditures = abs(capital_expenditures)
                                
                                key = (period_type, period_str)
                                if key not in financial_records:
                                    financial_records[key] = {
                                        'period_type': period_type,
                                        'period': period_str,
                                        'period_date': period_date
                                    }
                                
                                financial_records[key].update({
                                    'operating_cash_flow': operating_cash_flow,
                                    'capital_expenditures': capital_expenditures
                                })
                                
                                # Calculate free cash flow if we have both
                                if operating_cash_flow is not None and capital_expenditures is not None:
                                    financial_records[key]['free_cash_flow'] = operating_cash_flow - capital_expenditures
                            except Exception as e:
                                continue
                
                # Insert all records into database
                for key, data in financial_records.items():
                    try:
                        insert_query = text("""
                            INSERT INTO financial_data (
                                stock_id, period_type, period, period_date,
                                revenue, net_profit, operating_profit,
                                operating_cash_flow, capital_expenditures, free_cash_flow,
                                data_source, created_at, updated_at
                            ) VALUES (
                                :stock_id, :period_type, :period, :period_date,
                                :revenue, :net_profit, :operating_profit,
                                :operating_cash_flow, :capital_expenditures, :free_cash_flow,
                                'vnstock', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                            )
                            ON CONFLICT (stock_id, period_type, period)
                            DO UPDATE SET
                                revenue = COALESCE(EXCLUDED.revenue, financial_data.revenue),
                                net_profit = COALESCE(EXCLUDED.net_profit, financial_data.net_profit),
                                operating_profit = COALESCE(EXCLUDED.operating_profit, financial_data.operating_profit),
                                operating_cash_flow = COALESCE(EXCLUDED.operating_cash_flow, financial_data.operating_cash_flow),
                                capital_expenditures = COALESCE(EXCLUDED.capital_expenditures, financial_data.capital_expenditures),
                                free_cash_flow = COALESCE(EXCLUDED.free_cash_flow, financial_data.free_cash_flow),
                                updated_at = CURRENT_TIMESTAMP
                        """)
                        
                        db.execute(insert_query, {
                            "stock_id": stock_id,
                            "period_type": data.get('period_type'),
                            "period": data.get('period'),
                            "period_date": data.get('period_date'),
                            "revenue": data.get('revenue'),
                            "net_profit": data.get('net_profit'),
                            "operating_profit": data.get('operating_profit'),
                            "operating_cash_flow": data.get('operating_cash_flow'),
                            "capital_expenditures": data.get('capital_expenditures'),
                            "free_cash_flow": data.get('free_cash_flow')
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
    """Sync market_data from vnstock with detailed logging"""
    logger.info(f"Starting market_data sync: ticker={ticker}, days={days}")
    
    if not HAS_VNSTOCK:
        logger.error("vnstock library not available")
        return {
            "success": False,
            "error": "vnstock library not available",
            "processed": 0
        }
    
    try:
        # Get stocks to sync
        if ticker:
            logger.info(f"Fetching market data for specific ticker: {ticker}")
            stocks_query = text("SELECT id, ticker FROM stocks WHERE ticker = :ticker AND is_active = TRUE")
            stocks = db.execute(stocks_query, {"ticker": ticker.upper()}).fetchall()
        else:
            logger.info("Fetching market data for all active stocks")
            stocks_query = text("SELECT id, ticker FROM stocks WHERE is_active = TRUE")
            stocks = db.execute(stocks_query).fetchall()
        
        logger.info(f"Found {len(stocks)} active stock(s) to sync")
        
        results = {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        if not stocks:
            logger.warning("No active stocks found in database")
            return {
                "success": False,
                "error": "No active stocks found in database",
                "processed": 0
            }
        
        for idx, stock in enumerate(stocks):
            # Add delay between requests to avoid rate limit
            if idx > 0:
                logger.debug(f"Waiting 2 seconds before next request (rate limit protection)")
                time.sleep(2)
            
            try:
                stock_id = stock.id
                stock_ticker = stock.ticker
                logger.info(f"[{idx+1}/{len(stocks)}] Processing {stock_ticker} (ID: {stock_id})")
                
                # Fetch historical price data
                from io import StringIO
                import sys as sys_module
                old_stdout = sys_module.stdout
                old_stderr = sys_module.stderr
                sys_module.stdout = StringIO()
                sys_module.stderr = StringIO()
                
                price_df = None
                
                try:
                    end_date = datetime.now().date()
                    start_date = end_date - timedelta(days=days)
                    logger.info(f"Fetching historical data for {stock_ticker} from {start_date} to {end_date}")
                    
                    vnstock = Vnstock()
                    stock_obj = vnstock.stock(symbol=stock_ticker.upper(), source="VCI")
                    try:
                        price_df = stock_obj.historical_data(start_date=start_date.strftime('%Y-%m-%d'), 
                                                             end_date=end_date.strftime('%Y-%m-%d'))
                        if HAS_PANDAS:
                            logger.info(f"Received {len(price_df)} rows of market data for {stock_ticker}")
                        else:
                            logger.info(f"Received market data for {stock_ticker} (pandas not available for row count)")
                    except (SystemExit, Exception) as e:
                        error_msg = str(e)
                        logger.error(f"Error fetching historical data for {stock_ticker}: {error_msg}")
                        if "Rate limit" in error_msg or "quota" in error_msg.lower():
                            logger.error(f"Rate limit exceeded for {stock_ticker}")
                            raise SystemExit(f"Rate limit exceeded: {error_msg}")
                        price_df = pd.DataFrame() if HAS_PANDAS else None
                except SystemExit as e:
                    raise
                finally:
                    sys_module.stdout = old_stdout
                    sys_module.stderr = old_stderr
                
                inserted_count = 0
                updated_count = 0
                
                if price_df is not None and (not HAS_PANDAS or (not price_df.empty and len(price_df) > 0)):
                    logger.info(f"Processing {len(price_df) if HAS_PANDAS else 'unknown'} rows for {stock_ticker}")
                    
                    # Log column names for debugging
                    if HAS_PANDAS and not price_df.empty:
                        logger.debug(f"Available columns for {stock_ticker}: {list(price_df.columns)}")
                        # Log first row for debugging
                        if len(price_df) > 0:
                            logger.debug(f"First row sample for {stock_ticker}: {price_df.iloc[0].to_dict()}")
                    
                    for row_idx, row in price_df.iterrows():
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
                            
                            # Try multiple possible column names for date
                            trade_date = safe_get_date(row, 'time', row_idx)
                            if not trade_date:
                                trade_date = safe_get_date(row, 'date', row_idx)
                            if not trade_date:
                                trade_date = safe_get_date(row, 'Time', row_idx)
                            if not trade_date:
                                trade_date = safe_get_date(row, 'Date', row_idx)
                            if not trade_date:
                                logger.debug(f"Skipping row {row_idx} for {stock_ticker}: invalid trade_date")
                                continue
                            
                            def safe_get_float(row, key, alt_keys=None):
                                """Try to get float value, checking multiple possible column names"""
                                keys_to_try = [key]
                                if alt_keys:
                                    keys_to_try.extend(alt_keys)
                                
                                for k in keys_to_try:
                                    if k in row.index:
                                        value = row.get(k)
                                        if HAS_PANDAS:
                                            if pd.notna(value):
                                                try:
                                                    return float(value)
                                                except (ValueError, TypeError):
                                                    continue
                                        else:
                                            if value is not None:
                                                try:
                                                    return float(value)
                                                except (ValueError, TypeError):
                                                    continue
                                return None
                            
                            def safe_get_int(row, key, alt_keys=None):
                                """Try to get int value, checking multiple possible column names"""
                                keys_to_try = [key]
                                if alt_keys:
                                    keys_to_try.extend(alt_keys)
                                
                                for k in keys_to_try:
                                    if k in row.index:
                                        value = row.get(k)
                                        if HAS_PANDAS:
                                            if pd.notna(value):
                                                try:
                                                    return int(value)
                                                except (ValueError, TypeError):
                                                    continue
                                        else:
                                            if value is not None:
                                                try:
                                                    return int(value)
                                                except (ValueError, TypeError):
                                                    continue
                                return None
                            
                            # Try multiple possible column name variations (lowercase, uppercase, capitalized)
                            open_price = safe_get_float(row, 'open', ['Open', 'OPEN', 'open_price', 'Open Price'])
                            high_price = safe_get_float(row, 'high', ['High', 'HIGH', 'high_price', 'High Price'])
                            low_price = safe_get_float(row, 'low', ['Low', 'LOW', 'low_price', 'Low Price'])
                            close_price = safe_get_float(row, 'close', ['Close', 'CLOSE', 'close_price', 'Close Price'])
                            volume = safe_get_int(row, 'volume', ['Volume', 'VOLUME', 'vol'])
                            
                            # Log if we couldn't find the expected columns
                            if open_price is None or high_price is None or low_price is None or close_price is None:
                                logger.warning(f"Missing OHLC data for {stock_ticker} on {trade_date}. Found: open={open_price}, high={high_price}, low={low_price}, close={close_price}")
                                logger.debug(f"Available columns: {list(row.index) if HAS_PANDAS else 'N/A'}")
                            
                            # Validate OHLC data before inserting
                            if open_price is None or high_price is None or low_price is None or close_price is None:
                                logger.warning(f"Skipping row {row_idx} for {stock_ticker} on {trade_date}: missing OHLC data")
                                continue
                            
                            # Validate logical consistency: high >= low, high >= open, high >= close, low <= open, low <= close
                            if high_price < low_price or high_price < open_price or high_price < close_price or low_price > open_price or low_price > close_price:
                                logger.warning(f"Invalid OHLC data for {stock_ticker} on {trade_date}: O={open_price}, H={high_price}, L={low_price}, C={close_price}. Skipping.")
                                continue
                            
                            # Check if record already exists
                            check_query = text("SELECT COUNT(*) FROM market_data WHERE stock_id = :stock_id AND trade_date = :trade_date")
                            exists = db.execute(check_query, {"stock_id": stock_id, "trade_date": trade_date}).scalar() > 0
                            
                            # Insert or update - always update OHLC data from historical_data (more accurate)
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
                                    adjusted_close = EXCLUDED.close_price,
                                    volume = EXCLUDED.volume,
                                    data_source = CASE 
                                        WHEN EXCLUDED.data_source = 'vnstock' THEN 'vnstock'
                                        ELSE EXCLUDED.data_source
                                    END,
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
                            
                            if exists:
                                updated_count += 1
                            else:
                                inserted_count += 1
                                
                        except Exception as e:
                            logger.warning(f"Error processing row {row_idx} for {stock_ticker} on {trade_date}: {e}")
                            continue
                
                db.commit()
                logger.info(f"Successfully synced {stock_ticker}: {inserted_count} inserted, {updated_count} updated, total {inserted_count + updated_count} records")
                
                results["success"] += 1
                results["details"].append({
                    "ticker": stock_ticker,
                    "status": "success",
                    "records_inserted": inserted_count,
                    "records_updated": updated_count,
                    "total_records": inserted_count + updated_count
                })
                
            except SystemExit as e:
                # Handle vnstock rate limit - stop processing
                db.rollback()
                error_msg = str(e)
                logger.error(f"Rate limit exceeded while processing {stock_ticker}: {error_msg}")
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
                logger.error(f"Error processing {stock_ticker}: {e}", exc_info=True)
                results["failed"] += 1
                results["details"].append({
                    "ticker": stock_ticker,
                    "status": "error",
                    "error": str(e)
                })
            
            results["processed"] += 1
        
        logger.info(f"Market data sync completed: {results['success']} success, {results['failed']} failed, {results['processed']} processed")
        return results
        
    except Exception as e:
        logger.error(f"Error in sync_market_data: {e}", exc_info=True)
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


def sync_current_price(db: Session, ticker: Optional[str] = None) -> Dict:
    """Sync current stock price from vnstock to database and Redis"""
    logger.info(f"Starting current price sync: ticker={ticker or 'all'}")
    
    if not HAS_VNSTOCK:
        logger.error("vnstock library not available")
        return {
            "success": False,
            "error": "vnstock library not available",
            "processed": 0
        }
    
    try:
        # Get stocks to sync
        if ticker:
            logger.info(f"Fetching current price for specific ticker: {ticker}")
            stocks_query = text("SELECT id, ticker FROM stocks WHERE ticker = :ticker AND is_active = TRUE")
            stocks = db.execute(stocks_query, {"ticker": ticker.upper()}).fetchall()
        else:
            logger.info("Fetching current price for all active stocks")
            stocks_query = text("SELECT id, ticker FROM stocks WHERE is_active = TRUE")
            stocks = db.execute(stocks_query).fetchall()
        
        logger.info(f"Found {len(stocks)} active stock(s) to sync")
        
        results = {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        if not stocks:
            logger.warning("No active stocks found in database")
            return {
                "success": False,
                "error": "No active stocks found in database",
                "processed": 0
            }
        
        for idx, stock in enumerate(stocks):
            # Add delay between requests to avoid rate limit
            if idx > 0:
                time.sleep(1)  # 1 second delay between stocks
            
            try:
                stock_id = stock.id
                stock_ticker = stock.ticker
                logger.info(f"[{idx+1}/{len(stocks)}] Fetching current price for {stock_ticker}")
                
                # Fetch current price from vnstock
                from io import StringIO
                import sys as sys_module
                old_stdout = sys_module.stdout
                old_stderr = sys_module.stderr
                sys_module.stdout = StringIO()
                sys_module.stderr = StringIO()
                
                current_price = None
                market_cap = None
                pe_ratio = None
                
                try:
                    vnstock = Vnstock()
                    stock_obj = vnstock.stock(symbol=stock_ticker.upper(), source="VCI")
                    
                    # Get price board data
                    try:
                        price_board_df = stock_obj.trading.price_board([stock_obj.symbol])
                        if price_board_df is not None and not price_board_df.empty:
                            current_price = float(price_board_df.iloc[0][('match', 'match_price')])
                            logger.info(f"Got current price for {stock_ticker}: {current_price:,.0f}")
                    except Exception as e:
                        logger.warning(f"Could not get price board for {stock_ticker}: {e}")
                    
                    # Get market cap and PE if available
                    try:
                        overview_df = stock_obj.company.overview()
                        if overview_df is not None and not overview_df.empty:
                            # Try to get market cap and PE from overview
                            for col in overview_df.columns:
                                if 'market' in col.lower() and 'cap' in col.lower():
                                    market_cap = overview_df.iloc[0][col]
                                if 'pe' in col.lower() or 'p/e' in col.lower():
                                    pe_ratio = overview_df.iloc[0][col]
                    except Exception as e:
                        logger.debug(f"Could not get overview for {stock_ticker}: {e}")
                        
                except SystemExit as e:
                    error_msg = str(e)
                    if "Rate limit" in error_msg or "quota" in error_msg.lower():
                        logger.error(f"Rate limit exceeded for {stock_ticker}")
                        raise SystemExit(f"Rate limit exceeded: {error_msg}")
                    raise
                finally:
                    sys_module.stdout = old_stdout
                    sys_module.stderr = old_stderr
                
                if current_price and current_price > 0:
                    # Update market_data table with latest price (today's date)
                    today = datetime.now().date()
                    
                    # Check if record exists for today
                    check_query = text("""
                        SELECT id FROM market_data 
                        WHERE stock_id = :stock_id AND trade_date = :trade_date
                    """)
                    existing = db.execute(check_query, {"stock_id": stock_id, "trade_date": today}).fetchone()
                    
                    if existing:
                        # Update existing record - only update close_price if open/high/low are already set
                        # If open/high/low are all equal to close_price, it means they were set by sync_current_price
                        # In that case, we should not update to preserve historical data
                        check_data_query = text("""
                            SELECT open_price, high_price, low_price, close_price 
                            FROM market_data 
                            WHERE stock_id = :stock_id AND trade_date = :trade_date
                        """)
                        existing_data = db.execute(check_data_query, {"stock_id": stock_id, "trade_date": today}).fetchone()
                        
                        if existing_data:
                            existing_open = existing_data.open_price
                            existing_high = existing_data.high_price
                            existing_low = existing_data.low_price
                            existing_close = existing_data.close_price
                            
                            # Only update if open/high/low are all equal (meaning they were set by sync_current_price)
                            # Otherwise, preserve the historical data
                            if existing_open == existing_close and existing_high == existing_close and existing_low == existing_close:
                                # This was set by sync_current_price, safe to update close_price only
                                update_query = text("""
                                    UPDATE market_data 
                                    SET close_price = :close_price,
                                        adjusted_close = :close_price,
                                        updated_at = CURRENT_TIMESTAMP
                                    WHERE stock_id = :stock_id AND trade_date = :trade_date
                                """)
                                db.execute(update_query, {
                                    "stock_id": stock_id,
                                    "trade_date": today,
                                    "close_price": current_price
                                })
                                logger.info(f"Updated close_price for {stock_ticker} on {today}: {current_price:,.0f}")
                            else:
                                # Historical data exists, only update close_price if it's different
                                if existing_close != current_price:
                                    update_query = text("""
                                        UPDATE market_data 
                                        SET close_price = :close_price,
                                            adjusted_close = :close_price,
                                            updated_at = CURRENT_TIMESTAMP
                                        WHERE stock_id = :stock_id AND trade_date = :trade_date
                                    """)
                                    db.execute(update_query, {
                                        "stock_id": stock_id,
                                        "trade_date": today,
                                        "close_price": current_price
                                    })
                                    logger.info(f"Updated close_price for {stock_ticker} on {today}: {current_price:,.0f} (preserving OHLC data)")
                                else:
                                    logger.debug(f"Close price unchanged for {stock_ticker} on {today}: {current_price:,.0f}")
                    else:
                        # Insert new record
                        insert_query = text("""
                            INSERT INTO market_data (
                                stock_id, trade_date,
                                open_price, high_price, low_price, close_price, adjusted_close,
                                volume, data_source, created_at, updated_at
                            ) VALUES (
                                :stock_id, :trade_date,
                                :close_price, :close_price, :close_price, :close_price, :close_price,
                                0, 'vnstock_price_sync', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                            )
                        """)
                        db.execute(insert_query, {
                            "stock_id": stock_id,
                            "trade_date": today,
                            "close_price": current_price
                        })
                        logger.info(f"Inserted price for {stock_ticker} on {today}: {current_price:,.0f}")
                    
                    # Update Redis cache
                    try:
                        from src.utils.redis_client import get_redis_client
                        redis_client = get_redis_client()
                        if redis_client and redis_client._client:
                            redis_client.cache_market_data(stock_ticker, {
                                'current_price': current_price,
                                'market_cap': market_cap,
                                'pe_ratio': pe_ratio,
                                'source': 'vnstock_price_sync',
                                'updated_at': datetime.now().isoformat()
                            })
                            logger.info(f"Cached price to Redis for {stock_ticker}")
                    except Exception as e:
                        logger.debug(f"Could not cache to Redis for {stock_ticker}: {e}")
                    
                    db.commit()
                    
                    results["success"] += 1
                    results["details"].append({
                        "ticker": stock_ticker,
                        "status": "success",
                        "price": current_price,
                        "updated": True
                    })
                else:
                    logger.warning(f"No valid price retrieved for {stock_ticker}")
                    results["failed"] += 1
                    results["details"].append({
                        "ticker": stock_ticker,
                        "status": "error",
                        "error": "No valid price retrieved"
                    })
                
            except SystemExit as e:
                # Handle vnstock rate limit - stop processing
                db.rollback()
                error_msg = str(e)
                logger.error(f"Rate limit exceeded while processing {stock_ticker}: {error_msg}")
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
                logger.error(f"Error processing {stock_ticker}: {e}", exc_info=True)
                results["failed"] += 1
                results["details"].append({
                    "ticker": stock_ticker,
                    "status": "error",
                    "error": str(e)
                })
            
            results["processed"] += 1
        
        logger.info(f"Current price sync completed: {results['success']} success, {results['failed']} failed, {results['processed']} processed")
        return results
        
    except Exception as e:
        logger.error(f"Error in sync_current_price: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "processed": 0
        }


def sync_base_pe(db: Session, ticker: Optional[str] = None) -> Dict:
    """Calculate and update base PE for stocks based on industry and current PE"""
    logger.info(f"Starting base PE update: ticker={ticker or 'all'}")
    
    try:
        # Import PE calculation functions
        from src.core.industry_pe import get_current_pe, suggest_base_pe
        import configparser
        import os
        from pathlib import Path
        
        # Get stocks to process
        if ticker:
            stocks_query = text("SELECT id, ticker, industry FROM stocks WHERE ticker = :ticker AND is_active = TRUE")
            stocks = db.execute(stocks_query, {"ticker": ticker.upper()}).fetchall()
        else:
            stocks_query = text("SELECT id, ticker, industry FROM stocks WHERE is_active = TRUE")
            stocks = db.execute(stocks_query).fetchall()
        
        logger.info(f"Found {len(stocks)} active stock(s) to update base PE")
        
        results = {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        if not stocks:
            logger.warning("No active stocks found in database")
            return {
                "success": False,
                "error": "No active stocks found in database",
                "processed": 0
            }
        
        # Get config directory
        if Path('/app').exists():
            config_dir = Path('/app/config')
        else:
            config_dir = Path(__file__).parent.parent.parent / 'config'
        
        for idx, stock in enumerate(stocks):
            # Add delay between requests
            if idx > 0:
                time.sleep(1)
            
            try:
                stock_id = stock.id
                stock_ticker = stock.ticker
                industry = stock.industry
                logger.info(f"[{idx+1}/{len(stocks)}] Updating base PE for {stock_ticker}")
                
                # Calculate current PE
                try:
                    current_pe = get_current_pe(stock_ticker)
                    logger.info(f"Current PE for {stock_ticker}: {current_pe:.2f}" if current_pe else f"Could not calculate PE for {stock_ticker}")
                except Exception as e:
                    logger.warning(f"Could not calculate current PE for {stock_ticker}: {e}")
                    current_pe = None
                
                # Suggest base PE
                try:
                    suggested_base_pe = suggest_base_pe(stock_ticker, industry, current_pe)
                    logger.info(f"Suggested base PE for {stock_ticker}: {suggested_base_pe:.2f}")
                except Exception as e:
                    logger.warning(f"Could not suggest base PE for {stock_ticker}: {e}")
                    suggested_base_pe = 8.5  # Default
                
                # Update config file
                config_file = config_dir / f"{stock_ticker.lower()}.cfg"
                if config_file.exists():
                    config = configparser.ConfigParser()
                    config.read(config_file)
                    
                    # Ensure [graham] section exists
                    if 'graham' not in config:
                        config.add_section('graham')
                    
                    # Update base_pe
                    old_base_pe = config.getfloat('graham', 'base_pe', fallback=8.5)
                    config.set('graham', 'base_pe', str(suggested_base_pe))
                    
                    # Write back to file
                    with open(config_file, 'w') as f:
                        config.write(f)
                    
                    logger.info(f"Updated base PE for {stock_ticker}: {old_base_pe:.2f} -> {suggested_base_pe:.2f}")
                    
                    results["success"] += 1
                    results["details"].append({
                        "ticker": stock_ticker,
                        "status": "success",
                        "old_base_pe": old_base_pe,
                        "new_base_pe": suggested_base_pe,
                        "current_pe": current_pe
                    })
                else:
                    logger.warning(f"Config file not found for {stock_ticker}: {config_file}")
                    results["failed"] += 1
                    results["details"].append({
                        "ticker": stock_ticker,
                        "status": "error",
                        "error": "Config file not found"
                    })
                
            except Exception as e:
                logger.error(f"Error processing {stock_ticker}: {e}", exc_info=True)
                results["failed"] += 1
                results["details"].append({
                    "ticker": stock_ticker,
                    "status": "error",
                    "error": str(e)
                })
            
            results["processed"] += 1
        
        logger.info(f"Base PE update completed: {results['success']} success, {results['failed']} failed, {results['processed']} processed")
        return results
        
    except Exception as e:
        logger.error(f"Error in sync_base_pe: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "processed": 0
        }
