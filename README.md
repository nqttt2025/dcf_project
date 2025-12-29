# DCF Valuation Project

[![Version](https://img.shields.io/badge/version-v1.0.0-blue.svg)](https://github.com/your-repo/dcf_project)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

Hệ thống phân tích định giá cổ phiếu sử dụng mô hình **DCF (Discounted Cash Flow)** và **Graham Valuation** với kiến trúc microservices.

## ✨ Tính Năng Chính

- 🎯 **DCF Analysis**: Tính toán định giá cổ phiếu bằng mô hình DCF
- 📊 **Graham Valuation**: Định giá theo công thức Graham
- 🚀 **Microservices Architecture**: Gateway, DCF Service, Stock Service, Frontend
- ⚡ **Real-time Progress**: Theo dõi tiến độ phân tích với progress bars
- 🔄 **Redis Cache**: Status tracking và caching
- 🐳 **Docker Support**: Containerization với base image caching
- 🔥 **Hot Reload**: Development mode với auto-reload
- 📈 **Version Management**: Unified versioning với Git tags

## 🏗️ Kiến Trúc

```
┌─────────────┐
│  Frontend   │  :8080 (Nginx)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Gateway   │  :8000 (FastAPI)
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

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Make (optional, for convenience commands)
- Git

### 1. Clone Repository

```bash
git clone <repository-url>
cd dcf_project
```

### 2. Build Base Image

```bash
make docker-build-base
```

### 3. Build All Services

```bash
make docker-build
```

### 4. Start Services

```bash
make docker-up
```

### 5. Access Application

- **Frontend**: http://localhost:8080
- **Gateway API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📖 Usage

### Web Interface

1. Truy cập http://localhost:8080
2. Chọn mã cổ phiếu từ danh sách
3. Click "Chạy DCF" để bắt đầu phân tích
4. Theo dõi progress bar trong quá trình tính toán
5. Xem kết quả khi hoàn tất

### Command Line

#### Run DCF Analysis

```bash
# Single stock
make dcf-single TICKER=FPT

# All stocks
make dcf-all
```

#### Run PE Calculation

```bash
# Single stock
make pe-single TICKER=FPT

# All stocks
make pe-all
```

### Development Mode (Hot Reload)

```bash
# Start dev services
make docker-dev

# View logs
make docker-dev-logs

# Stop services
make docker-dev-down
```

## 🛠️ Development

### Project Structure

```
dcf_project/
├── src/              # Source code
│   ├── core/        # Core business logic (DCF, Graham)
│   └── utils/       # Utility modules (logger, cache, config)
├── services/         # Microservices
│   ├── gateway/     # API Gateway (FastAPI)
│   ├── dcf/         # DCF Service
│   ├── stock/       # Stock Service
│   ├── database/    # Database Service
│   └── common/      # Common utilities for services
├── scripts/         # Management scripts (refactored with SOLID)
│   ├── lib/         # Core library modules
│   ├── version/     # Version management
│   ├── docker/      # Docker scripts
│   ├── analysis/    # DCF & PE analysis scripts
│   ├── dev/         # Development tools
│   └── utils/       # Utility scripts
├── config/          # Stock configuration files (.cfg)
├── tests/           # Test suite (ut, ft, st, scripts)
└── docs/            # Documentation
```

Xem chi tiết: [docs/architecture/project-structure.md](docs/architecture/project-structure.md)

### Running Tests

```bash
# All tests
make test

# Unit tests only
make ut

# Function tests
make ft

# System tests
make st

# Script tests
make test-scripts

# Linting
make lint
```

### Building Docker Images

```bash
# Build base image
make docker-build-base

# Build all services
make docker-build

# Rebuild everything
make docker-rebuild
```

## 📚 Documentation

Xem [docs/README.md](docs/README.md) để có overview đầy đủ về documentation.

### Quick Links
- **[Getting Started](docs/getting-started/README.md)**: Hướng dẫn bắt đầu
- **[Architecture](docs/architecture/README.md)**: Kiến trúc hệ thống
- **[Operations](docs/operations/README.md)**: Quản lý và vận hành
- **[Scripts](scripts/README.md)**: Hướng dẫn scripts (SOLID refactored)
- **[Tests](tests/README.md)**: Test suite documentation

## 🔧 Configuration

### Stock Config (`config/*.cfg`)

```ini
[dcf]
yr = 5                    # Forecast years
dr = 10                   # Discount rate (%)
pr = 2.5                  # Perpetual growth rate (%)

[graham]
base_pe = 8.5             # Base PE ratio
growth_multiplier = 2     # Growth multiplier

[ticker]
ticker = FPT              # Stock ticker
```

## 📊 DCF Model

```
Fair Value = Σ(CF_t / (1 + DR)^t) + Terminal Value
Terminal Value = CF_n × (1 + PR) / (DR - PR)
```

## 🎯 Key Commands

### Docker Commands

```bash
make docker-build          # Build all images
make docker-build-base     # Build base image only
make docker-up             # Start services
make docker-down           # Stop services
make docker-logs           # View logs
make docker-dev            # Start dev mode (hot reload)
```

### Analysis Commands

```bash
make dcf-single TICKER=FPT    # Run DCF for single stock
make dcf-all                   # Run DCF for all stocks
make pe-single TICKER=FPT      # Run PE calculation
```

### Maintenance Commands

```bash
make clean                    # Clean logs, cache, reports
make lint                     # Run linters
make test                     # Run tests
```

## 🔄 Version Management

- **Project Version**: Derived from Git tags (`v1.0.0`, `v1.0.1`, etc.)
- **Base Image Version**: Independent, increments when dependencies change
- **Service Versions**: Synchronized with Git tag

```bash
# Create new version tag
make git-tag-patch    # v1.0.1
make git-tag-minor    # v1.1.0
make git-tag-major    # v2.0.0

# Check versions
make docker-versions
```

## 🐛 Troubleshooting

### Redis Connection Issues

Nếu Redis không kết nối được, services sẽ chạy ở fallback mode (không có real-time status tracking).

### Docker Build Issues

```bash
# Clean build (no cache)
make docker-build-base-no-cache
make docker-rebuild
```

### Port Conflicts

Kiểm tra ports đang được sử dụng:
- 8080: Frontend
- 8000: Gateway
- 8001: DCF Service
- 8002: Stock Service
- 6379: Redis

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

MIT License

Copyright (c) 2025 Nguyen Quyet Tien/ NQTTT's Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

## 👥 Authors

[Nguyen Quyet Tien/ NQTTT's Team]

## 🙏 Acknowledgments

- vnstock library for financial data
- FastAPI for web framework
- Redis for caching

---

**Last Updated**: 2025-12-30  
**Version**: 2.1

### Recent Updates
- ✅ Refactored scripts directory following SOLID principles
- ✅ Organized Python scripts into appropriate directories
- ✅ Added comprehensive test suite for scripts
- ✅ Improved path resolution for all scripts
- ✅ Consolidated documentation (removed redundant README files)

