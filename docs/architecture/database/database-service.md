# Database Service Design

**Database Service cho VN30 Stock Data trong Microservices Architecture**

## 🎯 Overview

Database Service là một microservice mới được thiết kế để quản lý dữ liệu cổ phiếu VN30, tuân thủ nguyên tắc microservices.

## 🏗️ Service Architecture

### Service Details

**Service Name**: `database`  
**Technology**: FastAPI + SQLAlchemy + PostgreSQL  
**Port**: 8003  
**Base Path**: `/api/database`

### Responsibilities

1. **Data Management**
   - CRUD operations cho stock data
   - Data validation và sanitization
   - Data consistency management

2. **Data Synchronization**
   - Sync với vnstock API
   - Scheduled sync jobs
   - Error handling và retry logic

3. **Query Optimization**
   - Efficient queries
   - Caching strategy
   - Index management

4. **Data Access Layer**
   - Provide APIs cho other services
   - Abstract database complexity
   - Handle transactions

## 📁 Service Structure

```
services/database/
├── main.py                 # FastAPI application
├── Dockerfile              # Docker image
├── requirements.txt        # Dependencies
├── models/                 # SQLAlchemy models
│   ├── __init__.py
│   ├── stock.py
│   ├── financial_data.py
│   ├── market_data.py
│   └── ...
├── schemas/                # Pydantic schemas
│   ├── __init__.py
│   ├── stock.py
│   ├── financial.py
│   └── ...
├── crud/                   # CRUD operations
│   ├── __init__.py
│   ├── stock.py
│   ├── financial.py
│   └── ...
├── sync/                   # Data sync logic
│   ├── __init__.py
│   ├── vnstock_sync.py
│   └── scheduler.py
├── cache/                  # Cache utilities
│   ├── __init__.py
│   └── redis_cache.py
└── database.py             # Database connection
```

## 🔌 API Endpoints

### Stock Endpoints

```python
# List all stocks
GET /api/database/stocks
Response: List[StockSchema]

# Get VN30 stocks
GET /api/database/stocks/vn30
Response: List[StockSchema]

# Get stock by ticker
GET /api/database/stocks/{ticker}
Response: StockSchema

# Create stock (admin)
POST /api/database/stocks
Body: StockCreateSchema
Response: StockSchema

# Update stock (admin)
PUT /api/database/stocks/{ticker}
Body: StockUpdateSchema
Response: StockSchema
```

### Financial Data Endpoints

```python
# Get financial data
GET /api/database/stocks/{ticker}/financial
Query params: period_type, start_date, end_date
Response: List[FinancialDataSchema]

# Get latest financial data
GET /api/database/stocks/{ticker}/financial/latest
Response: FinancialDataSchema

# Get TTM financial data
GET /api/database/stocks/{ticker}/financial/ttm
Response: FinancialTTMSchema

# Sync financial data
POST /api/database/stocks/{ticker}/financial/sync
Response: SyncResultSchema
```

### Market Data Endpoints

```python
# Get market data
GET /api/database/stocks/{ticker}/market
Query params: start_date, end_date
Response: List[MarketDataSchema]

# Get latest market price
GET /api/database/stocks/{ticker}/market/latest
Response: MarketDataSchema

# Sync market data
POST /api/database/stocks/{ticker}/market/sync
Response: SyncResultSchema
```

### Shares Outstanding Endpoints

```python
# Get shares outstanding
GET /api/database/stocks/{ticker}/shares
Query params: start_date, end_date
Response: List[SharesOutstandingSchema]

# Get latest shares
GET /api/database/stocks/{ticker}/shares/latest
Response: SharesOutstandingSchema

# Sync shares
POST /api/database/stocks/{ticker}/shares/sync
Response: SyncResultSchema
```

### DCF Config Endpoints

```python
# Get DCF config
GET /api/database/stocks/{ticker}/config
Response: DCFConfigSchema

# Update DCF config
PUT /api/database/stocks/{ticker}/config
Body: DCFConfigUpdateSchema
Response: DCFConfigSchema
```

### DCF Results Endpoints

```python
# Get DCF results
GET /api/database/stocks/{ticker}/results
Query params: start_date, end_date, limit
Response: List[DCFResultSchema]

# Get latest DCF result
GET /api/database/stocks/{ticker}/results/latest
Response: DCFResultSchema

# Save DCF result
POST /api/database/stocks/{ticker}/results
Body: DCFResultCreateSchema
Response: DCFResultSchema
```

