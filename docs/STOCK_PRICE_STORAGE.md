# Giá Cổ Phiếu - Lưu Trữ và Cập Nhật

## 1. Nơi Lưu Trữ Giá Cổ Phiếu

### Database: Bảng `market_data`

Giá cổ phiếu được lưu trong bảng **`market_data`** của PostgreSQL với các cột chính:

```sql
CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id),
    trade_date DATE NOT NULL,
    open_price DECIMAL(18,2),
    high_price DECIMAL(18,2),
    low_price DECIMAL(18,2),
    close_price DECIMAL(18,2),        -- ⭐ Giá đóng cửa (giá hiện tại)
    adjusted_close DECIMAL(18,2),     -- Giá đóng cửa đã điều chỉnh
    volume BIGINT,
    data_source VARCHAR(255),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(stock_id, trade_date)
);
```

### Cấu Trúc Dữ Liệu:

- **`stock_id`**: Foreign key đến bảng `stocks`
- **`trade_date`**: Ngày giao dịch (DATE)
- **`close_price`**: ⭐ **Giá đóng cửa - đây là giá hiện tại được sử dụng**
- **`adjusted_close`**: Giá đóng cửa đã điều chỉnh (thường bằng `close_price`)
- **`open_price`, `high_price`, `low_price`**: Giá mở cửa, cao nhất, thấp nhất trong ngày
- **`volume`**: Khối lượng giao dịch
- **`data_source`**: Nguồn dữ liệu (ví dụ: 'vnstock_price_sync')

### Cách Lấy Giá Hiện Tại:

Giá hiện tại được lấy từ record mới nhất trong `market_data`:

```sql
SELECT close_price 
FROM market_data 
WHERE stock_id = :stock_id 
ORDER BY trade_date DESC 
LIMIT 1;
```

**Location**: `services/database/main.py` - endpoint `/api/database/stocks/{ticker}`

---

## 2. Các Đường Cập Nhật Giá Cổ Phiếu

### 2.1. Sync Giá Hiện Tại (Current Price Sync)

**Endpoint**: `POST /api/database/sync/current-price`

**Query Parameters**:
- `ticker` (optional): Mã cổ phiếu cụ thể, nếu không có thì sync tất cả

**Chức năng**:
- Lấy giá hiện tại từ **vnstock API**
- Cập nhật vào bảng `market_data` với `trade_date = hôm nay`
- Nếu đã có record cho hôm nay → **UPDATE**
- Nếu chưa có → **INSERT** record mới
- Cập nhật Redis cache

**Code Location**: `services/database/sync_service.py` - function `sync_current_price()`

**Luồng xử lý**:
```
1. Fetch giá từ vnstock API (price_board)
2. Kiểm tra record cho hôm nay trong market_data
3. Nếu có → UPDATE close_price
4. Nếu không → INSERT record mới
5. Update Redis cache
```

**Ví dụ**:
```bash
# Sync giá cho tất cả stocks
curl -X POST "http://localhost:8003/api/database/sync/current-price"

# Sync giá cho một ticker cụ thể
curl -X POST "http://localhost:8003/api/database/sync/current-price?ticker=FPT"
```

---

### 2.2. Sync Dữ Liệu Lịch Sử (Market Data Sync)

**Endpoint**: `POST /api/database/sync/market_data`

**Query Parameters**:
- `ticker` (optional): Mã cổ phiếu cụ thể
- `days` (required): Số ngày cần sync (1-365)

**Chức năng**:
- Lấy dữ liệu lịch sử từ **vnstock API** (historical_data)
- Sync nhiều ngày cùng lúc (7 hoặc 30 ngày)
- INSERT hoặc UPDATE records trong `market_data`
- Bao gồm: open, high, low, close, volume

**Code Location**: `services/database/sync_service.py` - function `sync_market_data()`

**Luồng xử lý**:
```
1. Tính start_date = today - days
2. Fetch historical_data từ vnstock
3. Loop qua từng ngày:
   - Kiểm tra record đã tồn tại?
   - Nếu có → UPDATE (upsert)
   - Nếu không → INSERT
```

**Ví dụ**:
```bash
# Sync 7 ngày gần nhất cho tất cả stocks
curl -X POST "http://localhost:8003/api/database/sync/market_data?days=7"

# Sync 30 ngày cho một ticker cụ thể
curl -X POST "http://localhost:8003/api/database/sync/market_data?ticker=FPT&days=30"
```

---

### 2.3. Scheduled Jobs (Tự Động)

Có 2 scheduled jobs để sync giá:

#### a) Current Price Sync
- **Job ID**: `current_price_sync`
- **Trigger**: Manual (qua UI)
- **Chức năng**: Sync giá hiện tại cho tất cả stocks
- **Endpoint**: `POST /api/database/sync/jobs/current_price_sync/trigger`

#### b) Market Data Sync (Recent)
- **Job ID**: `market_data_sync_recent`
- **Trigger**: Manual (qua UI)
- **Chức năng**: Sync 7 ngày gần nhất
- **Endpoint**: `POST /api/database/sync/jobs/market_data_sync_recent/trigger`

