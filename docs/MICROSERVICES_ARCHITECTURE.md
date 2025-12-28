# Microservices Architecture

DCF Analysis Project được tổ chức theo kiến trúc microservices, tương tự như dự án mẫu `/home/eenitug/learning_python/services`.

## Kiến trúc

```
┌─────────────┐
│  Frontend   │
│  (Nginx)    │
│  :8080      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Gateway   │
│  (FastAPI)  │
│  :8000      │
└──────┬──────┘
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
┌──────────┐    ┌──────────┐    ┌──────────┐
│   DCF    │    │  Stock   │    │  Common  │
│ Service  │    │ Service  │    │  (Base)  │
│ :8001    │    │ :8002    │    │          │
└──────────┘    └──────────┘    └──────────┘
```

## Services

### 1. Gateway Service (`services/gateway/`)
- **Role**: API Gateway - Route requests đến các microservices
- **Technology**: FastAPI
- **Port**: 8000
- **Endpoints**:
  - `GET /` - Root endpoint
  - `GET /health` - Health check (checks all services)
  - `GET /api/stocks` - List stocks (→ Stock Service)
  - `GET /api/stocks/{ticker}` - Stock detail (→ Stock Service)
  - `POST /api/stocks/{ticker}/run` - Run DCF analysis (→ DCF Service)
  - `GET /api/analysis/{ticker}` - Get analysis result (→ DCF Service)

### 2. DCF Service (`services/dcf/`)
- **Role**: Xử lý phân tích DCF
- **Technology**: FastAPI
- **Port**: 8001
- **Endpoints**:
  - `GET /` - Root endpoint
  - `GET /health` - Health check
  - `POST /analyze/{ticker}` - Run DCF analysis (async)
  - `GET /analysis/{ticker}` - Get analysis result
  - `GET /status` - Service status

### 3. Stock Service (`services/stock/`)
- **Role**: Quản lý thông tin cổ phiếu
- **Technology**: FastAPI
- **Port**: 8002
- **Endpoints**:
  - `GET /` - Root endpoint
  - `GET /health` - Health check
  - `GET /stocks` - List all stocks
  - `GET /stocks/{ticker}` - Stock detail
  - `GET /stocks/{ticker}/config` - Stock config
  - `GET /stocks/{ticker}/status` - Stock status
  - `GET /status` - System status

### 4. Frontend Service (`services/frontend/`)
- **Role**: Serve static files (HTML, CSS, JS)
- **Technology**: Nginx
- **Port**: 8080 (mapped to 80)
- **Features**: Reverse proxy to Gateway

### 5. Common (`services/common/`)
- **Role**: Shared Dockerfile và requirements.txt
- **Purpose**: Base image cho các Python services

## Communication Flow

1. **Client Request** → Frontend (Nginx)
2. **Frontend** → Gateway (proxy `/api/*`)
3. **Gateway** → Appropriate Service (DCF or Stock)
4. **Service** → Process request
5. **Service** → Return response
6. **Gateway** → Return to Frontend
7. **Frontend** → Return to Client

## Service Discovery

Services communicate qua Docker network sử dụng service names:
- `gateway` → `http://gateway:8000`
- `dcf` → `http://dcf:8001`
- `stock` → `http://stock:8002`
- `frontend` → `http://frontend:80`

## Docker Compose

```yaml
services:
  gateway:    # API Gateway
  dcf:        # DCF Analysis Service
  stock:      # Stock Data Service
  frontend:   # Frontend (Nginx)
```

All services trong cùng network: `dcf-network`

## Volumes

Shared volumes cho data persistence:
- `./data` → `/app/data` (results, cache)
- `./config` → `/app/config` (config files)
- `./log` → `/app/log` (logs)

## Health Checks

Mỗi service có health check endpoint:
- Gateway: `/health` (checks all services)
- DCF: `/health`
- Stock: `/health`
- Frontend: `/health` (nginx)

## Benefits

1. **Separation of Concerns**: Mỗi service có trách nhiệm riêng
2. **Scalability**: Có thể scale từng service độc lập
3. **Maintainability**: Dễ maintain và update từng service
4. **Technology Flexibility**: Có thể dùng công nghệ khác nhau cho mỗi service
5. **Fault Isolation**: Lỗi ở một service không ảnh hưởng service khác

## Development

### Local Development (không Docker)

```bash
# Gateway
cd services/gateway
uvicorn main:app --host 0.0.0.0 --port 8000

# DCF Service
cd services/dcf
uvicorn main:app --host 0.0.0.0 --port 8001

# Stock Service
cd services/stock
uvicorn main:app --host 0.0.0.0 --port 8002
```

### Docker Development

```bash
# Build all services
make docker-build

# Start all services
make docker-up

# View logs
make docker-logs-gateway
make docker-logs-dcf
make docker-logs-stock
```

## Scaling

Scale từng service độc lập:

```bash
# Scale DCF service to 3 instances
docker-compose up -d --scale dcf=3

# Scale Stock service to 2 instances
docker-compose up -d --scale stock=2
```

## Monitoring

Có thể tích hợp với:
- Prometheus (metrics)
- Grafana (visualization)
- ELK Stack (logging)
- Jaeger (tracing)

## API Documentation

Gateway tự động generate API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

**Version:** 2.0 (Microservices Architecture)  
**Last Updated:** 2025-12-28

