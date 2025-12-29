-- Database Migration Script for VN30 Stock Data
-- PostgreSQL Database Schema
-- Version: 1.0
-- Created: 2025-12-29

-- Enable UUID extension (if needed)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. STOCKS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS stocks (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    exchange VARCHAR(20) DEFAULT 'HOSE',
    is_vn30 BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stocks_ticker ON stocks(ticker);
CREATE INDEX IF NOT EXISTS idx_stocks_vn30 ON stocks(is_vn30);
CREATE INDEX IF NOT EXISTS idx_stocks_active ON stocks(is_active);

-- ============================================================================
-- 2. FINANCIAL_DATA TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS financial_data (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    period_type VARCHAR(20) NOT NULL CHECK (period_type IN ('quarter', 'year')),
    period VARCHAR(20) NOT NULL,
    period_date DATE NOT NULL,
    
    -- Balance Sheet
    total_assets BIGINT,
    total_liabilities BIGINT,
    total_equity BIGINT,
    common_shares_capital BIGINT,
    paid_in_capital BIGINT,
    
    -- Income Statement
    revenue BIGINT,
    net_profit BIGINT,
    operating_profit BIGINT,
    ebit BIGINT,
    ebitda BIGINT,
    
    -- Cash Flow Statement
    operating_cash_flow BIGINT,
    investing_cash_flow BIGINT,
    capital_expenditures BIGINT,
    free_cash_flow BIGINT,
    
    -- Ratios
    eps DECIMAL(15, 2),
    roe DECIMAL(10, 4),
    roa DECIMAL(10, 4),
    
    -- Metadata
    data_source VARCHAR(50) DEFAULT 'vnstock',
    data_quality VARCHAR(20) DEFAULT 'good' CHECK (data_quality IN ('good', 'warning', 'error')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_id, period_type, period)
);

CREATE INDEX IF NOT EXISTS idx_financial_stock_period ON financial_data(stock_id, period_date);
CREATE INDEX IF NOT EXISTS idx_financial_period_type ON financial_data(period_type, period_date);

-- ============================================================================
-- 3. SHARES_OUTSTANDING TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS shares_outstanding (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    period_date DATE NOT NULL,
    shares_outstanding BIGINT NOT NULL,
    par_value DECIMAL(15, 2) DEFAULT 10000,
    calculation_method VARCHAR(50),
    source_column VARCHAR(100),
    data_source VARCHAR(50) DEFAULT 'vnstock',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_id, period_date)
);

CREATE INDEX IF NOT EXISTS idx_shares_stock_date ON shares_outstanding(stock_id, period_date);

-- ============================================================================
-- 4. MARKET_DATA TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS market_data (
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
    market_cap BIGINT,
    
    -- Ratios
    pe_ratio DECIMAL(10, 4),
    pb_ratio DECIMAL(10, 4),
    ps_ratio DECIMAL(10, 4),
    
    -- Metadata
    data_source VARCHAR(50) DEFAULT 'vnstock',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_id, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_market_stock_date ON market_data(stock_id, trade_date);
CREATE INDEX IF NOT EXISTS idx_market_trade_date ON market_data(trade_date);

-- ============================================================================
-- 5. GROWTH_METRICS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS growth_metrics (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    period_date DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL CHECK (period_type IN ('quarter', 'year')),
    
    -- Growth Rates (%)
    revenue_growth_yoy DECIMAL(10, 4),
    net_profit_growth_yoy DECIMAL(10, 4),
    operating_profit_growth_yoy DECIMAL(10, 4),
    fcf_growth_yoy DECIMAL(10, 4),
    
    -- Weighted Average Growth (for DCF)
    weighted_growth_rate DECIMAL(10, 4),
    
    -- Historical Average
    historical_avg_growth DECIMAL(10, 4),
    
    -- Metadata
    calculation_method VARCHAR(100),
    data_points_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_id, period_date, period_type)
);

CREATE INDEX IF NOT EXISTS idx_growth_stock_period ON growth_metrics(stock_id, period_date);

-- ============================================================================
-- 6. DCF_CONFIGS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS dcf_configs (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    
    -- DCF Parameters
    forecast_years INTEGER DEFAULT 5 CHECK (forecast_years > 0),
    discount_rate DECIMAL(5, 2) DEFAULT 10.00 CHECK (discount_rate > 0),
    perpetual_growth_rate DECIMAL(5, 2) DEFAULT 2.50 CHECK (perpetual_growth_rate >= 0),
    
    -- Graham Parameters
    base_pe DECIMAL(5, 2) DEFAULT 8.50 CHECK (base_pe > 0),
    growth_multiplier DECIMAL(5, 2) DEFAULT 2.00 CHECK (growth_multiplier > 0),
    
    -- Metadata
    is_default BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_id)
);

