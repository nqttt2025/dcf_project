# Sync Service Architecture

**Version:** 2.0  
**Last Updated:** 2025-12-30

## Tổng Quan

Sync Service là service chuyên biệt xử lý tất cả hoạt động đồng bộ dữ liệu. Service này kết nối **trực tiếp** đến PostgreSQL để đảm bảo hiệu suất và tính nhất quán.

## Kiến trúc

```
┌─────────────────────────────────────────────────────────────────┐
│                      SYNC SERVICE                                │
│                    (sync-service:8004)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Data Fetcher │  │ Job Manager  │  │   API Layer  │          │
│  │              │  │              │  │              │          │
│  │ - vnstock    │  │ - CRUD jobs  │  │ - REST APIs  │          │
│  │ - Parse data │  │ - Execution  │  │ - Progress   │          │
│  │ - Transform  │  │ - Logs       │  │ - Status     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                │
│                            │                                    │
│  ┌─────────────────────────┴─────────────────────────┐         │
│  │              PostgreSQL Connection                 │         │
│  │             (Direct via SQLAlchemy)                │         │
│  └───────────────────────────────────────────────────┘         │
│                            │                                    │
└────────────────────────────┼────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
    ┌─────────┐         ┌─────────┐         ┌─────────┐
    │ vnstock │         │PostgreSQL│         │ Redis   │
    │   API   │         │         │         │ Cache   │
    └─────────┘         └─────────┘         └─────────┘
```

## Modules

### 1. Data Fetcher (`data_fetcher.py`)
- **Chức năng**: Fetch và transform data từ vnstock API
- **Kết nối**: Trực tiếp đến PostgreSQL qua SQLAlchemy
- **Functions**:
  - `sync_current_price(db, ticker)` - Sync giá hiện tại
  - `sync_market_data(db, ticker, days)` - Sync OHLCV data
  - `sync_financial_data(db, ticker)` - Sync báo cáo tài chính
  - `sync_shares_outstanding(db, ticker)` - Sync số cổ phiếu
  - `sync_base_pe(db, ticker)` - Cập nhật base PE

### 2. Database Connection (`database.py`)
- **Chức năng**: Quản lý kết nối PostgreSQL
- **Technology**: SQLAlchemy với connection pooling
- **Features**:
  - Connection pool (size=5, max_overflow=10)
  - Auto-reconnect
  - Session management

### 3. Job Manager (`main.py`)
- **Chức năng**: Quản lý sync jobs
- **Storage**: In-memory (sẽ migrate sang PostgreSQL)
- **Features**:
  - Job CRUD operations
  - Execution tracking
  - Progress updates
  - Logs management

## API Endpoints

### Health & Status
```http
GET /health
GET /
```

### Direct Sync APIs
```http
POST /api/sync/current-price?ticker={ticker}
POST /api/sync/market-data?ticker={ticker}&days={days}
POST /api/sync/financial-data?ticker={ticker}
POST /api/sync/shares-outstanding?ticker={ticker}
POST /api/sync/base-pe?ticker={ticker}
POST /api/sync/{table_name}?ticker={ticker}&days={days}
```

### Job Management APIs
```http
GET  /api/jobs                              # List all jobs
GET  /api/jobs/{job_id}                     # Get job details
POST /api/jobs                              # Create new job
POST /api/jobs/{job_id}/run                 # Run job
POST /api/jobs/{job_id}/stop                # Stop job
GET  /api/jobs/{job_id}/executions/{id}     # Get execution details
GET  /api/jobs/{job_id}/executions/{id}/logs # Get execution logs (SSE)
```

## Job Types

| Job Type | Description | Parameters |
|----------|-------------|------------|
| `current_price` | Sync giá hiện tại | `ticker` (optional) |
| `market_data` | Sync OHLCV historical | `ticker`, `days` |
| `financial_data` | Sync income/cashflow | `ticker` |
| `shares_outstanding` | Sync số cổ phiếu | `ticker` |
| `base_pe` | Update base PE ratios | `ticker` |

