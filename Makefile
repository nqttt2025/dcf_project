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

# Run all tests
test: ut complete
	@echo "All tests completed"

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
	@rm -rf results/*.json results/*.text 2>/dev/null || true
	@rm -rf data/results/*.json data/results/*.text 2>/dev/null || true

clean-data:
	@rm -rf data/cache/*.json 2>/dev/null || true

# Full clean (including data and results)
clean-all: clean clean-results clean-data
	@echo "Full cleanup completed"

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
	@echo "  make lint         - Run all linters"
	@echo "  make pylint       - Run pylint"
	@echo "  make flake8       - Run flake8"
	@echo ""
	@echo "  make clean        - Clean generated files"
	@echo "  make clean-all    - Clean everything including data"
	@echo "  make help         - Show this help message"

.PHONY: test ut complete all test-config test-cache test-result test-dcf lint pylint flake8 clean clean-reports clean-cache clean-logs clean-results clean-data clean-all help

