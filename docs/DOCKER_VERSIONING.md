# Docker Image Versioning

Hệ thống versioning cho Docker images sử dụng git tags.

## Tổng quan

Docker images được tag tự động dựa trên git tags. Mỗi service có image name riêng với version tag.

## Image Naming Convention

Format: `dcf-project-<service>:<version>`

Ví dụ:
- `dcf-project-gateway:v1.0.0`
- `dcf-project-dcf:v1.0.0`
- `dcf-project-stock:v1.0.0`
- `dcf-project-frontend:v1.0.0`

## Version Sources

Version được lấy theo thứ tự ưu tiên:

1. **Git Tag** (nếu có): Sử dụng tag mới nhất
   ```bash
   git tag v1.0.0
   # Version sẽ là: v1.0.0
   ```

2. **Git Commit Hash** (nếu không có tag): Sử dụng short commit hash
   ```bash
   # Version sẽ là: dev-da5700d
   ```

3. **Timestamp** (nếu không phải git repo): Sử dụng timestamp
   ```bash
   # Version sẽ là: dev-20251229-002516
   ```

## Workflow

### 1. Tạo Git Tag

```bash
# Tạo tag mới
make git-tag VERSION=v1.0.0

# Hoặc thủ công
./scripts/create_git_tag.sh v1.0.0

# Push tag lên remote
git push origin v1.0.0
```

### 2. Build Docker Images

```bash
# Build với version từ git tag
make docker-build

# Hoặc rebuild (xóa old images trước)
make docker-rebuild
```

Images sẽ được tag với version từ git tag:
- `dcf-project-gateway:v1.0.0`
- `dcf-project-dcf:v1.0.0`
- `dcf-project-stock:v1.0.0`
- `dcf-project-frontend:v1.0.0`

### 3. Xem Images

```bash
# List tất cả images với versions
make docker-images

# Hoặc thủ công
docker images | grep dcf-project
```

### 4. Cleanup Old Images

```bash
# Xóa old images, giữ lại 3 version mới nhất
make docker-clean-old KEEP=3
```

## Commands

### Build Commands

```bash
# Build với versioning
make docker-build

# Rebuild với cleanup old images
make docker-rebuild
```

### Git Tag Commands

```bash
# Tạo git tag
make git-tag VERSION=v1.0.0

# Xem version hiện tại
make get-version
```

### Image Management

```bash
# List images
make docker-images

# Cleanup old images
make docker-clean-old KEEP=3
```

## Version trong Dockerfile

Mỗi Dockerfile nhận `VERSION` build argument:

```dockerfile
ARG VERSION=latest
ENV APP_VERSION=${VERSION}
LABEL version="${VERSION}"
```

Version được set trong environment variable `APP_VERSION` và có thể được sử dụng trong application.

## Docker Compose

`docker-compose.yml` sử dụng `VERSION` environment variable:

```bash
# Build với version cụ thể
VERSION=v1.0.0 docker-compose build

# Run với version cụ thể
VERSION=v1.0.0 docker-compose up
```

## Best Practices

### 1. Semantic Versioning

Sử dụng semantic versioning cho git tags:
- `v1.0.0` - Major release
- `v1.1.0` - Minor release
- `v1.1.1` - Patch release

### 2. Tag Before Build

Luôn tạo git tag trước khi build production images:

```bash
make git-tag VERSION=v1.0.0
make docker-rebuild
```

### 3. Cleanup Regularly

Xóa old images định kỳ để giải phóng disk space:

```bash
make docker-clean-old KEEP=5
```

### 4. Version in Application

Sử dụng `APP_VERSION` environment variable trong application để hiển thị version:

```python
import os
version = os.getenv('APP_VERSION', 'unknown')
```

## Troubleshooting

### Version không được set

Kiểm tra git tag:
```bash
git tag
./scripts/get_version.sh
```

### Old images không bị xóa

Kiểm tra image names:
```bash
docker images | grep dcf-project
```

### Build với version cụ thể

```bash
VERSION=v1.0.0 docker-compose build
```

---

**Version:** 1.0  
**Last Updated:** 2025-12-29

