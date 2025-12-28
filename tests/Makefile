SHELL = bash

# Default target: run all tests
test: ut

# Run unit tests
ut:
	@echo "Running unit tests for DCF Project"
	@python3 ut/run_ut

# Run integration/complete test
complete:
	@echo "Running complete DCF functionality test"
	@cd .. && PYTHONPATH=src:$$PYTHONPATH python3 tests/test_dcf_complete.py || echo "Complete test failed (may require external API access)"

# Run all tests (unit + complete)
all: ut complete

# Run a specific unit test file
test-config:
	@echo "Running ConfigManager tests"
	@python3 -m unittest tests.ut.test_config_manager -v

test-cache:
	@echo "Running CacheManager tests"
	@python3 -m unittest tests.ut.test_cache_manager -v

test-result:
	@echo "Running ResultManager tests"
	@python3 -m unittest tests.ut.test_result_manager -v

test-dcf:
	@echo "Running DCFCalculator tests"
	@python3 -m unittest tests.ut.test_dcf_calculator -v

# Linting
PYTHON = python3
PYLINT_IGNORE_WARN = W1514,W1202,W0703,W0511,W0102,W0201,W1203,W0120
PYLINT_LEVEL = -E
PYTHON_LIB_PATH = ../src

pylint:
	@$(PYTHON) -m pylint --version
	@env PYTHONPATH=$(subst $() $(),:,$(PYTHON_LIB_PATH)):$(PYTHONPATH) \
		$(PYTHON) -m pylint -v -j 0 $(PYLINT_LEVEL) $$(find . -type f -name "*.py") \
		|& tee -a test-pylint.log

.PHONY: ut complete all test test-config test-cache test-result test-dcf pylint

