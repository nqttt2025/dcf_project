# Microservices Architecture

**Version:** 3.0  
**Last Updated:** 2025-12-30

DCF Analysis Project được tổ chức theo kiến trúc microservices với phân chia trách nhiệm rõ ràng.

## Kiến trúc Tổng quan

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND LAYER                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Frontend (Nginx) :8081                           │    │
│  │     index.html | stock-info.html | database.html | jobs.html        │    │
│  │                        monitoring.html                              │    │
│  └───────────────────────────────┬─────────────────────────────────────┘    │
└──────────────────────────────────┼──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY LAYER                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Gateway (FastAPI) :8000                          │    │
│  │           Routes, Load Balancing, Health Checks, SSL                │    │
│  └───────────────────────────────┬─────────────────────────────────────┘    │
└──────────────────────────────────┼──────────────────────────────────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
           ▼                       ▼                       ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   DCF Service    │    │  Stock Service   │    │  Sync Service    │
│   (FastAPI)      │    │   (FastAPI)      │    │   (FastAPI)      │
│    :8001         │    │    :8002         │    │    :8004         │
├──────────────────┤    ├──────────────────┤    ├──────────────────┤
│ DCF Analysis     │    │ Stock Info       │    │ Data Sync        │
│ Graham Valuation │    │ Price Fetching   │    │ Job Management   │
│ Result Storage   │    │ Config Files     │    │ vnstock API      │
└────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘
         │                       │                       │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           ▼                     ▼                     ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Database Service │    │   PostgreSQL     │    │     Redis        │
│   (FastAPI)      │    │     :5432        │    │     :6379        │
│    :8003         │    │                  │    │                  │
├──────────────────┤    ├──────────────────┤    ├──────────────────┤
│ Data Viewing     │    │ Persistent       │    │ Caching          │
│ Table Schema     │    │ Storage          │    │ Status Tracking  │
│ Stock Info API   │    │ Stock Data       │    │ Analysis Status  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

## Services Chi Tiết

### 1. Frontend Service (`services/frontend/`)
- **Role**: Serve static files và reverse proxy
- **Technology**: Nginx
- **Port**: 8081
- **Pages**:
  - `/` - Dashboard chính
  - `/static/stock-info.html` - Thông tin cổ phiếu
  - `/static/database.html` - Quản lý database
  - `/static/jobs.html` - Quản lý sync jobs
  - `/static/monitoring.html` - System monitoring

### 2. Gateway Service (`services/gateway/`)
- **Role**: API Gateway - Route requests, health checks, SSL termination
- **Technology**: FastAPI
- **Port**: 8000
- **Key Endpoints**:
  - `GET /health` - Health check tất cả services
  - `GET /api/stocks` - List stocks
  - `POST /api/stocks/{ticker}/run` - Run DCF analysis
  - `GET /api/database/*` - Database operations
  - `POST /api/sync/*` - Sync operations

### 3. DCF Service (`services/dcf/`)
- **Role**: Xử lý phân tích DCF và Graham valuation
- **Technology**: FastAPI
- **Port**: 8001
- **Endpoints**:
  - `POST /analyze/{ticker}` - Run DCF analysis (async)
  - `GET /analysis/{ticker}` - Get analysis result
  - `GET /status` - Running analyses status

### 4. Stock Service (`services/stock/`)
- **Role**: Quản lý thông tin và giá cổ phiếu
- **Technology**: FastAPI
- **Port**: 8002
- **Endpoints**:
  - `GET /stocks` - List all stocks với current price
  - `GET /stocks/{ticker}` - Stock detail
  - `GET /stocks/{ticker}/status` - Analysis status

### 5. Sync Service (`services/sync-service/`) ⭐ NEW
- **Role**: **Tất cả sync operations** - Kết nối trực tiếp PostgreSQL
- **Technology**: FastAPI + SQLAlchemy
- **Port**: 8004
- **Key Features**:
  - Kết nối **trực tiếp** đến PostgreSQL (không qua Database Service)
  - Gọi vnstock API để fetch data
  - Job management (create, run, stop, history)
  - Redis cache updates
- **Endpoints**:
  - `POST /api/sync/current-price` - Sync giá hiện tại
  - `POST /api/sync/market-data` - Sync OHLCV data
  - `POST /api/sync/financial-data` - Sync báo cáo tài chính
  - `POST /api/sync/shares-outstanding` - Sync số lượng cổ phiếu
  - `POST /api/sync/base-pe` - Cập nhật base PE
  - `GET /api/jobs` - List sync jobs
  - `POST /api/jobs/{job_id}/run` - Run job

