# Database Design for VN30 Stocks

**Database Architecture cho Microservices - VN30 Stock Data**

## 🎯 Mục Tiêu

Xây dựng database để lưu trữ thông tin của 30 mã cổ phiếu VN30 phục vụ việc tính toán DCF, tuân thủ mô hình Microservices.

## 🏗️ Kiến Trúc Database Service

### Architecture Overview

```
┌─────────────┐
│   Gateway   │
└──────┬──────┘
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
┌──────────┐    ┌──────────┐    ┌──────────┐
│   DCF    │    │  Stock   │    │Database  │
│ Service  │    │ Service  │    │ Service  │
│ :8001    │    │ :8002    │    │ :8003    │
└────┬─────┘    └────┬─────┘    └────┬─────┘
     │               │               │
     └───────────────┴───────────────┘
                     │
                     ▼
            ┌─────────────────┐
            │   PostgreSQL    │
            │   Database      │
            │   :5432         │
            └─────────────────┘
                     │
                     ▼
            ┌─────────────────┐
            │     Redis       │
            │   Cache Layer   │
            │   :6379         │
            └─────────────────┘
```

### Database Service

**New Service: Database Service** (`services/database/`)
- **Role**: Quản lý database operations cho stock data
- **Technology**: FastAPI + SQLAlchemy + PostgreSQL
- **Port**: 8003
- **Responsibilities**:
  - CRUD operations cho stock data
  - Data synchronization với vnstock
  - Query optimization
  - Data validation

## 📊 Database Schema Design

### Technology Choice: PostgreSQL

**Lý do chọn PostgreSQL:**
- ✅ ACID compliance
- ✅ Rich data types (JSONB, arrays)
- ✅ Excellent performance
- ✅ Strong consistency
- ✅ Full-text search
- ✅ Extensions (PostGIS, etc.)
- ✅ Phù hợp với microservices

### Schema Tables

#### 1. `stocks` - Thông tin cơ bản cổ phiếu

```sql
CREATE TABLE stocks (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    exchange VARCHAR(20) DEFAULT 'HOSE',
    is_vn30 BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_ticker (ticker),
    INDEX idx_vn30 (is_vn30),
    INDEX idx_active (is_active)
);
```

**Fields:**
- `ticker`: Mã cổ phiếu (FPT, VNM, VCB, etc.)
- `name`: Tên công ty
- `sector`: Ngành (Technology, Banking, Consumer, etc.)
- `industry`: Lĩnh vực cụ thể
- `exchange`: Sàn giao dịch (HOSE, HNX, UPCOM)
- `is_vn30`: Có trong rổ VN30 không
- `is_active`: Còn giao dịch không

#### 2. `financial_data` - Dữ liệu tài chính theo quý

```sql
CREATE TABLE financial_data (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    period_type VARCHAR(20) NOT NULL, -- 'quarter', 'year'
    period VARCHAR(20) NOT NULL, -- '2024Q1', '2024', etc.
    period_date DATE NOT NULL,
    
    -- Balance Sheet
    total_assets BIGINT,
    total_liabilities BIGINT,
    total_equity BIGINT,
    common_shares_capital BIGINT, -- VND
    paid_in_capital BIGINT, -- VND
    
    -- Income Statement
    revenue BIGINT, -- VND
    net_profit BIGINT, -- VND
    operating_profit BIGINT, -- VND
    ebit BIGINT, -- VND
    ebitda BIGINT, -- VND
    
    -- Cash Flow Statement
    operating_cash_flow BIGINT, -- VND
    investing_cash_flow BIGINT, -- VND
    capital_expenditures BIGINT, -- VND (CapEx)
    free_cash_flow BIGINT, -- VND (FCF = OCF - CapEx)
    
    -- Ratios
    eps DECIMAL(15, 2), -- Earnings per Share
    roe DECIMAL(10, 4), -- Return on Equity (%)
    roa DECIMAL(10, 4), -- Return on Assets (%)
    
    -- Metadata
    data_source VARCHAR(50) DEFAULT 'vnstock',
    data_quality VARCHAR(20) DEFAULT 'good', -- 'good', 'warning', 'error'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_id, period_type, period),
    INDEX idx_stock_period (stock_id, period_date),
    INDEX idx_period_type (period_type, period_date)
);
```

**Fields:**
- `period_type`: Loại kỳ ('quarter', 'year')
- `period`: Kỳ báo cáo ('2024Q1', '2024')
- `period_date`: Ngày kết thúc kỳ
- Financial metrics từ Balance Sheet, Income Statement, Cash Flow
- `free_cash_flow`: Tính từ OCF - CapEx
- `data_quality`: Chất lượng dữ liệu

#### 3. `shares_outstanding` - Số cổ phiếu lưu hành

