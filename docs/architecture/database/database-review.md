# Database Design Review

**Chi tiết review và cải thiện database design cho VN30**

## 🔍 Review Process

Đã review database design dựa trên:
1. Codebase hiện tại (`src/core/`)
2. DCF calculation requirements
3. Data flow và usage patterns
4. Microservices best practices

## ✅ Những Gì Đúng và Cần Giữ

### 1. Core Tables - Đúng và Cần Thiết

#### ✅ `stocks` Table
- **Đúng**: Cần thiết cho basic stock info
- **Fields hợp lý**: ticker, name, sector, industry
- **Indexes tốt**: ticker, is_vn30, is_active

#### ✅ `financial_data` Table
- **Đúng**: Cần thiết cho DCF calculation
- **Fields quan trọng**: 
  - `operating_cash_flow` ✅ (cần cho FCF)
  - `capital_expenditures` ✅ (cần cho FCF)
  - `free_cash_flow` ✅ (calculated, cần cho DCF)
  - `revenue` ✅ (cần cho growth calculation)
  - `net_profit` ✅ (cần cho growth calculation)
  - `eps` ✅ (cần cho Graham)

#### ✅ `shares_outstanding` Table
- **Đúng**: Cần thiết cho DCF (fair_value = dcf_value / shares)
- **Fields hợp lý**: shares_outstanding, par_value, calculation_method

#### ✅ `dcf_configs` Table
- **Đúng**: Cần thiết để lưu parameters
- **Fields đầy đủ**: yr, dr, pr, base_pe, growth_multiplier

#### ✅ `dcf_results` Table
- **Đúng**: Cần thiết để lưu kết quả
- **Fields tốt**: forecast_data (JSONB), present_values (JSONB)

## ⚠️ Vấn Đề Cần Sửa

### 1. `financial_data` Table - Thiếu Fields

**Vấn đề**: Thiếu một số fields quan trọng từ codebase

**Cần thêm:**
```sql
-- Thêm vào financial_data table
-- Market Cap (cần cho advanced analysis)
market_cap BIGINT, -- VND

-- Thêm index cho market_cap queries
CREATE INDEX idx_financial_market_cap ON financial_data(market_cap) WHERE market_cap IS NOT NULL;
```

**Lý do**: `get_market_cap()` được sử dụng trong DCF calculation

### 2. `market_data` Table - Có Thể Tối Ưu

**Vấn đề**: 
- `market_cap` đã có trong `market_data` nhưng cũng cần trong `financial_data` (theo period)
- `pe_ratio`, `pb_ratio`, `ps_ratio` có thể không cần thiết nếu không dùng

**Giải pháp**:
- Giữ `market_cap` trong `market_data` (daily)
- Thêm `market_cap` vào `financial_data` (theo period) - có thể tính từ close_price × shares
- Xem xét loại bỏ `pb_ratio`, `ps_ratio` nếu không dùng

### 3. `growth_metrics` Table - Cần Cải Thiện

**Vấn đề**: 
- `period_type` có thể không cần thiết (chỉ cần latest)
- Thiếu `operating_profit_growth_yoy` trong codebase

**Cần sửa**:
```sql
-- Đơn giản hóa: chỉ lưu latest growth metrics
-- Loại bỏ period_type, chỉ cần period_date (latest)
-- Thêm field: operating_profit_growth_yoy (nếu cần trong tương lai)
```

**Hoặc**: Tính toán on-the-fly từ `financial_data` thay vì lưu riêng

### 4. `shares_outstanding` Table - Cần Cải Thiện

**Vấn đề**: 
- `period_date` có thể không cần thiết nếu shares không thay đổi thường xuyên
- Có thể chỉ cần lưu latest shares

**Giải pháp**:
- Giữ `period_date` để track historical changes
- Thêm index để query latest nhanh hơn

### 5. `dcf_results` Table - Cần Bổ Sung

**Vấn đề**: Thiếu một số fields từ advanced analysis

