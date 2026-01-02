# 🏗️ Backend Architecture - Đánh giá & Đề xuất

**Version:** 1.0  
**Created:** 2026-01-02

---

## 📊 Đánh giá Kiến trúc Hiện tại

### Services hiện có (9 containers)

```
┌─────────────────────────────────────────────────────────────┐
│                    HIỆN TẠI: 9 CONTAINERS                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Infrastructure (3):                                        │
│  ├── postgres          (Database)                          │
│  ├── redis             (Cache)                              │
│  └── redis-commander   (Monitoring - DEV ONLY)              │
│                                                             │
│  Application (5):                                           │
│  ├── gateway           (API Gateway)                        │
│  ├── dcf               (DCF Analysis)                       │
│  ├── stock             (Stock Info)                         │
│  ├── database          (Data Viewing)                       │
│  └── sync-service      (Data Sync)                          │
│                                                             │
│  Frontend (1):                                              │
│  └── frontend          (Nginx)                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### ⚠️ Vấn đề với kiến trúc hiện tại

| Vấn đề | Mô tả | Impact |
|--------|-------|--------|
| **Quá nhiều services** | 5 Python services cho features đơn giản | Chi phí cao, phức tạp |
| **Trùng lặp chức năng** | stock + database + gateway đều query DB | Khó maintain |
| **Không scalable** | Mỗi service 1 instance, không auto-scale | Không đáp ứng được tải |
| **Dev overhead** | Mỗi service = 1 Dockerfile, 1 deploy | Chậm development |
| **Resource waste** | Mỗi Python container ~150-300MB RAM | Tốn tiền AWS |

---

## 💰 Ước tính Chi phí AWS (Kiến trúc Hiện tại)

### Option 1: EC2 Instance (Self-managed)

| Resource | Instance | Specs | Giá/tháng |
|----------|----------|-------|-----------|
| App Server | t3.medium | 2 vCPU, 4GB RAM | ~$30 |
| Database | t3.small | 2 vCPU, 2GB RAM | ~$15 |
| **Total** | | | **~$45/tháng** |

> ⚠️ Không bao gồm: Storage, Bandwidth, Backup

### Option 2: AWS Managed Services (Recommended cho Production)

| Service | Type | Specs | Giá/tháng |
|---------|------|-------|-----------|
| **ECS Fargate** | 2 tasks | 0.5 vCPU, 1GB each | ~$30 |
| **RDS PostgreSQL** | db.t3.micro | 1 vCPU, 1GB | ~$15 |
| **ElastiCache Redis** | cache.t3.micro | 0.5GB | ~$12 |
| **ALB** | Load Balancer | | ~$16 |
| **S3 + CloudFront** | Static hosting | | ~$5 |
| **Total** | | | **~$78/tháng** |

### Option 3: Budget Setup (Khởi đầu)

| Service | Type | Giá/tháng |
|---------|------|-----------|
| **EC2 t3.micro** | Free tier eligible | $0-8 |
| **RDS t3.micro** | Free tier eligible | $0-15 |
| **ElastiCache** | Skip, use Redis on EC2 | $0 |
| **Total (Free tier)** | | **~$0-23/tháng** |

---

## 🎯 Đề xuất: Kiến trúc Tối ưu

### Nguyên tắc

1. **Consolidate services** - Gộp services có chức năng liên quan
2. **Separate concerns** - Tách riêng API vs Background Jobs
3. **Use managed services** - Database, Cache dùng managed
4. **Scale horizontally** - Design cho horizontal scaling

### Kiến trúc đề xuất: 4 Containers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ĐỀ XUẤT: 4 CONTAINERS + MANAGED SERVICES             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                         FRONTEND                                 │   │
│   │              S3 + CloudFront (hoặc Nginx container)              │   │
│   └─────────────────────────────┬───────────────────────────────────┘   │
│                                 │                                       │
│                                 ▼                                       │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                     API SERVICE (Main)                          │   │
│   │  ┌─────────────────────────────────────────────────────────┐    │   │
│   │  │  FastAPI Application                                     │    │   │
│   │  │  • /api/stocks/* - Stock data & info                    │    │   │
│   │  │  • /api/analysis/* - DCF, Graham, PE                    │    │   │
│   │  │  • /api/ta/* - Technical Analysis                       │    │   │
│   │  │  • /api/users/* - Authentication                        │    │   │
│   │  │  • /api/watchlist/* - User watchlist                    │    │   │
│   │  │  • /api/screener/* - Stock screener                     │    │   │
│   │  └─────────────────────────────────────────────────────────┘    │   │
│   │  Port: 8000 | Replicas: 2-4 (auto-scale)                        │   │
│   └─────────────────────────────┬───────────────────────────────────┘   │
│                                 │                                       │
│         ┌───────────────────────┼───────────────────────┐               │
│         │                       │                       │               │
│         ▼                       ▼                       ▼               │
│   ┌───────────┐          ┌───────────┐          ┌───────────┐          │
│   │  WORKER   │          │ PostgreSQL│          │   Redis   │          │
│   │  SERVICE  │          │  (RDS)    │          │(ElastiCache)│         │
│   │           │          │           │          │           │          │
│   │ • Sync    │◄────────►│ • Stocks  │◄────────►│ • Cache   │          │
│   │ • Analysis│          │ • Users   │          │ • Session │          │
│   │ • Alerts  │          │ • Market  │          │ • Queue   │          │
│   │ • Reports │          │ • Financial│         │ • Pub/Sub │          │
│   └───────────┘          └───────────┘          └───────────┘          │
│   Replicas: 1-2                Managed              Managed             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Chi tiết Services Đề xuất

### 1. API Service (Gộp từ 5 services)

```python
# services/api/main.py
from fastapi import FastAPI
from routers import stocks, analysis, technical, users, watchlist, screener

