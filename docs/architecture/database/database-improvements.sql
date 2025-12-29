-- Database Improvements Based on Review
-- Additional migrations to improve database design
-- Version: 1.1
-- Created: 2025-12-29

-- ============================================================================
-- 1. ADD MISSING FIELDS
-- ============================================================================

-- Add market_cap to financial_data (needed for advanced analysis)
ALTER TABLE financial_data 
    ADD COLUMN IF NOT EXISTS market_cap BIGINT;

-- Add sync tracking to stocks
ALTER TABLE stocks 
    ADD COLUMN IF NOT EXISTS last_sync_date TIMESTAMP,
    ADD COLUMN IF NOT EXISTS sync_status VARCHAR(20) DEFAULT 'pending' 
        CHECK (sync_status IN ('pending', 'synced', 'failed'));

-- Add advanced fields to dcf_results
ALTER TABLE dcf_results 
    ADD COLUMN IF NOT EXISTS upside_potential DECIMAL(10, 4),
    ADD COLUMN IF NOT EXISTS downside_risk DECIMAL(10, 4),
    ADD COLUMN IF NOT EXISTS yearly_price_forecast JSONB,
    ADD COLUMN IF NOT EXISTS valuation_metrics JSONB,
    ADD COLUMN IF NOT EXISTS fair_value_avg DECIMAL(15, 2),
    ADD COLUMN IF NOT EXISTS calculation_method VARCHAR(50) DEFAULT 'standard',
    ADD COLUMN IF NOT EXISTS input_data_hash VARCHAR(64),
    ADD COLUMN IF NOT EXISTS calculation_duration_ms INTEGER;

-- Add data completeness tracking to financial_data
ALTER TABLE financial_data 
    ADD COLUMN IF NOT EXISTS data_completeness DECIMAL(5, 2) DEFAULT 100.00 
        CHECK (data_completeness >= 0 AND data_completeness <= 100);

-- ============================================================================
-- 2. CREATE STOCK_METADATA TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS stock_metadata (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    
    -- Company Info
    website VARCHAR(255),
    description TEXT,
    founded_year INTEGER,
    headquarters VARCHAR(255),
    
    -- Market Info
    listing_date DATE,
    market_cap_category VARCHAR(20) CHECK (market_cap_category IN ('large', 'mid', 'small')),
    
    -- VN30 specific
    vn30_weight DECIMAL(10, 4),
    vn30_rank INTEGER CHECK (vn30_rank > 0 AND vn30_rank <= 30),
    
    -- Metadata
    data_source VARCHAR(50) DEFAULT 'vnstock',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_id)
);

CREATE INDEX IF NOT EXISTS idx_metadata_stock ON stock_metadata(stock_id);
CREATE INDEX IF NOT EXISTS idx_metadata_vn30_rank ON stock_metadata(vn30_rank);

-- ============================================================================
-- 3. ADD PERFORMANCE INDEXES
-- ============================================================================

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_financial_stock_period_type 
    ON financial_data(stock_id, period_type, period_date DESC);

CREATE INDEX IF NOT EXISTS idx_market_stock_date_desc 
    ON market_data(stock_id, trade_date DESC);

CREATE INDEX IF NOT EXISTS idx_shares_stock_date_desc 
    ON shares_outstanding(stock_id, period_date DESC);

CREATE INDEX IF NOT EXISTS idx_growth_stock_date_desc 
    ON growth_metrics(stock_id, period_date DESC);

CREATE INDEX IF NOT EXISTS idx_results_stock_date_desc 
    ON dcf_results(stock_id, analysis_date DESC);

-- Partial indexes for latest data (more efficient)
CREATE INDEX IF NOT EXISTS idx_financial_latest_quarter 
    ON financial_data(stock_id, period_date DESC) 
    WHERE period_type = 'quarter';

CREATE INDEX IF NOT EXISTS idx_market_latest 
    ON market_data(stock_id, trade_date DESC);

CREATE INDEX IF NOT EXISTS idx_shares_latest 
    ON shares_outstanding(stock_id, period_date DESC);

-- Index for market_cap queries
CREATE INDEX IF NOT EXISTS idx_financial_market_cap 
    ON financial_data(market_cap) 
    WHERE market_cap IS NOT NULL;

-- ============================================================================
-- 4. ADD DATA VALIDATION CONSTRAINTS
-- ============================================================================

-- Ensure positive values where appropriate
ALTER TABLE shares_outstanding 
    DROP CONSTRAINT IF EXISTS chk_shares_positive,
    ADD CONSTRAINT chk_shares_positive CHECK (shares_outstanding > 0);

ALTER TABLE market_data 
    DROP CONSTRAINT IF EXISTS chk_price_positive,
    ADD CONSTRAINT chk_price_positive CHECK (close_price > 0);

ALTER TABLE dcf_configs 
    DROP CONSTRAINT IF EXISTS chk_discount_rate_valid,
    ADD CONSTRAINT chk_discount_rate_valid 
        CHECK (discount_rate > perpetual_growth_rate);

ALTER TABLE financial_data 
    DROP CONSTRAINT IF EXISTS chk_period_date_valid,
    ADD CONSTRAINT chk_period_date_valid 
        CHECK (period_date <= CURRENT_DATE);

-- ============================================================================
-- 5. CREATE USEFUL VIEWS
-- ============================================================================

