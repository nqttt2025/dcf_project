# 🗺️ DCF Project Roadmap - Final Version

**Version:** 3.0 (Final - Hợp nhất Frontend + Backend)  
**Created:** 2026-01-02  
**Target:** Thương mại hóa bộ công cụ phân tích cổ phiếu Việt Nam

---

## 📊 Tổng quan

### Timeline: 9 Sprints (18 tuần)

| Phase | Sprint | Tuần | Mục tiêu | Backend | Frontend |
|-------|--------|------|----------|---------|----------|
| **1** | 1-2 | 1-4 | Core Stability | Fix DCF, giữ 9 services | Giữ nguyên |
| **2** | 3-5 | 5-10 | Technical Analysis | Gộp → 4 services | Charts, Indicators |
| **3** | 6-7 | 11-14 | User Experience | User Auth, Alerts | Dashboard, Watchlist |
| **4** | 8-9 | 15-18 | Monetization | Payment, Scale | Reports, Polish |

### Kiến trúc Mục tiêu

```
┌─────────────────────────────────────────────────────────────┐
│                    TARGET: 4 CONTAINERS                      │
├─────────────────────────────────────────────────────────────┤
│  Frontend (Nginx/S3)                                        │
│      │                                                      │
│      ▼                                                      │
│  API Service ─────┬─────► PostgreSQL (RDS)                  │
│  (FastAPI)        │                                         │
│      │            └─────► Redis (ElastiCache)               │
│      ▼                                                      │
│  Worker Service (Celery) ──► Background Jobs                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ PHASE 1: CORE STABILITY (Tuần 1-4)

### Sprint 1 (Tuần 1-2): DCF Stability

**Mục tiêu:** Fix DCF tool, tăng success rate từ 70% → 95%

| ID | Task | Priority | Days |
|----|------|----------|------|
| S1.1 | Fix DCF timeout - add retry mechanism (tenacity) | 🔴 | 3 |
| S1.2 | Implement Redis caching với TTL | 🔴 | 2 |
| S1.3 | Cross-validation shares outstanding | 🔴 | 2 |
| S1.4 | Error recovery & graceful degradation | 🟡 | 2 |
| S1.5 | Unit tests (target 80% coverage) | 🟡 | 2 |
| S1.6 | Integration tests | 🟡 | 1 |

**Deliverables:**
- ✅ DCF success rate ≥ 95%
- ✅ API response < 30s
- ✅ Test coverage ≥ 80%

---

### Sprint 2 (Tuần 3-4): Infrastructure + Bắt đầu Consolidate

**Mục tiêu:** Setup monitoring, bắt đầu gộp services

| ID | Task | Priority | Days |
|----|------|----------|------|
| S2.1 | Structured logging (structlog) | 🔴 | 1 |
| S2.2 | Prometheus metrics endpoints | 🔴 | 2 |
| S2.3 | Grafana dashboard | 🟡 | 1 |
| S2.4 | Database migrations setup (Alembic) | 🔴 | 2 |
| S2.5 | **Tạo services/api/** - Gộp gateway+dcf+stock+database | 🔴 | 3 |
| S2.6 | **Tạo services/worker/** - Gộp sync-service | 🟡 | 2 |
| S2.7 | CI/CD pipeline (GitHub Actions) | 🟢 | 1 |

**Deliverables:**
- ✅ Monitoring working
- ✅ `services/api/` created (chưa deploy)
- ✅ `services/worker/` created (chưa deploy)

---

## 📈 PHASE 2: TECHNICAL ANALYSIS (Tuần 5-10)

### Sprint 3 (Tuần 5-6): Trend Indicators + Deploy New Architecture

**Mục tiêu:** TA indicators + Deploy kiến trúc 4 containers

| ID | Task | Priority | Days |
|----|------|----------|------|
| S3.1 | Moving Averages (SMA, EMA 20/50/200) | 🔴 | 2 |
| S3.2 | MACD Indicator | 🔴 | 1 |
| S3.3 | Bollinger Bands | 🔴 | 1 |
| S3.4 | Ichimoku Cloud | 🟡 | 2 |
| S3.5 | API: `GET /api/ta/{ticker}` endpoint | 🔴 | 1 |
| S3.6 | **Deploy new docker-compose (4 containers)** | 🔴 | 2 |
| S3.7 | **Loại bỏ old services, redis-commander** | 🟡 | 1 |

**API Endpoints:**
```
GET /api/ta/{ticker}              # All indicators
GET /api/ta/{ticker}/ma           # Moving Averages
GET /api/ta/{ticker}/macd         # MACD
GET /api/ta/{ticker}/bollinger    # Bollinger Bands
```

---

### Sprint 4 (Tuần 7-8): Momentum & Volume Indicators

| ID | Task | Priority | Days |
|----|------|----------|------|
| S4.1 | RSI (Relative Strength Index) | 🔴 | 1 |
| S4.2 | Stochastic Oscillator | 🔴 | 1 |
| S4.3 | Williams %R | 🟡 | 0.5 |
| S4.4 | OBV (On-Balance Volume) | 🔴 | 1 |
| S4.5 | VWAP | 🔴 | 1 |
| S4.6 | ATR (Average True Range) | 🟡 | 1 |
| S4.7 | Buy/Sell signals endpoint | 🔴 | 2 |
| S4.8 | Unit tests for all indicators | 🟡 | 1.5 |

**API Endpoints:**
```
GET /api/ta/{ticker}/rsi          # RSI
GET /api/ta/{ticker}/stochastic   # Stochastic
GET /api/ta/{ticker}/volume       # OBV, VWAP
GET /api/ta/signals/{ticker}      # Buy/Sell signals
```

---

### Sprint 5 (Tuần 9-10): Charts & Visualization

| ID | Task | Priority | Days |
|----|------|----------|------|
| S5.1 | TradingView Lightweight Charts setup | 🔴 | 2 |
| S5.2 | Candlestick chart with OHLC data | 🔴 | 2 |
| S5.3 | Indicator overlays (MA, Bollinger) | 🔴 | 2 |
| S5.4 | Sub-panels (RSI, MACD, Volume) | 🔴 | 2 |
| S5.5 | Timeframe switching (1D/1W/1M/1Y) | 🟡 | 1 |
| S5.6 | Chart state management (JS) | 🟡 | 1 |

**API Endpoints:**
```
GET /api/stocks/{ticker}/ohlc?timeframe=1D
GET /api/stocks/{ticker}/ohlc?timeframe=1W
```

**Frontend Files:**
```
static/js/charts/
├── chart-manager.js
├── candlestick.js
└── indicators/
    ├── ma.js
    ├── rsi.js
    └── macd.js
