# Docker Cleanup Guide

Hướng dẫn về các lệnh cleanup Docker trong DCF Project.

## Commands

### 1. `make docker-build`
Build images với cleanup tự động:
- Build Docker images
- Tự động xóa dangling images
- Tự động xóa stopped containers

**Sử dụng khi:** Build images lần đầu hoặc sau khi sửa code nhỏ.

### 2. `make docker-rebuild` ⭐ RECOMMENDED
Rebuild hoàn toàn từ đầu với cleanup:
- Stop tất cả containers
- Remove old containers
- Cleanup unused images
- Build từ đầu (--no-cache)
- Xóa dangling images

**Sử dụng khi:** 
- Sau khi sửa Dockerfile
- Sau khi thay đổi dependencies
- Cần rebuild hoàn toàn

**Ví dụ:**
```bash
make docker-rebuild
make docker-up
```

### 3. `make docker-clean`
Cleanup nhẹ:
- Stop và remove containers
- Remove dangling images
- Remove unused containers
- Giữ lại images đang được sử dụng

**Sử dụng khi:** Chỉ muốn cleanup mà không rebuild.

### 4. `make docker-clean-all`
Deep clean - xóa tất cả unused resources:
- Stop và remove containers
- Remove **TẤT CẢ** unused images (không chỉ dangling)
- Remove unused containers
- Remove unused networks
- Remove unused volumes

**⚠️ CẢNH BÁO:** Sẽ xóa tất cả images không được sử dụng, kể cả của projects khác!

**Sử dụng khi:** 
- Cần giải phóng nhiều disk space
- Cleanup toàn bộ Docker environment

## Workflow Khuyến Nghị

### Sau khi sửa code/Dockerfile:
```bash
make docker-rebuild  # Rebuild với cleanup
make docker-up       # Start services
```

### Build thông thường:
```bash
make docker-build    # Build với cleanup tự động
make docker-up       # Start services
```

### Cleanup định kỳ:
```bash
make docker-clean    # Cleanup nhẹ
```

### Deep cleanup (khi cần):
```bash
make docker-clean-all  # ⚠️ Cẩn thận!
```

## Chi tiết Cleanup

### Dangling Images
Images không có tag và không được sử dụng bởi containers nào.

### Unused Containers
Containers đã stopped và không còn được sử dụng.

### Unused Networks
Networks không được sử dụng bởi containers nào.

### Unused Volumes
Volumes không được sử dụng bởi containers nào.

## Disk Space

Kiểm tra disk space sử dụng:

```bash
# Xem disk space Docker sử dụng
docker system df

# Xem chi tiết
docker system df -v
```

## Manual Cleanup

Nếu cần cleanup thủ công:

```bash
# Xóa dangling images
docker image prune -f

# Xóa tất cả unused images
docker image prune -af

# Xóa unused containers
docker container prune -f

# Xóa unused networks
docker network prune -f

# Xóa unused volumes
docker volume prune -f

# Xóa tất cả (cẩn thận!)
docker system prune -af --volumes
```

## Troubleshooting

### Images không được xóa
Kiểm tra xem có containers nào đang sử dụng:
```bash
docker ps -a
docker images
```

### Containers không được xóa
Force remove:
```bash
docker-compose rm -f
docker container prune -f
```

### Disk space vẫn đầy
Deep clean:
```bash
make docker-clean-all
```

---

**Version:** 1.0  
**Last Updated:** 2025-12-28

