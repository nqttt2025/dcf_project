# Database Documentation

**Database Architecture và Design cho VN30 Stock Data**

## 📚 Tài Liệu

### 1. [Database Design](database-design.md) ⭐
Thiết kế database schema chi tiết cho VN30 stocks.

**Nội dung:**
- Database schema design (8 tables)
- Technology choice (PostgreSQL)
- Data flow và sync strategy
- Caching strategy với Redis
- Security và monitoring

### 2. [Database Service](database-service.md) ⭐
Thiết kế Database Service microservice.

**Nội dung:**
- Service architecture
- API endpoints specification
- Service structure
- Integration với other services
- Data synchronization

### 3. [Database Review](database-review.md)
Chi tiết review và recommendations.

**Nội dung:**
- Review process
- Issues và improvements
- Priority-based recommendations
- Migration strategy

### 4. [Database Migration](database-migration.sql)
SQL migration script để tạo database schema.

**Nội dung:**
- CREATE TABLE statements
- Indexes
- Triggers
- Seed data cho VN30
- Views

### 5. [Database Improvements](database-improvements.sql)
SQL migration script cho improvements.

**Nội dung:**
- Additional fields
- Performance indexes
- Data validation constraints
- Useful views
- stock_metadata table

## 🏗️ Database Architecture

### Schema Overview

```
8 Tables:
├── stocks              - Basic stock info (30 VN30 stocks)
├── financial_data      - Quarterly/yearly financials
├── shares_outstanding  - Share count data
├── market_data         - Daily market prices
├── growth_metrics      - Growth rate calculations
├── dcf_configs         - DCF parameters
├── dcf_results         - Analysis results
└── data_sync_logs      - Sync operation logs

+ stock_metadata        - Company metadata (improvement)
```

### Technology Stack

- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **ORM**: SQLAlchemy
- **API**: FastAPI
- **Service**: Database Service (:8003)

## 🚀 Quick Start

### 1. Review Design
Đọc [Database Design](database-design.md) để hiểu schema.

### 2. Review Improvements
Xem [Database Review](database-review.md) để biết improvements.

### 3. Run Migrations
```bash
# Create schema
psql -U dcf_user -d dcf_db -f database-migration.sql

# Apply improvements
psql -U dcf_user -d dcf_db -f database-improvements.sql
```

### 4. Setup Service
Xem [Database Service](database-service.md) để implement service.

## 📊 Database Schema

### Core Tables

1. **stocks** - Basic stock information
2. **financial_data** - Financial statements (quarterly/yearly)
3. **shares_outstanding** - Share count tracking
4. **market_data** - Daily market prices
5. **growth_metrics** - Growth rate calculations
6. **dcf_configs** - DCF parameters per stock
7. **dcf_results** - DCF analysis results
8. **data_sync_logs** - Sync operation logs

### Additional Tables (Improvements)

- **stock_metadata** - Company metadata và VN30 details

## 🔄 Data Flow

```
vnstock API
    │
    ▼
Database Service (sync)
    │
    ├──→ PostgreSQL (persistent storage)
    └──→ Redis (cache layer)
    │
    ▼
DCF Service / Stock Service (query)
```

## 📖 Đọc Tiếp

- [Database Design](database-design.md) - Chi tiết schema
- [Database Service](database-service.md) - Service design
- [Database Review](database-review.md) - Review và improvements

---

**Back to:** [Architecture README](../README.md)

