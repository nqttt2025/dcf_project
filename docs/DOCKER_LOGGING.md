# Docker Build Logging

Tất cả Docker build logs được tự động lưu lại để kiểm tra và debug.

## Log Directory

Tất cả logs được lưu trong: `logs/docker/`

## Log File Naming

Mỗi log file có tên với format:
```
<command>-YYYYMMDD-HHMMSS.log
```

Ví dụ:
- `docker-build-20251228-170530.log`
- `docker-rebuild-20251228-170545.log`
- `docker-clean-20251228-171000.log`
- `docker-clean-all-20251228-171015.log`
- `docker-logs-20251228-171030.log`

## Commands với Logging

### 1. `make docker-build`
**Log file:** `docker-build-YYYYMMDD-HHMMSS.log`

Chứa:
- Timestamp khi chạy
- Output của `docker-compose build`
- Cleanup operations
- Exit code

### 2. `make docker-rebuild`
**Log file:** `docker-rebuild-YYYYMMDD-HHMMSS.log`

Chứa:
- Timestamp khi chạy
- Stop containers
- Remove old containers
- Cleanup operations
- Build với `--no-cache`
- Exit code

### 3. `make docker-clean`
**Log file:** `docker-clean-YYYYMMDD-HHMMSS.log`

Chứa:
- Timestamp khi chạy
- Stop và remove containers
- Remove unused images
- Remove unused containers

### 4. `make docker-clean-all`
**Log file:** `docker-clean-all-YYYYMMDD-HHMMSS.log`

Chứa:
- Timestamp khi chạy
- Deep cleanup operations
- Remove all unused resources

### 5. `make docker-logs`
**Log file:** `docker-logs-YYYYMMDD-HHMMSS.log`

Chứa:
- Timestamp khi chạy
- Container logs (last 100 lines)

## Log File Format

Mỗi log file có format:

```
Building Docker images for microservices...
Log file: logs/docker/docker-build-20251228-170530.log
Timestamp: 2025-12-28 17:05:30
========================================
[Build output here...]
✓ Build completed and cleanup done
Log saved to: logs/docker/docker-build-20251228-170530.log
```

## Xem Logs

### List tất cả log files:
```bash
ls -lh logs/docker/
```

### Xem log file mới nhất:
```bash
ls -t logs/docker/*.log | head -1 | xargs cat
```

### Xem log file cụ thể:
```bash
cat logs/docker/docker-build-20251228-170530.log
```

### Follow log file:
```bash
tail -f logs/docker/docker-build-20251228-170530.log
```

### Tìm lỗi trong logs:
```bash
# Tìm ERROR trong tất cả logs
grep -i error logs/docker/*.log

# Tìm ERROR trong log file cụ thể
grep -i error logs/docker/docker-build-*.log

# Tìm WARNING
grep -i warning logs/docker/*.log
```

### Xem logs theo thời gian:
```bash
# Logs hôm nay
ls logs/docker/*$(date +%Y%m%d)*.log

# Logs của một ngày cụ thể
ls logs/docker/*20251228*.log
```

## Log Analysis

### Đếm số lần build:
```bash
ls logs/docker/docker-build-*.log | wc -l
```

### Xem build time:
```bash
grep "Timestamp:" logs/docker/docker-build-*.log | tail -5
```

### Xem build failures:
```bash
grep -l "ERROR\|FAILED\|error\|failed" logs/docker/docker-build-*.log
```

### Xem build success:
```bash
grep -l "✓ Build completed" logs/docker/docker-build-*.log
```

## Cleanup Old Logs

### Xóa logs cũ hơn 7 ngày:
```bash
find logs/docker -name "*.log" -mtime +7 -delete
```

### Xóa logs cũ hơn 30 ngày:
```bash
find logs/docker -name "*.log" -mtime +30 -delete
```

### Xóa tất cả logs (cẩn thận!):
```bash
rm -f logs/docker/*.log
```

## Git Ignore

Log files được ignore trong `.gitignore`:
```
logs/docker/*.log
!logs/docker/.gitkeep
```

Chỉ giữ lại `.gitkeep` để đảm bảo directory structure.

## Best Practices

1. **Kiểm tra logs sau mỗi build** để phát hiện warnings/errors sớm
2. **Giữ logs trong ít nhất 7 ngày** để có thể debug
3. **Xóa logs cũ định kỳ** để giải phóng disk space
4. **Backup logs quan trọng** nếu cần debug lâu dài

## Troubleshooting

### Log file không được tạo
- Kiểm tra quyền ghi: `ls -ld logs/docker/`
- Tạo directory: `mkdir -p logs/docker/`

### Log file quá lớn
- Xóa logs cũ: `find logs/docker -name "*.log" -mtime +7 -delete`
- Compress logs: `gzip logs/docker/*.log`

### Không tìm thấy log file
- Kiểm tra timestamp format
- List tất cả: `ls -lh logs/docker/`

---

**Version:** 1.0  
**Last Updated:** 2025-12-28