```

---

## 🎨 PHASE 3: USER EXPERIENCE (Tuần 11-14)

### Sprint 6 (Tuần 11-12): Dashboard + User System

**Mục tiêu:** New dashboard, user authentication

| ID | Task | Priority | Days |
|----|------|----------|------|
| S6.1 | **Database: users, watchlists tables** | 🔴 | 1 |
| S6.2 | User Authentication (JWT) | 🔴 | 3 |
| S6.3 | User Registration + Email verification | 🟡 | 2 |
| S6.4 | Dashboard redesign (Tailwind CSS) | 🔴 | 2 |
| S6.5 | Watchlist feature (CRUD) | 🔴 | 2 |
| S6.6 | Stock screener (filter by indicators) | 🔴 | 2 |

**Database Schema:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE watchlists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    ticker VARCHAR(10) NOT NULL,
    added_at TIMESTAMP DEFAULT NOW()
);
```

**API Endpoints:**
```
POST /api/users/register
POST /api/users/login
GET  /api/users/me
GET  /api/watchlist
POST /api/watchlist
DELETE /api/watchlist/{ticker}
POST /api/screener/filter
```

---

### Sprint 7 (Tuần 13-14): Alerts + Reports

| ID | Task | Priority | Days |
|----|------|----------|------|
| S7.1 | **Database: alerts, analysis_history tables** | 🔴 | 1 |
| S7.2 | Price alerts system | 🔴 | 2 |
| S7.3 | **Worker: alert checking task (Celery Beat)** | 🔴 | 2 |
| S7.4 | Email notifications (SendGrid/Mailgun) | 🟡 | 2 |
| S7.5 | PDF Report Generation (WeasyPrint) | 🔴 | 2 |
| S7.6 | Excel Export (openpyxl) | 🟡 | 1 |
| S7.7 | Role-based access (Free/Premium) | 🟡 | 2 |

