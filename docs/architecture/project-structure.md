# DCF Project - Cấu Trúc Dự Án

**Last Updated:** 2025-12-29  
**Version:** 2.0 (Microservices Architecture với Redis)

## Tổng Quan

DCF Project là một hệ thống phân tích định giá cổ phiếu sử dụng mô hình DCF (Discounted Cash Flow) và Graham Valuation. Dự án được tổ chức theo kiến trúc microservices với các tính năng:

- ✅ **Microservices Architecture**: Gateway, DCF Service, Stock Service, Frontend
- ✅ **Redis Cache**: Real-time status tracking và caching
- ✅ **Docker Containerization**: Base image caching, BuildKit optimization
- ✅ **Version Management**: Unified versioning với Git tags
- ✅ **Hot Reload Development**: Development mode với auto-reload
- ✅ **Progress Tracking**: Real-time progress bars trên web interface

## Cấu Trúc Thư Mục

```
dcf_project/
├── src/                          # Source code chính
│   ├── core/                     # Core business logic
│   │   ├── dcf_calculator.py     # Main DCF calculation engine
│   │   ├── fcfs.py              # Free Cash Flow calculations
│   │   ├── ge.py                # Growth Estimate module
│   │   ├── company.py           # Company data structures
│   │   ├── advanced_analysis.py # Advanced analysis features
│   │   ├── value_estimator.py   # Sequential valuation
│   │   └── value_estimator_async.py # Async valuation
│   │
│   └── utils/                    # Utility modules
│       ├── logger.py             # Centralized logging
│       ├── cache_manager.py      # File-based cache
│       ├── redis_client.py       # Redis client (NEW)
│       ├── result_manager.py    # Result file management
│       ├── config_manager.py    # Configuration management
│       ├── constants.py          # Project constants
│       └── translations.py       # i18n support
│
├── services/                     # Microservices
│   ├── common/                  # Shared resources
│   │   ├── Dockerfile.base      # Base Docker image
│   │   └── requirements.txt     # Common Python dependencies
│   │
│   ├── gateway/                  # API Gateway Service
│   │   ├── main.py              # FastAPI gateway application
│   │   ├── Dockerfile.gateway   # Gateway Docker image
│   │   └── requirements.txt     # Gateway dependencies
│   │
│   ├── dcf/                      # DCF Analysis Service
│   │   ├── main.py              # DCF service application
│   │   ├── Dockerfile.dcf       # DCF Docker image
│   │   └── requirements.txt     # DCF dependencies
│   │
│   ├── stock/                    # Stock Data Service
│   │   ├── main.py              # Stock service application
│   │   ├── Dockerfile.stock     # Stock Docker image
│   │   └── requirements.txt     # Stock dependencies
│   │
│   ├── database/                 # Database Service
│   │   ├── main.py              # Database service application
│   │   ├── Dockerfile.database  # Database Docker image
│   │   ├── database.py          # Database connection
│   │   └── models/              # SQLAlchemy models
│   │
│   └── frontend/                 # Frontend Service
│       ├── static/              # Static files (HTML, CSS, JS)
│       │   ├── css/
│       │   ├── js/
│       │   ├── index.html
│       │   ├── database.html    # Database monitoring page
│       │   └── health.html      # Health status page
│       ├── Dockerfile.frontend  # Frontend Docker image (Nginx)
│       └── nginx.conf           # Nginx configuration
│
├── scripts/                      # Management scripts
│   ├── common.sh               # Shared utilities
│   ├── docker.sh               # Docker management
│   ├── docker_version.sh       # Docker versioning
│   ├── build_base.sh           # Base image builder
│   ├── health_check.sh         # Health check script
│   ├── git.sh                   # Git tag management
│   ├── test.sh                  # Test runner
│   ├── lint.sh                  # Linting
│   ├── clean.sh                 # Cleanup
│   ├── dcf.sh                   # DCF analysis runner
│   ├── pe.sh                    # PE calculation
│   └── web.sh                   # Web service management
│
├── config/                       # Configuration files
│   ├── *.cfg                    # Stock-specific configs (FPT, VNM, etc.)
│   └── README.md                # Config documentation
│
├── data/                         # Data directory (gitignored)
│   ├── cache/                   # Cached financial data
│   └── results/                 # Analysis results (JSON + text)
│
├── logs/                         # Log files (gitignored)
│   └── docker/                 # Docker build logs
│
├── docs/                         # Documentation
│   ├── PROJECT_STRUCTURE.md    # This file
│   ├── MICROSERVICES_ARCHITECTURE.md
│   ├── DOCKER_VERSION_MANAGEMENT.md
│   ├── DOCKER_BUILD_OPTIMIZATION.md
│   └── ... (other docs)
│
├── tests/                        # Test files
│   └── test_*.py               # Unit and integration tests
│
├── docker-compose.yml           # Production Docker Compose
├── docker-compose.dev.yml       # Development Docker Compose (hot reload)
├── docker-versions.json         # Docker image version tracking
├── Makefile                     # Main Makefile (orchestrator)
└── .dockerignore                # Docker build exclusions
```