```sql
CREATE TABLE shares_outstanding (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    period_date DATE NOT NULL,
    shares_outstanding BIGINT NOT NULL, -- Số cổ phiếu
    par_value DECIMAL(15, 2) DEFAULT 10000, -- Mệnh giá (VND)
    calculation_method VARCHAR(50), -- 'charter_capital', 'paid_in_capital', 'direct'
    source_column VARCHAR(100), -- Column name từ vnstock
    data_source VARCHAR(50) DEFAULT 'vnstock',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_id, period_date),
    INDEX idx_stock_date (stock_id, period_date)
);
```

**Fields:**
- `shares_outstanding`: Số cổ phiếu lưu hành
- `par_value`: Mệnh giá (thường 10,000 VND)
- `calculation_method`: Cách tính (từ charter capital, paid-in capital, hoặc direct)
- `source_column`: Column từ vnstock được sử dụng

#### 4. `market_data` - Dữ liệu thị trường

```sql
CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    trade_date DATE NOT NULL,
    
    -- Price Data
    open_price DECIMAL(15, 2),
    high_price DECIMAL(15, 2),
    low_price DECIMAL(15, 2),
    close_price DECIMAL(15, 2),
    adjusted_close DECIMAL(15, 2),
    
    -- Volume & Market Cap
    volume BIGINT,
    market_cap BIGINT, -- VND
    
    -- Ratios
    pe_ratio DECIMAL(10, 4),
    pb_ratio DECIMAL(10, 4), -- Price to Book
    ps_ratio DECIMAL(10, 4), -- Price to Sales
    
    -- Metadata
    data_source VARCHAR(50) DEFAULT 'vnstock',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_id, trade_date),
    INDEX idx_stock_date (stock_id, trade_date),
    INDEX idx_trade_date (trade_date)
);
```

**Fields:**
- Price data: open, high, low, close
- Volume và market cap
- Ratios: PE, PB, PS

#### 5. `growth_metrics` - Chỉ số tăng trưởng

```sql
CREATE TABLE growth_metrics (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    period_date DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL, -- 'quarter', 'year'
    
    -- Growth Rates (%)
    revenue_growth_yoy DECIMAL(10, 4), -- Revenue Growth YoY
    net_profit_growth_yoy DECIMAL(10, 4), -- Net Profit Growth YoY
    operating_profit_growth_yoy DECIMAL(10, 4),
    fcf_growth_yoy DECIMAL(10, 4), -- FCF Growth YoY
    
    -- Weighted Average Growth (for DCF)
    weighted_growth_rate DECIMAL(10, 4), -- Weighted average của các metrics
    
    -- Historical Average
    historical_avg_growth DECIMAL(10, 4), -- Trung bình lịch sử
    
    -- Metadata
    calculation_method VARCHAR(100),
    data_points_count INTEGER, -- Số điểm dữ liệu sử dụng
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_id, period_date, period_type),
    INDEX idx_stock_period (stock_id, period_date)
);
```

**Fields:**
- Growth rates: Revenue, Net Profit, Operating Profit, FCF
- `weighted_growth_rate`: Weighted average cho DCF (50% Net Profit, 30% Revenue, 20% Historical)
- `historical_avg_growth`: Trung bình lịch sử

#### 6. `dcf_configs` - Cấu hình DCF cho từng mã

```sql
CREATE TABLE dcf_configs (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    
    -- DCF Parameters
    forecast_years INTEGER DEFAULT 5, -- yr
    discount_rate DECIMAL(5, 2) DEFAULT 10.00, -- dr (%)
    perpetual_growth_rate DECIMAL(5, 2) DEFAULT 2.50, -- pr (%)
    
    -- Graham Parameters
    base_pe DECIMAL(5, 2) DEFAULT 8.50,
    growth_multiplier DECIMAL(5, 2) DEFAULT 2.00,
    
    -- Metadata
    is_default BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_id),
    INDEX idx_stock (stock_id)
);
```

**Fields:**
- DCF parameters: forecast_years, discount_rate, perpetual_growth_rate
- Graham parameters: base_pe, growth_multiplier
- `is_default`: Config mặc định

#### 7. `dcf_results` - Kết quả phân tích DCF

