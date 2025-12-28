# This Makefile orchestrates common tasks for DCF Project
# Most logic has been moved to scripts/ for better maintainability
# Usage: 'make' or 'make help' for available commands

PYTHON = python3
SHELL = bash
TEST_DIR = tests
REPORT_DIR = reports

# Default target: run all tests
.DEFAULT_GOAL := test

# ============================================================================
# Test Commands
# ============================================================================

test: ut
	@echo "Unit tests completed"
	@echo "Note: Run 'make ft' for function tests, 'make st' for system tests, 'make complete' for integration tests"

ut:
	@./scripts/test.sh ut

ft:
	@./scripts/test.sh ft

st:
	@./scripts/test.sh st

complete:
	@./scripts/test.sh complete

all: ut ft st complete

test-config:
	@./scripts/test.sh config

test-cache:
	@./scripts/test.sh cache

test-result:
	@./scripts/test.sh result

test-dcf:
	@./scripts/test.sh dcf

# ============================================================================
# DCF Analysis Commands
# ============================================================================

dcf:
	@if [ -z "$(TICKER)" ]; then \
		echo "Usage: make dcf TICKER=<ticker>"; \
		echo "Example: make dcf TICKER=VNM"; \
		./scripts/dcf.sh help; \
		exit 1; \
	fi
	@./scripts/dcf.sh single $(TICKER)

dcf-all:
	@./scripts/dcf.sh all

dcf-all-fast:
	@./scripts/dcf.sh all-fast

dcf-help:
	@./scripts/dcf.sh help

# ============================================================================
# PE Calculation Commands
# ============================================================================

pe:
	@if [ -z "$(TICKER)" ]; then \
		echo "Usage: make pe TICKER=<ticker> [INDUSTRY=<industry>]"; \
		./scripts/pe.sh help; \
		exit 1; \
	fi
	@./scripts/pe.sh single $(TICKER) $(INDUSTRY)

pe-all:
	@./scripts/pe.sh all

pe-help:
	@./scripts/pe.sh help

# ============================================================================
# Linting Commands
# ============================================================================

lint: pylint flake8
	@echo "Linting completed"

pylint:
	@./scripts/lint.sh pylint

flake8:
	@./scripts/lint.sh flake8

# ============================================================================
# Cleanup Commands
# ============================================================================

clean: clean-reports clean-cache clean-logs
	@echo "Cleanup completed"

clean-reports:
	@./scripts/clean.sh reports

clean-cache:
	@./scripts/clean.sh cache

clean-logs:
	@./scripts/clean.sh logs

clean-results:
	@./scripts/clean.sh results

clean-data:
	@./scripts/clean.sh data

clean-all: clean clean-results clean-data
	@echo "Full cleanup completed"

# ============================================================================
# Web Service Commands
# ============================================================================

web:
	@./scripts/web.sh start

web-install:
	@./scripts/web.sh install

# ============================================================================
# Docker Commands
# ============================================================================

docker-build:
	@./scripts/docker.sh build

docker-build-fast:
	@PARALLEL=true ./scripts/docker.sh build

docker-versions:
	@./scripts/docker_version.sh get

docker-version-check-base:
	@./scripts/docker_version.sh check-base

docker-build-auto:
	@echo "Building with auto-tagging..."
	@CURRENT_VERSION=$$(git describe --tags --abbrev=0 2>/dev/null || echo ""); \
	if [ -z "$$CURRENT_VERSION" ] || [ -n "$$(git status --porcelain)" ]; then \
		echo "No tag or uncommitted changes detected. Auto-creating tag..."; \
		NEW_VERSION=$$(./scripts/auto_version.sh patch); \
		echo "Created tag: $$NEW_VERSION"; \
	fi; \
	$(MAKE) docker-build

docker-rebuild:
	@./scripts/docker.sh rebuild

docker-rebuild-auto:
	@echo "Rebuilding with auto-tagging..."
	@CURRENT_VERSION=$$(git describe --tags --abbrev=0 2>/dev/null || echo ""); \
	if [ -z "$$CURRENT_VERSION" ] || [ -n "$$(git status --porcelain)" ]; then \
		echo "No tag or uncommitted changes detected. Auto-creating tag..."; \
		NEW_VERSION=$$(./scripts/auto_version.sh patch); \
		echo "Created tag: $$NEW_VERSION"; \
	fi; \
	$(MAKE) docker-rebuild

docker-up:
	@./scripts/docker.sh up

docker-down:
	@./scripts/docker.sh down

docker-logs:
	@./scripts/docker.sh logs

docker-logs-follow:
	@./scripts/docker.sh logs-follow

docker-logs-gateway:
	@./scripts/docker.sh logs-gateway

docker-logs-dcf:
	@./scripts/docker.sh logs-dcf

docker-logs-stock:
	@./scripts/docker.sh logs-stock

docker-logs-frontend:
	@./scripts/docker.sh logs-frontend

docker-restart:
	@./scripts/docker.sh restart

docker-clean:
	@./scripts/docker.sh clean

docker-clean-all:
	@./scripts/docker.sh clean-all

docker-ps:
	@./scripts/docker.sh ps

docker-images:
	@./scripts/docker.sh images

docker-clean-old:
	@if [ -z "$(KEEP)" ]; then \
		echo "Usage: make docker-clean-old KEEP=3"; \
		echo "Keeps last 3 versions of each image"; \
		exit 1; \
	fi
	@./scripts/docker.sh clean-old $(KEEP)

docker-exec-gateway:
	@./scripts/docker.sh exec-gateway

docker-exec-dcf:
	@./scripts/docker.sh exec-dcf

docker-exec-stock:
	@./scripts/docker.sh exec-stock

docker-exec-frontend:
	@./scripts/docker.sh exec-frontend

docker-dev:
	@./scripts/docker.sh dev

docker-dev-down:
	@./scripts/docker.sh dev-down

docker-dev-logs:
	@./scripts/docker.sh dev-logs

docker-dev-restart:
	@./scripts/docker.sh dev-restart

# ============================================================================
# Backend Development Commands
# ============================================================================

backend-dev:
	@echo "Starting backend services locally (fastest development mode)..."
	@echo "⚠️  This runs services directly on host (no Docker)"
	@echo "⚠️  Make sure you have dependencies installed: pip install -r services/common/requirements.txt"
	@echo ""
	@./scripts/run_backend_dev.sh

backend-gateway:
	@echo "Starting Gateway service locally..."
	@PYTHONPATH="$$(pwd):$$(pwd)/src" \
	cd services/gateway && \
	uvicorn main:app --host 0.0.0.0 --port 8000 --reload

backend-dcf:
	@echo "Starting DCF service locally..."
	@PYTHONPATH="$$(pwd):$$(pwd)/src" \
	cd services/dcf && \
	uvicorn main:app --host 0.0.0.0 --port 8001 --reload

backend-stock:
	@echo "Starting Stock service locally..."
	@PYTHONPATH="$$(pwd):$$(pwd)/src" \
	cd services/stock && \
	uvicorn main:app --host 0.0.0.0 --port 8002 --reload

# ============================================================================
# Git Tag Management Commands
# ============================================================================

get-version:
	@./scripts/get_version.sh

git-tag:
	@if [ -z "$(VERSION)" ]; then \
		echo "Usage: make git-tag VERSION=v1.0.0"; \
		echo "Example: make git-tag VERSION=v1.0.0"; \
		exit 1; \
	fi
	@./scripts/git.sh tag $(VERSION)

git-tag-patch:
	@./scripts/git.sh tag-patch

git-tag-minor:
	@./scripts/git.sh tag-minor

git-tag-major:
	@./scripts/git.sh tag-major

git-tag-from-commit:
	@./scripts/git.sh tag-from-commit

# ============================================================================
# Help
# ============================================================================

