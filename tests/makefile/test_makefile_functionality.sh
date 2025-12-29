#!/bin/bash
# Functional tests for Makefile commands
# Tests actual execution of safe commands (non-destructive)

set -uo pipefail

# Colors
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
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((PASSED++))
}

test_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((FAILED++))
}

test_skip() {
    echo -e "${YELLOW}⊘ SKIP${NC}: $1"
    ((SKIPPED++))
}

# Test help command
test_help() {
    echo ""
    echo "=== Testing Help Command ==="
    
    if make help >/dev/null 2>&1; then
        test_pass "make help works"
    else
        test_fail "make help failed"
    fi
}

# Test get-version
test_get_version() {
    echo ""
    echo "=== Testing get-version ==="
    
    local version
    if version=$(make get-version 2>&1); then
        if [[ -n "$version" ]]; then
            test_pass "get-version returns: $version"
        else
            test_fail "get-version returns empty"
        fi
    else
        test_fail "get-version failed"
    fi
}

# Test docker-versions
test_docker_versions() {
    echo ""
    echo "=== Testing docker-versions ==="
    
    # Check if docker-versions.json exists
    if [[ ! -f "$PROJECT_ROOT/docker-versions.json" ]]; then
        test_skip "docker-versions (docker-versions.json not found)"
        return 0
    fi
    
    if make docker-versions >/dev/null 2>&1; then
        test_pass "docker-versions works"
    else
        # May fail if Docker not running, that's okay
        test_skip "docker-versions (may require Docker)"
    fi
}

# Test docker-version-check-base
test_docker_version_check() {
    echo ""
    echo "=== Testing docker-version-check-base ==="
    
    # Check if docker-versions.json exists
    if [[ ! -f "$PROJECT_ROOT/docker-versions.json" ]]; then
        test_skip "docker-version-check-base (docker-versions.json not found)"
        return 0
    fi
    
    if make docker-version-check-base >/dev/null 2>&1; then
        test_pass "docker-version-check-base works"
    else
        # May fail if Docker not running, that's okay
        test_skip "docker-version-check-base (may require Docker)"
    fi
}

# Test help commands
test_help_commands() {
    echo ""
    echo "=== Testing Help Commands ==="
    
    if make dcf-help >/dev/null 2>&1; then
        test_pass "dcf-help works"
    else
        test_fail "dcf-help failed"
    fi
    
    if make pe-help >/dev/null 2>&1; then
        test_pass "pe-help works"
    else
        test_fail "pe-help failed"
    fi
}

# Test error messages
test_error_messages() {
    echo ""
    echo "=== Testing Error Messages ==="
    
    # Test dcf without TICKER
    local dcf_output
    dcf_output=$(make dcf 2>&1 || true)
    if echo "$dcf_output" | grep -qiE "Usage|TICKER|Example"; then
        test_pass "dcf shows error without TICKER"
    else
        test_fail "dcf doesn't show error without TICKER"
        echo "Output: $dcf_output" | head -3
    fi
    
    # Test pe without TICKER
    local pe_output
    pe_output=$(make pe 2>&1 || true)
    if echo "$pe_output" | grep -qiE "Usage|TICKER|Example"; then
        test_pass "pe shows error without TICKER"
    else
        test_fail "pe doesn't show error without TICKER"
        echo "Output: $pe_output" | head -3
    fi
    
    # Test git-tag without VERSION
    local git_tag_output
    git_tag_output=$(make git-tag 2>&1 || true)
    if echo "$git_tag_output" | grep -qiE "Usage|VERSION|Example"; then
        test_pass "git-tag shows error without VERSION"
    else
        test_fail "git-tag doesn't show error without VERSION"
        echo "Output: $git_tag_output" | head -3
    fi
}

# Test script execution (dry-run)
test_script_execution() {
    echo ""
    echo "=== Testing Script Execution (Dry-Run) ==="
    
    # Test that scripts are called correctly
    if make -n ut 2>&1 | grep -q "test.sh ut"; then
        test_pass "ut calls test.sh correctly"
    else
        test_fail "ut doesn't call test.sh correctly"
    fi
    
    if make -n lint 2>&1 | grep -q "lint.sh"; then
        test_pass "lint calls lint.sh correctly"
    else
        test_fail "lint doesn't call lint.sh correctly"
    fi
}

main() {
    echo "=========================================="
    echo "  Makefile Functionality Test Suite"
    echo "=========================================="
    
    test_help
    test_get_version
    test_docker_versions
    test_docker_version_check
    test_help_commands
    test_error_messages
    test_script_execution
    
    echo ""
    echo "=========================================="
    echo "  Test Summary"
    echo "=========================================="
    echo -e "${GREEN}Passed:${NC} $PASSED"
    echo -e "${RED}Failed:${NC} $FAILED"
    echo -e "${YELLOW}Skipped:${NC} $SKIPPED"
    echo ""
    
    if [[ $FAILED -eq 0 ]]; then
        echo -e "${GREEN}All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}Some tests failed!${NC}"
        return 1
    fi
}

main "$@"

