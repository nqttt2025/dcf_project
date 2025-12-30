# Performance Improvements cho Gateway Service

## Vấn đề

Khi chạy quá nhiều phân tích đồng thời, có thể gặp lỗi:
```
dcf service unavailable: All connection attempts failed
```

## Các cải thiện đã thực hiện

### 1. **Connection Pooling**
- Shared HTTP client thay vì tạo mới mỗi request
- Connection pool: max 200 connections, 50 keepalive
- Giảm overhead và tăng hiệu suất

### 2. **Retry Logic với Exponential Backoff**
- Tự động retry khi connection fails
- Exponential backoff: delay tăng dần (1s, 2s, 4s...)
- DCF analysis: 5 retries với delay 2s
- Other requests: 3 retries với delay 1s

### 3. **Rate Limiting**
- Giới hạn 10 analysis requests/phút/IP
- Tránh overload khi có quá nhiều request
- HTTP 429 khi vượt quá limit

### 4. **Concurrency Control**
- Semaphore: max 50 concurrent requests từ gateway
- DCF service: max 10 concurrent analyses
- Tránh resource exhaustion

### 5. **Uvicorn Workers**
- Gateway: 4 workers
- DCF Service: 2 workers với limit 20 concurrent requests
- Tăng throughput và xử lý parallel requests tốt hơn

### 6. **Improved Error Handling**
- Phân biệt connection errors vs timeout vs HTTP errors
- Retry chỉ với 5xx errors
- Thông báo lỗi rõ ràng hơn

## Cấu hình

### Gateway Service
```yaml
workers: 4
max_connections: 200
max_keepalive: 50
concurrent_requests: 50 (semaphore)
rate_limit: 10 requests/minute/IP
```

### DCF Service
```yaml
workers: 2
max_concurrent_analyses: 10
limit_concurrency: 20
```

## Monitoring

- Logs các retry attempts
- Track concurrent requests
- Monitor rate limit violations

## Best Practices

1. **Không gửi quá nhiều request đồng thời**
   - Sử dụng queue hoặc batch processing
   - Chờ kết quả trước khi gửi request tiếp theo

2. **Xử lý rate limit errors**
   - Check HTTP 429 status
   - Retry sau `retry_after` seconds

3. **Monitor service health**
   - Check `/health` endpoint trước khi gửi request
   - Implement circuit breaker nếu cần

4. **Sử dụng caching**
   - Cache kết quả analysis đã hoàn thành
   - Giảm số request đến DCF service

## Troubleshooting

### Lỗi "All connection attempts failed"
1. Kiểm tra DCF service có đang chạy không
2. Kiểm tra số lượng concurrent analyses (max 10)
3. Kiểm tra logs để xem retry attempts
4. Tăng timeout nếu analysis mất nhiều thời gian

### Lỗi "Rate limit exceeded"
- Giảm số request/phút
- Implement request queue
- Sử dụng batch processing

### Service overload
- Giảm số concurrent requests
- Tăng số workers
- Scale horizontally (nhiều instances)

