# Data Sync Strategy

**Chiến lược đồng bộ dữ liệu từ vnstock API - Đảm bảo hiệu năng và real-time data**

## 🎯 Overview

Dựa trên kiến trúc Database Service, đây là chiến lược sync data để:
- ✅ Lấy thông tin thị trường **theo thời gian thực** (real-time)
- ✅ Đảm bảo **hiệu năng** của API vnstock
- ✅ **Tối ưu** sync frequency cho từng loại data

## 🏗️ Service Responsibilities

### Database Service (Port 8003) - **Chịu Trách Nhiệm Chính**

**Database Service** là service **duy nhất** chịu trách nhiệm:
1. ✅ Sync data từ vnstock API
2. ✅ Lưu trữ vào PostgreSQL
3. ✅ Quản lý cache với Redis
4. ✅ Scheduled sync jobs

**Lý do:**
- **Single Responsibility**: Một service quản lý tất cả data operations
- **Centralized Control**: Dễ quản lý rate limiting và API calls
- **Data Consistency**: Đảm bảo data consistency trong database
- **Performance**: Tối ưu caching và sync strategy

### Other Services - **Chỉ Query, Không Sync**

- **Stock Service**: Query từ Database Service, không gọi vnstock trực tiếp
- **DCF Service**: Query từ Database Service, không gọi vnstock trực tiếp
- **Gateway Service**: Route requests đến các services

## 📊 Data Types và Sync Frequency

### 1. Market Data (Real-time) 📈

**Loại data:**
- Current price
- Volume
- Market cap
- PE ratio, PB ratio, PS ratio
- Price changes

**Sync Strategy:**
```
Frequency: Mỗi 15 phút (trading hours: 9:00 - 15:00)
Cache TTL: 5 phút (Redis)
Priority: HIGH (real-time data)
```

**Implementation:**
```python
# Scheduled job trong Database Service
@cron.schedule("*/15 * * * *")  # Mỗi 15 phút
async def sync_market_data():
    """
    Sync market data cho tất cả VN30 stocks
    - Chỉ sync trong trading hours (9:00 - 15:00)
    - Batch sync để giảm API calls
    - Update cache sau mỗi sync
    """
    if not is_trading_hours():
        return
    
    # Batch sync 30 stocks cùng lúc
    tickers = get_vn30_tickers()
    results = await asyncio.gather(*[
        sync_single_market_data(ticker) 
        for ticker in tickers
    ])
    
    # Update cache
    await update_market_cache(results)
```

**Cache Strategy:**
```python
# Redis cache keys
f"stock:{ticker}:market:latest"  # TTL: 5 minutes
f"stock:{ticker}:price"          # TTL: 5 minutes
f"stock:{ticker}:market_cap"     # TTL: 5 minutes

# Cache invalidation
- On sync: Update cache
- On query: Check cache first, fallback to DB
```

### 2. Financial Data (Quarterly) 📊

**Loại data:**
- Operating Cash Flow (OCF)
- Capital Expenditures (CapEx)
- Revenue
- Net Profit
- EPS
- Financial statements

**Sync Strategy:**
```
Frequency: Hàng ngày lúc 2:00 AM (sau khi market close)
Cache TTL: 6 giờ (Redis)
Priority: MEDIUM (quarterly data không thay đổi thường xuyên)
```

**Implementation:**
```python
# Scheduled job trong Database Service
@cron.schedule("0 2 * * *")  # Mỗi ngày lúc 2:00 AM
async def sync_financial_data():
    """
    Sync financial data cho tất cả VN30 stocks
    - Chỉ sync nếu có data mới (check last sync date)
    - Incremental sync (chỉ sync quarters mới)
    - Update TTM calculations
    """
    tickers = get_vn30_tickers()
    
    for ticker in tickers:
        # Check last sync date
        last_sync = await get_last_financial_sync(ticker)
        
        # Only sync if new quarter data available
        if needs_sync(last_sync):
            await sync_single_financial_data(ticker)
            
            # Update TTM calculations
            await update_ttm_calculations(ticker)
```

**Cache Strategy:**
```python
# Redis cache keys
f"stock:{ticker}:financial:ttm"     # TTL: 6 hours
f"stock:{ticker}:fcf"                 # TTL: 6 hours
f"stock:{ticker}:financial:latest"   # TTL: 6 hours

# Cache invalidation
- On sync: Invalidate và update cache
- TTM cache: Update khi có quarter mới
```

### 3. Shares Outstanding 📦

**Loại data:**
- Shares outstanding
- Par value
- Calculation method

**Sync Strategy:**
```
Frequency: Hàng tuần (Chủ nhật lúc 3:00 AM)
Cache TTL: 1 ngày (Redis)
Priority: LOW (shares không thay đổi thường xuyên)
```

**Implementation:**
```python
# Scheduled job trong Database Service
@cron.schedule("0 3 * * 0")  # Chủ nhật lúc 3:00 AM
async def sync_shares_outstanding():
    """
    Sync shares outstanding cho tất cả VN30 stocks
    - Shares thường không thay đổi thường xuyên
    - Chỉ sync nếu có thay đổi (check last sync)
    """
    tickers = get_vn30_tickers()
    
    for ticker in tickers:
        # Check if shares changed
        if shares_changed(ticker):
            await sync_single_shares(ticker)
```

### 4. Growth Metrics 📈

**Loại data:**
- Revenue growth
- Profit growth
- Weighted average growth

**Sync Strategy:**
```
Frequency: Calculated on-demand từ Financial Data
Cache TTL: 6 giờ (Redis)
Priority: MEDIUM (calculated, không cần sync từ API)
```

