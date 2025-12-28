# Development Mode - Fast Backend Testing

Hướng dẫn phát triển backend nhanh chóng mà không cần rebuild Docker mỗi lần code thay đổi.

## Vấn đề

Khi phát triển backend, mỗi lần code thay đổi cần:
1. Rebuild Docker images (mất 5-10 phút)
2. Restart containers
3. Test lại

→ **Rất tốn thời gian!**

## Giải pháp

Có 3 cách để phát triển backend nhanh hơn:

### Cách 1: Docker Development Mode (Hot Reload) ⚡

Sử dụng `docker-compose.dev.yml` với volume mounts và hot reload.

**Ưu điểm:**
- Vẫn dùng Docker (môi trường nhất quán)
- Hot reload tự động khi code thay đổi
- Không cần rebuild

**Cách dùng:**
```bash
# Start services với hot reload
make docker-dev

# Xem logs
make docker-dev-logs

# Stop
make docker-dev-down
```

**Cách hoạt động:**
- Source code được mount vào containers
- Uvicorn chạy với `--reload` flag
- Code changes → tự động reload

### Cách 2: Local Development (Nhanh nhất) 🚀

Chạy backend services trực tiếp trên host (không qua Docker).

**Ưu điểm:**
- **Nhanh nhất** - không có Docker overhead
- Hot reload tự động
- Dễ debug với IDE

**Cách dùng:**
```bash
# Option 1: Chạy tất cả services cùng lúc
make backend-dev

# Option 2: Chạy từng service riêng (khuyến nghị)
# Terminal 1:
make backend-gateway

# Terminal 2:
make backend-dcf

# Terminal 3:
make backend-stock
```

**Setup lần đầu:**
```bash
# Tạo virtual environment và install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r services/common/requirements.txt
```

### Cách 3: Script Helper

Sử dụng script helper để chạy từng service:

```bash
# Chạy Gateway
./scripts/run_backend_local.sh gateway

# Chạy DCF Service
./scripts/run_backend_local.sh dcf

# Chạy Stock Service
./scripts/run_backend_local.sh stock
```

## So sánh các phương pháp

| Phương pháp | Thời gian Start | Hot Reload | Môi trường | Khuyến nghị |
|------------|----------------|------------|------------|-------------|
| **Docker Production** | 5-10 phút (rebuild) | ❌ | Docker | Production |
| **Docker Dev Mode** | ~30 giây | ✅ | Docker | Development với Docker |
| **Local Development** | ~5 giây | ✅ | Host | **Development (nhanh nhất)** |

## Workflow khuyến nghị

### Khi phát triển backend:

1. **Start services:**
   ```bash
   # Cách nhanh nhất
   make backend-dev
   
   # Hoặc từng service riêng
   make backend-gateway  # Terminal 1
   make backend-dcf      # Terminal 2
   make backend-stock    # Terminal 3
   ```

2. **Edit code:**
   - Sửa code trong `services/*/main.py` hoặc `src/`
   - Changes tự động reload (không cần restart)

3. **Test:**
   ```bash
   # Test Gateway
   curl http://localhost:8000/health
   
   # Test DCF Service
   curl http://localhost:8001/health
   
   # Test Stock Service
   curl http://localhost:8002/health
   ```

4. **Khi hoàn thành:**
   ```bash
   # Rebuild Docker images cho production
   make docker-rebuild
   ```

## Lưu ý

### Local Development Mode:

1. **Dependencies:**
   - Cần install dependencies: `pip install -r services/common/requirements.txt`
   - Cần có Python 3.11+

2. **PYTHONPATH:**
   - Script tự động set `PYTHONPATH`
   - Nếu chạy thủ công, cần:
     ```bash
     export PYTHONPATH="$(pwd):$(pwd)/src"
     ```

3. **Ports:**
   - Gateway: 8000
   - DCF Service: 8001
   - Stock Service: 8002
   - Đảm bảo ports không bị conflict

4. **Data & Config:**
   - Services vẫn đọc từ `data/`, `config/`, `logs/` như bình thường
   - Không cần Docker volumes

### Docker Dev Mode:

1. **Volume Mounts:**
   - Source code được mount vào containers
   - Changes trên host → reflect trong container

2. **Hot Reload:**
   - Uvicorn `--reload` tự động detect file changes
   - Reload mất ~1-2 giây

## Troubleshooting

### Local Development:

**Lỗi: Module not found**
```bash
# Đảm bảo PYTHONPATH được set
export PYTHONPATH="$(pwd):$(pwd)/src"

# Hoặc chạy từ project root
cd /home/eenitug/dcf_project
make backend-dev
```

**Lỗi: Port already in use**
```bash
# Kiểm tra ports
lsof -i :8000
lsof -i :8001
lsof -i :8002

# Kill process nếu cần
kill -9 <PID>
```

### Docker Dev Mode:

**Lỗi: Changes không reload**
- Kiểm tra volume mounts trong `docker-compose.dev.yml`
- Đảm bảo `--reload` flag có trong command
- Check logs: `make docker-dev-logs`

## Quick Reference

```bash
# Development (nhanh nhất)
make backend-dev

# Docker Dev Mode (vẫn dùng Docker)
make docker-dev

# Production (rebuild images)
make docker-rebuild
make docker-up
```

---

**Version:** 1.0  
**Last Updated:** 2025-12-29

