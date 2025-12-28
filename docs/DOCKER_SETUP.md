# Docker Microservices Setup

Hướng dẫn chạy DCF Analysis Web Service với Docker theo mô hình microservices.

## Kiến trúc

Dự án được chia thành 2 microservices:

1. **API Service** (`services/api/`)
   - Flask backend API
   - Port: 5000
   - Xử lý tất cả API requests

2. **Frontend Service** (`services/frontend/`)
   - Nginx serving static files
   - Port: 8080 (mapped to 80 inside container)
   - Reverse proxy cho API requests

## Cấu trúc

```
dcf_project/
├── docker-compose.yml          # Orchestration file
├── services/
│   ├── api/
│   │   ├── Dockerfile         # API service image
│   │   ├── app.py             # Flask application
│   │   └── requirements.txt   # Python dependencies
│   └── frontend/
│       ├── Dockerfile         # Frontend service image
│       ├── nginx.conf         # Nginx configuration
│       ├── index.html         # Main HTML file
│       └── static/            # CSS, JS files
└── .dockerignore              # Docker ignore file
```

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
- **API**: http://localhost:5000
- **API Health Check**: http://localhost:5000/health

## Quản lý containers

### Xem logs

```bash
# Tất cả services
make docker-logs

# Chỉ API service
make docker-logs-api

# Chỉ Frontend service
make docker-logs-frontend
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
# API container
make docker-exec-api

# Frontend container
make docker-exec-frontend
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

Cả hai services đều có health checks:

- **API**: `/health` endpoint
- **Frontend**: `/health` endpoint

Docker sẽ tự động restart containers nếu health check fail.

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
docker build -t dcf-api:latest -f services/api/Dockerfile .
docker build -t dcf-frontend:latest -f services/frontend/Dockerfile .
```

---

**Version:** 1.0  
**Last Updated:** 2025-12-28