## Kiến Trúc Microservices

```
┌─────────────┐
│  Frontend   │  Port 8080 (Nginx)
│  (Static)   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Gateway   │  Port 8000 (FastAPI)
│  (Router)   │
└──────┬──────┘
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
┌──────────┐    ┌──────────┐    ┌──────────┐
│   DCF    │    │  Stock   │    │  Redis   │
│ Service  │    │ Service  │    │  Cache   │
│ :8001    │    │ :8002    │    │ :6379    │
└──────────┘    └──────────┘    └──────────┘
```

### Services Overview

#### 1. **Frontend Service** (`services/frontend/`)
- **Technology**: Nginx
- **Port**: 8080
- **Role**: Serve static files (HTML, CSS, JavaScript)
- **Features**: 
  - Real-time progress bars
  - Stock list display
  - DCF analysis trigger

#### 2. **Gateway Service** (`services/gateway/`)
- **Technology**: FastAPI
- **Port**: 8000
- **Role**: API Gateway - routes requests to microservices
- **Endpoints**:
  - `GET /api/stocks` → Stock Service
  - `GET /api/stocks/{ticker}` → Stock Service
  - `POST /api/stocks/{ticker}/run` → DCF Service
  - `GET /api/analysis/{ticker}` → DCF Service

#### 3. **DCF Service** (`services/dcf/`)
- **Technology**: FastAPI
- **Port**: 8001
- **Role**: DCF analysis calculation
- **Features**:
  - Async DCF calculation
  - Progress tracking (via Redis)
  - Result caching
- **Endpoints**:
  - `POST /analyze/{ticker}` - Run analysis
  - `GET /analysis/{ticker}` - Get results
  - `GET /status` - Service status

#### 4. **Stock Service** (`services/stock/`)
- **Technology**: FastAPI
- **Port**: 8002
- **Role**: Stock data management
- **Features**:
  - Stock list management
  - Status synchronization (from Redis)
  - Config management
- **Endpoints**:
  - `GET /stocks` - List all stocks
  - `GET /stocks/{ticker}` - Stock details
  - `GET /stocks/{ticker}/status` - Stock status

#### 5. **Redis Service**
- **Technology**: Redis 7-alpine
- **Port**: 6379
- **Role**: 
  - Real-time status tracking
  - Analysis progress caching
  - Session management

#### 6. **Base Image** (`services/common/`)
- **Technology**: Python 3.11-slim
- **Role**: Shared base image for Python services
- **Dependencies**: Common Python packages (FastAPI, pandas, redis, etc.)

## Core Modules

### `src/core/`

#### `dcf_calculator.py`
- Main DCF calculation engine
- Supports progress callbacks
- Integrates with Redis for status tracking

#### `fcfs.py`
- Free Cash Flow calculations
- Financial data fetching from vnstock
- Shares outstanding calculation (handles VND conversion)

#### `ge.py`
- Growth Estimate calculations
- Weighted average of multiple growth metrics

#### `company.py`
- Company data structures
- Financial metrics aggregation

### `src/utils/`

#### `redis_client.py` ⭐ NEW
- Singleton Redis client
- Auto-reconnect và fallback mode
- Status tracking methods

#### `logger.py`
- Centralized logging
- File rotation
- Structured logging format

#### `cache_manager.py`
- File-based caching
- GMT/UTC timestamps
- Lazy save mechanism

#### `config_manager.py`
- Configuration file parsing
- Singleton pattern
- Fallback values

## Docker Architecture

### Base Image Strategy
- **Base Image**: `dcf-project-base` (Python 3.11 + common deps)
- **Versioning**: Independent versioning based on `requirements.txt` hash
- **Caching**: Base image cached, only rebuilds when dependencies change

### Service Images
- **Gateway**: `dcf-project-gateway:${VERSION}`
- **DCF**: `dcf-project-dcf:${VERSION}`
- **Stock**: `dcf-project-stock:${VERSION}`
- **Frontend**: `dcf-project-frontend:${VERSION}`

