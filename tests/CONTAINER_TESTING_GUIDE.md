# Container Testing Guide

## Tại sao cần build containers trước khi test?

Khi test containers, chúng ta cần đảm bảo:
1. **Code mới nhất được build vào images** - Không test code cũ
2. **Version đúng** - Sử dụng version từ git tag và docker-versions.json
3. **Base image đúng** - Sử dụng base image version đúng

## Cách hoạt động

### Tự động build trong tests

Các test files đã được cập nhật để tự động build containers trước khi test:

```python
@classmethod
def setUpClass(cls):
    # Build containers với code mới nhất
    builder = get_container_builder(project_root)
    builder.build_containers(services=['gateway'])
```

### Build process

1. **Lấy version từ git tag** - Sử dụng git tag làm VERSION
2. **Lấy base version từ docker-versions.json** - Sử dụng BASE_VERSION
3. **Build với docker-compose** - `docker-compose build`
4. **Set environment variables** - VERSION và BASE_VERSION

### Sau khi build

Containers cần được start để test:
```bash
make docker-up
# hoặc
docker-compose up -d
```

## Tại sao không có test_container_networking?

### Giải thích

**test_container_networking đã được loại bỏ** vì:

1. **Microservice của bạn giao tiếp qua HTTP** - Gateway gọi DCF/Stock qua HTTP requests
2. **Docker tự động handle networking** - Containers trên cùng network tự động có thể giao tiếp
3. **Không cần test internal network** - Chỉ cần test external ports và API endpoints

### Thay thế bằng gì?

Thay vì test internal networking, chúng ta test:
- **External port mappings** - Ports được expose đúng (8000, 8001, 8002, 8003)
- **Service health endpoints** - Services có thể truy cập từ bên ngoài
- **API endpoints** - Gateway có thể proxy requests đến backend services

### Test gì thay vì networking?

1. **test_container_integration** - Test integration giữa containers
2. **test_container_health** - Test health checks
3. **test_external_service_access** - Test external access (mới thêm vào test_container_integration)

## Test Flow

```
1. Build containers với code mới nhất
   ↓
2. Start containers (manual hoặc trong CI/CD)
   ↓
3. Test containers:
   - Container status
   - Health endpoints
   - API endpoints
   - External access
```

## Best Practices

1. **Luôn build trước khi test** - Đảm bảo code mới nhất
2. **Test external ports** - Test từ bên ngoài như user thực tế
3. **Test API endpoints** - Test functionality thực tế
4. **Không cần test internal Docker network** - Docker tự động handle

## Summary

- ✅ **Build containers tự động** trong setUpClass
- ✅ **Loại bỏ test_container_networking** - Không cần thiết
- ✅ **Test external access** - Test như user thực tế
- ✅ **Test API endpoints** - Test functionality