-- View: Latest financial data TTM (Trailing Twelve Months)
CREATE OR REPLACE VIEW v_financial_ttm AS
SELECT 
    s.id as stock_id,
    s.ticker,
    s.name,
    SUM(fd.operating_cash_flow) FILTER (
        WHERE fd.period_type = 'quarter' 
        AND fd.period_date >= CURRENT_DATE - INTERVAL '1 year'
    ) as ttm_ocf,
    SUM(fd.capital_expenditures) FILTER (
        WHERE fd.period_type = 'quarter' 
        AND fd.period_date >= CURRENT_DATE - INTERVAL '1 year'
    ) as ttm_capex,
    SUM(fd.operating_cash_flow) FILTER (
        WHERE fd.period_type = 'quarter' 
        AND fd.period_date >= CURRENT_DATE - INTERVAL '1 year'
    ) - 
    SUM(fd.capital_expenditures) FILTER (
        WHERE fd.period_type = 'quarter' 
        AND fd.period_date >= CURRENT_DATE - INTERVAL '1 year'
    ) as ttm_fcf,
    MAX(fd.period_date) FILTER (
        WHERE fd.period_type = 'quarter'
    ) as latest_quarter_date
FROM stocks s
LEFT JOIN financial_data fd ON s.id = fd.stock_id
WHERE s.is_active = TRUE
GROUP BY s.id, s.ticker, s.name;

-- View: Latest market snapshot
CREATE OR REPLACE VIEW v_market_snapshot AS
SELECT DISTINCT ON (s.ticker)
    s.id as stock_id,
    s.ticker,
    s.name,
    md.close_price as current_price,
    md.market_cap,
    md.pe_ratio,
    md.volume,
    md.trade_date,
    md.pb_ratio,
    md.ps_ratio
FROM stocks s
JOIN market_data md ON s.id = md.stock_id
WHERE s.is_active = TRUE
ORDER BY s.ticker, md.trade_date DESC;

-- View: Latest shares outstanding
CREATE OR REPLACE VIEW v_shares_latest AS
SELECT DISTINCT ON (s.ticker)
    s.id as stock_id,
    s.ticker,
    s.name,
    so.shares_outstanding,
    so.par_value,
    so.calculation_method,
    so.period_date,
    so.updated_at
FROM stocks s
JOIN shares_outstanding so ON s.id = so.stock_id
WHERE s.is_active = TRUE
ORDER BY s.ticker, so.period_date DESC;

-- View: Latest DCF results with stock info
CREATE OR REPLACE VIEW v_dcf_results_latest AS
SELECT DISTINCT ON (s.ticker)
    s.id as stock_id,
    s.ticker,
    s.name,
    dr.analysis_date,
    dr.fair_value_per_share as dcf_fair_value,
    dr.graham_value_per_share,
    dr.fair_value_avg,
    dr.market_price,
    dr.margin_of_safety,
    dr.recommendation,
    dr.status,
    dr.created_at
FROM stocks s
JOIN dcf_results dr ON s.id = dr.stock_id
WHERE s.is_active = TRUE 
    AND dr.status = 'completed'
ORDER BY s.ticker, dr.analysis_date DESC;

-- View: Complete stock overview (all latest data)
CREATE OR REPLACE VIEW v_stock_overview AS
SELECT 
    s.id,
    s.ticker,
    s.name,
    s.sector,
    s.industry,
    s.is_vn30,
    s.last_sync_date,
    s.sync_status,
    
    -- Latest market data
    ms.current_price,
    ms.market_cap,
    ms.pe_ratio,
    ms.trade_date as latest_market_date,
    
    -- Latest shares
    sl.shares_outstanding,
    sl.par_value,
    
    -- Latest financial TTM
    ft.ttm_fcf,
    ft.ttm_ocf,
    ft.ttm_capex,
    
    -- Latest DCF result
    dr.dcf_fair_value,
    dr.graham_value_per_share,
    dr.fair_value_avg,
    dr.margin_of_safety,
    dr.recommendation,
    dr.analysis_date as latest_analysis_date,
    
    -- DCF config
    dc.forecast_years,
    dc.discount_rate,
    dc.perpetual_growth_rate,
    dc.base_pe,
    dc.growth_multiplier
    
FROM stocks s
LEFT JOIN v_market_snapshot ms ON s.id = ms.stock_id
LEFT JOIN v_shares_latest sl ON s.id = sl.stock_id
LEFT JOIN v_financial_ttm ft ON s.id = ft.stock_id
LEFT JOIN v_dcf_results_latest dr ON s.id = dr.stock_id
LEFT JOIN dcf_configs dc ON s.id = dc.stock_id
WHERE s.is_active = TRUE;

-- ============================================================================
-- 6. UPDATE TRIGGERS
-- ============================================================================

-- Add trigger for stock_metadata
CREATE TRIGGER update_stock_metadata_updated_at BEFORE UPDATE ON stock_metadata
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 7. COMMENTS
-- ============================================================================

COMMENT ON COLUMN financial_data.market_cap IS 'Market capitalization calculated from price × shares for this period';
COMMENT ON COLUMN stocks.last_sync_date IS 'Last successful data synchronization date';
COMMENT ON COLUMN stocks.sync_status IS 'Current synchronization status: pending, synced, or failed';
COMMENT ON COLUMN dcf_results.input_data_hash IS 'SHA256 hash of input data to detect changes';
COMMENT ON COLUMN dcf_results.calculation_duration_ms IS 'Time taken to calculate DCF in milliseconds';
COMMENT ON TABLE stock_metadata IS 'Additional metadata about stocks including company info and VN30 details';

-- ============================================================================
-- END OF IMPROVEMENTS
-- ============================================================================