**Implementation:**
```python
# Calculated từ Financial Data, không sync từ API
async def calculate_growth_metrics(ticker: str):
    """
    Tính toán growth metrics từ financial data
    - Không cần sync từ API
    - Tính toán từ historical financial data
    - Cache kết quả
    """
    # Get financial data từ DB
    financial_data = await get_financial_data(ticker)
    
    # Calculate growth
    growth = calculate_weighted_growth(financial_data)
    
    # Save và cache
    await save_growth_metrics(ticker, growth)
    await cache_growth_metrics(ticker, growth)
```

## 🚀 Performance Optimization

### 1. Rate Limiting Strategy

```python
# Database Service quản lý rate limiting
class VnstockRateLimiter:
    """
    Rate limiter để tránh overload vnstock API
    - Max 10 requests/second
    - Batch requests khi có thể
    - Exponential backoff on errors
    """
    MAX_REQUESTS_PER_SECOND = 10
    BATCH_SIZE = 5
    
    async def sync_with_rate_limit(self, tickers: List[str]):
        """
        Sync với rate limiting
        - Batch requests
        - Delay giữa các batches
        """
        batches = [tickers[i:i+self.BATCH_SIZE] 
                  for i in range(0, len(tickers), self.BATCH_SIZE)]
        
        for batch in batches:
            await asyncio.gather(*[
                self.sync_single(ticker) for ticker in batch
            ])
            
            # Rate limit: delay giữa batches
            await asyncio.sleep(1.0 / self.MAX_REQUESTS_PER_SECOND)
```

### 2. Caching Strategy

```python
# Multi-layer caching
class DataCache:
    """
    3-layer caching strategy:
    1. Redis (hot cache) - 5 phút cho market data
    2. PostgreSQL (warm cache) - persistent storage
    3. vnstock API (cold cache) - fallback
    """
    
    async def get_market_data(self, ticker: str):
        # Layer 1: Redis cache
        cached = await redis.get(f"stock:{ticker}:market:latest")
        if cached and not expired(cached, ttl=300):  # 5 minutes
            return cached
        
        # Layer 2: PostgreSQL
        db_data = await db.get_latest_market_data(ticker)
        if db_data and not expired(db_data, ttl=900):  # 15 minutes
            await redis.set(f"stock:{ticker}:market:latest", db_data, ttl=300)
            return db_data
        
        # Layer 3: vnstock API (only if cache expired)
        api_data = await vnstock.get_market_data(ticker)
        await db.save_market_data(ticker, api_data)
        await redis.set(f"stock:{ticker}:market:latest", api_data, ttl=300)
        return api_data
```

### 3. Incremental Sync

```python
# Chỉ sync data mới, không sync lại toàn bộ
async def sync_financial_data_incremental(ticker: str):
    """
    Incremental sync - chỉ sync quarters mới
    """
    # Get last synced quarter
    last_sync = await db.get_last_financial_sync(ticker)
    
    # Get latest quarter from API
    latest_quarter = await vnstock.get_latest_quarter(ticker)
    
    # Chỉ sync nếu có quarter mới
    if latest_quarter > last_sync:
        new_data = await vnstock.get_financial_data(ticker, since=last_sync)
        await db.save_financial_data(ticker, new_data)
        
        # Update TTM
        await update_ttm(ticker)
```

## 📋 Sync Schedule Summary

| Data Type | Frequency | Time | Cache TTL | Priority |
|-----------|-----------|------|-----------|----------|
| **Market Data** | 15 phút | 9:00-15:00 | 5 phút | HIGH |
| **Financial Data** | Hàng ngày | 2:00 AM | 6 giờ | MEDIUM |
| **Shares Outstanding** | Hàng tuần | Chủ nhật 3:00 AM | 1 ngày | LOW |
| **Growth Metrics** | On-demand | Calculated | 6 giờ | MEDIUM |

## 🔄 Data Flow

```
┌─────────────────┐
│  vnstock API    │
└────────┬────────┘
         │
         │ Scheduled Sync Jobs
         ▼
┌─────────────────┐
│ Database Service│ ← Chịu trách nhiệm sync
│   (Port 8003)   │
└────────┬────────┘
         │
         ├──→ PostgreSQL (persistent)
         │
         └──→ Redis (cache)
              │
              ▼
┌─────────────────┐
│  Stock Service  │ ← Query từ Database Service
│   (Port 8002)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  DCF Service     │ ← Query từ Database Service
│   (Port 8001)   │
└─────────────────┘
```

## 🎯 Key Points

### ✅ Database Service Responsibilities:
1. **Sync từ vnstock API** - Scheduled jobs
2. **Lưu vào PostgreSQL** - Persistent storage
3. **Cache với Redis** - Performance optimization
4. **Rate limiting** - Bảo vệ vnstock API
5. **Incremental sync** - Chỉ sync data mới

### ✅ Other Services:
- **Chỉ query** từ Database Service
- **Không gọi** vnstock API trực tiếp
- **Sử dụng cache** từ Redis

### ✅ Performance:
- **Real-time data**: Cache 5 phút, sync mỗi 15 phút
- **Quarterly data**: Cache 6 giờ, sync hàng ngày
- **Rate limiting**: Max 10 requests/second
- **Batch sync**: Giảm số lượng API calls

## 📖 Related Documents

- [Database Service Design](database-service.md) - Service architecture
- [Database Design](database-design.md) - Schema design
- [Microservices Architecture](../microservices.md) - Overall architecture

---

**Tóm lại**: **Database Service** là service duy nhất chịu trách nhiệm sync data từ vnstock API, với chiến lược sync khác nhau cho từng loại data để đảm bảo hiệu năng và real-time data.

