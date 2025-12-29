# Quick Start - Web Application

Hướng dẫn nhanh để truy cập vào web application DCF Analysis.

## Bước 1: Build Docker Images

Lần đầu tiên, bạn cần build Docker images:

```bash
make docker-build
```

Hoặc thủ công:

```bash
docker-compose build
```

Quá trình này có thể mất vài phút để download và build images.

## Bước 2: Start Services

Start tất cả microservices:

```bash
make docker-up
```

Hoặc thủ công:

```bash
docker-compose up -d
```

## Bước 3: Kiểm tra Services

Kiểm tra xem tất cả services đã chạy:

```bash
make docker-ps
```

Hoặc:

```bash
docker-compose ps
```

Bạn sẽ thấy 4 containers:
- `dcf-gateway` (Gateway Service)
- `dcf-service` (DCF Service)
- `dcf-stock` (Stock Service)
- `dcf-frontend` (Frontend Service)

## Bước 4: Truy cập Web Application

Mở trình duyệt và truy cập:

### 🌐 Frontend Dashboard
**http://localhost:8080**

Đây là giao diện chính để xem và quản lý DCF analysis.

### 📚 API Gateway
**http://localhost:8000**

API Gateway endpoint.

### 📖 API Documentation (Swagger UI)
**http://localhost:8000/docs**

Interactive API documentation với Swagger UI.

### 📘 ReDoc Documentation
**http://localhost:8000/redoc**

Alternative API documentation với ReDoc.

### 💚 Health Check
**http://localhost:8000/health**

Kiểm tra trạng thái của tất cả services.

## Bước 5: Xem Logs (nếu cần)

Nếu có vấn đề, xem logs:

```bash
# Tất cả logs
make docker-logs

# Logs của từng service
make docker-logs-gateway
make docker-logs-dcf
make docker-logs-stock
make docker-logs-frontend
```

## Troubleshooting

### Port đã được sử dụng

Nếu port 8080 hoặc 8000 đã được sử dụng, sửa trong `docker-compose.yml`:

```yaml
services:
  frontend:
    ports:
      - "8081:80"  # Đổi từ 8080 sang 8081
  gateway:
    ports:
      - "8001:8000"  # Đổi từ 8000 sang 8001
```

Sau đó restart:

```bash
make docker-down
make docker-up
```

### Services không start

Kiểm tra logs:

```bash
docker-compose logs gateway
docker-compose logs dcf
docker-compose logs stock
docker-compose logs frontend
```

### Không thể truy cập

1. Kiểm tra containers đang chạy:
   ```bash
   docker-compose ps
   ```

2. Kiểm tra health checks:
   ```bash
   curl http://localhost:8000/health
   ```

3. Kiểm tra firewall:
   ```bash
   # Nếu dùng WSL2, có thể cần expose ports
   ```

### Services chậm khởi động

Services cần vài giây để khởi động hoàn toàn. Đợi 10-20 giây sau khi start và thử lại.

## Stop Services

Để dừng tất cả services:

```bash
make docker-down
```

Hoặc:

```bash
docker-compose down
```

## Restart Services

Để restart services:

```bash
make docker-restart
```

Hoặc:

```bash
docker-compose restart
```

## Development Mode

Nếu muốn chạy ở development mode (không dùng Docker):

```bash
# Install dependencies
make web-install

# Run web service
make web
```

Sau đó truy cập: **http://localhost:5000**

## Next Steps

Sau khi truy cập được web application:

1. Xem danh sách cổ phiếu VN30
2. Click vào một cổ phiếu để xem chi tiết
3. Xem config của cổ phiếu
4. Chạy DCF analysis cho cổ phiếu (nếu chưa có)

---

**Version:** 1.0  
**Last Updated:** 2025-12-28

