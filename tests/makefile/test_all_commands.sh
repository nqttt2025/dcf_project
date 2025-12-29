#!/bin/bash
# Test all Makefile commands systematically
# This script tests every command in the Makefile

set -uo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0
SKIPPED=0

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

test_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

test_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

test_skip() {
    echo -e "${YELLOW}⊘${NC} $1"
    ((SKIPPED++))
}

test_command() {
    local cmd="$1"
    local description="${2:-$cmd}"
    
    if make -n "$cmd" >/dev/null 2>&1; then
        test_pass "$description"
        return 0
    else
        test_fail "$description"
        return 1
    fi
}

echo "=========================================="
echo "  Testing All Makefile Commands"
echo "=========================================="
echo ""

# Test commands
echo "=== Test Commands ==="
test_command "test" "test"
test_command "ut" "ut"
test_command "ft" "ft"
test_command "st" "st"
test_command "complete" "complete"
test_command "all" "all"
test_command "test-config" "test-config"
test_command "test-cache" "test-cache"
test_command "test-result" "test-result"
test_command "test-dcf" "test-dcf"
test_command "test-scripts" "test-scripts"
test_command "test-scripts-bash" "test-scripts-bash"
test_command "test-scripts-python" "test-scripts-python"
test_command "test-makefile" "test-makefile"
test_command "test-makefile-commands" "test-makefile-commands"
test_command "test-makefile-functionality" "test-makefile-functionality"

# Analysis commands
echo ""
echo "=== Analysis Commands ==="
test_command "dcf-help" "dcf-help"
test_command "pe-help" "pe-help"
test_skip "dcf (requires TICKER)"
test_skip "pe (requires TICKER)"
test_command "dcf-all" "dcf-all"
test_command "dcf-all-fast" "dcf-all-fast"
test_command "pe-all" "pe-all"

# Lint commands
echo ""
echo "=== Lint Commands ==="
test_command "lint" "lint"
test_command "pylint" "pylint"
test_command "flake8" "flake8"

# Clean commands
echo ""
echo "=== Clean Commands ==="
test_command "clean" "clean"
test_command "clean-reports" "clean-reports"
test_command "clean-cache" "clean-cache"
test_command "clean-logs" "clean-logs"
test_command "clean-results" "clean-results"
test_command "clean-data" "clean-data"
test_command "clean-all" "clean-all"

# Web commands
echo ""
echo "=== Web Commands ==="
test_command "web-install" "web-install"
test_skip "web (starts server)"

# Docker commands (dry-run only)
echo ""
echo "=== Docker Commands (Dry-Run) ==="
test_command "docker-versions" "docker-versions"
test_command "docker-version-check-base" "docker-version-check-base"
test_command "docker-ps" "docker-ps"
test_command "docker-images" "docker-images"
test_skip "docker-build (takes too long)"
test_skip "docker-build-fast (takes too long)"
test_skip "docker-build-base (takes too long)"
test_skip "docker-build-base-no-cache (takes too long)"
test_skip "docker-build-auto (takes too long)"
test_skip "docker-rebuild (takes too long)"
test_skip "docker-rebuild-auto (takes too long)"
test_skip "docker-up (requires Docker)"
test_skip "docker-down (requires Docker)"
test_skip "docker-logs (requires Docker)"
test_skip "docker-restart (requires Docker)"
test_skip "docker-clean (requires Docker)"
test_skip "docker-clean-all (requires Docker)"
test_skip "docker-dev (requires Docker)"
test_skip "docker-dev-down (requires Docker)"
test_skip "docker-dev-logs (requires Docker)"
test_skip "docker-dev-restart (requires Docker)"

# Backend commands
echo ""
echo "=== Backend Commands ==="
test_command "backend-dev" "backend-dev"
test_skip "backend-gateway (starts server)"
test_skip "backend-dcf (starts server)"
test_skip "backend-stock (starts server)"

# Version commands
echo ""
echo "=== Version Commands ==="
test_command "get-version" "get-version"
test_skip "git-tag (requires VERSION)"
test_command "git-tag-patch" "git-tag-patch"
test_command "git-tag-minor" "git-tag-minor"
test_command "git-tag-major" "git-tag-major"
test_command "git-tag-from-commit" "git-tag-from-commit"

# Help
echo ""
echo "=== Help Command ==="
test_command "help" "help"

# Summary
echo ""
echo "=========================================="
echo "  Summary"
echo "=========================================="
echo -e "${GREEN}Passed:${NC} $PASSED"
echo -e "${RED}Failed:${NC} $FAILED"
echo -e "${YELLOW}Skipped:${NC} $SKIPPED"
echo ""

if [[ $FAILED -eq 0 ]]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi

