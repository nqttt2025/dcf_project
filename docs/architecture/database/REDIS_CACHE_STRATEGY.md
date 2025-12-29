# Redis Cache Strategy

**Chiến lược caching với Redis cho DCF Project**

## 📊 Redis Keys Hiện Tại

### 1. Analysis Status Tracking

**Key Pattern:** `analysis:{ticker}`

**Ví dụ:**
- `analysis:FPT`
- `analysis:VNM`
- `analysis:BID`

**Data Structure:**
```json
{
  "ticker": "FPT",
  "status": "running|processing|completed|failed",
  "progress": "Fetching financial data...",
  "progress_percent": 50.0,
  "started_at": "2025-01-01T10:00:00",
  "updated_at": "2025-01-01T10:05:00",
  "completed_at": "2025-01-01T10:10:00",  // optional
  "result": {...}  // optional, khi completed
}
```

**TTL:** 3600 giây (1 giờ)

**Usage:**
- Track trạng thái phân tích DCF đang chạy
- Hiển thị progress bar trên frontend
- Lưu kết quả tạm thời sau khi hoàn thành

### 2. Running Analyses Set

**Key:** `running_analyses`

**Type:** Redis Set

**Members:** Danh sách các ticker đang chạy analysis

**Ví dụ:**
```
running_analyses = {"FPT", "VNM", "BID"}
```

**Usage:**
- Quick lookup để check ticker nào đang chạy
- Sync giữa các services

## 🔄 Data Flow Strategy (Database → Redis → File)

### Priority Order

```
1. Database (PostgreSQL) - Primary source
   ↓ (if not found)
2. Redis Cache - Fast cache layer
   ↓ (if not found)
3. File Cache (JSON) - Fallback
   ↓ (if not found)
4. vnstock API - Fetch fresh data
```

### Proposed Redis Keys for Data Caching

#### 1. Stock Financial Data

**Key Pattern:** `stock:{ticker}:financial:ttm`

**TTL:** 21600 giây (6 giờ)

**Data:**
```json
{
  "ticker": "FPT",
  "ttm_ocf": 1000000000,
  "ttm_capex": 500000000,
  "ttm_fcf": 500000000,
  "latest_quarter_date": "2024-12-31",
  "cached_at": "2025-01-01T10:00:00"
}
```

#### 2. Market Data

**Key Pattern:** `stock:{ticker}:market:latest`

**TTL:** 300 giây (5 phút)

**Data:**
```json
{
  "ticker": "FPT",
  "current_price": 150000,
  "market_cap": 50000000000,
  "pe_ratio": 15.5,
  "pb_ratio": 3.2,
  "volume": 1000000,
  "trade_date": "2025-01-01",
  "cached_at": "2025-01-01T10:00:00"
}
```

#### 3. Shares Outstanding

**Key Pattern:** `stock:{ticker}:shares:latest`

**TTL:** 86400 giây (1 ngày)

**Data:**
```json
{
  "ticker": "FPT",
  "shares_outstanding": 1000000000,
  "par_value": 10000,
  "calculation_method": "from_balance_sheet",
  "period_date": "2024-12-31",
  "cached_at": "2025-01-01T10:00:00"
}
```

#### 4. Stock Info

**Key Pattern:** `stock:{ticker}:info`

**TTL:** 3600 giây (1 giờ)

**Data:**
```json
{
  "ticker": "FPT",
  "name": "FPT Corporation",
  "sector": "Technology",
  "industry": "Software",
  "exchange": "HOSE",
  "is_vn30": true,
  "cached_at": "2025-01-01T10:00:00"
}
```

#### 5. DCF Config

**Key Pattern:** `stock:{ticker}:config`

**TTL:** 86400 giây (1 ngày)

**Data:**
```json
{
  "ticker": "FPT",
  "forecast_years": 5,
  "discount_rate": 10.0,
  "perpetual_growth_rate": 3.0,
  "base_pe": 15.0,
  "growth_multiplier": 1.5,
  "cached_at": "2025-01-01T10:00:00"
}
```