app = FastAPI(title="Stock Analysis API")

# Routers
app.include_router(stocks.router, prefix="/api/stocks", tags=["Stocks"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(technical.router, prefix="/api/ta", tags=["Technical"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["Watchlist"])
app.include_router(screener.router, prefix="/api/screener", tags=["Screener"])
```

**Cấu trúc:**
```
services/api/
├── main.py                 # FastAPI app
├── config.py               # Settings
├── database.py             # Database connection
├── redis_client.py         # Redis connection
│
├── routers/                # API Routes
│   ├── stocks.py           # Stock CRUD
│   ├── analysis.py         # DCF, Graham
│   ├── technical.py        # TA indicators
│   ├── users.py            # Auth
│   ├── watchlist.py        # User watchlist
│   └── screener.py         # Stock screener
│
├── services/               # Business Logic
│   ├── stock_service.py
│   ├── dcf_service.py
│   ├── graham_service.py
│   ├── ta_service.py
│   └── user_service.py
│
├── models/                 # SQLAlchemy Models
│   ├── stock.py
│   ├── user.py
│   └── analysis.py
│
└── schemas/                # Pydantic Schemas
    ├── stock.py
    ├── analysis.py
    └── user.py
```

### 2. Worker Service (Background Jobs)

```python
# services/worker/main.py
from celery import Celery
from tasks import sync, analysis, alerts, reports

app = Celery('worker')
app.config_from_object('celeryconfig')

# Register tasks
app.autodiscover_tasks(['tasks'])
```

**Cấu trúc:**
```
services/worker/
├── main.py                 # Celery app
├── celeryconfig.py         # Celery settings
│
├── tasks/                  # Background Tasks
│   ├── sync_tasks.py       # Data sync từ vnstock
│   ├── analysis_tasks.py   # DCF calculation (heavy)
│   ├── alert_tasks.py      # Price alerts
│   └── report_tasks.py     # PDF generation
│
└── schedulers/             # Scheduled Jobs
    ├── daily_sync.py       # Sync data hàng ngày
    └── market_hours.py     # Sync trong giờ giao dịch
```

### 3. Frontend (Static)

**Option A: Nginx Container**
```nginx
# Serve static files
location / {
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;
}

# Proxy API
location /api {
    proxy_pass http://api:8000;
}
```

**Option B: S3 + CloudFront (Recommended)**
- Cheaper, faster, CDN built-in
- ~$1-5/month

---

## 🔄 So sánh: Trước vs Sau

| Aspect | Hiện tại (9 containers) | Đề xuất (4 containers) |
|--------|------------------------|----------------------|
| **Python services** | 5 | 2 |
| **Total containers** | 9 | 4 |
| **RAM usage** | ~2GB+ | ~1GB |
| **Complexity** | High | Medium |
| **Deploy time** | Slow (5 builds) | Fast (2 builds) |
| **AWS cost** | ~$78/month | ~$50/month |
| **Scalability** | Poor | Good |

---

## 📋 Migration Plan: Services Merge

### Gộp vào API Service

| Service cũ | Merge vào | Lý do |
|------------|-----------|-------|
| gateway | API Service | Proxy không cần thiết |
| dcf | API Service | Lightweight calculation |
| stock | API Service | Simple CRUD |
| database | API Service | Read-only queries |

### Gộp vào Worker Service

| Service cũ | Merge vào | Lý do |
|------------|-----------|-------|
| sync-service | Worker | Background job |
| DCF heavy calc | Worker | Long-running task |

### Loại bỏ

| Service | Lý do |
|---------|-------|
| redis-commander | Dev tool, không cần production |

---

## 🗄️ Database Schema (Mở rộng cho Roadmap)

```sql
-- Existing tables
stocks, market_data, financial_data, shares_outstanding, growth_metrics

-- New tables for Roadmap
-- User Management
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    tier VARCHAR(50) DEFAULT 'free', -- free, basic, pro, enterprise
    created_at TIMESTAMP DEFAULT NOW()
);

-- Watchlist
CREATE TABLE watchlists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    ticker VARCHAR(10) NOT NULL,
    added_at TIMESTAMP DEFAULT NOW()
);

-- Alerts
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    ticker VARCHAR(10) NOT NULL,
    condition VARCHAR(50), -- price_above, price_below, rsi_overbought...
    value DECIMAL,
    active BOOLEAN DEFAULT TRUE,
    triggered_at TIMESTAMP
);

