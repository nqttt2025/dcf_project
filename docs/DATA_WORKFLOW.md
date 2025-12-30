# Data Workflow

**Version:** 2.0  
**Last Updated:** 2025-12-30

## Workflow Hiện Tại (NEW Architecture)

### 1. Data Sync Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                       DATA SYNC WORKFLOW                             │
│                                                                      │
│  User triggers sync (via Frontend or API)                           │
│         │                                                            │
│         ▼                                                            │
│    Gateway (/api/sync/*)                                             │
│         │                                                            │
│         ▼                                                            │
│    ┌─────────────────────────────────────┐                          │
│    │         SYNC SERVICE                 │                          │
│    │  ┌─────────────────────────────┐    │                          │
│    │  │     data_fetcher.py         │    │      ┌──────────────┐   │
│    │  │  - sync_current_price()     │───────────►  vnstock API  │   │
│    │  │  - sync_market_data()       │    │      └──────────────┘   │
│    │  │  - sync_financial_data()    │    │                          │
│    │  │  - sync_shares_outstanding()│    │                          │
│    │  └─────────────┬───────────────┘    │                          │
│    │                │                     │                          │
│    │                ▼ Direct SQL          │                          │
│    │         ┌──────────────┐            │                          │
│    │         │  PostgreSQL  │            │                          │
│    │         └──────────────┘            │                          │
│    │                │                     │                          │
│    │                ▼                     │                          │
│    │         ┌──────────────┐            │                          │
│    │         │    Redis     │            │                          │
│    │         │  (cache)     │            │                          │
│    │         └──────────────┘            │                          │
│    └─────────────────────────────────────┘                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. Data Viewing Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                       DATA VIEWING WORKFLOW                          │
│                                                                      │
│  User opens Stock Info page                                         │
│         │                                                            │
│         ▼                                                            │
│    Frontend (stock-info.html)                                        │
│         │                                                            │
│         ▼                                                            │
│    Gateway (/api/database/stocks/{ticker})                           │
│         │                                                            │
│         ▼                                                            │
│    ┌─────────────────────────────────────┐                          │
│    │       DATABASE SERVICE               │                          │
│    │         (Read-only)                  │                          │
│    │                │                     │                          │
│    │                ▼                     │                          │
│    │         ┌──────────────┐            │                          │
│    │         │  PostgreSQL  │            │                          │
│    │         │   (query)    │            │                          │
│    │         └──────────────┘            │                          │
│    └─────────────────────────────────────┘                          │
│         │                                                            │
│         ▼                                                            │
│    Return comprehensive stock info                                   │
│    (market_data + financial_data + metrics)                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3. DCF Analysis Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DCF ANALYSIS WORKFLOW                            │
│                                                                      │
│  User clicks "Run DCF"                                              │
│         │                                                            │
│         ▼                                                            │
│    Gateway (/api/stocks/{ticker}/run)                                │
│         │                                                            │
│         ▼                                                            │
│    ┌─────────────────────────────────────┐                          │
│    │          DCF SERVICE                 │                          │
│    │                                      │                          │
│    │  1. Set status in Redis (running)   │                          │
│    │         │                            │                          │
│    │         ▼                            │                          │
│    │  2. Read data from:                  │                          │
│    │     - Config files                   │                          │
│    │     - PostgreSQL                     │                          │
│    │     - Redis cache                    │                          │
│    │         │                            │                          │
│    │         ▼                            │                          │
│    │  3. Calculate DCF valuation          │                          │
│    │     - Free cash flow                 │                          │
│    │     - Discount rate                  │                          │
│    │     - Terminal value                 │                          │
│    │         │                            │                          │
│    │         ▼                            │                          │
│    │  4. Calculate Graham valuation       │                          │
│    │         │                            │                          │
│    │         ▼                            │                          │
│    │  5. Save results (JSON files)        │                          │
│    │  6. Update Redis status (completed)  │                          │
│    └─────────────────────────────────────┘                          │
│         │                                                            │
│         ▼                                                            │
│    Frontend polls status via Stock Service                           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Sync Jobs

### Các loại sync jobs:

| Job Type | Nguồn | Đích | Trigger |
|----------|-------|------|---------|
| `current_price` | vnstock API | `market_data` table | Manual/Scheduled |
| `market_data` | vnstock API | `market_data` table | Manual (7/30 days) |
| `financial_data` | vnstock API | `financial_data` table | Manual/Weekly |
| `shares_outstanding` | vnstock API | `shares_outstanding` table | Manual |
| `base_pe` | Calculated | `stocks` table | Manual |

### Job Management

Quản lý jobs qua:
- **UI**: `http://localhost:8081/static/jobs.html`
- **API**: `POST /api/sync/jobs/{job_id}/run`

## Service Responsibilities

| Service | Responsibilities |
|---------|------------------|
| **Sync Service** | vnstock API calls, Data fetching, PostgreSQL writes, Job management |
| **Database Service** | Data viewing (GET only), Table schema, Stock info |
| **DCF Service** | DCF calculation, Graham valuation, Result storage |
| **Stock Service** | Stock list, Analysis status, Price display |

## Frontend Pages

| Page | URL | Data Source |
|------|-----|-------------|
| Dashboard | `/` | Stock Service → PostgreSQL |
| Stock Info | `/static/stock-info.html` | Database Service → PostgreSQL |
| Database | `/static/database.html` | Database Service → PostgreSQL |
| Jobs | `/static/jobs.html` | Sync Service |
| Monitoring | `/static/monitoring.html` | Gateway → All Services |

## Data Refresh

### Automatic Refresh
- **Dashboard**: Polls `/api/stocks` every 30 seconds
- **Jobs**: Auto-refresh every 5 seconds (configurable)
- **Monitoring**: Real-time via SSE

### Manual Sync
Trigger sync qua Jobs page hoặc API calls.

---

**Version:** 2.0  
**Last Updated:** 2025-12-30
