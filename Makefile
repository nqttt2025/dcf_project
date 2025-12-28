# This Makefile will run common tasks for DCF Project
#	'make':             run all tests
#	'make test':        run all tests
#	'make ut':          run unit tests
#	'make complete':   run complete functionality test
#	'make clean':       remove unnecessary files generated from other tasks
#	'make lint':        run linters for our repository

PYTHON = python3
SHELL = bash
TEST_DIR = tests
REPORT_DIR = reports

# Default target: run all tests
.DEFAULT_GOAL := test

# Run all tests (unit tests only - complete test may require external APIs)
test: ut
	@echo "Unit tests completed"
	@echo "Note: Run 'make ft' for function tests, 'make st' for system tests, 'make complete' for integration tests"

# Run unit tests
ut:
	@echo "Running unit tests..."
	@$(MAKE) ut -C $(TEST_DIR)

# Run complete functionality test
complete:
	@echo "Running complete functionality test..."
	@$(MAKE) complete -C $(TEST_DIR)

# Run function tests
ft:
	@echo "Running function tests..."
	@$(MAKE) ft -C $(TEST_DIR)

# Run system tests
st:
	@echo "Running system tests..."
	@$(MAKE) st -C $(TEST_DIR)

# Run all tests (unit + function + system + complete)
all: ut ft st complete

# Run specific unit test
test-config:
	@$(MAKE) test-config -C $(TEST_DIR)

test-cache:
	@$(MAKE) test-cache -C $(TEST_DIR)

test-result:
	@$(MAKE) test-result -C $(TEST_DIR)

test-dcf:
	@$(MAKE) test-dcf -C $(TEST_DIR)

# Linters
PYTHON_LIB_PATH = src
PYTHON_CHECK_DIR = src tests
PYLINT_DIR = $(REPORT_DIR)/pylint
PYLINT_IGNORE_WARN = W1514,W1202,W0703,W0511,W0102,W0201,W1203,W0120
PYLINT_LEVEL = -E

# Run pylint
pylint: clean-reports
	@mkdir -p $(PYLINT_DIR)
	@$(PYTHON) -m pylint --version |& tee $(PYLINT_DIR)/pylint.log
	@env PYTHONPATH=$(subst $() $(),:,$(PYTHON_LIB_PATH)):$(PYTHONPATH) \
		$(PYTHON) -m pylint -v -j 0 $(PYLINT_LEVEL) $$(find $(PYTHON_CHECK_DIR) -type f -name "*.py") \
		|& tee -a $(PYLINT_DIR)/pylint.log
	@echo "Pylint log: $$(realpath $(PYLINT_DIR))/pylint.log"

# Run flake8 (if available)
flake8:
	@$(PYTHON) -m flake8 --version || echo "flake8 not installed, skipping..."
	@$(PYTHON) -m flake8 $(PYTHON_CHECK_DIR) --max-line-length=120 --ignore=E501,W503 || true

# Run all linters
lint: pylint flake8
	@echo "Linting completed"

# Clean up generated files
clean: clean-reports clean-cache clean-logs
	@echo "Cleanup completed"

clean-reports:
	@rm -rf $(REPORT_DIR)
	@rm -f test-pylint.log

clean-cache:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true

