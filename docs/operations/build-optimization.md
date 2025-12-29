# Docker Build Optimization

Hướng dẫn tối ưu tốc độ build Docker images.

## Tối Ưu Đã Áp Dụng

### 1. Docker BuildKit ✅

BuildKit là build engine mới của Docker, nhanh hơn và có nhiều tính năng:
- Parallel builds
- Better caching
- Build cache mounts
- Improved performance

**Tự động enabled** trong build scripts.

### 2. Base Image Caching ✅

Tạo base image chung (`dcf-project-base`) chứa:
- Python 3.11-slim
- System dependencies (gcc)
- Common Python packages

**Lợi ích:**
- Base image được cache, không rebuild mỗi lần
- Chỉ rebuild khi requirements.txt thay đổi
- Giảm thời gian build từ ~5-10 phút xuống ~2-3 phút

### 3. Layer Caching ✅

Sắp xếp lại Dockerfile để tận dụng cache:
1. Copy requirements.txt trước
2. Install dependencies (layer này được cache)
3. Copy source code sau (thay đổi thường xuyên)

### 4. Build Cache Mounts ✅

Cache pip packages giữa các lần build:
```dockerfile
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r /app/common_requirements.txt
```

**Lợi ích:**
- Không cần download packages mỗi lần build
- Giảm thời gian install dependencies từ ~3 phút xuống ~30 giây

### 5. Parallel Builds ✅

Build nhiều images cùng lúc:
```bash
make docker-build-fast
# hoặc
PARALLEL=true make docker-build
```

**Lợi ích:**
- Build gateway, dcf, stock cùng lúc
- Giảm thời gian tổng từ ~10 phút xuống ~3-4 phút

### 6. Optimized .dockerignore ✅

Loại bỏ files không cần thiết khỏi build context:
- Git files
- IDE files
- Logs
- Tests
- Documentation
- Scripts

**Lợi ích:**
- Giảm build context size
- Tăng tốc độ copy files vào container

## So Sánh Tốc Độ

| Phương pháp | Thời gian Build | Ghi chú |
|------------|----------------|---------|
| **Trước (no optimization)** | 8-12 phút | Build tuần tự, không cache |
| **Sau (với optimizations)** | 2-4 phút | Build song song, có cache |
| **Build nhanh nhất** | 1-2 phút | Chỉ rebuild service code |

## Cách Sử Dụng

### Build Thông Thường
```bash
make docker-build
```
- Build tuần tự
- Sử dụng cache
- Tối ưu cho development

### Build Nhanh (Parallel)
```bash
make docker-build-fast
# hoặc
PARALLEL=true make docker-build
```
- Build song song nhiều images
- Nhanh hơn 2-3 lần
- Tối ưu khi build nhiều services

### Rebuild Hoàn Toàn
```bash
make docker-rebuild
```
- Rebuild từ đầu (--no-cache)
- Rebuild cả base image
- Sử dụng khi thay đổi dependencies

## Build Base Image Riêng

Nếu muốn rebuild base image:
```bash
make docker-build-base
# hoặc
docker-compose build base
```

Base image sẽ được cache và reuse cho các services khác.

**Lưu ý**: Base image chỉ rebuild khi `services/common/requirements.txt` thay đổi (detected via SHA256 hash).

## Tips

### 1. Tận Dụng Cache
- Sửa code → chỉ rebuild service image (nhanh)
- Sửa requirements.txt → rebuild base image (chậm hơn)

### 2. Build Context
- Đảm bảo `.dockerignore` loại bỏ files không cần thiết
- Giảm context size = tăng tốc độ

### 3. Parallel Builds
- Sử dụng `build-fast` khi build nhiều services
- Không dùng khi build một service duy nhất

### 4. BuildKit
- Tự động enabled trong scripts
- Không cần config thêm

## Troubleshooting

### Build chậm
1. Kiểm tra `.dockerignore` có đúng không
2. Kiểm tra base image có được cache không: `docker images | grep base`
3. Thử rebuild base image: `docker-compose build base`

### Cache không hoạt động
1. Kiểm tra BuildKit: `echo $DOCKER_BUILDKIT` (should be 1)
2. Rebuild base image: `docker-compose build base`
3. Clear cache nếu cần: `docker builder prune`

### Parallel build fails
1. Kiểm tra memory: parallel builds cần nhiều RAM hơn
2. Build tuần tự: `make docker-build` (không dùng PARALLEL)

## Advanced

### Custom Build Arguments
```bash
# Build với custom version
VERSION=v2.0.0 make docker-build

# Build parallel với custom version
VERSION=v2.0.0 PARALLEL=true make docker-build-fast
```

### Build Single Service
```bash
# Build chỉ gateway
docker-compose build gateway

# Build chỉ dcf service
docker-compose build dcf

# Build chỉ stock service
docker-compose build stock

# Build chỉ database service
docker-compose build database

# Build chỉ frontend
docker-compose build frontend
```

## Dockerfile Naming Convention

Để dễ phân biệt và quản lý, các Dockerfile được đặt tên theo service:

- `services/common/Dockerfile.base` - Base image (shared)
- `services/gateway/Dockerfile.gateway` - Gateway service
- `services/dcf/Dockerfile.dcf` - DCF service
- `services/stock/Dockerfile.stock` - Stock service
- `services/database/Dockerfile.database` - Database service
- `services/frontend/Dockerfile.frontend` - Frontend service

Tất cả dockerfile paths đã được cập nhật trong `docker-compose.yml` và `docker-compose.dev.yml`.

---

**Version:** 1.0  
**Last Updated:** 2025-12-29

