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
	@echo "Note: Run 'make complete' separately for integration tests (requires external API access)"

# Run unit tests
ut:
	@echo "Running unit tests..."
	@$(MAKE) ut -C $(TEST_DIR)

# Run complete functionality test
complete:
	@echo "Running complete functionality test..."
	@$(MAKE) complete -C $(TEST_DIR)

# Run all tests (unit + complete)
all: ut complete

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

# Run DCF analysis for all VN30 stocks
dcf-all:
	@echo "Running DCF analysis for all VN30 stocks..."
	@$(PYTHON) run_all_dcf_main.py

# Show DCF analysis help
dcf-help:
	@echo "DCF Analysis Commands:"
	@echo ""
	@echo "  make dcf TICKER=<ticker>     - Run DCF analysis for a specific stock"
	@echo "  make dcf-all                 - Run DCF analysis for all VN30 stocks"
	@echo "  make dcf-help                - Show this help"
	@echo ""
	@echo "Examples:"
	@echo "  make dcf TICKER=VNM"
	@echo "  make dcf TICKER=VCB"
	@echo "  make dcf TICKER=FPT"
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
	@echo "  make dcf-all                 - Run DCF analysis for all VN30 stocks"
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
	@echo "  make help         - Show this help message"

.PHONY: test ut complete all test-config test-cache test-result test-dcf lint pylint flake8 clean clean-reports clean-cache clean-logs clean-results clean-data clean-all help dcf dcf-all dcf-help pe pe-all pe-help