**Cần thêm**:
```sql
-- Thêm vào dcf_results table
-- Advanced Analysis fields
upside_potential DECIMAL(10, 4), -- % upside từ current price
downside_risk DECIMAL(10, 4), -- % downside risk
yearly_price_forecast JSONB, -- Forecast price cho từng năm
valuation_metrics JSONB, -- Các metrics khác

-- Market comparison
current_price DECIMAL(15, 2), -- Alias cho market_price (rõ ràng hơn)
fair_value_avg DECIMAL(15, 2), -- Average của DCF và Graham
```

### 6. Thiếu Table: `stock_metadata`

**Vấn đề**: Một số metadata không có chỗ lưu

**Cần thêm**:
```sql
CREATE TABLE stock_metadata (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    
    -- Company Info
    website VARCHAR(255),
    description TEXT,
    founded_year INTEGER,
    headquarters VARCHAR(255),
    
    -- Market Info
    listing_date DATE,
    market_cap_category VARCHAR(20), -- 'large', 'mid', 'small'
    
    -- VN30 specific
    vn30_weight DECIMAL(10, 4), -- Weight trong VN30 index
    vn30_rank INTEGER, -- Rank trong VN30
    
    -- Metadata
    data_source VARCHAR(50) DEFAULT 'vnstock',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_id)
);
```

## 🔧 Cải Thiện Đề Xuất

### 1. Tối Ưu Indexes

**Thêm indexes quan trọng**:
```sql
-- Composite index cho queries phổ biến
CREATE INDEX idx_financial_stock_period_type ON financial_data(stock_id, period_type, period_date DESC);
CREATE INDEX idx_market_stock_date_desc ON market_data(stock_id, trade_date DESC);
CREATE INDEX idx_shares_stock_date_desc ON shares_outstanding(stock_id, period_date DESC);

-- Partial indexes cho latest data
CREATE INDEX idx_financial_latest ON financial_data(stock_id, period_date DESC) 
    WHERE period_type = 'quarter';
CREATE INDEX idx_market_latest ON market_data(stock_id, trade_date DESC);
```

### 2. Thêm Constraints

**Data validation constraints**:
```sql
-- Ensure positive values where appropriate
ALTER TABLE financial_data 
    ADD CONSTRAINT chk_shares_positive CHECK (shares_outstanding > 0);
    
ALTER TABLE market_data 
    ADD CONSTRAINT chk_price_positive CHECK (close_price > 0);
    
ALTER TABLE dcf_configs 
    ADD CONSTRAINT chk_discount_rate_valid CHECK (discount_rate > perpetual_growth_rate);
```

### 3. Thêm Views Hữu Ích

**Views cho queries phổ biến**:
```sql
-- View: Latest financial data TTM
CREATE VIEW v_financial_ttm AS
SELECT 
    s.ticker,
    s.name,
    SUM(fd.operating_cash_flow) FILTER (WHERE fd.period_type = 'quarter') as ttm_ocf,
    SUM(fd.capital_expenditures) FILTER (WHERE fd.period_type = 'quarter') as ttm_capex,
    SUM(fd.operating_cash_flow) FILTER (WHERE fd.period_type = 'quarter') - 
    SUM(fd.capital_expenditures) FILTER (WHERE fd.period_type = 'quarter') as ttm_fcf
FROM stocks s
JOIN financial_data fd ON s.id = fd.stock_id
WHERE fd.period_date >= CURRENT_DATE - INTERVAL '1 year'
GROUP BY s.id, s.ticker, s.name;

-- View: Latest market snapshot
CREATE VIEW v_market_snapshot AS
SELECT DISTINCT ON (s.ticker)
    s.ticker,
    s.name,
    md.close_price as current_price,
    md.market_cap,
    md.pe_ratio,
    md.volume,
    md.trade_date
FROM stocks s
JOIN market_data md ON s.id = md.stock_id
ORDER BY s.ticker, md.trade_date DESC;
```

### 4. Loại Bỏ Dư Thừa

**Fields có thể loại bỏ hoặc đơn giản hóa**:

1. **`financial_data.ebitda`**: 
   - Không được sử dụng trong DCF calculation
   - **Quyết định**: Giữ lại (có thể dùng trong tương lai cho advanced analysis)

2. **`financial_data.roe`, `financial_data.roa`**:
   - Không được sử dụng trong DCF calculation
   - **Quyết định**: Giữ lại (có thể dùng cho analysis khác)

