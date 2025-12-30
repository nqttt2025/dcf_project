# Real-time Updates Implementation - Hybrid Approach

## Tổng Quan

Đã implement hybrid approach kết hợp:
1. **Server-Sent Events (SSE)** cho real-time updates
2. **Smart Polling** với adaptive interval làm fallback

## Implementation Details

### 1. Backend - SSE Endpoint (`/api/stocks/stream`)

**Location**: `services/gateway/main.py`

**Features**:
- Stream stock updates mỗi 5 giây khi có thay đổi
- Heartbeat mỗi 30 giây để maintain connection
- Adaptive interval: 5s khi có changes, 10s khi stable
- Chỉ gửi data khi có thay đổi (hash-based change detection)

**Code**:
```python
@app.get("/api/stocks/stream")
async def stream_stocks():
    """SSE endpoint for real-time stock updates"""
    async def event_generator():
        last_data_hash = None
        consecutive_no_change = 0
        
        while True:
            # Fetch latest stocks data
            stocks_data = await make_service_request(...)
            
            # Create hash to detect changes
            stocks_hash = json.dumps([...])
            
            # Only send if data changed
            data_changed = stocks_hash != last_data_hash
            if data_changed:
                yield f"data: {json.dumps(stocks_data)}\n\n"
                await asyncio.sleep(5)
            else:
                # Send heartbeat every 30 seconds
                if consecutive_no_change >= 6:
                    yield f": heartbeat\n\n"
                await asyncio.sleep(10)
```

---

### 2. Frontend - Main Page (`/`)

**Location**: `services/frontend/static/js/app.js`

**Features**:
- **SSE Connection**: Tự động kết nối SSE khi page load
- **Smart Polling Fallback**: Tự động chuyển sang polling nếu SSE fail
- **Adaptive Interval**: 
  - 5s khi có thay đổi
  - Tăng dần lên 30s khi không có thay đổi
- **Change Detection**: Hash-based để detect changes

**Code Flow**:
```javascript
// Initialize SSE
function initSSE() {
    eventSource = new EventSource('/api/stocks/stream');
    eventSource.onmessage = (event) => {
        // Update stocks immediately
        updateStocks(data);
    };
    eventSource.onerror = () => {
        // Fallback to polling
        startSmartPolling();
    };
}

// Smart polling fallback
function startSmartPolling() {
    const poll = async () => {
        await loadStocks();
        // Adaptive interval
        pollTimeout = setTimeout(poll, pollInterval);
    };
    poll();
}
```

---

### 3. Frontend - Database Page (`/static/database.html`)

**Location**: `services/frontend/static/database.html`

**Features**:
- **Smart Polling**: Adaptive interval cho sync jobs
- **Activity-based**: 
  - 5s khi có active jobs
  - 10s khi có changes nhưng không có active jobs
  - Tăng dần lên 30s khi idle
- **Change Detection**: Hash-based để detect changes

**Code**:
```javascript
async function loadSyncJobs() {
    const data = await fetch('/api/database/sync/jobs');
    
    // Adaptive interval based on activity
    const hasActiveJobs = (data.total_active || 0) > 0;
    if (hasActiveJobs) {
        jobsPollInterval = 5000; // Fast when active
    } else if (jobsHash !== lastJobsHash) {
        jobsPollInterval = 10000; // Moderate when changed
    } else {
        jobsPollInterval = Math.min(jobsPollInterval * 1.2, 30000); // Slow when idle
    }
}
```

---

## Benefits

### 1. **Real-time Updates**
- ✅ Thấy thay đổi ngay lập tức qua SSE
- ✅ Không cần refresh trang
- ✅ Responsive user experience

### 2. **Performance Optimization**
- ✅ Chỉ gửi data khi có thay đổi
- ✅ Adaptive interval giảm unnecessary requests
- ✅ Heartbeat để maintain connection hiệu quả

### 3. **Reliability**
- ✅ Auto fallback sang polling nếu SSE fail
- ✅ Auto reconnect khi SSE disconnect
- ✅ Graceful degradation

### 4. **Resource Efficiency**
- ✅ Giảm bandwidth usage
- ✅ Giảm server load
- ✅ Tối ưu cho mobile devices

---

## Testing

### Test SSE Connection:
```bash
curl -N http://localhost:8000/api/stocks/stream
```

### Test Frontend:
1. Mở `http://localhost:8081/`
2. Mở Browser DevTools → Network tab
3. Tìm request `/api/stocks/stream`
4. Verify SSE connection established
5. Trigger price sync job
6. Verify stocks update in real-time

### Test Fallback:
1. Disable SSE trong browser (block `/api/stocks/stream`)
2. Verify polling fallback hoạt động
3. Verify adaptive interval hoạt động

---

## Monitoring

### Metrics to Track:
- SSE connection count
- Polling fallback rate
- Average update interval
- Data change frequency
- Error rate

### Logs:
- SSE connection/disconnection events
- Polling fallback triggers
- Error events

---

## Future Enhancements

1. **WebSocket Support**: Cho bidirectional communication
2. **Redis Pub/Sub**: Cho distributed real-time updates
3. **Client-side Caching**: Giảm server requests
4. **Compression**: Giảm bandwidth cho SSE
5. **Multi-client Support**: Broadcast updates to all clients

---

## Troubleshooting

### SSE không kết nối:
- Check gateway logs
- Verify CORS settings
- Check nginx proxy configuration
- Verify browser support

### Polling fallback không hoạt động:
- Check JavaScript console
- Verify `sseSupported` flag
- Check network connectivity

### Updates không real-time:
- Check SSE connection status
- Verify change detection logic
- Check server-side hash generation