### 6. Database Service (`services/database/`)
- **Role**: **Data viewing only** - Không có sync logic
- **Technology**: FastAPI + SQLAlchemy
- **Port**: 8003
- **Key Features**:
  - GET endpoints để xem data
  - Table schema information
  - Stock comprehensive info
  - Database statistics
- **Endpoints**:
  - `GET /api/database/stocks` - List stocks
  - `GET /api/database/stocks/{ticker}` - Stock comprehensive info
  - `GET /api/database/tables` - List tables
  - `GET /api/database/stats` - Database statistics

### 7. PostgreSQL Database
- **Role**: Persistent data storage
- **Technology**: PostgreSQL 15-alpine
- **Port**: 5432 (container), 5433 (host)
- **Tables**: stocks, market_data, financial_data, shares_outstanding, growth_metrics

### 8. Redis Cache
- **Role**: Caching và status tracking
- **Technology**: Redis 7-alpine
- **Port**: 6379
- **Usage**:
  - Analysis status tracking (`analysis:{ticker}`)
  - Market data cache (`market:{ticker}`)
  - Financial data cache (`financial:{ticker}`)

## Phân Chia Trách Nhiệm (NEW Architecture)

```
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICE RESPONSIBILITIES                      │
├────────────────────┬────────────────────────────────────────────┤
│    Sync Service    │         Database Service                   │
│  (sync-service)    │       (database service)                   │
├────────────────────┼────────────────────────────────────────────┤
│ ✓ vnstock API      │ ✓ Data viewing (GET)                      │
│ ✓ Data fetching    │ ✓ Table schema                            │
│ ✓ PostgreSQL write │ ✓ Stock info                              │
│ ✓ Job management   │ ✓ Database statistics                     │
│ ✓ Redis cache      │ ✗ NO sync operations                      │
│ ✓ Scheduling       │ ✗ NO vnstock calls                        │
└────────────────────┴────────────────────────────────────────────┘
```

## Communication Flow

### Sync Data Flow
```
User clicks "Sync" on Frontend
         │
         ▼
    Gateway (/api/sync/*)
         │
         ▼
    Sync Service ────────────► vnstock API
         │                         │
         ▼                         │
    PostgreSQL ◄───────────────────┘
         │
         ▼
    Redis (cache update)
```

### Stock Info Flow
```
User opens Stock Info page
         │
         ▼
    Gateway (/api/database/stocks/{ticker})
         │
         ▼
    Database Service (read-only)
         │
         ▼
    PostgreSQL
         │
         ▼
    Return comprehensive stock info
```

### DCF Analysis Flow
```
User clicks "Run DCF"
         │
         ▼
    Gateway (/api/stocks/{ticker}/run)
         │
         ▼
    DCF Service
         │
         ├──► Update Redis status
         ├──► Read from PostgreSQL/Redis
         ├──► Calculate DCF & Graham
         └──► Save results
```

## Docker Compose Services

```yaml
services:
  redis:          # Cache Service
  postgres:       # Database
  gateway:        # API Gateway
  dcf:            # DCF Analysis
  stock:          # Stock Info
  database:       # Data Viewing (read-only)
  sync-service:   # Data Sync (write)
  frontend:       # Nginx Static Files
```

### Service Dependencies
```
postgres ◄─── database, sync-service, dcf, stock, gateway
redis    ◄─── dcf, stock, sync-service, gateway
database ◄─── gateway
sync-service ◄─── gateway
dcf, stock ◄─── gateway
gateway  ◄─── frontend
```

## Ports Summary

| Service | Container Port | Host Port | URL |
|---------|---------------|-----------|-----|
| Frontend | 80 | 8081 | http://localhost:8081 |
| Gateway | 8000 | 8000 | https://localhost:8000 |
| DCF | 8001 | 8001 | http://localhost:8001 |
| Stock | 8002 | 8002 | http://localhost:8002 |
| Database | 8003 | 8003 | http://localhost:8003 |
| Sync Service | 8004 | 8004 | http://localhost:8004 |
| PostgreSQL | 5432 | 5433 | localhost:5433 |
| Redis | 6379 | 6379 | localhost:6379 |

## Health Checks

Mỗi service có health check endpoint:
- Gateway: `/health` (checks all services)
- DCF: `/health`
- Stock: `/health`
- Database: `/health`
- Sync Service: `/health`
- Frontend: `/health` (nginx)
- Redis: `redis-cli ping`

## Development

### Start All Services
```bash
make docker-up
```

### Rebuild Services
```bash
make docker-rebuild
```

### View Logs
```bash
make docker-logs
```

### Stop Services
```bash
make docker-down
```

## API Documentation

- **Swagger UI**: https://localhost:8000/docs
- **ReDoc**: https://localhost:8000/redoc

---

**Version:** 3.0 (Refactored Architecture với Sync Service)  
**Last Updated:** 2025-12-30