**Database Schema:**
```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    ticker VARCHAR(10) NOT NULL,
    condition VARCHAR(50),
    value DECIMAL,
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE analysis_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    ticker VARCHAR(10) NOT NULL,
    type VARCHAR(50),
    result JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Worker Tasks:**
```python
# services/worker/tasks/alert_tasks.py
@celery.task
def check_price_alerts():
    """Run every 5 minutes during market hours"""
    pass

@celery.task
def generate_pdf_report(ticker, user_id):
    """Generate PDF report async"""
    pass
```

---

## 💰 PHASE 4: MONETIZATION & LAUNCH (Tuần 15-18)

### Sprint 8 (Tuần 15-16): Payment + Subscription

| ID | Task | Priority | Days |
|----|------|----------|------|
| S8.1 | **Database: subscriptions table** | 🔴 | 1 |
| S8.2 | Subscription tiers logic | 🔴 | 2 |
| S8.3 | Stripe integration | 🔴 | 3 |
| S8.4 | VNPay integration (Vietnam) | 🟡 | 2 |
| S8.5 | Invoice generation | 🟡 | 1 |
| S8.6 | Admin dashboard (basic) | 🟡 | 2 |

**Subscription Tiers:**
| Tier | Price | Stocks | Analyses | Alerts | PDF |
|------|-------|--------|----------|--------|-----|
| Free | 0 | 3 | 1/day | ❌ | ❌ |
| Basic | 99k | 20 | 10/day | 5 | ❌ |
| Pro | 299k | ∞ | ∞ | ∞ | ✅ |

**API Endpoints:**
```
GET  /api/subscriptions/plans
POST /api/subscriptions/create
POST /api/payment/stripe/webhook
POST /api/payment/vnpay/create
GET  /api/payment/vnpay/callback
```

---

### Sprint 9 (Tuần 17-18): Launch Preparation

| ID | Task | Priority | Days |
|----|------|----------|------|
| S9.1 | Load testing (Locust - 1000 users) | 🔴 | 2 |
| S9.2 | Security audit (Bandit, OWASP) | 🔴 | 2 |
| S9.3 | **AWS deployment (EC2/ECS)** | 🔴 | 2 |
| S9.4 | User documentation (MkDocs) | 🟡 | 2 |
| S9.5 | Landing page | 🔴 | 2 |
| S9.6 | Beta testing (50 users) | 🔴 | 3 |
| S9.7 | Bug fixes | 🔴 | 2 |
| S9.8 | **🚀 GO LIVE** | 🔴 | 1 |

**AWS Setup:**
| Service | Dev | Production |
|---------|-----|------------|
| Compute | EC2 t3.small | ECS Fargate |
| Database | RDS t3.micro | RDS t3.small |
| Cache | Redis on EC2 | ElastiCache |
| CDN | - | CloudFront |
| **Cost** | ~$31/month | ~$98/month |

---

## 📁 Cấu trúc Project Cuối cùng

```
dcf_project/
├── services/
│   ├── api/                      # Main API (gộp từ 5 services)
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── stocks.py         # /api/stocks/*
│   │   │   ├── analysis.py       # /api/analysis/*
│   │   │   ├── technical.py      # /api/ta/*
│   │   │   ├── users.py          # /api/users/*
│   │   │   ├── watchlist.py      # /api/watchlist/*
│   │   │   ├── screener.py       # /api/screener/*
│   │   │   └── payment.py        # /api/payment/*
│   │   └── services/
│   │       ├── dcf_service.py
│   │       ├── ta_service.py
│   │       └── user_service.py
│   │
│   ├── worker/                   # Background Jobs (Celery)
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── tasks/
│   │       ├── sync_tasks.py
│   │       ├── alert_tasks.py
│   │       └── report_tasks.py
│   │
│   └── frontend/                 # Static files (Nginx)
│       ├── Dockerfile
│       ├── nginx.conf
│       ├── pages/
│       │   ├── dashboard.html
│       │   ├── stock-analysis.html
│       │   ├── screener.html
│       │   └── watchlist.html
│       └── static/
│           ├── css/
│           └── js/
│               ├── charts/
│               └── tools/
│
├── src/core/                     # Business logic (shared)
├── config/                       # Stock configs
├── docs/                         # Documentation
└── docker-compose.yml            # 4 containers
```

---

## 🐳 Docker Compose Cuối cùng

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: dcf_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: dcf_db
    volumes:
      - postgres-data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data

  api:
    build: ./services/api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://dcf_user:${DB_PASSWORD}@postgres:5432/dcf_db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    depends_on: [postgres, redis]

  worker:
    build: ./services/worker
    environment:
      - DATABASE_URL=postgresql://dcf_user:${DB_PASSWORD}@postgres:5432/dcf_db
      - REDIS_URL=redis://redis:6379/0
    depends_on: [postgres, redis]

  frontend:
    build: ./services/frontend
    ports:
      - "80:80"
    depends_on: [api]

volumes:
  postgres-data:
  redis-data:
```

