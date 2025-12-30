# Documentation Index

**Version:** 3.0  
**Last Updated:** 2025-12-30

## Recent Updates (2025-12-30)
- ✅ Architecture documentation updated (Sync Service refactoring)
- ✅ Obsolete documents moved to historical folder
- ✅ API reference updated with all current endpoints
- ✅ Documentation structure consolidated

## 📚 Cấu Trúc Documentation

```
docs/
├── README.md                    # Main documentation entry
├── DOCUMENTATION_INDEX.md       # This file
├── DATA_WORKFLOW.md             # Data flow documentation
├── getting-started/             # Getting started guides
├── business/                    # Business documentation
├── architecture/                # Architecture documentation
│   ├── microservices.md        # ⭐ Main architecture (UPDATED)
│   ├── sync-service.md         # ⭐ Sync service (NEW)
│   ├── database/               # Database documentation
│   └── ...
├── operations/                  # Operations documentation
├── reference/                   # Technical reference
│   ├── api.md                  # ⭐ API reference (UPDATED)
│   └── ...
└── historical/                  # Historical/legacy docs
```

## 🎯 Quick Navigation

### ⭐ Must Read (Updated)
- **[Microservices Architecture](architecture/microservices.md)** - System architecture
- **[Sync Service](architecture/sync-service.md)** - Data sync architecture
- **[API Reference](reference/api.md)** - All API endpoints

### 🚀 Getting Started
- **[README.md](getting-started/README.md)** - Overview
- **[Quick Start Guide](getting-started/quick-start.md)** - 5-minute start
- **[Installation Guide](getting-started/installation.md)** - Detailed installation
- **[First Steps](getting-started/first-steps.md)** - First steps guide

### 💼 Business
- **[Overview](business/overview.md)** - Project overview
- **[Goals & Objectives](business/goals.md)** - Project goals
- **[Features](business/features.md)** - Current features
- **[Vision](business/vision.md)** - Project vision
- **[Value Proposition](business/value-proposition.md)** - Value proposition

### 🏗️ Architecture
- **[README.md](architecture/README.md)** - Architecture overview
- **[Microservices](architecture/microservices.md)** ⭐ - Microservices architecture
- **[Sync Service](architecture/sync-service.md)** ⭐ - Sync service design
- **[Project Structure](architecture/project-structure.md)** - Project structure
- **[Database](architecture/database/README.md)** - Database design
- **[Docker](architecture/docker.md)** - Docker configuration
- **[Scripts](architecture/scripts.md)** - Scripts organization

### 🔧 Operations
- **[README.md](operations/README.md)** - Operations overview
- **[Version Management](operations/version-management.md)** - Version management
- **[Docker Version Management](operations/docker-version-management.md)** - Docker versioning
- **[Build Optimization](operations/build-optimization.md)** - Build optimization
- **[Docker Cleanup](operations/docker-cleanup.md)** - Cleanup strategies

### 📖 Reference
- **[README.md](reference/README.md)** - Reference overview
- **[API Reference](reference/api.md)** ⭐ - All API endpoints
- **[DCF Calculation](reference/dcf-calculation.md)** - DCF model
- **[Graham Valuation](reference/graham-valuation.md)** - Graham model
- **[PE Calculation](reference/pe-calculation.md)** - PE ratio calculation
- **[vnstock Data Format](reference/VNSTOCK_DATA_FORMAT.md)** - vnstock data format
- **[Shares Outstanding](reference/shares-outstanding.md)** - Shares calculation

### 📜 Historical (Reference Only)
- **[README.md](historical/README.md)** - Historical docs index
- Old implementation notes
- Legacy documentation
- Historical fixes and changes

## 🔍 Search by Topic

### System Architecture
- [Microservices Architecture](architecture/microservices.md) ⭐
- [Sync Service](architecture/sync-service.md) ⭐
- [Database Design](architecture/database/README.md)
- [Docker Architecture](architecture/docker.md)

### Data Synchronization
- [Sync Service](architecture/sync-service.md) ⭐
- [Data Workflow](DATA_WORKFLOW.md)
- [API Reference - Sync](reference/api.md#-sync-service-api-data-synchronization)

### API & Integration
- [API Reference](reference/api.md) ⭐
- [Gateway API](reference/api.md#-gateway-api)
- [Sync Service API](reference/api.md#-sync-service-api-data-synchronization)

### Getting Started
- [Quick Start](getting-started/quick-start.md)
- [Installation](getting-started/installation.md)
- [First Steps](getting-started/first-steps.md)

### Valuation Models
- [DCF Calculation](reference/dcf-calculation.md)
- [Graham Valuation](reference/graham-valuation.md)
- [PE Calculation](reference/pe-calculation.md)

## 📋 Document Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Current/Updated |
| ⭐ | Important/Must Read |
| 📜 | Historical/Legacy |
| 🆕 | Newly Added |

## 🔄 Recent Changes Summary

### Architecture Changes (2025-12-30)
1. **Sync Service Refactored**
   - Now connects directly to PostgreSQL
   - All sync operations moved from Database Service
   - Job management integrated

2. **Database Service Updated**
   - Now read-only for data viewing
   - No sync operations
   - No vnstock API calls

3. **Documentation Consolidated**
   - Merged sync-related docs
   - Moved obsolete docs to historical
   - Updated API reference

---

**Version:** 3.0  
**Last Updated:** 2025-12-30  
**Maintainer:** Project Team