```sql
CREATE TABLE dcf_results (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    analysis_date TIMESTAMP NOT NULL,
    
    -- Input Data
    fcf_ttm BIGINT, -- Free Cash Flow TTM
    shares_outstanding BIGINT,
    growth_rate DECIMAL(10, 4), -- Growth rate used
    
    -- DCF Calculation
    dcf_value BIGINT, -- Total DCF value (VND)
    fair_value_per_share DECIMAL(15, 2), -- Fair value per share
    terminal_value BIGINT, -- Terminal value
    
    -- Graham Calculation
    graham_value_per_share DECIMAL(15, 2),
    eps DECIMAL(15, 2),
    
    -- Market Comparison
    market_price DECIMAL(15, 2),
    margin_of_safety DECIMAL(10, 4), -- %
    recommendation VARCHAR(20), -- 'buy', 'hold', 'sell'
    
    -- Forecast Data (JSONB)
    forecast_data JSONB, -- {year1: value, year2: value, ...}
    present_values JSONB, -- {year1: pv, year2: pv, ...}
    
    -- Metadata
    config_id INTEGER REFERENCES dcf_configs(id),
    calculation_version VARCHAR(20) DEFAULT '1.0',
    status VARCHAR(20) DEFAULT 'completed', -- 'running', 'completed', 'failed'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_stock_date (stock_id, analysis_date),
    INDEX idx_analysis_date (analysis_date),
    INDEX idx_status (status)
);
```

**Fields:**
- Input data: FCF TTM, shares, growth rate
- DCF results: DCF value, fair value per share, terminal value
- Graham results: Graham value per share
- Market comparison: market price, margin of safety, recommendation
- `forecast_data`: JSONB chứa forecast cho từng năm
- `present_values`: JSONB chứa present values

#### 8. `data_sync_logs` - Log đồng bộ dữ liệu

```sql
CREATE TABLE data_sync_logs (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id) ON DELETE SET NULL,
    sync_type VARCHAR(50) NOT NULL, -- 'financial', 'market', 'shares', 'all'
    sync_status VARCHAR(20) NOT NULL, -- 'success', 'failed', 'partial'
    records_updated INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    error_message TEXT,
    sync_duration_ms INTEGER,
    data_source VARCHAR(50) DEFAULT 'vnstock',
    sync_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_stock_sync (stock_id, sync_date),
    INDEX idx_sync_status (sync_status),
    INDEX idx_sync_date (sync_date)
);
```

**Fields:**
- `sync_type`: Loại sync (financial, market, shares, all)
- `sync_status`: Trạng thái sync
- `records_updated/inserted`: Số records được cập nhật/thêm
- `sync_duration_ms`: Thời gian sync (milliseconds)

## 🔄 Data Flow

### 1. Data Synchronization Flow

```
vnstock API
    │
    ▼
Data Sync Service (cron job)
    │
    ├──→ financial_data (quarterly)
    ├──→ market_data (daily)
    ├──→ shares_outstanding (quarterly)
    └──→ growth_metrics (calculated)
    │
    ▼
Redis Cache (hot data)
    │
    ▼
Database Service API
    │
    ▼
DCF Service / Stock Service
```

### 2. DCF Calculation Flow

```
DCF Service
    │
    ├──→ Query financial_data (FCF TTM)
    ├──→ Query shares_outstanding (latest)
    ├──→ Query growth_metrics (weighted average)
    ├──→ Query market_data (current price)
    └──→ Query dcf_configs (parameters)
    │
    ▼
Calculate DCF
    │
    ▼
Save to dcf_results
    │
    ▼
Update Redis cache
```

## 🛠️ Database Service API

### Endpoints

#### Stocks
```http
GET    /api/stocks                    # List all stocks
GET    /api/stocks/{ticker}           # Get stock detail
GET    /api/stocks/vn30               # Get all VN30 stocks
POST   /api/stocks                    # Create stock (admin)
PUT    /api/stocks/{ticker}           # Update stock (admin)
```

#### Financial Data
```http
GET    /api/stocks/{ticker}/financial # Get financial data
GET    /api/stocks/{ticker}/financial/latest # Get latest quarter
GET    /api/stocks/{ticker}/financial/ttm    # Get TTM data
POST   /api/stocks/{ticker}/financial # Sync financial data
```

#### Market Data
```http
GET    /api/stocks/{ticker}/market    # Get market data
GET    /api/stocks/{ticker}/market/latest # Get latest price
POST   /api/stocks/{ticker}/market    # Sync market data
```

#### Shares Outstanding
```http
GET    /api/stocks/{ticker}/shares    # Get shares outstanding
GET    /api/stocks/{ticker}/shares/latest # Get latest shares
POST   /api/stocks/{ticker}/shares    # Sync shares
```

#### DCF Configs
```http
GET    /api/stocks/{ticker}/config    # Get DCF config
PUT    /api/stocks/{ticker}/config    # Update DCF config
```

#### DCF Results
```http
GET    /api/stocks/{ticker}/results  # Get DCF results
GET    /api/stocks/{ticker}/results/latest # Get latest result
POST   /api/stocks/{ticker}/results   # Save DCF result
```

