# 🏃 Sprint 2: Infrastructure & Consolidation

**Phase:** 1 - Core Stability  
**Thời gian:** Tuần 3-4 (16/01/2026 - 29/01/2026)  
**Mục tiêu:** Setup monitoring, bắt đầu gộp services

---

## 📊 Sprint Overview

| Metric | Target |
|--------|--------|
| Logging | Structured logs (JSON) |
| Monitoring | Prometheus + Grafana working |
| Services | `services/api/` và `services/worker/` created |
| CI/CD | GitHub Actions pipeline |

---

## 📋 Task Breakdown

### S2.1 - Structured Logging (structlog)
**Priority:** 🔴 High | **Estimate:** 1 day | **Status:** ⬜ Pending

**Tasks:**
- [ ] Install & configure structlog
- [ ] Replace print statements với structured logs
- [ ] Add request ID tracking
- [ ] Configure JSON output for production

**Files cần sửa:**
```
src/utils/logging.py (new)
services/dcf/main.py
services/stock/main.py
requirements.txt
```

**Code Example:**
```python
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()
logger.info("dcf_calculation_started", ticker="FPT", user_id=123)
```

---

### S2.2 - Prometheus Metrics Endpoints
**Priority:** 🔴 High | **Estimate:** 2 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Install prometheus-client
- [ ] Add `/metrics` endpoint to each service
- [ ] Track: request count, latency, errors
- [ ] Track: DCF success/failure rate
- [ ] Track: Cache hit/miss rate

**Metrics:**
```python
from prometheus_client import Counter, Histogram

DCF_REQUESTS = Counter('dcf_requests_total', 'Total DCF requests', ['status'])
DCF_LATENCY = Histogram('dcf_request_latency_seconds', 'DCF request latency')
CACHE_HITS = Counter('cache_hits_total', 'Cache hits', ['cache_type'])
```

---

### S2.3 - Grafana Dashboard
**Priority:** 🟡 Medium | **Estimate:** 1 day | **Status:** ⬜ Pending

**Tasks:**
- [ ] Deploy Grafana container (dev only)
- [ ] Create dashboard: API Overview
- [ ] Create dashboard: DCF Performance
- [ ] Setup alerts (optional)

**Dashboard Panels:**
- Request Rate (per minute)
- Error Rate
- P50/P95/P99 Latency
- DCF Success Rate
- Cache Hit Rate

---

### S2.4 - Database Migrations (Alembic)
**Priority:** 🔴 High | **Estimate:** 2 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Install & init Alembic
- [ ] Create initial migration from existing schema
- [ ] Test migration up/down
- [ ] Document migration process

**Structure:**
```
alembic/
├── alembic.ini
├── env.py
└── versions/
    └── 001_initial_schema.py
```

---

### S2.5 - Create services/api/ Structure
**Priority:** 🔴 High | **Estimate:** 3 days | **Status:** ⬜ Pending

**Mô tả:**
Tạo cấu trúc mới để gộp 5 services (gateway, dcf, stock, database) vào 1 API service.

**Tasks:**
- [ ] Create folder structure
- [ ] Setup FastAPI app với routers
- [ ] Migrate existing code vào new structure
- [ ] Create Dockerfile
- [ ] Test locally

**New Structure:**
```
services/api/
├── Dockerfile
├── main.py                 # FastAPI app
├── config.py               # Settings
├── database.py             # SQLAlchemy
├── redis_client.py         # Redis
│
├── routers/
│   ├── __init__.py
│   ├── stocks.py           # From: services/stock
│   ├── analysis.py         # From: services/dcf
│   └── health.py           # Health check
│
├── services/
│   ├── __init__.py
│   ├── stock_service.py
│   └── dcf_service.py
│
├── models/
│   └── __init__.py
│
└── schemas/
    └── __init__.py
```

**main.py:**
```python
from fastapi import FastAPI
from routers import stocks, analysis, health

app = FastAPI(title="Stock Analysis API", version="2.0.0")

app.include_router(health.router, tags=["Health"])
app.include_router(stocks.router, prefix="/api/stocks", tags=["Stocks"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
```

---

### S2.6 - Create services/worker/ Structure
**Priority:** 🟡 Medium | **Estimate:** 2 days | **Status:** ⬜ Pending

**Mô tả:**
Tạo cấu trúc cho Worker service (Celery) để xử lý background jobs.

**Tasks:**
- [ ] Create folder structure
- [ ] Setup Celery app
- [ ] Migrate sync-service code
- [ ] Create Dockerfile
- [ ] Test locally

**New Structure:**
```
services/worker/
├── Dockerfile
├── main.py                 # Celery app
├── celeryconfig.py         # Celery settings
│
└── tasks/
    ├── __init__.py
    └── sync_tasks.py       # From: sync-service
```

---

### S2.7 - CI/CD Pipeline (GitHub Actions)
**Priority:** 🟢 Low | **Estimate:** 1 day | **Status:** ⬜ Pending

**Tasks:**
- [ ] Create `.github/workflows/ci.yml`
- [ ] Run tests on PR
- [ ] Run linting (ruff/flake8)
- [ ] Build Docker images (don't push yet)

**Workflow:**
```yaml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov
```

---

## 📅 Daily Plan

### Week 1 (16/01 - 22/01)
| Day | Tasks |
|-----|-------|
| 1 | S2.1 - Structured logging |
| 2 | S2.2 - Prometheus metrics (part 1) |
| 3 | S2.2 - Prometheus metrics (part 2) |
| 4 | S2.3 - Grafana dashboard |
| 5 | S2.4 - Alembic setup |

### Week 2 (23/01 - 29/01)
| Day | Tasks |
|-----|-------|
| 6 | S2.4 - Alembic migrations |
| 7 | S2.5 - API service structure |
| 8 | S2.5 - Migrate existing code |
| 9 | S2.5 - Testing + S2.6 Worker setup |
| 10 | S2.6 - Worker + S2.7 CI/CD |

---

## ✅ Definition of Done

- [ ] Structured logging working
- [ ] `/metrics` endpoint returning Prometheus data
- [ ] Grafana dashboard accessible
- [ ] Alembic migrations working
- [ ] `services/api/` structure created (not deployed)
- [ ] `services/worker/` structure created (not deployed)
- [ ] CI pipeline passing

---

## 📦 Dependencies

```txt
structlog>=23.1.0
prometheus-client>=0.17.0
alembic>=1.12.0
celery>=5.3.0
```

---

**Previous Sprint:** [Sprint 1 - DCF Stability](./SPRINT_1.md)  
**Next Sprint:** [Sprint 3 - Technical Analysis](./SPRINT_3.md)