### Sync Endpoints

```python
# Sync all data for ticker
POST /api/database/sync/{ticker}
Response: SyncResultSchema

# Sync all VN30 stocks
POST /api/database/sync/vn30
Response: BatchSyncResultSchema

# Get sync logs
GET /api/database/sync/logs
Query params: ticker, status, start_date, end_date
Response: List[SyncLogSchema]
```

## 🔄 Data Synchronization

### Sync Strategy

1. **Scheduled Sync** (Cron Jobs)
   - Financial data: Daily at 2 AM
   - Market data: Every 15 minutes during trading hours
   - Shares outstanding: Weekly on Sunday

2. **On-Demand Sync**
   - Triggered via API
   - Used for immediate updates

3. **Incremental Sync**
   - Only sync new/updated data
   - Track last sync timestamp

### Sync Process

```python
async def sync_financial_data(ticker: str):
    """
    1. Fetch data from vnstock
    2. Validate data
    3. Check for changes
    4. Insert/Update database
    5. Update cache
    6. Log sync result
    """
    pass
```

## 💾 Caching Strategy

### Redis Cache Keys

```python
# Stock info
f"stock:{ticker}:info"  # TTL: 1 hour

# Financial TTM
f"stock:{ticker}:financial:ttm"  # TTL: 6 hours

# Latest market price
f"stock:{ticker}:market:latest"  # TTL: 5 minutes

# Shares outstanding
f"stock:{ticker}:shares:latest"  # TTL: 1 day

# DCF config
f"stock:{ticker}:config"  # TTL: 1 day

# Latest DCF result
f"stock:{ticker}:result:latest"  # TTL: 1 hour
```

### Cache Invalidation

- On data sync: Invalidate related keys
- On config update: Invalidate config cache
- On new result: Invalidate result cache

## 🔐 Security

1. **Authentication**: JWT tokens cho admin endpoints
2. **Authorization**: Role-based access control
3. **Input Validation**: Pydantic schemas
4. **SQL Injection Prevention**: Parameterized queries
5. **Rate Limiting**: Limit API calls

## 📊 Monitoring

1. **Health Check**: `/health`
2. **Metrics**: Query performance, cache hit rate
3. **Logging**: Structured logging
4. **Alerts**: Sync failures, slow queries

## 🐳 Docker Integration

### docker-compose.yml Addition

```yaml
services:
  database-service:
    build:
      context: .
      dockerfile: services/database/Dockerfile
    image: dcf-project-database:latest
    container_name: dcf-database-service
    ports:
      - "8003:8003"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/dcf_db
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - postgres
      - redis
    networks:
      - dcf-network

  postgres:
    image: postgres:15-alpine
    container_name: dcf-postgres
    environment:
      - POSTGRES_USER=dcf_user
      - POSTGRES_PASSWORD=dcf_password
      - POSTGRES_DB=dcf_db
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - dcf-network
```

## 🔗 Integration với Services Khác

### Stock Service Integration

```python
# Stock Service queries Database Service
async def get_stock_info(ticker: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://database-service:8003/api/database/stocks/{ticker}"
        )
        return response.json()
```

### DCF Service Integration

```python
# DCF Service queries Database Service for data
async def get_financial_data_ttm(ticker: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://database-service:8003/api/database/stocks/{ticker}/financial/ttm"
        )
        return response.json()
```

## 📈 Performance Considerations

1. **Connection Pooling**: SQLAlchemy connection pool
2. **Query Optimization**: Use indexes, avoid N+1 queries
3. **Caching**: Aggressive caching với Redis
4. **Async Operations**: Async/await cho I/O operations
5. **Batch Operations**: Batch inserts/updates

## 🚀 Next Steps

1. Setup PostgreSQL trong docker-compose
2. Create Database Service structure
3. Implement models và schemas
4. Implement CRUD operations
5. Implement data sync với vnstock
6. Add caching layer
7. Integrate với Stock và DCF services
8. Testing và optimization

---

**Related Documents:**
- [Database Design](database-design.md) - Schema design
- [Microservices Architecture](microservices.md) - Overall architecture