#### Data Sync
```http
POST   /api/sync/{ticker}             # Sync all data for ticker
POST   /api/sync/vn30                 # Sync all VN30 stocks
GET    /api/sync/logs                 # Get sync logs
```

## 💾 Caching Strategy

### Redis Cache Structure

```
# Stock basic info (TTL: 1 hour)
stock:{ticker}:info -> JSON

# Financial data TTM (TTL: 6 hours)
stock:{ticker}:financial:ttm -> JSON

# Latest market price (TTL: 5 minutes)
stock:{ticker}:market:latest -> JSON

# Shares outstanding (TTL: 1 day)
stock:{ticker}:shares:latest -> JSON

# DCF config (TTL: 1 day)
stock:{ticker}:config -> JSON

# Latest DCF result (TTL: 1 hour)
stock:{ticker}:result:latest -> JSON

# Growth metrics (TTL: 6 hours)
stock:{ticker}:growth:latest -> JSON
```

### Cache Invalidation

- **On data sync**: Invalidate related cache keys
- **On config update**: Invalidate config cache
- **On new DCF result**: Invalidate result cache

## 🔧 Implementation Plan

### Phase 1: Database Setup
1. Setup PostgreSQL container
2. Create schema và migrations
3. Seed VN30 stocks data
4. Create indexes

### Phase 2: Database Service
1. Create Database Service (`services/database/`)
2. Implement CRUD operations
3. Implement data sync với vnstock
4. Add caching layer với Redis

### Phase 3: Integration
1. Update Stock Service để dùng Database Service
2. Update DCF Service để query từ database
3. Migrate từ file-based sang database
4. Update Gateway routes

### Phase 4: Optimization
1. Query optimization
2. Index tuning
3. Cache strategy refinement
4. Monitoring và logging

## 📊 Database Size Estimation

### VN30 Stocks (30 stocks)

**Financial Data:**
- 30 stocks × 4 quarters/year × 5 years = 600 records
- ~2KB per record = ~1.2MB

**Market Data:**
- 30 stocks × 250 trading days/year × 2 years = 15,000 records
- ~500 bytes per record = ~7.5MB

**Total Estimated Size:**
- Initial: ~10-15MB
- After 1 year: ~50-100MB
- After 5 years: ~200-500MB

## 🔐 Security Considerations

1. **Database Access**: Chỉ Database Service có quyền write
2. **API Authentication**: JWT tokens cho admin endpoints
3. **Data Validation**: Validate tất cả inputs
4. **SQL Injection**: Sử dụng parameterized queries
5. **Backup Strategy**: Daily backups
6. **Connection Pooling**: Limit connections

## 📈 Monitoring

1. **Query Performance**: Log slow queries (>100ms)
2. **Cache Hit Rate**: Monitor Redis cache performance
3. **Sync Status**: Monitor data sync success rate
4. **Database Size**: Monitor growth
5. **Connection Pool**: Monitor active connections

## 📋 Review và Improvements

### Review Summary

Database design đã được review chi tiết dựa trên codebase hiện tại. Xem chi tiết tại [Database Review](database-review.md).

#### ✅ Keep As Is
- `stocks` table structure
- `financial_data` core fields (OCF, CapEx, FCF, revenue, net_profit, eps)
- `shares_outstanding` table
- `dcf_configs` table
- `dcf_results` core structure
- `data_sync_logs` table

#### 🔧 Needs Improvement

**Priority 1 (Must Have):**
1. ✅ Add `market_cap` to `financial_data`
2. ✅ Add performance indexes
3. ✅ Add data validation constraints
4. ✅ Add `stock_metadata` table

**Priority 2 (Should Have):**
1. ✅ Add views for common queries
2. ✅ Add advanced analysis fields to `dcf_results`
3. ✅ Add `input_data_hash` tracking

**Priority 3 (Nice to Have):**
1. ⚠️ Simplify `growth_metrics` (có thể tính on-the-fly)
2. ⚠️ Add `data_completeness` score

### Improvements

Tất cả improvements đã được implement trong:
- **[Database Improvements SQL](database-improvements.sql)** - Migration script
- **[Database Review](database-review.md)** - Chi tiết review

**Key Improvements:**
- ✅ Added `market_cap` field to `financial_data`
- ✅ Added `stock_metadata` table
- ✅ Added performance indexes (composite, partial)
- ✅ Added data validation constraints
- ✅ Added useful views (v_financial_ttm, v_market_snapshot, v_stock_overview)
- ✅ Added advanced analysis fields to `dcf_results`

---

**Next Steps:**
1. Review và approve schema design
2. Run `database-migration.sql` để tạo schema
3. Run `database-improvements.sql` để apply improvements
4. Setup PostgreSQL trong docker-compose
5. Create Database Service
6. Implement data sync
7. Migrate existing data

