# Installation Guide

**Hướng dẫn cài đặt chi tiết DCF Project**

## System Requirements

### Minimum Requirements
- **OS**: Linux, macOS, hoặc Windows (với WSL2)
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 5GB free space
- **CPU**: 2 cores minimum

### Recommended
- **OS**: Linux hoặc macOS
- **Docker**: Latest version
- **RAM**: 8GB+
- **Disk**: 10GB+ free space
- **CPU**: 4+ cores

## Installation Steps

### 1. Install Docker

#### Linux (Ubuntu/Debian)
```bash
# Update package index
sudo apt-get update

# Install Docker
sudo apt-get install docker.io docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group (optional)
sudo usermod -aG docker $USER
```

#### macOS
```bash
# Install via Homebrew
brew install docker docker-compose

# Or download Docker Desktop
# https://www.docker.com/products/docker-desktop
```

#### Windows
1. Install WSL2
2. Install Docker Desktop for Windows
3. Enable WSL2 integration

### 2. Install Git

```bash
# Linux
sudo apt-get install git

# macOS
brew install git

# Windows
# Download from https://git-scm.com/download/win
```

### 3. Clone Repository

```bash
git clone <repository-url>
cd dcf_project
```

### 4. Verify Installation

```bash
# Check Docker
docker --version
docker-compose --version

# Check Git
git --version

# Check Make (optional)
make --version
```

## Configuration

### Environment Variables

Tạo file `.env` nếu cần (optional):

```bash
# .env
VERSION=latest
BASE_VERSION=latest
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
```

### Stock Configuration

Tạo config files trong `config/`:

```bash
# Example: config/FPT.cfg
[dcf]
yr = 5
dr = 10
pr = 2.5

[graham]
base_pe = 8.5
growth_multiplier = 2

[ticker]
ticker = FPT
```

Xem thêm tại [Configuration Guide](../reference/configuration.md).

## First Build

### Build Base Image

```bash
make docker-build-base
```

Lần đầu tiên có thể mất 5-10 phút.

### Build All Services

```bash
make docker-build
```

Hoặc với parallel builds (nhanh hơn):

```bash
make docker-build-fast
```

### Start Services

```bash
make docker-up
```

## Verify Installation

### Check Services

```bash
# Check running containers
make docker-ps

# Check logs
make docker-logs
```

### Test API

```bash
# Health check
curl http://localhost:8000/health

# List stocks
curl http://localhost:8000/api/stocks
```

### Access Web Interface

Mở browser: http://localhost:8080

## Development Setup

### Install Python Dependencies (Local Development)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r services/common/requirements.txt
```

### Run Locally (without Docker)

```bash
# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Start Gateway
cd services/gateway
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Start DCF Service (new terminal)
cd services/dcf
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Start Stock Service (new terminal)
cd services/stock
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

## Troubleshooting

### Docker Issues

**Problem**: Docker daemon not running
```bash
# Linux
sudo systemctl start docker

# macOS/Windows
# Start Docker Desktop
```

**Problem**: Permission denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and log back in
```

### Port Conflicts

**Problem**: Port already in use

```bash
# Check what's using the port
# Linux
sudo lsof -i :8080
sudo lsof -i :8000

# macOS
lsof -i :8080

# Stop conflicting service or change ports in docker-compose.yml
```

### Build Issues

**Problem**: Build fails with "no space left"

```bash
# Clean up Docker
docker system prune -a
docker volume prune

# Check disk space
df -h
```

**Problem**: Base image build fails

```bash
# Clean build
make docker-build-base-no-cache
```

### Network Issues

**Problem**: Services can't communicate

```bash
# Check Docker network
docker network ls
docker network inspect dcf_project_dcf-network

# Recreate network
docker network rm dcf_project_dcf-network
make docker-up
```

## Next Steps

- [First Steps](first-steps.md) - Các bước tiếp theo
- [Quick Start Guide](quick-start.md) - Chạy phân tích đầu tiên
- [Business Overview](../business/overview.md) - Hiểu về dự án

---

**Next:** [First Steps](first-steps.md) →