---

## 📦 Dependencies Tổng hợp

```txt
# requirements.txt

# Core
fastapi>=0.104.0
uvicorn>=0.24.0
sqlalchemy>=2.0.0
alembic>=1.12.0
pydantic>=2.5.0

# Cache & Queue
redis>=5.0.0
celery>=5.3.0

# Technical Analysis
pandas>=2.0.0
numpy>=1.24.0
pandas-ta>=0.3.14b

# Auth
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4

# Reports
weasyprint>=60.0
openpyxl>=3.1.0

# Payment
stripe>=7.0.0

# Data
vnstock>=3.0.0
httpx>=0.24.0

# Testing & Quality
pytest>=7.4.0
pytest-asyncio>=0.21.0
locust>=2.17.0
bandit>=1.7.0

# Monitoring
prometheus-client>=0.17.0
structlog>=23.1.0
```

---

## 📊 Tổng kết

| Metric | Hiện tại | Sau Roadmap |
|--------|----------|-------------|
| Containers | 9 | 4 |
| Python Services | 5 | 2 (API + Worker) |
| Features | DCF, Graham | + TA, Charts, Alerts, Auth, Payment |
| AWS Cost | ~$78/m | ~$50-98/m |
| Users | 0 | Target: 100 beta |
| Revenue | $0 | Target: 50 paying users |

---

## ✅ Checklist by Sprint

> 📁 Chi tiết từng Sprint: [docs/sprints/](./sprints/)

### Sprint 1-2 ⬜ (Tuần 1-4)
- [ ] [Sprint 1](./sprints/SPRINT_1.md): DCF stability fixes
- [ ] [Sprint 2](./sprints/SPRINT_2.md): Monitoring, bắt đầu consolidate services

### Sprint 3-5 ⬜ (Tuần 5-10)
- [ ] [Sprint 3](./sprints/SPRINT_3.md): Trend Indicators + Deploy 4 containers
- [ ] [Sprint 4](./sprints/SPRINT_4.md): Momentum & Volume Indicators
- [ ] [Sprint 5](./sprints/SPRINT_5.md): TradingView Charts

### Sprint 6-7 ⬜ (Tuần 11-14)
- [ ] [Sprint 6](./sprints/SPRINT_6.md): Dashboard, Auth, Watchlist, Screener
- [ ] [Sprint 7](./sprints/SPRINT_7.md): Alerts, Reports, Tier limits

### Sprint 8-9 ⬜ (Tuần 15-18)
- [ ] [Sprint 8](./sprints/SPRINT_8.md): Payment (Stripe, VNPay)
- [ ] [Sprint 9](./sprints/SPRINT_9.md): Testing, AWS, 🚀 Launch

---

**Last Updated:** 2026-01-02  
**Sprint 1 Start:** 02/01/2026  
**Estimated Launch:** 07/05/2026  
**Status:** ▶️ IN PROGRESS - Sprint 1