CREATE INDEX IF NOT EXISTS idx_config_stock ON dcf_configs(stock_id);

-- ============================================================================
-- 7. DCF_RESULTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS dcf_results (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    analysis_date TIMESTAMP NOT NULL,
    
    -- Input Data
    fcf_ttm BIGINT,
    shares_outstanding BIGINT,
    growth_rate DECIMAL(10, 4),
    
    -- DCF Calculation
    dcf_value BIGINT,
    fair_value_per_share DECIMAL(15, 2),
    terminal_value BIGINT,
    
    -- Graham Calculation
    graham_value_per_share DECIMAL(15, 2),
    eps DECIMAL(15, 2),
    
    -- Market Comparison
    market_price DECIMAL(15, 2),
    margin_of_safety DECIMAL(10, 4),
    recommendation VARCHAR(20) CHECK (recommendation IN ('buy', 'hold', 'sell')),
    
    -- Forecast Data (JSONB)
    forecast_data JSONB,
    present_values JSONB,
    
    -- Metadata
    config_id INTEGER REFERENCES dcf_configs(id),
    calculation_version VARCHAR(20) DEFAULT '1.0',
    status VARCHAR(20) DEFAULT 'completed' CHECK (status IN ('running', 'completed', 'failed')),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_results_stock_date ON dcf_results(stock_id, analysis_date);
CREATE INDEX IF NOT EXISTS idx_results_analysis_date ON dcf_results(analysis_date);
CREATE INDEX IF NOT EXISTS idx_results_status ON dcf_results(status);
CREATE INDEX IF NOT EXISTS idx_results_forecast_data ON dcf_results USING GIN(forecast_data);
CREATE INDEX IF NOT EXISTS idx_results_present_values ON dcf_results USING GIN(present_values);

-- ============================================================================
-- 8. DATA_SYNC_LOGS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS data_sync_logs (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id) ON DELETE SET NULL,
    sync_type VARCHAR(50) NOT NULL CHECK (sync_type IN ('financial', 'market', 'shares', 'all')),
    sync_status VARCHAR(20) NOT NULL CHECK (sync_status IN ('success', 'failed', 'partial')),
    records_updated INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    error_message TEXT,
    sync_duration_ms INTEGER,
    data_source VARCHAR(50) DEFAULT 'vnstock',
    sync_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sync_stock_date ON data_sync_logs(stock_id, sync_date);
CREATE INDEX IF NOT EXISTS idx_sync_status ON data_sync_logs(sync_status);
CREATE INDEX IF NOT EXISTS idx_sync_date ON data_sync_logs(sync_date);

-- ============================================================================
-- TRIGGERS: Auto-update updated_at timestamp
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to all tables with updated_at column
CREATE TRIGGER update_stocks_updated_at BEFORE UPDATE ON stocks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_financial_data_updated_at BEFORE UPDATE ON financial_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shares_outstanding_updated_at BEFORE UPDATE ON shares_outstanding
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_market_data_updated_at BEFORE UPDATE ON market_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_growth_metrics_updated_at BEFORE UPDATE ON growth_metrics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dcf_configs_updated_at BEFORE UPDATE ON dcf_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SEED DATA: VN30 Stocks
-- ============================================================================

-- Insert VN30 stocks
INSERT INTO stocks (ticker, name, sector, industry, is_vn30, is_active) VALUES
('ACB', 'Asia Commercial Bank', 'Financials', 'Banking', TRUE, TRUE),
('BID', 'Bank for Investment and Development of Vietnam', 'Financials', 'Banking', TRUE, TRUE),
('BVH', 'Bao Viet Holdings', 'Financials', 'Insurance', TRUE, TRUE),
('CTG', 'VietinBank', 'Financials', 'Banking', TRUE, TRUE),
('FPT', 'FPT Corporation', 'Technology', 'IT Services', TRUE, TRUE),
('GAS', 'PetroVietnam Gas', 'Energy', 'Oil & Gas', TRUE, TRUE),
('GVR', 'Vietnam Rubber Group', 'Materials', 'Chemicals', TRUE, TRUE),
('HDB', 'HDBank', 'Financials', 'Banking', TRUE, TRUE),
('HPG', 'Hoa Phat Group', 'Materials', 'Steel', TRUE, TRUE),
('MBB', 'Military Bank', 'Financials', 'Banking', TRUE, TRUE),
('MSN', 'Masan Group', 'Consumer', 'Consumer Goods', TRUE, TRUE),
('MWG', 'Mobile World Investment', 'Consumer', 'Retail', TRUE, TRUE),
('PLX', 'Petrolimex', 'Energy', 'Oil & Gas', TRUE, TRUE),
('POW', 'PetroVietnam Power', 'Utilities', 'Power', TRUE, TRUE),
('SAB', 'Sabeco', 'Consumer', 'Beverages', TRUE, TRUE),
('SSI', 'SSI Securities', 'Financials', 'Securities', TRUE, TRUE),
('STB', 'Saigon Thuong Tin Bank', 'Financials', 'Banking', TRUE, TRUE),
('TCB', 'Techcombank', 'Financials', 'Banking', TRUE, TRUE),
('TPB', 'TPBank', 'Financials', 'Banking', TRUE, TRUE),
('VCB', 'Vietcombank', 'Financials', 'Banking', TRUE, TRUE),
('VHM', 'Vinhomes', 'Real Estate', 'Real Estate', TRUE, TRUE),
('VIC', 'Vingroup', 'Real Estate', 'Conglomerate', TRUE, TRUE),
('VJC', 'VietJet Air', 'Industrials', 'Airlines', TRUE, TRUE),
('VNM', 'Vinamilk', 'Consumer', 'Food & Beverages', TRUE, TRUE),
('VPB', 'VPBank', 'Financials', 'Banking', TRUE, TRUE),
('VRE', 'Vincom Retail', 'Consumer', 'Retail', TRUE, TRUE),
('VSH', 'Vietnam Shipbuilding Industry', 'Industrials', 'Shipbuilding', TRUE, TRUE),
('VTI', 'Vietnam Technological and Commercial', 'Technology', 'IT Services', TRUE, TRUE),
('VTO', 'Vietnam Oil and Gas', 'Energy', 'Oil & Gas', TRUE, TRUE),
('VPB', 'VPBank', 'Financials', 'Banking', TRUE, TRUE)
ON CONFLICT (ticker) DO NOTHING;

-- Insert default DCF configs for all VN30 stocks
INSERT INTO dcf_configs (stock_id, forecast_years, discount_rate, perpetual_growth_rate, base_pe, growth_multiplier, is_default)
SELECT id, 5, 10.00, 2.50, 8.50, 2.00, TRUE
FROM stocks
WHERE is_vn30 = TRUE
ON CONFLICT (stock_id) DO NOTHING;

-- ============================================================================
-- VIEWS: Useful views for queries
-- ============================================================================

-- View: Latest financial data for each stock
CREATE OR REPLACE VIEW v_latest_financial_data AS
SELECT DISTINCT ON (stock_id)
    fd.*,
    s.ticker,
    s.name
FROM financial_data fd
JOIN stocks s ON fd.stock_id = s.id
ORDER BY stock_id, period_date DESC;

-- View: Latest market data for each stock
CREATE OR REPLACE VIEW v_latest_market_data AS
SELECT DISTINCT ON (stock_id)
    md.*,
    s.ticker,
    s.name
FROM market_data md
JOIN stocks s ON md.stock_id = s.id
ORDER BY stock_id, trade_date DESC;

-- View: Latest DCF results for each stock
CREATE OR REPLACE VIEW v_latest_dcf_results AS
SELECT DISTINCT ON (stock_id)
    dr.*,
    s.ticker,
    s.name
FROM dcf_results dr
JOIN stocks s ON dr.stock_id = s.id
WHERE dr.status = 'completed'
ORDER BY stock_id, analysis_date DESC;

-- ============================================================================
-- COMMENTS: Documentation
-- ============================================================================

COMMENT ON TABLE stocks IS 'Basic information about stocks, including VN30 stocks';
COMMENT ON TABLE financial_data IS 'Quarterly and yearly financial data from financial statements';
COMMENT ON TABLE shares_outstanding IS 'Shares outstanding data with calculation method';
COMMENT ON TABLE market_data IS 'Daily market data including prices, volume, and ratios';
COMMENT ON TABLE growth_metrics IS 'Growth rate metrics calculated from historical data';
COMMENT ON TABLE dcf_configs IS 'DCF and Graham valuation parameters for each stock';
COMMENT ON TABLE dcf_results IS 'DCF analysis results with forecast data and recommendations';
COMMENT ON TABLE data_sync_logs IS 'Logs of data synchronization operations';

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================

