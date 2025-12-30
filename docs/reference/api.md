# API Reference

**Version:** 3.0  
**Last Updated:** 2025-12-30

## 🌐 Base URLs

| Service | URL | Description |
|---------|-----|-------------|
| Gateway | `https://localhost:8000` | Main API entry point |
| DCF Service | `http://localhost:8001` | DCF Analysis |
| Stock Service | `http://localhost:8002` | Stock Information |
| Database Service | `http://localhost:8003` | Data Viewing |
| Sync Service | `http://localhost:8004` | Data Synchronization |

---

## 📚 Gateway API

Gateway routes requests đến các services phía sau.

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "dcf": {"status": "healthy"},
    "stock": {"status": "healthy"},
    "database": {"status": "healthy"},
    "sync-service": {"status": "healthy"}
  },
  "gateway_database": {"database": "connected"}
}
```

### Stock Operations

#### List Stocks
```http
GET /api/stocks
```

#### Get Stock Detail
```http
GET /api/stocks/{ticker}
```

#### Run DCF Analysis
```http
POST /api/stocks/{ticker}/run
```

#### Get Analysis Result
```http
GET /api/analysis/{ticker}
```

---

## 🗄️ Database Service API (Read-Only)

Database Service chỉ cung cấp **read operations**.

### Health Check
```http
GET /health
```

### List Stocks
```http
GET /api/database/stocks?skip=0&limit=100&vn30_only=false
```

**Response:**
```json
{
  "total": 30,
  "skip": 0,
  "limit": 100,
  "stocks": [
    {
      "id": 1,
      "ticker": "FPT",
      "name": "FPT Corporation",
      "sector": "Technology",
      "is_vn30": true,
      "is_active": true
    }
  ]
}
```

### Get Stock Comprehensive Info
```http
GET /api/database/stocks/{ticker}
```

**Response:**
```json
{
  "ticker": "FPT",
  "stock": {...},
  "market_data": {
    "close_price": 96500,
    "open_price": 96000,
    "high_price": 97000,
    "low_price": 95500,
    "volume": 1234567
  },
  "financial_data": {
    "ttm_ocf": 5000000000000,
    "ttm_capex": 1000000000000,
    "ttm_fcf": 4000000000000
  },
  "shares_outstanding": {
    "shares_outstanding": 1145678900
  },
  "metrics": {
    "current_price": 96500,
    "market_cap": 110578033850000,
    "pe_ratio": 15.5,
    "eps": 6226,
    "ttm_fcf": 4000000000000,
    "shares": 1145678900
  }
}
```

### Database Statistics
```http
GET /api/database/stats
```

### List Tables
```http
GET /api/database/tables
```

### Get Table Schema
```http
GET /api/database/tables/{table_name}/schema
```

### Get Table Data
```http
GET /api/database/tables/{table_name}/data?skip=0&limit=100
```

### Get Database Relationships
```http
GET /api/database/relationships
```

---

## 🔄 Sync Service API (Data Synchronization)

Sync Service xử lý tất cả hoạt động đồng bộ dữ liệu.

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "sync-service",
  "database": "connected",
  "database_info": {
    "connected": true,
    "database": "dcf_db"
  }
}
```

### Direct Sync Endpoints

#### Sync Current Price
```http
POST /api/sync/current-price?ticker={ticker}
```

**Parameters:**
- `ticker` (optional): Sync specific ticker, or all if not provided

**Response:**
```json
{
  "processed": 1,
  "success": 1,
  "failed": 0,
  "details": [
    {
      "ticker": "FPT",
      "status": "success",
      "price": 96500.0,
      "updated": true
    }
  ]
}
```

#### Sync Market Data
```http
POST /api/sync/market-data?ticker={ticker}&days={days}
```

**Parameters:**
- `ticker` (optional): Sync specific ticker
- `days` (default: 7): Number of days to sync

#### Sync Financial Data
```http
POST /api/sync/financial-data?ticker={ticker}
```

#### Sync Shares Outstanding
```http
POST /api/sync/shares-outstanding?ticker={ticker}
```

#### Sync Base PE
```http
POST /api/sync/base-pe?ticker={ticker}
```

#### Generic Sync Endpoint
```http
POST /api/sync/{table_name}?ticker={ticker}&days={days}
```

**Valid table_name values:**
- `market_data`
- `financial_data`
- `shares_outstanding`
- `current_price`
- `base_pe`

### Job Management

#### List Jobs
```http
GET /api/jobs
```

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "daily_price_sync",
      "name": "Daily Price Sync",
      "job_type": "current_price",
      "schedule_type": "manual",
      "enabled": true,
      "status": "idle",
      "last_execution": null
    }
  ],
  "total": 1
}
```

#### Get Job Details
```http
GET /api/jobs/{job_id}
```

#### Create Job
```http
POST /api/jobs
Content-Type: application/json

{
  "job_id": "daily_price_sync",
  "name": "Daily Price Sync",
  "description": "Sync current prices daily",
  "job_type": "current_price",
  "schedule_type": "manual",
  "config": {
    "ticker": null
  },
  "enabled": true
}
```

#### Run Job
```http
POST /api/jobs/{job_id}/run
```

**Response:**
```json
{
  "message": "Job 'daily_price_sync' started",
  "execution_id": "exec_abc123",
  "status": "pending"
}
```

#### Stop Job
```http
POST /api/jobs/{job_id}/stop?execution_id={execution_id}
```

#### Get Execution Details
```http
GET /api/jobs/{job_id}/executions/{execution_id}
```

#### Get Execution Logs (SSE)
```http
GET /api/jobs/{job_id}/executions/{execution_id}/logs
```

---

## 🔧 DCF Service API

### Health Check
```http
GET /health
```

### Run Analysis
```http
POST /analyze/{ticker}
```

**Response:**
```json
{
  "message": "Analysis started",
  "ticker": "FPT"
}
```

### Get Analysis Result
```http
GET /analysis/{ticker}
```

### Service Status
```http
GET /status
```

---

## 📊 Stock Service API

### Health Check
```http
GET /health
```

### List Stocks
```http
GET /stocks
```

### Get Stock Detail
```http
GET /stocks/{ticker}
```

### Get Stock Status
```http
GET /stocks/{ticker}/status
```

### Service Status
```http
GET /status
```

---

## 🔒 Authentication

Hiện tại API không yêu cầu authentication.

---

## ⚠️ Error Responses

### Standard Error Format
```json
{
  "detail": "Error message here"
}
```

### Common HTTP Status Codes
| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

---

## 📖 API Documentation

Interactive API documentation available at:
- **Swagger UI**: https://localhost:8000/docs
- **ReDoc**: https://localhost:8000/redoc

---

**Version:** 3.0  
**Last Updated:** 2025-12-30

**Back to:** [Reference README](README.md)
