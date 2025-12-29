# Database Integration Guide

**Hướng dẫn tích hợp database vào các services**

## 🎯 Overview

Tất cả các services trong dự án đã được cấu hình để có thể kết nối đến PostgreSQL database thông qua shared database client utility.

## 🔌 Database Connection

### Connection String

```
postgresql://dcf_user:dcf_password@postgres:5432/dcf_db
```

### Environment Variable

Tất cả services có `DATABASE_URL` environment variable:
- **DCF Service**: `DATABASE_URL=postgresql://dcf_user:dcf_password@postgres:5432/dcf_db`
- **Stock Service**: `DATABASE_URL=postgresql://dcf_user:dcf_password@postgres:5432/dcf_db`
- **Gateway Service**: `DATABASE_URL=postgresql://dcf_user:dcf_password@postgres:5432/dcf_db`
- **Database Service**: `DATABASE_URL=postgresql://dcf_user:dcf_password@postgres:5432/dcf_db`

## 📦 Database Client Utility

### Location

`src/utils/database_client.py`

### Usage

```python
from src.utils.database_client import (
    get_db,
    check_database_connection,
    get_database_info
)

# Check if database is available
if check_database_connection():
    # Use database with context manager
    with get_db() as db:
        # Your database operations here
        result = db.execute(text("SELECT * FROM stocks"))
        stocks = result.fetchall()

# Get database information
db_info = get_database_info()
print(f"Database: {db_info['database']}")
print(f"Version: {db_info['version']}")
print(f"Active connections: {db_info['active_connections']}")
```

### Functions

1. **`get_db()`** - Context manager for database session
   - Automatically commits on success
   - Rolls back on error
   - Closes session when done

2. **`check_database_connection()`** - Check if database is available
   - Returns `True` if connected
   - Returns `False` if not connected

3. **`get_database_info()`** - Get database information
   - Returns dict with database name, version, connection count

## 🏗️ Service Configuration

### Docker Compose (Production)

**docker-compose.yml:**
- PostgreSQL service với health check
- Database Service (port 8003)
- Tất cả services có `DATABASE_URL` environment variable
- Tất cả services `depends_on: postgres`

### Docker Compose (Development)

**docker-compose.dev.yml:**
- PostgreSQL service với hot reload volumes
- Database Service với hot reload
- Tất cả services có `DATABASE_URL` environment variable
- Tất cả services `depends_on: postgres`

## 🔍 Health Checks

### DCF Service

```python
@app.get("/health")
def health_check():
    health_status = {"status": "healthy", "service": "dcf-service"}
    
    # Check database connection
    try:
        from src.utils.database_client import check_database_connection, get_database_info
        db_connected = check_database_connection()
        health_status["database"] = "connected" if db_connected else "disconnected"
        if db_connected:
            db_info = get_database_info()
            health_status["database_info"] = db_info
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
    
    return health_status
```

### Stock Service

Tương tự như DCF Service.

### Gateway Service

```python
@app.get("/health")
async def health_check():
    # Check all services including database
    # Check database connection directly
    gateway_db_status = {}
    try:
        from src.utils.database_client import check_database_connection, get_database_info
        db_connected = check_database_connection()
        gateway_db_status["connected"] = db_connected
        if db_connected:
            gateway_db_status["info"] = get_database_info()
    except Exception as e:
        gateway_db_status["error"] = str(e)
    
    return {
        "status": "healthy",
        "service": "gateway",
        "services": services_status,
        "gateway_database": gateway_db_status
    }
```

## 📊 Example Usage in Services

### Example 1: Query Stocks

```python
from src.utils.database_client import get_db
from sqlalchemy import text

def get_all_stocks():
    with get_db() as db:
        result = db.execute(text("SELECT * FROM stocks WHERE is_active = TRUE"))
        return [dict(row) for row in result]
```

### Example 2: Insert Data

```python
from src.utils.database_client import get_db
from sqlalchemy import text

def create_stock(ticker: str, name: str):
    with get_db() as db:
        db.execute(
            text("INSERT INTO stocks (ticker, name) VALUES (:ticker, :name)"),
            {"ticker": ticker, "name": name}
        )
        db.commit()
```

### Example 3: Check Before Using

```python
from src.utils.database_client import get_db, check_database_connection

def get_stock_from_db(ticker: str):
    if not check_database_connection():
        # Fallback to file-based or API
        return get_stock_from_file(ticker)
    
    with get_db() as db:
        result = db.execute(
            text("SELECT * FROM stocks WHERE ticker = :ticker"),
            {"ticker": ticker}
        )
        return result.fetchone()
```

## 🔄 Migration Strategy

### Phase 1: Database Available (Current)
- ✅ All services can connect to database
- ✅ Health checks show database status
- ✅ Services can use database_client utility
- ⚠️ Services still use file-based storage (backward compatible)

### Phase 2: Gradual Migration
- Services start using database for new data
- Keep file-based as fallback
- Compare results between database and files

### Phase 3: Full Migration
- All data in database
- File-based storage as backup only
- Database becomes primary source

## 🚀 Testing Database Connection

### From Service

```python
# In any service
from src.utils.database_client import check_database_connection, get_database_info

# Check connection
if check_database_connection():
    print("✅ Database connected")
    info = get_database_info()
    print(f"Database: {info['database']}")
    print(f"Version: {info['version']}")
else:
    print("❌ Database not connected")
```

### From Health Check Endpoint

```bash
# Check DCF Service
curl http://localhost:8001/health

# Check Stock Service
curl http://localhost:8002/health

# Check Gateway Service
curl http://localhost:8000/health

# Check Database Service
curl http://localhost:8003/health
```

## 📋 Checklist

- ✅ PostgreSQL service in docker-compose.yml
- ✅ PostgreSQL service in docker-compose.dev.yml
- ✅ Database Service created
- ✅ Database client utility created
- ✅ All services have DATABASE_URL
- ✅ All services depend_on postgres
- ✅ Health checks include database status
- ✅ Frontend monitoring page created

## 🔗 Related Documents

- [Database Design](database-design.md) - Schema design
- [Database Service](database-service.md) - Service design
- [Data Sync Strategy](data-sync-strategy.md) - Sync strategy

---

**Status**: ✅ All services can connect to database

