"""
Database Service - Main FastAPI application
Provides data viewing and query operations for VN30 stock data.

Note: All sync operations have been moved to sync-service.
This service is for data viewing only.
"""
import os
import sys
from pathlib import Path

# Setup project path first (before importing services.common)
if Path('/app').exists():
    project_root = Path('/app')
else:
    project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from typing import List, Optional
import redis
from datetime import datetime, timezone
import json
import logging

# Import common utilities after path setup
from services.common import setup_cors, create_health_response

# Setup service-specific logger
from src.utils.service_logger import setup_service_logger
logger = setup_service_logger('database', level=logging.INFO)

from .database import get_db, engine, Base
from .models import Stock

app = FastAPI(
    title="Database Service",
    description="Database viewing service for VN30 stock data (sync operations moved to sync-service)",
    version=os.getenv("APP_VERSION", "latest")
)

# Setup CORS
setup_cors(app)

# Redis connection
redis_client = None
try:
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    redis_client = redis.from_url(redis_url)
except Exception as e:
    print(f"Warning: Redis connection failed: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "database-service",
        "version": os.getenv("APP_VERSION", "latest"),
        "status": "running",
        "note": "Sync operations are now handled by sync-service"
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    # Check database connection
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check Redis connection
    redis_status = "healthy"
    if redis_client:
        try:
            redis_client.ping()
        except Exception as e:
            redis_status = f"unhealthy: {str(e)}"
    else:
        redis_status = "not_configured"
    
    return create_health_response(
        "database-service",
        include_database=False,
        additional_status={
            "database": db_status,
            "redis": redis_status,
            "overall_status": "healthy" if db_status == "healthy" else "degraded"
        }
    )


@app.get("/api/database/stats")
async def get_database_stats(db: Session = Depends(get_db)):
    """Get database statistics"""
    stats = {}
    
    try:
        # Get table names
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        stats["tables"] = []
        total_rows = 0
        
        for table_name in tables:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                total_rows += count
                
                # Get table size
                size_result = db.execute(text(
                    f"SELECT pg_size_pretty(pg_total_relation_size('{table_name}'))"
                ))
                size = size_result.scalar()
                
                stats["tables"].append({
                    "name": table_name,
                    "row_count": count,
                    "size": size
                })
            except Exception as e:
                stats["tables"].append({
                    "name": table_name,
                    "row_count": "error",
                    "error": str(e)
                })
        
        stats["total_tables"] = len(tables)
        stats["total_rows"] = total_rows
        
        # Get database size
        db_size_result = db.execute(text(
            "SELECT pg_size_pretty(pg_database_size(current_database()))"
        ))
        stats["database_size"] = db_size_result.scalar()
        
        # Get connection info
        conn_info = db.execute(text("SELECT version()"))
        stats["postgres_version"] = conn_info.scalar().split(",")[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")
    
    return stats


@app.get("/api/database/tables")
async def get_tables(db: Session = Depends(get_db)):
    """Get list of all tables"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        table_info = []
        for table_name in tables:
            columns = inspector.get_columns(table_name)
            table_info.append({
                "name": table_name,
                "columns": [col["name"] for col in columns],
                "column_count": len(columns)
            })
        
        return {"tables": table_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting tables: {str(e)}")


@app.get("/api/database/tables/{table_name}/schema")
async def get_table_schema(table_name: str, db: Session = Depends(get_db)):
    """Get detailed schema information for a specific table"""
    try:
        inspector = inspect(engine)
        
        # Check if table exists
        if table_name not in inspector.get_table_names():
            raise HTTPException(status_code=404, detail=f"Table {table_name} not found")
        
        # Get columns with detailed info
        columns = inspector.get_columns(table_name)
        column_details = []
        
        for col in columns:
            col_info = {
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col.get("nullable", True),
                "default": str(col.get("default", "None")),
                "autoincrement": col.get("autoincrement", False),
                "primary_key": col.get("primary_key", False)
            }
            column_details.append(col_info)
        
        # Get primary keys
        pk_constraint = inspector.get_pk_constraint(table_name)
        primary_keys = pk_constraint.get("constrained_columns", [])
        
        # Get foreign keys
        foreign_keys = inspector.get_foreign_keys(table_name)
        fk_details = []
        for fk in foreign_keys:
            fk_details.append({
                "name": fk.get("name", ""),
                "constrained_columns": fk.get("constrained_columns", []),
                "referred_table": fk.get("referred_table", ""),
                "referred_columns": fk.get("referred_columns", [])
            })
        
        # Get indexes
        indexes = inspector.get_indexes(table_name)
        index_details = []
        for idx in indexes:
            index_details.append({
                "name": idx.get("name", ""),
                "columns": idx.get("column_names", []),
                "unique": idx.get("unique", False)
            })
        
        # Get row count
        row_count_result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        row_count = row_count_result.scalar()
        
        # Get table size
        size_result = db.execute(text(
            f"SELECT pg_size_pretty(pg_total_relation_size('{table_name}'))"
        ))
        table_size = size_result.scalar()
        
        # Get sample data (first 5 rows)
        sample_result = db.execute(text(f"SELECT * FROM {table_name} LIMIT 5"))
        sample_rows = []
        for row in sample_result:
            row_dict = {}
            for key, value in row._mapping.items():
                if isinstance(value, datetime):
                    row_dict[key] = value.isoformat()
                else:
                    row_dict[key] = str(value) if value is not None else None
            sample_rows.append(row_dict)
        
        return {
            "table_name": table_name,
            "columns": column_details,
            "primary_keys": primary_keys,
            "foreign_keys": fk_details,
            "indexes": index_details,
            "row_count": row_count,
            "table_size": table_size,
            "sample_data": sample_rows
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting table schema: {str(e)}")


@app.get("/api/database/tables/{table_name}/data")
async def get_table_data(
    table_name: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get data from a specific table with pagination"""
    try:
        inspector = inspect(engine)
        
        # Check if table exists
        if table_name not in inspector.get_table_names():
            raise HTTPException(status_code=404, detail=f"Table {table_name} not found")
        
        # Get total count
        count_result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        total_count = count_result.scalar()
        
        # Get data with pagination
        data_result = db.execute(text(f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {skip}"))
        rows = []
        for row in data_result:
            row_dict = {}
            for key, value in row._mapping.items():
                if isinstance(value, datetime):
                    row_dict[key] = value.isoformat()
                elif isinstance(value, (int, float)):
                    row_dict[key] = value
                else:
                    row_dict[key] = str(value) if value is not None else None
            rows.append(row_dict)
        
        return {
            "table_name": table_name,
            "total_rows": total_count,
            "skip": skip,
            "limit": limit,
            "data": rows
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting table data: {str(e)}")


@app.get("/api/database/relationships")
async def get_database_relationships(db: Session = Depends(get_db)):
    """Get all relationships between tables"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        relationships = []
        tables_info = []
        
        for table_name in tables:
            # Get table info
            columns = inspector.get_columns(table_name)
            pk_constraint = inspector.get_pk_constraint(table_name)
            primary_keys = pk_constraint.get("constrained_columns", [])
            
            tables_info.append({
                "name": table_name,
                "columns": [col["name"] for col in columns],
                "primary_keys": primary_keys
            })
            
            # Get foreign keys
            foreign_keys = inspector.get_foreign_keys(table_name)
            for fk in foreign_keys:
                relationships.append({
                    "from_table": table_name,
                    "from_columns": fk.get("constrained_columns", []),
                    "to_table": fk.get("referred_table", ""),
                    "to_columns": fk.get("referred_columns", []),
                    "name": fk.get("name", "")
                })
        
        return {
            "tables": tables_info,
            "relationships": relationships
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting relationships: {str(e)}")


@app.get("/api/database/stocks")
async def list_stocks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    vn30_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """List all stocks"""
    query = db.query(Stock)
    
    if vn30_only:
        query = query.filter(Stock.is_vn30 == True)
    
    query = query.filter(Stock.is_active == True)
    total = query.count()
    stocks = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "stocks": [
            {
                "id": s.id,
                "ticker": s.ticker,
                "name": s.name,
                "sector": s.sector,
                "industry": s.industry,
                "exchange": s.exchange,
                "is_vn30": s.is_vn30,
                "is_active": s.is_active,
                "last_sync_date": s.last_sync_date.isoformat() if s.last_sync_date else None,
                "sync_status": s.sync_status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in stocks
        ]
    }


@app.get("/api/database/stocks/{ticker}")
async def get_stock_info(ticker: str, db: Session = Depends(get_db)):
    """Get comprehensive stock information from database"""
    ticker = ticker.upper()
    
    try:
        # Get stock basic info
        stock_query = text("SELECT * FROM stocks WHERE ticker = :ticker AND is_active = TRUE")
        stock = db.execute(stock_query, {"ticker": ticker}).fetchone()
        
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock {ticker} not found or inactive")
        
        stock_dict = dict(stock._mapping) if hasattr(stock, '_mapping') else dict(zip(stock.keys(), stock))
        
        # Get latest market data
        market_data_query = text("""
            SELECT * FROM market_data 
            WHERE stock_id = :stock_id 
            ORDER BY trade_date DESC 
            LIMIT 1
        """)
        market_data = db.execute(market_data_query, {"stock_id": stock_dict['id']}).fetchone()
        market_data_dict = None
        if market_data:
            market_data_dict = dict(market_data._mapping) if hasattr(market_data, '_mapping') else dict(zip(market_data.keys(), market_data))
        
        # Get latest financial data (TTM)
        financial_query = text("""
            SELECT 
                SUM(CASE WHEN period_type = 'quarter' AND period_date >= CURRENT_DATE - INTERVAL '1 year' 
                    THEN operating_cash_flow ELSE 0 END) as ttm_ocf,
                SUM(CASE WHEN period_type = 'quarter' AND period_date >= CURRENT_DATE - INTERVAL '1 year' 
                    THEN capital_expenditures ELSE 0 END) as ttm_capex,
                SUM(CASE WHEN period_type = 'quarter' AND period_date >= CURRENT_DATE - INTERVAL '1 year' 
                    THEN operating_cash_flow ELSE 0 END) - 
                ABS(SUM(CASE WHEN period_type = 'quarter' AND period_date >= CURRENT_DATE - INTERVAL '1 year' 
                    THEN capital_expenditures ELSE 0 END)) as ttm_fcf
            FROM financial_data 
            WHERE stock_id = :stock_id
        """)
        financial_data = db.execute(financial_query, {"stock_id": stock_dict['id']}).fetchone()
        financial_dict = None
        if financial_data:
            financial_dict = dict(financial_data._mapping) if hasattr(financial_data, '_mapping') else dict(zip(financial_data.keys(), financial_data))
        
        # Get latest shares outstanding
        shares_query = text("""
            SELECT * FROM shares_outstanding 
            WHERE stock_id = :stock_id 
            ORDER BY period_date DESC 
            LIMIT 1
        """)
        shares_data = db.execute(shares_query, {"stock_id": stock_dict['id']}).fetchone()
        shares_dict = None
        if shares_data:
            shares_dict = dict(shares_data._mapping) if hasattr(shares_data, '_mapping') else dict(zip(shares_data.keys(), shares_data))
        
        # Get latest EPS - calculate from net_profit and shares if available
        eps = None
        try:
            # First try: Calculate EPS from TTM net_profit (sum of last 4 quarters)
            ttm_eps_query = text("""
                SELECT SUM(net_profit) as ttm_net_profit
                FROM financial_data 
                WHERE stock_id = :stock_id 
                  AND net_profit IS NOT NULL
                  AND period_type = 'quarter'
                  AND period_date >= CURRENT_DATE - INTERVAL '1 year'
            """)
            ttm_net_profit_result = db.execute(ttm_eps_query, {"stock_id": stock_dict['id']}).fetchone()
            shares_outstanding = shares_dict.get('shares_outstanding') if shares_dict else None
            
            if ttm_net_profit_result and ttm_net_profit_result[0] and shares_outstanding and shares_outstanding > 0:
                ttm_net_profit = float(ttm_net_profit_result[0])
                if ttm_net_profit > 0:
                    eps = ttm_net_profit / shares_outstanding
                    logger.debug(f"Calculated EPS from TTM net_profit for {ticker}: {eps:.2f}")
            
            # Fallback: Try latest single quarter/year if TTM not available
            if eps is None:
                eps_query = text("""
                    SELECT net_profit, period_type FROM financial_data 
                    WHERE stock_id = :stock_id AND net_profit IS NOT NULL
                    ORDER BY period_date DESC 
                    LIMIT 1
                """)
                net_profit_result = db.execute(eps_query, {"stock_id": stock_dict['id']}).fetchone()
                if net_profit_result and net_profit_result[0] and shares_outstanding and shares_outstanding > 0:
                    net_profit = float(net_profit_result[0])
                    period_type = net_profit_result[1] if len(net_profit_result) > 1 else None
                    
                    # If it's annual data, use directly; if quarterly, multiply by 4 for annualized
                    if period_type == 'year':
                        eps = net_profit / shares_outstanding
                    elif period_type == 'quarter':
                        eps = (net_profit * 4) / shares_outstanding
                    else:
                        eps = net_profit / shares_outstanding
                    
                    logger.debug(f"Calculated EPS from {period_type or 'latest'} net_profit for {ticker}: {eps:.2f}")
        except Exception as e:
            logger.debug(f"Could not calculate EPS for {ticker}: {e}")
            eps = None
        
        # Calculate PE ratio if we have price and EPS
        pe_ratio = None
        if market_data_dict and market_data_dict.get('close_price') and eps and eps > 0:
            try:
                close_price = float(market_data_dict['close_price'])
                pe_ratio = close_price / eps
                logger.debug(f"Calculated P/E ratio for {ticker}: {pe_ratio:.2f}")
            except (ZeroDivisionError, TypeError, ValueError):
                pe_ratio = None
        
        # Calculate market cap if we have price and shares
        market_cap = None
        shares_outstanding = shares_dict.get('shares_outstanding') if shares_dict else None
        if market_data_dict and market_data_dict.get('close_price') and shares_outstanding:
            market_cap = market_data_dict['close_price'] * shares_outstanding
        
        return {
            "ticker": ticker,
            "stock": stock_dict,
            "market_data": market_data_dict,
            "financial_data": financial_dict,
            "shares_outstanding": shares_dict,
            "metrics": {
                "current_price": market_data_dict.get('close_price') if market_data_dict else None,
                "market_cap": market_cap,
                "pe_ratio": pe_ratio,
                "eps": eps,
                "ttm_fcf": financial_dict.get('ttm_fcf') if financial_dict else None,
                "shares": shares_outstanding
            },
            "last_updated": {
                "market_data": market_data_dict.get('trade_date').isoformat() if market_data_dict and market_data_dict.get('trade_date') else None,
                "financial_data": financial_dict.get('period_date').isoformat() if financial_dict and financial_dict.get('period_date') else None,
                "shares": shares_dict.get('period_date').isoformat() if shares_dict and shares_dict.get('period_date') else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stock info for {ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving stock information: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