help:
	@echo "DCF Project Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make              - Run all tests (default)"
	@echo "  make test         - Run all tests"
	@echo "  make ut           - Run unit tests only"
	@echo "  make ft           - Run function tests"
	@echo "  make st           - Run system tests"
	@echo "  make complete     - Run complete functionality test"
	@echo "  make all          - Run all tests (unit + function + system + complete)"
	@echo ""
	@echo "  make test-config  - Run ConfigManager tests"
	@echo "  make test-cache   - Run CacheManager tests"
	@echo "  make test-result  - Run ResultManager tests"
	@echo "  make test-dcf     - Run DCFCalculator tests"
	@echo ""
	@echo "  make dcf TICKER=<ticker>     - Run DCF analysis for a stock"
	@echo "  make dcf-all                 - Run DCF analysis for all VN30 stocks (with retry & delay)"
	@echo "  make dcf-all-fast            - Run DCF analysis for all VN30 stocks (fast, no retry)"
	@echo "  make dcf-help                - Show DCF analysis help"
	@echo ""
	@echo "  make pe TICKER=<ticker> [INDUSTRY=<industry>] - Calculate PE for a stock"
	@echo "  make pe-all       - Analyze PE for all VN30 stocks"
	@echo "  make pe-help      - Show PE calculation help"
	@echo ""
	@echo "  make lint         - Run all linters"
	@echo "  make pylint       - Run pylint"
	@echo "  make flake8       - Run flake8"
	@echo ""
	@echo "  make clean        - Clean generated files"
	@echo "  make clean-all    - Clean everything including data"
	@echo ""
	@echo "  make web          - Start web service (development, http://localhost:5000)"
	@echo "  make web-install  - Install web service dependencies"
	@echo ""
	@echo "  make docker-build      - Build Docker images (with auto cleanup)"
	@echo "  make docker-rebuild    - Rebuild from scratch (with cleanup)"
	@echo "  make docker-up         - Start Docker containers (http://localhost:8080)"
	@echo "  make docker-down       - Stop Docker containers"
	@echo "  make docker-logs       - View container logs (last 100 lines)"
	@echo "  make docker-logs-follow - Follow container logs (real-time)"
	@echo "  make docker-ps         - Show running containers"
	@echo "  make docker-clean      - Clean unused containers and images"
	@echo "  make docker-clean-all  - Deep clean (removes all unused resources)"
	@echo ""
	@echo "  make docker-dev              - Start services in DEV mode (hot reload, no rebuild)"
	@echo "  make docker-dev-down         - Stop dev services"
	@echo "  make docker-dev-logs         - View dev logs"
	@echo "  make backend-dev             - Run backend locally (fastest for development)"
	@echo ""
	@echo "  make git-tag VERSION=<version> - Create a git tag"
	@echo "  make git-tag-patch            - Auto-increment patch version"
	@echo "  make git-tag-minor            - Auto-increment minor version"
	@echo "  make git-tag-major            - Auto-increment major version"
	@echo ""
	@echo "  make help         - Show this help message"
	@echo ""
	@echo "Note: Most commands delegate to scripts/ for better maintainability."
	@echo "      See scripts/*.sh for implementation details."

.PHONY: test ut ft st complete all test-config test-cache test-result test-dcf lint pylint flake8 clean clean-reports clean-cache clean-logs clean-results clean-data clean-all help dcf dcf-all dcf-all-fast dcf-help pe pe-all pe-help web web-install docker-build docker-rebuild docker-up docker-down docker-logs docker-logs-follow docker-logs-gateway docker-logs-dcf docker-logs-stock docker-logs-frontend docker-restart docker-clean docker-clean-all docker-ps docker-exec-gateway docker-exec-dcf docker-exec-stock docker-exec-frontend docker-dev docker-dev-down docker-dev-logs docker-dev-restart backend-dev backend-gateway backend-dcf backend-stock get-version git-tag git-tag-patch git-tag-minor git-tag-major git-tag-from-commit
