# Architecture Documentation

**Cấu trúc và kiến trúc của DCF Valuation Project**

## 📚 Tài Liệu

### 1. [Project Structure](project-structure.md) ⭐
Chi tiết cấu trúc thư mục và modules của dự án.

### 2. [Microservices Architecture](microservices.md) ⭐
Kiến trúc microservices và cách các services giao tiếp.

### 3. [Database](database/README.md) ⭐
Database architecture và design cho VN30 stock data.

### 4. [Docker Architecture](docker.md)
Docker setup và containerization strategy.

### 5. [Development Guide](development.md)
Hướng dẫn phát triển và development workflow.

## 🏗️ Architecture Overview

### System Architecture
```
┌─────────────┐
│  Frontend   │  :8080 (Nginx)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Gateway   │  :8000 (FastAPI)
└──────┬──────┘
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
┌──────────┐    ┌──────────┐    ┌──────────┐
│   DCF    │    │  Stock   │    │  Redis   │
│ Service  │    │ Service  │    │  Cache   │
│ :8001    │    │ :8002    │    │ :6379    │
└──────────┘    └──────────┘    └──────────┘
```

### Key Components
- **Frontend**: Web interface (Nginx)
- **Gateway**: API Gateway (FastAPI)
- **DCF Service**: DCF calculation engine
- **Stock Service**: Stock data management
- **Redis**: Caching và status tracking

## 🎯 Key Concepts

### Microservices
- Separation of concerns
- Independent scaling
- Fault isolation
- Technology flexibility

### Docker
- Containerization
- Base image caching
- Build optimization
- Development mode

### Redis
- Real-time status tracking
- Progress caching
- TTL-based expiration

## 📖 Đọc Tiếp

- [Project Structure](project-structure.md) - Chi tiết cấu trúc
- [Microservices](microservices.md) - Kiến trúc microservices
- [Database](database/README.md) - Database design
- [Docker](docker.md) - Docker setup
- [Development](development.md) - Development guide

---

**Next:** [Project Structure](project-structure.md) →

