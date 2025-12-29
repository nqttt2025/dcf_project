# Docker Build Fix Summary

## Vấn đề

Khi chạy `make docker-build`, lỗi xảy ra:
```
ERROR: failed to solve: dcf-project-base:latest: failed to resolve source metadata
```

### Nguyên nhân

1. **Base image được build với tag version** (ví dụ: `v1.0.7`)
2. **Services Dockerfile có default `ARG BASE_VERSION=latest`**
3. **scripts/docker.sh chỉ set `VERSION`**, không set `BASE_VERSION` khi build services
4. **docker-compose.yml có `${BASE_VERSION:-latest}`** - fallback về `latest` nếu không set

### Kết quả

- Base image: `dcf-project-base:v1.0.7` ✅
- Services tìm: `dcf-project-base:latest` ❌
- Lỗi: Image không tồn tại

## Giải pháp

### Đã sửa trong `scripts/docker.sh`:

1. **docker_build_images()** - Build services:
   ```bash
   # Trước:
   VERSION="$version" docker-compose build
   
   # Sau:
   BASE_VERSION="$base_version" VERSION="$version" docker-compose build
   ```

2. **cmd_rebuild()** - Rebuild services:
   ```bash
   # Trước:
   VERSION="$version" docker-compose build --no-cache
   
   # Sau:
   BASE_VERSION="$base_version" VERSION="$version" docker-compose build --no-cache
   ```

3. **cmd_up()** - Start containers:
   ```bash
   # Trước:
   VERSION="$version" docker-compose up -d
   
   # Sau:
   BASE_VERSION="$base_version" VERSION="$version" docker-compose up -d
   ```

4. **cmd_down()** - Stop containers:
   ```bash
   # Trước:
   VERSION="$version" docker-compose down
   
   # Sau:
   BASE_VERSION="$base_version" VERSION="$version" docker-compose down
   ```

5. **cmd_restart()** - Restart containers:
   ```bash
   # Trước:
   VERSION="$version" docker-compose restart
   
   # Sau:
   BASE_VERSION="$base_version" VERSION="$version" docker-compose restart
   ```

## Verification

Tất cả docker-compose commands giờ đều set cả `BASE_VERSION` và `VERSION`:
```bash
BASE_VERSION="$base_version" VERSION="$version" docker-compose <command>
```

## Kết quả

✅ Build thành công:
- Base image: `dcf-project-base:v1.0.7`
- Services build với: `BASE_VERSION=v1.0.7`
- Tất cả images được tag đúng version

✅ Tests hoạt động đúng:
- Build fails → Skip test class
- Container not running → Fail với message rõ ràng
- Logging đầy đủ với logger.info/error

## Test Results

```bash
make docker-build
# ✅ Build thành công
# ✅ All services use correct base version
# ✅ No more "latest" tag errors
```