clean-logs:
	@find . -type f -name "*.log" -delete 2>/dev/null || true
	@rm -rf log/*.log 2>/dev/null || true

clean-results:
	@rm -rf data/results/*.json data/results/*.text 2>/dev/null || true

clean-data:
	@rm -rf data/cache/*.json 2>/dev/null || true

# Full clean (including data and results)
clean-all: clean clean-results clean-data
	@echo "Full cleanup completed"

# DCF Analysis Scripts
DCF_SCRIPT = run_dcf.py
CONFIG_DIR = config

# Run DCF analysis for a specific stock
dcf:
	@if [ -z "$(TICKER)" ]; then \
		echo "Usage: make dcf TICKER=<ticker>"; \
		echo "Example: make dcf TICKER=VNM"; \
		echo "         make dcf TICKER=VCB"; \
		echo ""; \
		echo "Available tickers: VNM, VCB, FPT, BID, VIC, VHM, VRE, ... (all VN30 stocks)"; \
		exit 1; \
	fi
	@if [ ! -f "$(CONFIG_DIR)/$(TICKER).cfg" ]; then \
		echo "Error: Config file not found: $(CONFIG_DIR)/$(TICKER).cfg"; \
		echo "Available config files:"; \
		ls -1 $(CONFIG_DIR)/*.cfg | sed 's|$(CONFIG_DIR)/||' | sed 's|\.cfg||' | tr '\n' ' ' && echo ""; \
		exit 1; \
	fi
	@echo "Running DCF analysis for $(TICKER)..."
	@$(PYTHON) $(DCF_SCRIPT) $(TICKER).cfg

# Run DCF analysis for all VN30 stocks (with retry & delay for API stability)
dcf-all:
	@echo "Running DCF analysis for all VN30 stocks (with retry & delay for API stability)..."
	@$(PYTHON) scripts/run_all_dcf_with_retry.py

# Run DCF analysis for all VN30 stocks (fast, no retry - use with caution)
dcf-all-fast:
	@echo "Running DCF analysis for all VN30 stocks (fast mode, no retry)..."
	@echo "Warning: This may fail due to API rate limiting. Use 'make dcf-all' for stable runs."
	@$(PYTHON) run_all_dcf_main.py

# Show DCF analysis help
dcf-help:
	@echo "DCF Analysis Commands:"
	@echo ""
	@echo "  make dcf TICKER=<ticker>     - Run DCF analysis for a specific stock"
	@echo "  make dcf-all                 - Run DCF analysis for all VN30 stocks (with retry & delay)"
	@echo "  make dcf-all-fast            - Run DCF analysis for all VN30 stocks (fast, no retry)"
	@echo "  make dcf-help                - Show this help"
	@echo ""
	@echo "Examples:"
	@echo "  make dcf TICKER=VNM"
	@echo "  make dcf TICKER=VCB"
	@echo "  make dcf TICKER=FPT"
	@echo "  make dcf-all                 # Recommended: includes retry & delay for API stability"
	@echo ""
	@echo "Note: 'make dcf-all' uses retry logic and delays to ensure API stability."
	@echo "      Use 'make dcf-all-fast' only if you need faster execution (may fail due to rate limits)."
	@echo ""
	@echo "Available tickers (VN30):"
	@ls -1 $(CONFIG_DIR)/*.cfg 2>/dev/null | sed 's|$(CONFIG_DIR)/||' | sed 's|\.cfg||' | sort | tr '\n' ' ' && echo ""

# PE Calculation Scripts
SCRIPT_DIR = scripts
PE_SCRIPT = $(SCRIPT_DIR)/calculate_pe.py

# Calculate PE for a specific ticker
pe:
	@if [ -z "$(TICKER)" ]; then \
		echo "Usage: make pe TICKER=<ticker> [INDUSTRY=<industry>]"; \
		echo "Example: make pe TICKER=VNM INDUSTRY=consumer"; \
		echo ""; \
		echo "Available industries: banking, real_estate, technology, consumer, energy, industrial, aviation"; \
		exit 1; \
	fi
	@echo "Calculating PE for $(TICKER)..."
	@$(PYTHON) $(PE_SCRIPT) $(TICKER) $(INDUSTRY) || true

# Analyze PE for all VN30 stocks
pe-all:
	@echo "Analyzing PE for all VN30 stocks..."
	@$(PYTHON) $(PE_SCRIPT)

# Show PE calculation help
pe-help:
	@echo "PE Calculation Commands:"
	@echo ""
	@echo "  make pe TICKER=<ticker>              - Calculate PE for a specific stock"
	@echo "  make pe TICKER=<ticker> INDUSTRY=<industry> - Calculate PE with industry suggestion"
	@echo "  make pe-all                          - Analyze all VN30 stocks"
	@echo "  make pe-help                         - Show this help"
	@echo ""
	@echo "Examples:"
	@echo "  make pe TICKER=VNM"
	@echo "  make pe TICKER=VCB INDUSTRY=banking"
	@echo "  make pe TICKER=FPT INDUSTRY=technology"
	@echo ""
	@echo "Available industries:"
	@echo "  - banking      (Ngân hàng)"
	@echo "  - real_estate  (Bất động sản)"
	@echo "  - technology   (Công nghệ)"
	@echo "  - consumer     (Tiêu dùng)"
	@echo "  - energy       (Năng lượng)"
	@echo "  - industrial   (Công nghiệp)"
	@echo "  - aviation     (Hàng không)"

# Help target
help:
	@echo "DCF Project Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make              - Run all tests (default)"
	@echo "  make test         - Run all tests"
	@echo "  make ut           - Run unit tests only"
	@echo "  make complete     - Run complete functionality test"
	@echo "  make all          - Run all tests (unit + complete)"
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
	@echo "  make help         - Show this help message"

# Web Service
WEB_DIR = web
WEB_APP = $(WEB_DIR)/app.py

# Run web service (development)
web:
	@echo "Starting DCF Web Service (Development)..."
	@echo "Open http://localhost:5000 in your browser"
	@cd $(WEB_DIR) && $(PYTHON) app.py

web-install:
	@echo "Installing web service dependencies..."
	@$(PYTHON) -m pip install -r $(WEB_DIR)/requirements.txt

# Docker Commands (Microservices Architecture)
DOCKER_LOG_DIR = logs/docker
DOCKER_IMAGE_PREFIX = dcf-project

# Get version from git tag or generate one
get-version:
	@./scripts/get_version.sh

# Docker image names
DOCKER_IMAGES = gateway dcf stock frontend

docker-build:
	@mkdir -p $(DOCKER_LOG_DIR)
	@VERSION=$$(./scripts/get_version.sh); \
	LOG_FILE="$(DOCKER_LOG_DIR)/docker-build-$$(date +%Y%m%d-%H%M%S).log"; \
	echo "Building Docker images for microservices..." | tee -a $$LOG_FILE; \
	echo "Version: $$VERSION" | tee -a $$LOG_FILE; \
	echo "Log file: $$LOG_FILE" | tee -a $$LOG_FILE; \
	echo "Timestamp: $$(date '+%Y-%m-%d %H:%M:%S')" | tee -a $$LOG_FILE; \
	echo "========================================" | tee -a $$LOG_FILE; \
	echo "Removing old versioned images..." | tee -a $$LOG_FILE; \
	for img in $(DOCKER_IMAGES); do \
		docker images --format "{{.Repository}}:{{.Tag}}" | grep "^$(DOCKER_IMAGE_PREFIX)-$$img:" | grep -v "$$VERSION" | xargs -r docker rmi -f 2>&1 | tee -a $$LOG_FILE || true; \
	done; \
	echo "Building images with tag: $$VERSION" | tee -a $$LOG_FILE; \
	VERSION=$$VERSION docker-compose build 2>&1 | tee -a $$LOG_FILE; \
	BUILD_EXIT=$$?; \
	if [ $$BUILD_EXIT -eq 0 ]; then \
		echo "Tagging images with version $$VERSION..." | tee -a $$LOG_FILE; \
		for img in $(DOCKER_IMAGES); do \
			IMAGE_NAME="$(DOCKER_IMAGE_PREFIX)-$$img"; \
			if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^$$IMAGE_NAME:latest"; then \
				docker tag $$IMAGE_NAME:latest $$IMAGE_NAME:$$VERSION 2>&1 | tee -a $$LOG_FILE || true; \
			fi; \
		done; \
	fi; \
	echo "" | tee -a $$LOG_FILE; \
	echo "Cleaning up unused images and containers..." | tee -a $$LOG_FILE; \
	docker-compose down --remove-orphans 2>&1 | tee -a $$LOG_FILE || true; \
	docker image prune -f --filter "dangling=true" 2>&1 | tee -a $$LOG_FILE || true; \
	echo "✓ Build completed and cleanup done" | tee -a $$LOG_FILE; \
	echo "Version: $$VERSION" | tee -a $$LOG_FILE; \
	echo "Log saved to: $$LOG_FILE" | tee -a $$LOG_FILE; \
	exit $$BUILD_EXIT

# Build with auto-tagging (creates tag automatically if not exists)
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
	@mkdir -p $(DOCKER_LOG_DIR)
	@VERSION=$$(./scripts/get_version.sh); \
	LOG_FILE="$(DOCKER_LOG_DIR)/docker-rebuild-$$(date +%Y%m%d-%H%M%S).log"; \
	echo "Rebuilding Docker images (with cleanup)..." | tee -a $$LOG_FILE; \
	echo "Version: $$VERSION" | tee -a $$LOG_FILE; \
	echo "Log file: $$LOG_FILE" | tee -a $$LOG_FILE; \
	echo "Timestamp: $$(date '+%Y-%m-%d %H:%M:%S')" | tee -a $$LOG_FILE; \
	echo "========================================" | tee -a $$LOG_FILE; \
	echo "Stopping containers..." | tee -a $$LOG_FILE; \
	docker-compose down --remove-orphans 2>&1 | tee -a $$LOG_FILE || true; \
	echo "Removing old containers..." | tee -a $$LOG_FILE; \
	docker-compose rm -f 2>&1 | tee -a $$LOG_FILE || true; \
	echo "Removing old versioned images..." | tee -a $$LOG_FILE; \
	for img in $(DOCKER_IMAGES); do \
		docker images --format "{{.Repository}}:{{.Tag}}" | grep "^$(DOCKER_IMAGE_PREFIX)-$$img:" | xargs -r docker rmi -f 2>&1 | tee -a $$LOG_FILE || true; \
	done; \
	echo "Cleaning up unused images..." | tee -a $$LOG_FILE; \
	docker image prune -f --filter "dangling=true" 2>&1 | tee -a $$LOG_FILE || true; \
	echo "Building new images (--no-cache) with tag: $$VERSION..." | tee -a $$LOG_FILE; \
	VERSION=$$VERSION docker-compose build --no-cache 2>&1 | tee -a $$LOG_FILE; \
	BUILD_EXIT=$$?; \
	if [ $$BUILD_EXIT -eq 0 ]; then \
		echo "Tagging images with version $$VERSION..." | tee -a $$LOG_FILE; \
		for img in $(DOCKER_IMAGES); do \
			IMAGE_NAME="$(DOCKER_IMAGE_PREFIX)-$$img"; \
			if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^$$IMAGE_NAME:latest"; then \
				docker tag $$IMAGE_NAME:latest $$IMAGE_NAME:$$VERSION 2>&1 | tee -a $$LOG_FILE || true; \
			fi; \
		done; \
	fi; \
	echo "✓ Rebuild completed" | tee -a $$LOG_FILE; \
	echo "Version: $$VERSION" | tee -a $$LOG_FILE; \
	echo "Log saved to: $$LOG_FILE" | tee -a $$LOG_FILE; \
	exit $$BUILD_EXIT

# Rebuild with auto-tagging (creates tag automatically)
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
	@echo "Starting Docker microservices..."
	@docker-compose up -d
	@echo ""
	@echo "Microservices started:"
	@echo "  - Frontend: http://localhost:8080"
	@echo "  - Gateway: http://localhost:8000"
	@echo "  - DCF Service: http://localhost:8001"
	@echo "  - Stock Service: http://localhost:8002"
	@echo ""
	@echo "View logs: make docker-logs"
	@echo "Stop: make docker-down"

docker-down:
	@echo "Stopping Docker containers..."
	@docker-compose down

# Git tag management
git-tag:
	@if [ -z "$(VERSION)" ]; then \
		echo "Usage: make git-tag VERSION=v1.0.0"; \
		echo "Example: make git-tag VERSION=v1.0.0"; \
		exit 1; \
	fi
	@./scripts/create_git_tag.sh $(VERSION)

# Auto versioning - automatically increments version
git-tag-auto:
	@echo "Auto-incrementing version..."
	@VERSION=$$(./scripts/auto_version.sh patch); \
	echo "Created tag: $$VERSION"; \
	echo "To push: git push origin $$VERSION"

git-tag-patch:
	@echo "Incrementing patch version..."
	@VERSION=$$(./scripts/auto_version.sh patch); \
	echo "Created tag: $$VERSION"; \
	echo "To push: git push origin $$VERSION"

git-tag-minor:
	@echo "Incrementing minor version..."
	@VERSION=$$(./scripts/auto_version.sh minor); \
	echo "Created tag: $$VERSION"; \
	echo "To push: git push origin $$VERSION"

git-tag-major:
	@echo "Incrementing major version..."
	@VERSION=$$(./scripts/auto_version.sh major); \
	echo "Created tag: $$VERSION"; \
	echo "To push: git push origin $$VERSION"

# Auto tag from commit message
git-tag-from-commit:
	@echo "Creating tag from commit message..."
	@VERSION=$$(./scripts/auto_tag_from_commit.sh); \
	echo "Created tag: $$VERSION"; \
	echo "To push: git push origin $$VERSION"

# List Docker images with versions
docker-images:
	@echo "Docker Images:"
	@echo "=============="
	@for img in $(DOCKER_IMAGES); do \
		echo ""; \
		echo "$$img:"; \
		docker images --format "  {{.Repository}}:{{.Tag}} ({{.Size}}, {{.CreatedAt}})" | grep "^$(DOCKER_IMAGE_PREFIX)-$$img:" | head -10; \
	done

# Remove old Docker images (keep last N versions)
docker-clean-old:
	@if [ -z "$(KEEP)" ]; then \
		echo "Usage: make docker-clean-old KEEP=3"; \
		echo "Keeps last 3 versions of each image"; \
		exit 1; \
	fi
	@echo "Removing old Docker images (keeping last $(KEEP) versions)..."
	@for img in $(DOCKER_IMAGES); do \
		echo "Processing $$img..."; \
		docker images --format "{{.Repository}}:{{.Tag}} {{.CreatedAt}}" | grep "^$(DOCKER_IMAGE_PREFIX)-$$img:" | \
		sort -k2 -r | tail -n +$$((KEEP + 1)) | awk '{print $$1}' | \
		xargs -r docker rmi -f || true; \
	done
	@echo "✓ Cleanup completed"

docker-logs:
	@mkdir -p $(DOCKER_LOG_DIR)
	@LOG_FILE="$(DOCKER_LOG_DIR)/docker-logs-$$(date +%Y%m%d-%H%M%S).log"; \
	echo "Saving container logs to: $$LOG_FILE" | tee -a $$LOG_FILE; \
	echo "Timestamp: $$(date '+%Y-%m-%d %H:%M:%S')" | tee -a $$LOG_FILE; \
	echo "========================================" | tee -a $$LOG_FILE; \
	docker-compose logs --tail=100 2>&1 | tee -a $$LOG_FILE; \
	echo "" | tee -a $$LOG_FILE; \
	echo "Log saved to: $$LOG_FILE" | tee -a $$LOG_FILE

docker-logs-follow:
	@docker-compose logs -f

docker-logs-gateway:
	@docker-compose logs -f gateway

docker-logs-dcf:
	@docker-compose logs -f dcf

docker-logs-stock:
	@docker-compose logs -f stock

docker-logs-frontend:
	@docker-compose logs -f frontend

docker-restart:
	@echo "Restarting Docker containers..."
	@docker-compose restart

docker-clean:
	@mkdir -p $(DOCKER_LOG_DIR)
	@LOG_FILE="$(DOCKER_LOG_DIR)/docker-clean-$$(date +%Y%m%d-%H%M%S).log"; \
	echo "Cleaning Docker containers and images..." | tee -a $$LOG_FILE; \
	echo "Log file: $$LOG_FILE" | tee -a $$LOG_FILE; \
	echo "Timestamp: $$(date '+%Y-%m-%d %H:%M:%S')" | tee -a $$LOG_FILE; \
	echo "========================================" | tee -a $$LOG_FILE; \
	docker-compose down -v --remove-orphans 2>&1 | tee -a $$LOG_FILE; \
	echo "Removing unused images..." | tee -a $$LOG_FILE; \
	docker image prune -f --filter "dangling=true" 2>&1 | tee -a $$LOG_FILE; \
	echo "Removing unused containers..." | tee -a $$LOG_FILE; \
	docker container prune -f 2>&1 | tee -a $$LOG_FILE; \
	echo "✓ Cleanup completed" | tee -a $$LOG_FILE; \
	echo "Log saved to: $$LOG_FILE" | tee -a $$LOG_FILE

docker-clean-all:
	@mkdir -p $(DOCKER_LOG_DIR)
	@LOG_FILE="$(DOCKER_LOG_DIR)/docker-clean-all-$$(date +%Y%m%d-%H%M%S).log"; \
	echo "Deep cleaning Docker (removes all unused resources)..." | tee -a $$LOG_FILE; \
	echo "Log file: $$LOG_FILE" | tee -a $$LOG_FILE; \
	echo "Timestamp: $$(date '+%Y-%m-%d %H:%M:%S')" | tee -a $$LOG_FILE; \
	echo "========================================" | tee -a $$LOG_FILE; \
	docker-compose down -v --remove-orphans 2>&1 | tee -a $$LOG_FILE; \
	echo "Removing all unused images (not just dangling)..." | tee -a $$LOG_FILE; \
	docker image prune -af 2>&1 | tee -a $$LOG_FILE; \
	echo "Removing all unused containers..." | tee -a $$LOG_FILE; \
	docker container prune -f 2>&1 | tee -a $$LOG_FILE; \
	echo "Removing unused networks..." | tee -a $$LOG_FILE; \
	docker network prune -f 2>&1 | tee -a $$LOG_FILE; \
	echo "Removing unused volumes..." | tee -a $$LOG_FILE; \
	docker volume prune -f 2>&1 | tee -a $$LOG_FILE; \
	echo "✓ Deep cleanup completed" | tee -a $$LOG_FILE; \
	echo "Log saved to: $$LOG_FILE" | tee -a $$LOG_FILE

docker-ps:
	@docker-compose ps

docker-exec-gateway:
	@docker-compose exec gateway /bin/bash

docker-exec-dcf:
	@docker-compose exec dcf /bin/bash

docker-exec-stock:
	@docker-compose exec stock /bin/bash

docker-exec-frontend:
	@docker-compose exec frontend /bin/sh

.PHONY: test ut complete all test-config test-cache test-result test-dcf lint pylint flake8 clean clean-reports clean-cache clean-logs clean-results clean-data clean-all help dcf dcf-all dcf-all-fast dcf-help pe pe-all pe-help web web-install docker-build docker-rebuild docker-up docker-down docker-logs docker-logs-follow docker-logs-gateway docker-logs-dcf docker-logs-stock docker-logs-frontend docker-restart docker-clean docker-clean-all docker-ps docker-exec-gateway docker-exec-dcf docker-exec-stock docker-exec-frontend