#### 6. Latest DCF Result

**Key Pattern:** `stock:{ticker}:result:latest`

**TTL:** 3600 giây (1 giờ)

**Data:**
```json
{
  "ticker": "FPT",
  "analysis_date": "2025-01-01T10:00:00",
  "fair_value_per_share": 200000,
  "market_price": 150000,
  "margin_of_safety": 25.0,
  "recommendation": "BUY",
  "cached_at": "2025-01-01T10:00:00"
}
```

## 📋 Current Redis Keys Summary

### Currently Used Keys

| Key Pattern | Type | TTL | Purpose |
|------------|------|-----|---------|
| `analysis:{ticker}` | String (JSON) | 3600s | Analysis status tracking |
| `running_analyses` | Set | - | List of running analyses |

### Proposed Keys (Not Yet Implemented)

| Key Pattern | Type | TTL | Purpose |
|------------|------|-----|---------|
| `stock:{ticker}:financial:ttm` | String (JSON) | 21600s | Financial TTM data |
| `stock:{ticker}:market:latest` | String (JSON) | 300s | Latest market price |
| `stock:{ticker}:shares:latest` | String (JSON) | 86400s | Shares outstanding |
| `stock:{ticker}:info` | String (JSON) | 3600s | Stock basic info |
| `stock:{ticker}:config` | String (JSON) | 86400s | DCF configuration |
| `stock:{ticker}:result:latest` | String (JSON) | 3600s | Latest DCF result |

## 🔧 Implementation Strategy

### Step 1: Extend RedisClient

Thêm methods để cache data:

```python
# Cache financial data
redis_client.cache_financial_ttm(ticker, data, ttl=21600)

# Cache market data
redis_client.cache_market_data(ticker, data, ttl=300)

# Cache shares outstanding
redis_client.cache_shares(ticker, data, ttl=86400)

# Get cached data
financial_data = redis_client.get_financial_ttm(ticker)
market_data = redis_client.get_market_data(ticker)
```

### Step 2: Data Fetching Priority

```python
def get_financial_data_ttm(ticker):
    # 1. Try Database first
    if db_connected:
        data = db.get_financial_ttm(ticker)
        if data:
            # Cache to Redis
            redis_client.cache_financial_ttm(ticker, data)
            return data
    
    # 2. Try Redis
    data = redis_client.get_financial_ttm(ticker)
    if data:
        return data
    
    # 3. Try File cache
    data = cache_manager.get_with_timestamp(ticker, "financial_ttm")
    if data:
        # Cache to Redis
        redis_client.cache_financial_ttm(ticker, data)
        return data
    
    # 4. Fetch from vnstock API
    data = fetch_from_vnstock(ticker)
    if data:
        # Save to Database
        db.save_financial_ttm(ticker, data)
        # Cache to Redis
        redis_client.cache_financial_ttm(ticker, data)
        # Save to file cache
        cache_manager.set_with_timestamp(ticker, "financial_ttm", data)
        return data
    
    return None
```

### Step 3: Cache Invalidation

- **On Database Update:** Invalidate Redis cache
- **On Data Sync:** Invalidate related Redis keys
- **On Config Change:** Invalidate config cache

## 📊 Cache Hit Rate Monitoring

Track cache performance:

```python
# Metrics keys
cache:hits:financial_ttm
cache:misses:financial_ttm
cache:hits:market_data
cache:misses:market_data
```

## 🚀 Next Steps

1. ✅ Document current Redis usage
2. ⏳ Extend RedisClient với data caching methods
3. ⏳ Implement Database → Redis → File priority
4. ⏳ Add cache invalidation logic
5. ⏳ Add cache hit rate monitoring

---

**Related Documents:**
- [Database Integration](DATABASE_INTEGRATION.md) - Database integration guide
- [Data Sync Strategy](data-sync-strategy.md) - Data synchronization strategy