3. **`market_data.pb_ratio`, `market_data.ps_ratio`**:
   - Không được sử dụng trong codebase hiện tại
   - **Quyết định**: Giữ lại (có thể dùng trong tương lai)

4. **`growth_metrics.period_type`**:
   - Có thể đơn giản hóa
   - **Quyết định**: Giữ lại để track historical growth

### 5. Thêm Fields Quan Trọng

**Fields cần thêm**:

1. **`financial_data`**:
   ```sql
   -- Thêm market_cap theo period (tính từ price × shares)
   market_cap BIGINT,
   
   -- Thêm để track data quality
   data_completeness DECIMAL(5, 2), -- % completeness (0-100)
   ```

2. **`dcf_results`**:
   ```sql
   -- Thêm để track calculation details
   calculation_method VARCHAR(50) DEFAULT 'standard', -- 'standard', 'advanced'
   input_data_hash VARCHAR(64), -- SHA256 hash của input data để detect changes
   
   -- Thêm để track performance
   calculation_duration_ms INTEGER, -- Thời gian tính toán
   ```

3. **`stocks`**:
   ```sql
   -- Thêm để track stock status
   last_sync_date TIMESTAMP, -- Last successful data sync
   sync_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'synced', 'failed'
   ```

## 📊 Updated Schema Recommendations

### Priority 1: Critical Changes (Must Have)

1. ✅ Thêm `market_cap` vào `financial_data`
2. ✅ Thêm indexes cho latest data queries
3. ✅ Thêm constraints cho data validation
4. ✅ Thêm `stock_metadata` table

### Priority 2: Important Improvements (Should Have)

1. ✅ Thêm views cho common queries
2. ✅ Thêm fields vào `dcf_results` cho advanced analysis
3. ✅ Thêm `input_data_hash` để track changes
4. ✅ Thêm `calculation_duration_ms` để monitor performance

### Priority 3: Nice to Have (Optional)

1. ⚠️ Đơn giản hóa `growth_metrics` (có thể tính on-the-fly)
2. ⚠️ Thêm `data_completeness` score
3. ⚠️ Thêm `sync_status` tracking

## 🎯 Final Recommendations

### Keep As Is ✅
- `stocks` table structure
- `financial_data` core fields (OCF, CapEx, FCF, revenue, net_profit, eps)
- `shares_outstanding` table
- `dcf_configs` table
- `dcf_results` core structure
- `data_sync_logs` table

### Add/Modify 🔧
1. **Add `market_cap` to `financial_data`**
2. **Add `stock_metadata` table**
3. **Add indexes for latest data queries**
4. **Add constraints for data validation**
5. **Add views for common queries**
6. **Add advanced analysis fields to `dcf_results`**

### Consider Removing ⚠️
- `growth_metrics.period_type` (có thể đơn giản hóa)
- `market_data.pb_ratio`, `ps_ratio` (nếu không dùng)

### Performance Optimizations 🚀
1. Composite indexes cho common query patterns
2. Partial indexes cho latest data
3. Materialized views cho TTM calculations (nếu cần)

## 📝 Migration Strategy

### Phase 1: Add Missing Fields
```sql
-- Add market_cap to financial_data
ALTER TABLE financial_data ADD COLUMN market_cap BIGINT;

-- Add indexes
CREATE INDEX idx_financial_stock_period_type ON financial_data(stock_id, period_type, period_date DESC);
CREATE INDEX idx_market_stock_date_desc ON market_data(stock_id, trade_date DESC);
```

### Phase 2: Add New Tables
```sql
-- Create stock_metadata table
CREATE TABLE stock_metadata (...);
```

### Phase 3: Add Constraints
```sql
-- Add validation constraints
ALTER TABLE financial_data ADD CONSTRAINT ...;
```

### Phase 4: Add Views
```sql
-- Create useful views
CREATE VIEW v_financial_ttm AS ...;
CREATE VIEW v_market_snapshot AS ...;
```

---

**Conclusion**: Database design cơ bản là tốt, nhưng cần bổ sung một số fields và tối ưu indexes để phù hợp với codebase hiện tại và cải thiện performance.