-- Analysis History
CREATE TABLE analysis_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    ticker VARCHAR(10) NOT NULL,
    type VARCHAR(50), -- dcf, graham, technical
    result JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Subscriptions
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    tier VARCHAR(50) NOT NULL,
    started_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    payment_id VARCHAR(255)
);
```

---

## 🐳 Docker Compose Mới

```yaml
# docker-compose.yml (Optimized)
version: '3.8'

services:
  # === INFRASTRUCTURE (Managed in Production) ===
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: dcf_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: dcf_db
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dcf_user"]
    # Production: Use RDS

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
    # Production: Use ElastiCache

  # === APPLICATION ===
  api:
    build:
      context: .
      dockerfile: services/api/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://dcf_user:${DB_PASSWORD}@postgres:5432/dcf_db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]

  worker:
    build:
      context: .
      dockerfile: services/worker/Dockerfile
    environment:
      - DATABASE_URL=postgresql://dcf_user:${DB_PASSWORD}@postgres:5432/dcf_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 1
      resources:
        limits:
          memory: 512M

  # === FRONTEND ===
  frontend:
    build:
      context: .
      dockerfile: services/frontend/Dockerfile
    ports:
      - "80:80"
    depends_on:
      - api

volumes:
  postgres-data:
  redis-data:
```

---

## 💵 Chi phí AWS Đề xuất

### Development / MVP

| Service | Type | Cost/month |
|---------|------|------------|
| EC2 t3.small | API + Worker + Redis | $15 |
| RDS t3.micro | PostgreSQL | $15 |
| S3 | Static files | $1 |
| **Total** | | **~$31/month** |

### Production (Scale)

| Service | Type | Cost/month |
|---------|------|------------|
| ECS Fargate | 2 API + 1 Worker | $40 |
| RDS t3.small | PostgreSQL | $25 |
| ElastiCache | Redis | $12 |
| ALB | Load Balancer | $16 |
| CloudFront | CDN | $5 |
| **Total** | | **~$98/month** |

### High Traffic (1000+ users)

| Service | Type | Cost/month |
|---------|------|------------|
| ECS Fargate | 4 API + 2 Worker | $80 |
| RDS t3.medium | PostgreSQL | $50 |
| ElastiCache | Redis | $25 |
| ALB | Load Balancer | $20 |
| CloudFront | CDN | $10 |
| **Total** | | **~$185/month** |

---

## 📊 Feature to Service Mapping (Roadmap)

| Feature (Roadmap) | Service | Endpoint |
|-------------------|---------|----------|
| DCF Analysis | API | `POST /api/analysis/dcf/{ticker}` |
| Graham Valuation | API | `POST /api/analysis/graham/{ticker}` |
| PE Analysis | API | `GET /api/analysis/pe/{ticker}` |
| Technical Indicators | API | `GET /api/ta/{ticker}` |
| Stock Screener | API | `POST /api/screener/filter` |
| Watchlist | API | `GET/POST /api/watchlist` |
| Alerts | API + Worker | `POST /api/alerts`, Worker checks |
| Data Sync | Worker | Scheduled task |
| PDF Reports | Worker | `POST /api/reports/generate` |
| User Auth | API | `POST /api/users/login` |
| Payment | API | `POST /api/payment/create` |

---

## ✅ Recommendations

### Immediate (Sprint 1-2)
1. ✅ Giữ nguyên kiến trúc hiện tại cho development
2. ✅ Bắt đầu gộp code vào 2 services (API + Worker)
3. ✅ Loại bỏ redis-commander

### Short-term (Sprint 3-5)
1. ✅ Deploy kiến trúc mới lên EC2 single instance
2. ✅ Migrate database sang RDS (free tier)
3. ✅ Setup CI/CD với GitHub Actions

### Long-term (Sprint 6+)
1. ✅ Migrate sang ECS Fargate
2. ✅ Setup auto-scaling
3. ✅ Setup monitoring (CloudWatch)

---

## 🎯 Kết luận

| Metric | Hiện tại | Đề xuất | Cải thiện |
|--------|----------|---------|-----------|
| Services | 9 | 4 | -55% |
| AWS Cost | ~$78 | ~$50 | -36% |
| Complexity | High | Medium | Better |
| Scalability | Poor | Good | Better |
| Dev Speed | Slow | Fast | Better |

**Khuyến nghị:** Áp dụng kiến trúc 4 containers cho production, bắt đầu consolidate từ Sprint 2.

---

**Last Updated:** 2026-01-02

