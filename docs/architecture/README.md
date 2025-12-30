# Architecture Documentation

**Version:** 3.0  
**Last Updated:** 2025-12-30

**Cấu trúc và kiến trúc của DCF Valuation Project**

## 📚 Tài Liệu

### 1. [Microservices Architecture](microservices.md) ⭐ UPDATED
Kiến trúc microservices và cách các services giao tiếp.

### 2. [Sync Service](sync-service.md) ⭐ NEW
Kiến trúc và design của Sync Service - quản lý đồng bộ dữ liệu.

### 3. [Project Structure](project-structure.md) ⭐
Chi tiết cấu trúc thư mục và modules của dự án.

### 4. [Database](database/README.md) ⭐
Database architecture và design cho VN30 stock data.

### 5. [Docker Architecture](docker.md)
Docker setup và containerization strategy.

### 6. [Development Guide](development.md)
Hướng dẫn phát triển và development workflow.

### 7. [Scripts Architecture](scripts.md)
Cấu trúc và tổ chức scripts directory (SOLID refactored).

## 🏗️ Architecture Overview

### System Architecture (Updated)
```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Nginx)                          │
│                          Port: 8081                              │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GATEWAY (FastAPI)                           │
│                         Port: 8000                               │
└───────────────────────────────┬─────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ DCF Service  │    │Stock Service │    │ Sync Service │ ⭐ NEW
│   :8001      │    │   :8002      │    │   :8004      │
└──────────────┘    └──────────────┘    └───────┬──────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│Database Svc  │    │ PostgreSQL   │    │    Redis     │
│   :8003      │    │   :5432      │    │    :6379     │
│ (Read-only)  │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
```

### Key Components
- **Frontend**: Web interface (Nginx) - :8081
- **Gateway**: API Gateway (FastAPI) - :8000
- **DCF Service**: DCF calculation engine - :8001
- **Stock Service**: Stock data management - :8002
- **Sync Service**: Data synchronization - :8004 ⭐ NEW
- **Database Service**: Data viewing (read-only) - :8003
- **PostgreSQL**: Persistent storage - :5432
- **Redis**: Caching và status tracking - :6379

## 🔑 Service Responsibilities

| Service | Responsibilities |
|---------|------------------|
| **Sync Service** | vnstock API, Data fetch, PostgreSQL writes, Job management |
| **Database Service** | Data viewing (GET only), Table schema, Stock info |
| **DCF Service** | DCF calculation, Graham valuation, Result storage |
| **Stock Service** | Stock list, Analysis status, Price display |
| **Gateway** | API routing, Health checks, SSL termination |

## 🎯 Key Concepts

### Microservices
- Separation of concerns
- Independent scaling
- Fault isolation
- Technology flexibility

### Data Flow
- **Sync Service** → Writes data to PostgreSQL
- **Database Service** → Reads data from PostgreSQL
- **Clear separation**: No duplicate sync logic

### Docker
- Containerization
- Base image caching
- Build optimization
- Development mode

## 📖 Đọc Tiếp

- [Microservices](microservices.md) ⭐ - Kiến trúc microservices chi tiết
- [Sync Service](sync-service.md) ⭐ - Data sync architecture
- [Project Structure](project-structure.md) - Chi tiết cấu trúc
- [Database](database/README.md) - Database design
- [Docker](docker.md) - Docker setup
- [Development](development.md) - Development guide

---

**Next:** [Microservices Architecture](microservices.md) →