### Build Optimizations
- ✅ Docker BuildKit enabled
- ✅ Base image caching
- ✅ Layer caching optimization
- ✅ Build cache mounts (pip cache)
- ✅ Parallel builds

## Version Management

### Git Tags (Single Source of Truth)
- Project version derived from latest Git tag
- Format: `v1.0.0`, `v1.0.1`, etc.

### Docker Versioning
- **Base Image**: Independent versioning (increments when `requirements.txt` changes)
- **Service Images**: Synchronized with Git tag
- **Tracking**: `docker-versions.json` file

### Version Scripts
- `scripts/git.sh` - Git tag management
- `scripts/docker_version.sh` - Docker version management
- `scripts/build_base.sh` - Base image builder

## Development Workflow

### Local Development
```bash
# Run tests
make test

# Run DCF analysis
make dcf-single TICKER=FPT

# Run linting
make lint

# Clean up
make clean
```

### Docker Development (Hot Reload)
```bash
# Start dev services
make docker-dev

# View logs
make docker-dev-logs

# Stop services
make docker-dev-down
```

### Production Build
```bash
# Build base image
make docker-build-base

# Build all services
make docker-build

# Start services
make docker-up
```

## Data Flow

### DCF Analysis Flow
1. **User** clicks "Chạy DCF" on Frontend
2. **Frontend** → Gateway `/api/stocks/{ticker}/run`
3. **Gateway** → DCF Service `/analyze/{ticker}`
4. **DCF Service**:
   - Sets status in Redis (running, progress updates)
   - Calls `dcf_calculator.calculate()` with progress callback
   - Updates Redis at each progress milestone (5%, 15%, 50%, 70%, 85%, 95%, 100%)
   - Saves results to file
   - Deletes Redis status on completion
5. **Frontend** polls Stock Service for status updates
6. **Stock Service** reads from Redis and returns status
7. **Frontend** displays progress bar

### Progress Tracking
- **5%**: Initializing calculation...
- **15%**: Fetching financial data...
- **50%**: Calculating DCF valuation...
- **70%**: Calculating Graham valuation...
- **85%**: Generating advanced analysis...
- **95%**: Saving results...
- **100%**: Analysis completed!

## Configuration

### Stock Config Files (`config/*.cfg`)
```ini
[dcf]
yr = 5                    # Forecast years
dr = 10                    # Discount rate (%)
pr = 2.5                   # Perpetual growth rate (%)

[graham]
base_pe = 8.5              # Base PE ratio
growth_multiplier = 2      # Growth multiplier

[ticker]
ticker = FPT               # Stock ticker

[data_source]
source = VCI               # Data source
```

## Key Features

### ✅ Microservices Architecture
- Separation of concerns
- Independent scaling
- Fault isolation

### ✅ Real-time Progress Tracking
- Redis-based status management
- Progress bars on frontend
- Real-time updates

### ✅ Docker Optimization
- Base image caching
- BuildKit acceleration
- Parallel builds

### ✅ Version Management
- Git tags as single source of truth
- Docker image versioning
- Automatic synchronization

### ✅ Development Mode
- Hot reload support
- Volume mounts for code changes
- Auto-restart on file changes

## Technology Stack

- **Backend**: Python 3.11, FastAPI, Uvicorn
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **Cache**: Redis 7-alpine
- **Containerization**: Docker, Docker Compose
- **Data Source**: vnstock library
- **Web Server**: Nginx

## Dependencies

### Common Dependencies (`services/common/requirements.txt`)
- fastapi==0.104.1
- uvicorn[standard]==0.24.0
- httpx==0.25.2
- pydantic==2.5.0
- requests==2.31.0
- pandas==2.1.4
- lxml==5.1.0
- cloudscraper==1.2.71
- vnstock>=0.2.6
- redis==5.0.1 ⭐

## Quick Start

### 1. Build Base Image
```bash
make docker-build-base
```

### 2. Build All Services
```bash
make docker-build
```

### 3. Start Services
```bash
make docker-up
```

### 4. Access Application
- Frontend: http://localhost:8080
- Gateway API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Documentation

- **Architecture**: `docs/MICROSERVICES_ARCHITECTURE.md`
- **Docker**: `docs/DOCKER_VERSION_MANAGEMENT.md`
- **Build Optimization**: `docs/DOCKER_BUILD_OPTIMIZATION.md`
- **Development**: `docs/DEVELOPMENT_MODE.md`

---

**Last Updated**: 2025-12-29  
**Version**: 2.0
