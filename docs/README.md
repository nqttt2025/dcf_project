# DCF Project Documentation

**Version:** 3.0  
**Last Updated:** 2025-12-30

## Recent Updates (2025-12-30)
- ✅ **Architecture refactored**: Sync operations moved to dedicated Sync Service
- ✅ **Database Service**: Now read-only for data viewing
- ✅ **Sync Service**: Direct PostgreSQL connection for all sync operations
- ✅ **Documentation consolidated**: Merged and organized docs

Chào mừng đến với documentation của DCF Valuation Project!

## 📚 Cấu Trúc Documentation

### 🚀 [Getting Started](getting-started/)
**Dành cho người mới bắt đầu**
- [Quick Start Guide](getting-started/quick-start.md) ⭐
- [Installation Guide](getting-started/installation.md)
- [First Steps](getting-started/first-steps.md)

### 💼 [Business](business/)
**Business của dự án**
- [Overview](business/overview.md) ⭐
- [Goals & Objectives](business/goals.md)
- [Features](business/features.md)
- [Vision](business/vision.md)

### 🏗️ [Architecture](architecture/)
**Cấu trúc và kiến trúc**
- [Microservices Architecture](architecture/microservices.md) ⭐ **UPDATED**
- [Sync Service](architecture/sync-service.md) ⭐ **NEW**
- [Project Structure](architecture/project-structure.md)
- [Database](architecture/database/)
- [Docker](architecture/docker.md)

### 🔧 [Operations](operations/)
**Quản lý và vận hành**
- [Version Management](operations/version-management.md) ⭐
- [Docker Management](operations/docker-version-management.md)
- [Build Optimization](operations/build-optimization.md)

### 📖 [Reference](reference/)
**Tài liệu tham khảo**
- [API Reference](reference/api.md) ⭐ **UPDATED**
- [DCF Calculation](reference/dcf-calculation.md)
- [Graham Valuation](reference/graham-valuation.md)
- [vnstock Data Format](reference/VNSTOCK_DATA_FORMAT.md)

### 📜 [Historical](historical/)
**Tài liệu lịch sử** (chỉ để tham khảo)
- Old implementation notes
- Historical fixes
- Legacy documentation

## 🎯 Quick Navigation

### Cho Người Mới
1. **[Getting Started](getting-started/README.md)** - Bắt đầu từ đây
2. **[Business Overview](business/overview.md)** - Hiểu về dự án
3. **[Quick Start Guide](getting-started/quick-start.md)** - Chạy trong 5 phút

### Cho Developers
1. **[Microservices Architecture](architecture/microservices.md)** - Hiểu kiến trúc ⭐
2. **[Sync Service](architecture/sync-service.md)** - Data sync architecture ⭐
3. **[API Reference](reference/api.md)** - API endpoints

### Cho DevOps
1. **[Operations](operations/README.md)** - Vận hành
2. **[Version Management](operations/version-management.md)** - Quản lý version
3. **[Docker Management](operations/docker-version-management.md)** - Docker

## 🏛️ System Architecture

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
│ DCF Service  │    │Stock Service │    │ Sync Service │
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

## 📋 Services Summary

| Service | Port | Role |
|---------|------|------|
| Frontend | 8081 | Static files, Nginx |
| Gateway | 8000 | API routing, SSL |
| DCF | 8001 | DCF/Graham analysis |
| Stock | 8002 | Stock info, status |
| Database | 8003 | Data viewing (read-only) |
| Sync | 8004 | Data sync (write) |
| PostgreSQL | 5432 | Data storage |
| Redis | 6379 | Cache, status |

## 🚀 Quick Start

```bash
# Start all services
make docker-up

# View frontend
open http://localhost:8081

# View API docs
open https://localhost:8000/docs

# Stop services
make docker-down
```

## 📝 Document Status

- ✅ **Current**: Up-to-date
- ⭐ **Important**: Must read
- 📜 **Historical**: Reference only

---

**Version:** 3.0  
**Last Updated:** 2025-12-30  
**Maintainer:** Project Team
