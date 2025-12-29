"""
Database Service - Main FastAPI application
Manages database operations and data synchronization
"""
import os
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from typing import List, Optional
import redis
from datetime import datetime

from .database import get_db, engine, Base
from .models import Stock

app = FastAPI(
    title="Database Service",
    description="Database management service for VN30 stock data",
    version=os.getenv("APP_VERSION", "latest")
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
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
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "redis": redis_status,
        "timestamp": datetime.utcnow().isoformat()
    }


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