## Sync Flow

### 1. Current Price Sync
```
Request → Sync Service → vnstock.quote() → Parse price
                                              │
                      PostgreSQL ◄────────────┘
                      (market_data table)
                              │
                      Redis cache update
```

### 2. Market Data Sync
```
Request → Sync Service → vnstock.history() → Parse OHLCV
                                               │
                      PostgreSQL ◄─────────────┘
                      (market_data table)
                              │
                      Redis cache update
```

### 3. Financial Data Sync
```
Request → Sync Service → vnstock.finance() → Parse statements
                         ├── income_statement
                         └── cash_flow
                                   │
                      PostgreSQL ◄─┘
                      (financial_data table)
```

## Configuration

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@postgres:5432/dcf_db
REDIS_URL=redis://redis:6379/0
```

### Docker Compose
```yaml
sync-service:
  build:
    dockerfile: services/sync-service/Dockerfile.sync
  environment:
    - DATABASE_URL=postgresql://dcf_user:dcf_password@postgres:5432/dcf_db
    - REDIS_URL=redis://redis:6379/0
  depends_on:
    - postgres
    - redis
  ports:
    - "8004:8004"
```

## Usage Examples

### Sync Current Price
```bash
# Single ticker
curl -X POST "http://localhost:8004/api/sync/current-price?ticker=FPT"

# All active stocks
curl -X POST "http://localhost:8004/api/sync/current-price"
```

### Sync Market Data
```bash
# Last 7 days for FPT
curl -X POST "http://localhost:8004/api/sync/market-data?ticker=FPT&days=7"

# Last 30 days for all stocks
curl -X POST "http://localhost:8004/api/sync/market-data?days=30"
```

### Create and Run Job
```bash
# Create job
curl -X POST "http://localhost:8004/api/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "daily_price_sync",
    "name": "Daily Price Sync",
    "job_type": "current_price",
    "schedule_type": "manual",
    "enabled": true
  }'

# Run job
curl -X POST "http://localhost:8004/api/jobs/daily_price_sync/run"
```

## Frontend Integration

### Jobs Management Page
**URL**: `http://localhost:8081/static/jobs.html`

**Features**:
- Job list với status indicators
- Run/Stop buttons
- Execution history
- Real-time logs viewer (SSE)
- Progress tracking

## Error Handling

### Rate Limiting
- vnstock API có rate limit
- Delay 1-2 giây giữa các requests
- Retry với exponential backoff

### Common Errors
| Error | Cause | Solution |
|-------|-------|----------|
| Connection refused | PostgreSQL not ready | Wait for healthcheck |
| Rate limited | Too many vnstock calls | Increase delay |
| Ticker not found | Invalid ticker | Verify ticker exists |

## Performance

### Recommendations
- Sync `current_price` cho quick updates
- Sync `market_data` với 7 days cho daily sync
- Sync `financial_data` weekly (data doesn't change often)

### Parallel Processing
- Multiple tickers được sync tuần tự (avoid rate limit)
- Different job types có thể chạy parallel

## Monitoring

### Health Check
```bash
curl http://localhost:8004/health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "sync-service",
  "database": "connected",
  "database_info": {
    "connected": true,
    "database": "dcf_db",
    "version": "PostgreSQL 15.x"
  }
}
```

### Logs
```bash
docker logs dcf-sync-service
```

## Migration Notes

### From Database Service
Previously, sync operations were in `database/data_fetcher.py`. Now:
- **Moved**: `data_fetcher.py` → `sync-service/data_fetcher.py`
- **Removed**: All `/api/database/sync/*` endpoints from database service
- **Database Service**: Now **read-only** for data viewing

### Benefits
- ✅ Clear separation of concerns
- ✅ Better error handling
- ✅ Reliable job execution
- ✅ Direct PostgreSQL connection
- ✅ Scalable architecture

---

**Version:** 2.0  
**Last Updated:** 2025-12-30

