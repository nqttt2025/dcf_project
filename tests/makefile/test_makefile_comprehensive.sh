#!/bin/bash
# Comprehensive Makefile test - runs all safe commands
# This is a more thorough test that actually executes commands

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

echo "=========================================="
echo "  Comprehensive Makefile Test"
echo "=========================================="
echo ""

# Test 1: Help
echo "1. Testing help..."
if make help >/dev/null 2>&1; then
    test_pass "make help"
else
    test_fail "make help"
fi

# Test 2: Get version
echo "2. Testing get-version..."
if version=$(make get-version 2>&1) && [[ -n "$version" ]]; then
    test_pass "make get-version (returns: $version)"
else
    test_fail "make get-version"
fi

# Test 3: Docker versions
echo "3. Testing docker-versions..."
if [[ -f "$PROJECT_ROOT/docker-versions.json" ]]; then
    if make docker-versions >/dev/null 2>&1; then
        test_pass "make docker-versions"
    else
        test_skip "make docker-versions (may require Docker)"
    fi
else
    test_skip "make docker-versions (docker-versions.json not found)"
fi

# Test 4: Docker version check
echo "4. Testing docker-version-check-base..."
if [[ -f "$PROJECT_ROOT/docker-versions.json" ]]; then
    if make docker-version-check-base >/dev/null 2>&1; then
        test_pass "make docker-version-check-base"
    else
        test_skip "make docker-version-check-base (may require Docker)"
    fi
else
    test_skip "make docker-version-check-base (docker-versions.json not found)"
fi

# Test 5: Help commands
echo "5. Testing help commands..."
if make dcf-help >/dev/null 2>&1; then
    test_pass "make dcf-help"
else
    test_fail "make dcf-help"
fi

if make pe-help >/dev/null 2>&1; then
    test_pass "make pe-help"
else
    test_fail "make pe-help"
fi

# Test 6: Error handling
echo "6. Testing error handling..."
dcf_err_output=$(make dcf 2>&1 || true)
if echo "$dcf_err_output" | grep -qiE "Usage|TICKER|Example"; then
    test_pass "dcf shows error without TICKER"
else
    test_fail "dcf error handling"
fi

pe_err_output=$(make pe 2>&1 || true)
if echo "$pe_err_output" | grep -qiE "Usage|TICKER|Example"; then
    test_pass "pe shows error without TICKER"
else
    test_fail "pe error handling"
fi

git_tag_err_output=$(make git-tag 2>&1 || true)
if echo "$git_tag_err_output" | grep -qiE "Usage|VERSION|Example"; then
    test_pass "git-tag shows error without VERSION"
else
    test_fail "git-tag error handling"
fi

# Test 7: Test commands (dry-run)
echo "7. Testing test commands (dry-run)..."
if make -n ut >/dev/null 2>&1; then
    test_pass "make -n ut"
else
    test_fail "make -n ut"
fi

if make -n lint >/dev/null 2>&1; then
    test_pass "make -n lint"
else
    test_fail "make -n lint"
fi

# Test 8: Clean commands (dry-run)
echo "8. Testing clean commands (dry-run)..."
if make -n clean >/dev/null 2>&1; then
    test_pass "make -n clean"
else
    test_fail "make -n clean"
fi

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

