"""
Database Service - Main FastAPI application
Manages database operations and data synchronization
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
from datetime import datetime
import json
import logging

# Import common utilities after path setup
from services.common import setup_cors, create_health_response

# Setup service-specific logger với rotation và tối ưu hiệu năng
from src.utils.service_logger import setup_service_logger
logger = setup_service_logger('database', level=logging.INFO)

from .database import get_db, engine, Base
from .models import Stock

# Redis connection for sync status tracking (must be defined before use)
HAS_REDIS = False
sync_redis_client = None
try:
    from src.utils.redis_client import get_redis_client
    sync_redis_client = get_redis_client()
    HAS_REDIS = sync_redis_client._client is not None if sync_redis_client else False
except Exception as e:
    HAS_REDIS = False
    sync_redis_client = None
    # Logger sẽ được setup sau
    pass

# Lazy import sync_service to prevent service crash if sync_service has errors
# Import only when needed (in sync endpoints)
SYNC_SERVICE_AVAILABLE = False
try:
    from .sync_service import sync_financial_data, sync_market_data, sync_shares_outstanding
    SYNC_SERVICE_AVAILABLE = True
except Exception as e:
    # Logger sẽ được setup sau
    pass

app = FastAPI(
    title="Database Service",
    description="Database management service for VN30 stock data",
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


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "database-service",
        "version": os.getenv("APP_VERSION", "latest"),
        "status": "running"
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting table schema: {str(e)}")


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
async def get_stock(ticker: str, db: Session = Depends(get_db)):
    """Get stock by ticker"""
    stock = db.query(Stock).filter(Stock.ticker == ticker.upper()).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
    
    return {
        "id": stock.id,
        "ticker": stock.ticker,
        "name": stock.name,
        "sector": stock.sector,
        "industry": stock.industry,
        "exchange": stock.exchange,
        "is_vn30": stock.is_vn30,
        "is_active": stock.is_active,
        "last_sync_date": stock.last_sync_date.isoformat() if stock.last_sync_date else None,
        "sync_status": stock.sync_status,
        "created_at": stock.created_at.isoformat() if stock.created_at else None,
        "updated_at": stock.updated_at.isoformat() if stock.updated_at else None,
    }


@app.post("/api/database/sync/growth-metrics")
async def sync_growth_metrics(
    ticker: Optional[str] = Query(None, description="Sync for specific ticker, or all if not provided"),
    db: Session = Depends(get_db)
):
    """Calculate and sync growth metrics from financial_data"""
    try:
        # Get stocks to process
        if ticker:
            stocks = db.query(Stock).filter(Stock.ticker == ticker.upper(), Stock.is_active == True).all()
            if not stocks:
                raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
        else:
            stocks = db.query(Stock).filter(Stock.is_active == True).all()
        
        results = {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        for stock in stocks:
            try:
                # Get financial data for this stock, ordered by period_date DESC
                financial_query = text("""
                    SELECT 
                        period_date, period_type, period,
                        revenue, net_profit, operating_profit, free_cash_flow
                    FROM financial_data
                    WHERE stock_id = :stock_id
                    ORDER BY period_date DESC
                    LIMIT 20
                """)
                
                financial_rows = db.execute(financial_query, {"stock_id": stock.id}).fetchall()
                
                if len(financial_rows) < 2:
                    results["details"].append({
                        "ticker": stock.ticker,
                        "status": "skipped",
                        "reason": "Insufficient financial data (need at least 2 periods)"
                    })
                    results["failed"] += 1
                    continue
                
                # Calculate growth metrics for each period
                inserted_count = 0
                for i in range(len(financial_rows) - 1):
                    current = financial_rows[i]
                    previous = financial_rows[i + 1]
                    
                    # Calculate YoY growth rates
                    revenue_growth = None
                    net_profit_growth = None
                    operating_profit_growth = None
                    fcf_growth = None
                    
                    if current.revenue and previous.revenue and previous.revenue != 0:
                        revenue_growth = ((current.revenue - previous.revenue) / abs(previous.revenue)) * 100
                    
                    if current.net_profit and previous.net_profit and previous.net_profit != 0:
                        net_profit_growth = ((current.net_profit - previous.net_profit) / abs(previous.net_profit)) * 100
                    
                    if current.operating_profit and previous.operating_profit and previous.operating_profit != 0:
                        operating_profit_growth = ((current.operating_profit - previous.operating_profit) / abs(previous.operating_profit)) * 100
                    
                    if current.free_cash_flow and previous.free_cash_flow and previous.free_cash_flow != 0:
                        fcf_growth = ((current.free_cash_flow - previous.free_cash_flow) / abs(previous.free_cash_flow)) * 100
                    
                    # Calculate weighted growth rate (50% net profit, 30% revenue, 20% operating profit)
                    growth_rates = []
                    weights = []
                    if net_profit_growth is not None:
                        growth_rates.append(net_profit_growth)
                        weights.append(0.5)
                    if revenue_growth is not None:
                        growth_rates.append(revenue_growth)
                        weights.append(0.3)
                    if operating_profit_growth is not None:
                        growth_rates.append(operating_profit_growth)
                        weights.append(0.2)
                    
                    weighted_growth = None
                    if growth_rates:
                        total_weight = sum(weights[:len(growth_rates)])
                        if total_weight > 0:
                            weighted_growth = sum(g * w for g, w in zip(growth_rates, weights[:len(growth_rates)])) / total_weight
                    
                    # Calculate historical average (from all available periods)
                    all_growth_rates = [g for g in [revenue_growth, net_profit_growth, operating_profit_growth, fcf_growth] if g is not None]
                    historical_avg = sum(all_growth_rates) / len(all_growth_rates) if all_growth_rates else None
                    
                    # Insert or update growth_metrics
                    insert_query = text("""
                        INSERT INTO growth_metrics (
                            stock_id, period_date, period_type,
                            revenue_growth_yoy, net_profit_growth_yoy,
                            operating_profit_growth_yoy, fcf_growth_yoy,
                            weighted_growth_rate, historical_avg_growth,
                            calculation_method, data_points_count,
                            created_at, updated_at
                        ) VALUES (
                            :stock_id, :period_date, :period_type,
                            :revenue_growth, :net_profit_growth,
                            :operating_profit_growth, :fcf_growth,
                            :weighted_growth, :historical_avg,
                            'calculated_from_financial_data', :data_points,
                            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                        ON CONFLICT (stock_id, period_date, period_type)
                        DO UPDATE SET
                            revenue_growth_yoy = EXCLUDED.revenue_growth_yoy,
                            net_profit_growth_yoy = EXCLUDED.net_profit_growth_yoy,
                            operating_profit_growth_yoy = EXCLUDED.operating_profit_growth_yoy,
                            fcf_growth_yoy = EXCLUDED.fcf_growth_yoy,
                            weighted_growth_rate = EXCLUDED.weighted_growth_rate,
                            historical_avg_growth = EXCLUDED.historical_avg_growth,
                            calculation_method = EXCLUDED.calculation_method,
                            data_points_count = EXCLUDED.data_points_count,
                            updated_at = CURRENT_TIMESTAMP
                    """)
                    
                    db.execute(insert_query, {
                        "stock_id": stock.id,
                        "period_date": current.period_date,
                        "period_type": current.period_type or "quarter",
                        "revenue_growth": revenue_growth,
                        "net_profit_growth": net_profit_growth,
                        "operating_profit_growth": operating_profit_growth,
                        "fcf_growth": fcf_growth,
                        "weighted_growth": weighted_growth,
                        "historical_avg": historical_avg,
                        "data_points": len(financial_rows)
                    })
                    inserted_count += 1
                
                db.commit()
                
                results["success"] += 1
                results["details"].append({
                    "ticker": stock.ticker,
                    "status": "success",
                    "records_inserted": inserted_count
                })
                
            except Exception as e:
                db.rollback()
                results["failed"] += 1
                results["details"].append({
                    "ticker": stock.ticker,
                    "status": "error",
                    "error": str(e)
                })
            
            results["processed"] += 1
        
        return {
            "message": f"Growth metrics sync completed",
            "summary": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing growth metrics: {str(e)}")


# Store sync status in memory (fallback if Redis not available)
sync_status_store = {}

def perform_sync_sync(
    table_name: str,
    ticker: Optional[str],
    days: int,
    sync_id: str
):
    """Perform sync in background (sync function wrapper)"""
    import json
    from .database import get_db
    
    # Get new DB session for background task
    db = next(get_db())
    
    try:
        # Update status to running
        status = {
            "status": "running",
            "table": table_name,
            "ticker": ticker,
            "progress": "Starting sync...",
            "progress_percent": 0.0,
            "started_at": datetime.now().isoformat()
        }
        try:
            if 'HAS_REDIS' in globals() and HAS_REDIS and 'sync_redis_client' in globals() and sync_redis_client and sync_redis_client._client:
                sync_redis_client._client.setex(f"sync:{sync_id}", 3600, json.dumps(status))
        except:
            pass
        else:
            sync_status_store[sync_id] = status
        
        # Lazy import sync functions
        from .sync_service import sync_financial_data, sync_market_data, sync_shares_outstanding
        
        sync_functions = {
            "financial_data": sync_financial_data,
            "market_data": sync_market_data,
            "shares_outstanding": sync_shares_outstanding
        }
        
        if table_name not in sync_functions:
            raise ValueError(f"Table '{table_name}' not supported")
        
        sync_func = sync_functions[table_name]
        
        # Update progress
        status["progress"] = "Fetching data from vnstock..."
        status["progress_percent"] = 10.0
        try:
            if 'HAS_REDIS' in globals() and HAS_REDIS and 'sync_redis_client' in globals() and sync_redis_client and sync_redis_client._client:
                sync_redis_client._client.setex(f"sync:{sync_id}", 3600, json.dumps(status))
        except:
            pass
        else:
            sync_status_store[sync_id] = status
        
        # Run sync (this is a blocking sync function)
        if table_name == "market_data":
            results = sync_func(db, ticker, days)
        else:
            results = sync_func(db, ticker)
        
        # Update status to completed
        status["status"] = "completed"
        status["progress"] = "Sync completed"
        status["progress_percent"] = 100.0
        status["completed_at"] = datetime.now().isoformat()
        status["summary"] = results
        
        try:
            if 'HAS_REDIS' in globals() and HAS_REDIS and 'sync_redis_client' in globals() and sync_redis_client and sync_redis_client._client:
                sync_redis_client._client.setex(f"sync:{sync_id}", 3600, json.dumps(status))
        except:
            pass
        else:
            sync_status_store[sync_id] = status
            
    except Exception as e:
        # Update status to failed
        status = {
            "status": "failed",
            "table": table_name,
            "ticker": ticker,
            "progress": f"Error: {str(e)}",
            "progress_percent": 0.0,
            "started_at": datetime.now().isoformat(),
            "failed_at": datetime.now().isoformat(),
            "error": str(e)
        }
        try:
            if 'HAS_REDIS' in globals() and HAS_REDIS and 'sync_redis_client' in globals() and sync_redis_client and sync_redis_client._client:
                sync_redis_client._client.setex(f"sync:{sync_id}", 3600, json.dumps(status))
        except:
            pass
        else:
            sync_status_store[sync_id] = status
    finally:
        db.close()

@app.post("/api/database/sync/{table_name}")
async def sync_table_data(
    table_name: str,
    ticker: Optional[str] = Query(None, description="Sync for specific ticker, or all if not provided"),
    days: int = Query(30, ge=1, le=365, description="Number of days for market_data sync"),
    db: Session = Depends(get_db)
):
    """Sync data for a specific table (runs in background)"""
    # Check if sync service is available
    if not SYNC_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Sync service is not available. Please check service logs for details."
        )
    
    # Handle growth_metrics separately (it's already an endpoint)
    if table_name == "growth_metrics":
        return await sync_growth_metrics(ticker, db)
    
    sync_functions = {
        "financial_data": "financial_data",
        "market_data": "market_data",
        "shares_outstanding": "shares_outstanding"
    }
    
    if table_name not in sync_functions:
        raise HTTPException(
            status_code=400, 
            detail=f"Table '{table_name}' is not supported for sync. Supported tables: {', '.join(sync_functions.keys())}, growth_metrics"
        )
    
    # Generate sync ID (use simple format for status lookup)
    sync_id = f"{table_name}_{ticker or 'all'}"
    
    # Start sync in background using threading (since sync functions are blocking)
    import threading
    thread = threading.Thread(
        target=perform_sync_sync,
        args=(table_name, ticker, days, sync_id),
        daemon=True
    )
    thread.start()
    
    return {
        "message": f"Sync started for {table_name}",
        "table": table_name,
        "sync_id": sync_id,
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/database/sync/{table_name}/status")
async def get_sync_status(
    table_name: str,
    ticker: Optional[str] = Query(None)
):
    """Get sync status for a table"""
    import json
    sync_id = f"{table_name}_{ticker or 'all'}"
    
    # Try to get from Redis first
    if HAS_REDIS and sync_redis_client and sync_redis_client._client:
        try:
            status_data = sync_redis_client._client.get(f"sync:{sync_id}")
            if status_data:
                return json.loads(status_data)
        except Exception as e:
            pass
    
    # Fallback to memory store
    if sync_id in sync_status_store:
        return sync_status_store[sync_id]
    
    # Check for any matching key
    for key, status in sync_status_store.items():
        if key.startswith(sync_id):
            return status
    
    return {
        "status": "not_found",
        "message": "No sync status found. Sync may not have started yet."
    }


@app.get("/api/database/sync/jobs")
async def list_sync_jobs():
    """List all active sync jobs"""
    import json
    jobs = []
    
    # Get jobs from Redis
    if HAS_REDIS and sync_redis_client and sync_redis_client._client:
        try:
            # Get all sync keys from Redis
            keys = sync_redis_client._client.keys("sync:*")
            for key in keys:
                try:
                    key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                    sync_id = key_str.replace("sync:", "")
                    status_data = sync_redis_client._client.get(key_str)
                    if status_data:
                        status = json.loads(status_data)
                        status['sync_id'] = sync_id
                        jobs.append(status)
                except Exception as e:
                    continue
        except Exception as e:
            pass
    
    # Add jobs from memory store
    for sync_id, status in sync_status_store.items():
        # Check if not already added from Redis
        if not any(j.get('sync_id') == sync_id for j in jobs):
            status_copy = status.copy()
            status_copy['sync_id'] = sync_id
            jobs.append(status_copy)
    
    # Sort by started_at (most recent first)
    jobs.sort(key=lambda x: x.get('started_at', ''), reverse=True)
    
    # Filter out completed/failed jobs older than 1 hour
    from datetime import datetime, timedelta
    cutoff_time = datetime.now() - timedelta(hours=1)
    active_jobs = []
    completed_jobs = []
    
    for job in jobs:
        started_at_str = job.get('started_at')
        if started_at_str:
            try:
                started_at = datetime.fromisoformat(started_at_str.replace('Z', '+00:00'))
                if started_at.tzinfo:
                    started_at = started_at.replace(tzinfo=None)
                cutoff = cutoff_time.replace(tzinfo=None)
                
                status = job.get('status', 'unknown')
                if status in ['running', 'pending']:
                    active_jobs.append(job)
                elif status in ['completed', 'failed'] and started_at > cutoff:
                    completed_jobs.append(job)
            except:
                # If parsing fails, include it anyway
                if job.get('status') in ['running', 'pending']:
                    active_jobs.append(job)
        else:
            if job.get('status') in ['running', 'pending']:
                active_jobs.append(job)
    
    return {
        "active_jobs": active_jobs,
        "recent_completed": completed_jobs,
        "total_active": len(active_jobs),
        "total_recent_completed": len(completed_jobs)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

