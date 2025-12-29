# Docker Microservices Setup

Hướng dẫn chạy DCF Analysis Web Service với Docker theo mô hình microservices.

## Kiến trúc

Dự án được chia thành các microservices:

1. **Gateway Service** (`services/gateway/`)
   - FastAPI API Gateway
   - Port: 8000
   - Routes requests to appropriate services

2. **DCF Service** (`services/dcf/`)
   - FastAPI DCF Analysis Service
   - Port: 8001
   - Handles DCF calculations

3. **Stock Service** (`services/stock/`)
   - FastAPI Stock Data Service
   - Port: 8002
   - Manages stock information

4. **Database Service** (`services/database/`)
   - FastAPI Database Service
   - Port: 8003
   - Manages database operations and sync

5. **Frontend Service** (`services/frontend/`)
   - Nginx serving static files
   - Port: 8080 (mapped to 80 inside container)
   - Reverse proxy cho API requests

6. **PostgreSQL** (`postgres`)
   - Database server
   - Port: 5432

7. **Redis** (`redis`)
   - Cache và status tracking
   - Port: 6379

## Cấu trúc

```
dcf_project/
├── docker-compose.yml          # Orchestration file
├── docker-compose.dev.yml      # Development mode
├── services/
│   ├── common/
│   │   ├── Dockerfile.base     # Base image (shared)
│   │   └── requirements.txt    # Common dependencies
│   ├── gateway/
│   │   ├── Dockerfile.gateway  # Gateway service image
│   │   └── main.py            # FastAPI gateway
│   ├── dcf/
│   │   ├── Dockerfile.dcf      # DCF service image
│   │   └── main.py            # DCF service
│   ├── stock/
│   │   ├── Dockerfile.stock    # Stock service image
│   │   └── main.py            # Stock service
│   ├── database/
│   │   ├── Dockerfile.database # Database service image
│   │   └── main.py            # Database service
│   └── frontend/
│       ├── Dockerfile.frontend # Frontend service image
│       ├── nginx.conf         # Nginx configuration
│       ├── index.html         # Main HTML file
│       └── static/            # CSS, JS files
└── .dockerignore              # Docker ignore file
```

## Dockerfile Naming Convention

Để dễ phân biệt và quản lý, các Dockerfile được đặt tên theo service:

- `Dockerfile.base` - Base image (shared)
- `Dockerfile.gateway` - Gateway service
- `Dockerfile.dcf` - DCF service
- `Dockerfile.stock` - Stock service
- `Dockerfile.database` - Database service
- `Dockerfile.frontend` - Frontend service

## Cài đặt và chạy

### 1. Build Docker images

```bash
make docker-build
```

Hoặc thủ công:

```bash
docker-compose build
```

### 2. Start services

```bash
make docker-up
```

Hoặc thủ công:

```bash
docker-compose up -d
```

### 3. Truy cập services

- **Frontend**: http://localhost:8080
- **Gateway**: http://localhost:8000
- **DCF Service**: http://localhost:8001
- **Stock Service**: http://localhost:8002
- **Database Service**: http://localhost:8003
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### 4. Health Check

```bash
# Check all services
make health-check

# Or via web interface
http://localhost:8080/static/health.html
```

## Quản lý containers

### Xem logs

```bash
# Tất cả services
make docker-logs

# Individual services
make docker-logs-gateway
make docker-logs-dcf
make docker-logs-stock
make docker-logs-database
make docker-logs-frontend
make docker-logs-postgres
```

### Xem trạng thái

```bash
make docker-ps
```

### Restart services

```bash
make docker-restart
```

### Stop services

```bash
make docker-down
```

### Clean up

```bash
# Stop và xóa containers, volumes
make docker-clean
```

### Exec vào container

```bash
# Service containers
make docker-exec-gateway
make docker-exec-dcf
make docker-exec-stock
make docker-exec-database
make docker-exec-frontend

# Database containers
make docker-exec-postgres
```

## Volumes

Docker compose mount các thư mục sau để persistence:

- `./data` → `/app/data` (results và cache)
- `./config` → `/app/config` (config files)
- `./log` → `/app/log` (logs)

## Networks

Tất cả services chạy trong cùng một Docker network (`dcf-network`) để có thể communicate với nhau.

Frontend service proxy API requests đến `http://api:5000` (sử dụng service name).

## Health Checks

Tất cả services đều có health checks:

- **Gateway**: `/health` endpoint (aggregates all services)
- **DCF Service**: `/health` endpoint
- **Stock Service**: `/health` endpoint
- **Database Service**: `/health` endpoint
- **PostgreSQL**: `pg_isready` health check
- **Redis**: `redis-cli ping` health check

Docker sẽ tự động restart containers nếu health check fail.

### Health Check Tools

1. **Command Line**: `make health-check`
   - Checks Docker containers
   - Checks HTTP endpoints
   - Checks database connection
   - Checks Redis connection

2. **Web Dashboard**: `http://localhost:8080/static/health.html`
   - Real-time monitoring
   - Auto-refresh (30s)
   - Visual status indicators

## Development vs Production

### Development (không dùng Docker)

```bash
make web-install
make web
```

Chạy Flask dev server trực tiếp trên host.

### Production (Docker)

```bash
make docker-build
make docker-up
```

Chạy với Gunicorn và Nginx trong containers.

## Troubleshooting

### Port đã được sử dụng

Sửa ports trong `docker-compose.yml`:

```yaml
services:
  api:
    ports:
      - "5001:5000"  # Đổi port host
  frontend:
    ports:
      - "8081:80"    # Đổi port host
```

### Container không start

Kiểm tra logs:

```bash
docker-compose logs api
docker-compose logs frontend
```

### API không kết nối được

Kiểm tra network:

```bash
docker network inspect dcf_project_dcf-network
```

Kiểm tra API service:

```bash
docker-compose exec api curl http://localhost:5000/health
```

### Frontend không load được API

Kiểm tra nginx config và đảm bảo `proxy_pass` trỏ đúng đến `http://api:5000`.

## Scaling

Để scale API service:

```bash
docker-compose up -d --scale api=3
```

Sẽ chạy 3 instances của API service.

## Environment Variables

Có thể set environment variables trong `docker-compose.yml`:

```yaml
services:
  api:
    environment:
      - FLASK_ENV=production
      - LOG_LEVEL=INFO
```

## Security

- Nginx có security headers
- Gunicorn chạy với non-root user (trong container)
- Health checks để monitor services
- Volumes chỉ mount cần thiết

## Monitoring

Có thể tích hợp với monitoring tools như:
- Prometheus
- Grafana
- ELK Stack

## CI/CD

Có thể tích hợp với:
- GitHub Actions
- GitLab CI
- Jenkins

Build và push images:

```bash
# Build base image
make docker-build-base

# Build all services
make docker-build

# Build individual service
docker-compose build gateway
docker-compose build dcf
docker-compose build stock
docker-compose build database
docker-compose build frontend
```

## Database Management

```bash
# Start database services
make docker-db-start

# Stop database services
make docker-db-stop

# Restart database services
make docker-db-restart

# Check database status
make docker-db-status
```

---

**Version:** 2.0  
**Last Updated:** 2025-12-29

