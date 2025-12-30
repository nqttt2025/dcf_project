# Workflow Lấy và Cập Nhật Dữ Liệu

## Workflow Hiện Tại

### 1. **Frontend - Trang Chính (`/`)**

#### Cập nhật dữ liệu:
- **Polling Interval**: 30 giây (cố định)
- **Cơ chế**: `setInterval(loadStocks, 30000)`
- **API Endpoint**: `/api/stocks`
- **Luồng dữ liệu**:
  ```
  Frontend (30s) → Gateway → Stock Service → Database Service → PostgreSQL
                                                      ↓
                                              Result Files (JSON)
  ```

#### Quy trình:
1. Frontend gọi `/api/stocks` mỗi 30 giây
2. Stock Service:
   - Đọc config files từ `config/` directory
   - Đọc result files từ `data/results/`
   - **Fetch giá từ Database Service** (parallel cho tất cả tickers)
   - Merge dữ liệu và trả về
3. Frontend render lại danh sách stocks

#### Hạn chế:
- ❌ Polling cố định 30s, không linh hoạt
- ❌ Không có real-time updates
- ❌ Phải đợi đến lượt polling mới thấy thay đổi
- ❌ Tốn bandwidth và server resources

---

### 2. **Frontend - Trang Database (`/static/database.html`)**

#### Cập nhật dữ liệu:
- **Auto-refresh Jobs**: 5 giây (có thể bật/tắt)
- **Cơ chế**: `setInterval(loadSyncJobs, 5000)`
- **API Endpoint**: `/api/database/sync/jobs`
- **Polling Sync Status**: 1 giây khi có job đang chạy

#### Quy trình:
1. Load scheduled jobs từ database
2. Auto-refresh mỗi 5 giây để cập nhật trạng thái jobs
3. Khi trigger sync job:
   - Poll status mỗi 1 giây
   - Dừng khi job completed/failed

---

### 3. **Backend - Sync Service**

#### Các loại sync jobs:

1. **Current Price Sync** (`sync_current_price`)
   - **Nguồn**: vnstock API
   - **Đích**: `market_data` table trong PostgreSQL
   - **Cách trigger**: Manual (qua Scheduled Jobs UI)
   - **Delay**: 1 giây giữa mỗi stock (tránh rate limit)

2. **Market Data Sync** (`sync_market_data`)
   - **Nguồn**: vnstock API
   - **Đích**: `market_data` table
   - **Tham số**: `days` (7 hoặc 30 ngày)
   - **Delay**: 2 giây giữa mỗi stock

3. **Financial Data Sync** (`sync_financial_data`)
   - **Nguồn**: vnstock API
   - **Đích**: `financial_data` table
   - **Delay**: 2 giây giữa mỗi stock

4. **Shares Outstanding Sync** (`sync_shares_outstanding`)
   - **Nguồn**: vnstock API
   - **Đích**: `shares_outstanding` table

5. **Base PE Update** (`sync_base_pe`)
   - **Nguồn**: Tính toán từ dữ liệu hiện có
   - **Đích**: `stocks` table

#### Quy trình sync:
```
Manual Trigger → Database Service → Sync Service → vnstock API
                                              ↓
                                        PostgreSQL
                                              ↓
                                    Redis (cache)
```

---

## Đề Xuất: Cập Nhật Theo Thời Gian Thực

### Giải Pháp 1: Server-Sent Events (SSE) - Khuyến nghị

#### Ưu điểm:
- ✅ Real-time updates
- ✅ Dễ implement với FastAPI
- ✅ Tự động reconnect khi mất kết nối
- ✅ Hỗ trợ tốt bởi browsers
- ✅ Ít overhead hơn WebSocket

#### Implementation:

**Backend (Gateway Service)**:
```python
@app.get("/api/stocks/stream")
async def stream_stocks():
    """SSE endpoint for real-time stock updates"""
    async def event_generator():
        while True:
            # Fetch latest data
            stocks_data = await get_latest_stocks()
            yield f"data: {json.dumps(stocks_data)}\n\n"
            await asyncio.sleep(5)  # Update every 5 seconds
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

**Frontend**:
```javascript
const eventSource = new EventSource('/api/stocks/stream');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateStocks(data.stocks);
};

eventSource.onerror = (error) => {
    console.error('SSE error:', error);
    // Auto-reconnect handled by browser
};
```

---

### Giải Pháp 2: WebSocket - Cho tương tác 2 chiều

#### Ưu điểm:
- ✅ Real-time bidirectional communication
- ✅ Có thể gửi commands từ client
- ✅ Hỗ trợ nhiều clients cùng lúc

#### Nhược điểm:
- ❌ Phức tạp hơn SSE
- ❌ Cần quản lý connections
- ❌ Overhead cao hơn

---

### Giải Pháp 3: Smart Polling với Adaptive Interval

#### Ưu điểm:
- ✅ Dễ implement (chỉ cần sửa frontend)
- ✅ Giảm bandwidth khi không có thay đổi
- ✅ Tăng tần suất khi có activity

#### Implementation:

```javascript
let pollInterval = 30000; // Start with 30s
let lastUpdateTime = Date.now();

async function loadStocks() {
    const response = await fetch('/api/stocks');
    const data = await response.json();
    
    // Check if data changed
    const dataHash = JSON.stringify(data.stocks.map(s => ({
        ticker: s.ticker,
        price: s.current_price,
        status: s.is_running
    })));
    
    if (dataHash !== lastDataHash) {
        // Data changed - increase polling frequency
        pollInterval = 5000; // Poll every 5s
        lastUpdateTime = Date.now();
        lastDataHash = dataHash;
    } else {
        // No changes - gradually increase interval
        const timeSinceUpdate = Date.now() - lastUpdateTime;
        if (timeSinceUpdate > 60000) {
            pollInterval = Math.min(pollInterval * 1.5, 30000); // Max 30s
        }
    }
    
    updateStocks(data.stocks);
    
    // Schedule next poll
    clearTimeout(pollTimeout);
    pollTimeout = setTimeout(loadStocks, pollInterval);
}
```

---

### Giải Pháp 4: Hybrid - SSE + Smart Polling

#### Kết hợp:
- **SSE** cho real-time updates khi có thay đổi
- **Polling** làm fallback khi SSE không available
- **Adaptive interval** để tối ưu bandwidth

---

## Khuyến Nghị Implementation

### Bước 1: Implement SSE cho Stock Updates (Ưu tiên cao)

1. **Backend**: Thêm SSE endpoint trong Gateway Service
2. **Frontend**: Thay thế `setInterval` bằng `EventSource`
3. **Fallback**: Giữ polling làm backup

### Bước 2: Implement Smart Polling cho Database Page

1. **Adaptive interval**: 5s khi có jobs running, 30s khi idle
2. **Event-driven**: Chỉ refresh khi cần thiết

### Bước 3: Thêm WebSocket cho Interactive Features (Tùy chọn)

1. Trigger jobs qua WebSocket
2. Real-time progress updates
3. Chat/notifications

---

## Lợi Ích Khi Cập Nhật Real-time

1. **User Experience**:
   - Thấy thay đổi ngay lập tức
   - Không cần refresh trang
   - Cảm giác responsive hơn

2. **Performance**:
   - Giảm unnecessary requests
   - Tối ưu bandwidth
   - Giảm server load

3. **Business Value**:
   - Dữ liệu luôn fresh
   - Quyết định nhanh hơn
   - Competitive advantage

---

## Timeline Đề Xuất

- **Week 1**: Implement SSE cho stock updates
- **Week 2**: Implement smart polling cho database page
- **Week 3**: Testing và optimization
- **Week 4**: Deploy và monitor