#### c) Market Data Sync (Full)
- **Job ID**: `market_data_sync_full`
- **Trigger**: Manual (qua UI)
- **Chức năng**: Sync 30 ngày gần nhất
- **Endpoint**: `POST /api/database/sync/jobs/market_data_sync_full/trigger`

**UI Location**: `http://localhost:8081/static/database.html` → Scheduled Jobs section

---

## 3. Luồng Dữ Liệu Tổng Quan

```
┌─────────────────┐
│   vnstock API   │
└────────┬────────┘
         │
         │ (Fetch price)
         ▼
┌─────────────────┐
│  Sync Service   │
│ (sync_current_  │
│   price)        │
└────────┬────────┘
         │
         │ (INSERT/UPDATE)
         ▼
┌─────────────────┐
│  PostgreSQL     │
│  market_data    │
│  (close_price)  │
└────────┬────────┘
         │
         │ (Query latest)
         ▼
┌─────────────────┐
│  Database API   │
│  /stocks/{ticker}│
└────────┬────────┘
         │
         │ (current_price)
         ▼
┌─────────────────┐
│  Stock Service  │
│  /api/stocks    │
└────────┬────────┘
         │
         │ (JSON response)
         ▼
┌─────────────────┐
│   Frontend      │
│   (Display)     │
└─────────────────┘
```

---

## 4. Cách Sử Dụng

### 4.1. Cập Nhật Giá Qua API

```bash
# 1. Sync giá hiện tại cho tất cả stocks
curl -X POST "http://localhost:8003/api/database/sync/current-price"

# 2. Sync giá cho một ticker cụ thể
curl -X POST "http://localhost:8003/api/database/sync/current-price?ticker=FPT"

# 3. Sync dữ liệu lịch sử 7 ngày
curl -X POST "http://localhost:8003/api/database/sync/market_data?days=7"

# 4. Sync dữ liệu lịch sử cho một ticker
curl -X POST "http://localhost:8003/api/database/sync/market_data?ticker=FPT&days=30"
```

### 4.2. Cập Nhật Giá Qua UI

1. Mở `http://localhost:8081/static/database.html`
2. Tìm section **"Scheduled Jobs"**
3. Tìm job **"Current Price Sync"**
4. Click **"🌐 All Stocks"** để sync tất cả
   hoặc nhập ticker và click **"▶️ Run"** để sync một ticker

### 4.3. Cập Nhật Giá Qua Gateway (Frontend)

```bash
# Qua Gateway (port 8081)
curl -X POST "http://localhost:8081/api/database/sync/current-price?ticker=FPT"

# Qua Gateway (port 8000)
curl -X POST "http://localhost:8000/api/database/sync/current-price?ticker=FPT"
```

---

## 5. Cache Layer

### Redis Cache

Giá cổ phiếu cũng được cache trong Redis để tăng tốc độ truy cập:

```python
redis_client.cache_market_data(ticker, {
    'current_price': current_price,
    'market_cap': market_cap,
    'pe_ratio': pe_ratio,
    'source': 'vnstock_price_sync',
    'updated_at': datetime.now().isoformat()
})
```

**Key Format**: `market_data:{ticker}`

---

## 6. Lưu Ý Quan Trọng

### Rate Limiting
- vnstock API có rate limit
- Delay 1 giây giữa mỗi stock khi sync
- Delay 2 giây cho market_data sync

### Data Consistency
- Giá hiện tại (`close_price`) được lấy từ record mới nhất (`trade_date DESC`)
- Nếu không có record cho hôm nay, sẽ lấy record gần nhất
- `adjusted_close` thường bằng `close_price` trong sync hiện tại

### Error Handling
- Nếu vnstock API fail → Log error và skip stock đó
- Nếu database error → Rollback transaction
- Redis cache failure không ảnh hưởng đến database

---

## 7. Monitoring

### Logs
- Sync logs: `logs/app/database.log`
- Success: `Updated price for {ticker} on {date}: {price}`
- Error: `Error in sync_current_price: {error}`

### Database Queries
```sql
-- Xem giá hiện tại của một stock
SELECT ticker, close_price, trade_date 
FROM market_data md
JOIN stocks s ON md.stock_id = s.id
WHERE s.ticker = 'FPT'
ORDER BY trade_date DESC
LIMIT 1;

-- Xem giá của tất cả stocks hôm nay
SELECT s.ticker, md.close_price, md.trade_date
FROM market_data md
JOIN stocks s ON md.stock_id = s.id
WHERE md.trade_date = CURRENT_DATE
ORDER BY s.ticker;
```

---

## 8. Tóm Tắt

| Thông Tin | Chi Tiết |
|-----------|----------|
| **Bảng lưu trữ** | `market_data` |
| **Cột giá** | `close_price` |
| **Nguồn dữ liệu** | vnstock API |
| **Sync hiện tại** | `POST /api/database/sync/current-price` |
| **Sync lịch sử** | `POST /api/database/sync/market_data?days=X` |
| **UI Trigger** | Database page → Scheduled Jobs |
| **Cache** | Redis (`market_data:{ticker}`) |
| **Update frequency** | Manual (qua UI hoặc API) |

