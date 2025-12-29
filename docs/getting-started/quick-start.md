# Quick Start Guide

**Chạy DCF Project trong 5 phút**

## Prerequisites

- Docker & Docker Compose đã cài đặt
- Git
- ~2GB disk space

## Bước 1: Clone Repository

```bash
git clone <repository-url>
cd dcf_project
```

## Bước 2: Build Base Image

```bash
make docker-build-base
```

Lần đầu tiên có thể mất 5-10 phút để download dependencies.

## Bước 3: Build All Services

```bash
make docker-build
```

Hoặc build nhanh với parallel builds:

```bash
make docker-build-fast
```

## Bước 4: Start Services

```bash
make docker-up
```

## Bước 5: Truy Cập Ứng Dụng

- **Frontend**: http://localhost:8080
- **Gateway API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Sử Dụng Web Interface

1. Mở http://localhost:8080
2. Chọn mã cổ phiếu từ danh sách (ví dụ: FPT, VNM, VCB)
3. Click "Chạy DCF" để bắt đầu phân tích
4. Theo dõi progress bar trong quá trình tính toán
5. Xem kết quả khi hoàn tất

## Sử Dụng Command Line

### Chạy DCF cho một mã cổ phiếu

```bash
make dcf-single TICKER=FPT
```

### Chạy DCF cho tất cả mã

```bash
make dcf-all
```

### Chạy PE calculation

```bash
make pe-single TICKER=FPT
```

## Development Mode (Hot Reload)

Để phát triển với hot reload:

```bash
make docker-dev
```

Code changes sẽ tự động reload.

## Kiểm Tra Services

```bash
# Xem status của services
make docker-ps

# Xem logs
make docker-logs

# Xem logs của service cụ thể
make docker-logs-dcf
make docker-logs-stock
make docker-logs-gateway
```

## Dừng Services

```bash
make docker-down
```

## Troubleshooting

### Port đã được sử dụng

Kiểm tra và dừng các services đang chạy trên ports:
- 8080 (Frontend)
- 8000 (Gateway)
- 8001 (DCF Service)
- 8002 (Stock Service)
- 6379 (Redis)

### Docker build fails

```bash
# Clean build
make docker-build-base-no-cache
make docker-rebuild
```

### Redis connection issues

Services sẽ chạy ở fallback mode nếu Redis không available. Kiểm tra logs:

```bash
make docker-logs-redis
```

## Tiếp Theo

- [Installation Guide](installation.md) - Cài đặt chi tiết
- [First Steps](first-steps.md) - Các bước tiếp theo
- [Business Overview](../business/overview.md) - Hiểu về dự án

---

**Next:** [Installation Guide](installation.md) →

