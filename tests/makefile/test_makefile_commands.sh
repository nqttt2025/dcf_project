#!/bin/bash
# Test suite for Makefile commands
# Tests all Makefile targets for syntax, existence, and basic functionality
# Ensures no duplicate functionality

set -uo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0
SKIPPED=0
WARNINGS=0

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

# Source test utilities
if [[ -f "$PROJECT_ROOT/scripts/lib/common.sh" ]]; then
    source "$PROJECT_ROOT/scripts/lib/common.sh" || true
fi

# Test helper functions
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

test_warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $1"
    ((WARNINGS++))
}

# Test Makefile syntax
test_makefile_syntax() {
    echo ""
    echo "=== Testing Makefile Syntax ==="
    
    if make -n -f Makefile help >/dev/null 2>&1; then
        test_pass "Makefile syntax is valid"
        return 0
    else
        test_fail "Makefile syntax error"
        make -n -f Makefile help 2>&1 || true
        return 1
    fi
}

# Test target exists and can be called
test_target_exists() {
    local target="$1"
    local description="${2:-$target}"
    
    if make -n "$target" >/dev/null 2>&1; then
        test_pass "Target exists: $description"
        return 0
    else
        test_fail "Target missing or invalid: $description"
        return 1
    fi
}

# Test target runs without error (dry-run)
test_target_dry_run() {
    local target="$1"
    local description="${2:-$target}"
    
    if make -n "$target" >/dev/null 2>&1; then
        test_pass "Target dry-run OK: $description"
        return 0
    else
        test_fail "Target dry-run failed: $description"
        return 1
    fi
}

# Test help command
test_help_command() {
    echo ""
    echo "=== Testing Help Command ==="
    
    if make help >/dev/null 2>&1; then
        test_pass "Help command works"
        return 0
    else
        test_fail "Help command failed"
        return 1
    fi
}

# Test version commands
test_version_commands() {
    echo ""
    echo "=== Testing Version Commands ==="
    
    # get-version
    if make -n get-version >/dev/null 2>&1; then
        test_pass "get-version target exists"
    else
        test_fail "get-version target missing"
    fi
    
    # git-tag (requires VERSION)
    if make -n git-tag VERSION=v99.99.99 >/dev/null 2>&1; then
        test_pass "git-tag target exists"
    else
        test_fail "git-tag target missing"
    fi
    
    # git-tag-patch
    test_target_exists "git-tag-patch" "git-tag-patch"
    
    # git-tag-minor
    test_target_exists "git-tag-minor" "git-tag-minor"
    
    # git-tag-major
    test_target_exists "git-tag-major" "git-tag-major"
}

# Test test commands
test_test_commands() {
    echo ""
    echo "=== Testing Test Commands ==="
    
    local test_targets=(
        "test"
        "ut"
        "ft"
        "st"
        "complete"
        "all"
        "test-config"
        "test-cache"
        "test-result"
        "test-dcf"
        "test-scripts"
        "test-scripts-bash"
        "test-scripts-python"
    )
    
    for target in "${test_targets[@]}"; do
        test_target_exists "$target" "test: $target"
    done
}

# Test analysis commands
test_analysis_commands() {
    echo ""
    echo "=== Testing Analysis Commands ==="
    
    # DCF commands
    test_target_exists "dcf-help" "dcf-help"
    
    # PE commands
    test_target_exists "pe-help" "pe-help"
    
    # Note: dcf and pe require TICKER, so we skip actual execution
    if make -n dcf TICKER=TEST >/dev/null 2>&1; then
        test_pass "dcf target exists (with TICKER)"
    else
        test_fail "dcf target missing or invalid"
    fi
    
    if make -n pe TICKER=TEST >/dev/null 2>&1; then
        test_pass "pe target exists (with TICKER)"
    else
        test_fail "pe target missing or invalid"
    fi
}

# Test lint commands
test_lint_commands() {
    echo ""
    echo "=== Testing Lint Commands ==="
    
    test_target_exists "lint" "lint"
    test_target_exists "pylint" "pylint"
    test_target_exists "flake8" "flake8"
}

# Test clean commands
test_clean_commands() {
    echo ""
    echo "=== Testing Clean Commands ==="
    
    local clean_targets=(
        "clean"
        "clean-reports"
        "clean-cache"
        "clean-logs"
        "clean-results"
        "clean-data"
        "clean-all"
    )
    
    for target in "${clean_targets[@]}"; do
        test_target_exists "$target" "clean: $target"
    done
}

# Test Docker commands (dry-run only)
test_docker_commands() {
    echo ""
    echo "=== Testing Docker Commands (Dry-Run) ==="
    
    local docker_targets=(
        "docker-versions"
        "docker-version-check-base"
        "docker-ps"
        "docker-images"
        "docker-down"  # Safe to test
    )
    
    for target in "${docker_targets[@]}"; do
        if make -n "$target" >/dev/null 2>&1; then
            test_pass "docker: $target (dry-run OK)"
        else
            test_fail "docker: $target (dry-run failed)"
        fi
    done
    
    # Commands that require parameters
    if make -n docker-clean-old KEEP=3 >/dev/null 2>&1; then
        test_pass "docker-clean-old (with KEEP)"
    else
        test_fail "docker-clean-old (with KEEP)"
    fi
    
    # Skip actual build/up commands (they take too long)
    test_skip "docker-build (skipped - takes too long)"
    test_skip "docker-up (skipped - requires Docker)"
    test_skip "docker-rebuild (skipped - takes too long)"
}

# Test web commands
test_web_commands() {
    echo ""
    echo "=== Testing Web Commands ==="
    
    test_target_exists "web-install" "web-install"
    test_skip "web (skipped - starts server)"
}

# Test backend commands
test_backend_commands() {
    echo ""
    echo "=== Testing Backend Commands ==="
    
    test_target_exists "backend-dev" "backend-dev"
    test_skip "backend-gateway (skipped - starts server)"
    test_skip "backend-dcf (skipped - starts server)"
    test_skip "backend-stock (skipped - starts server)"
}

# Check for duplicate functionality
check_duplicates() {
    echo ""
    echo "=== Checking for Duplicate Functionality ==="
    
    local duplicates_found=0
    
    # Check if test and ut do the same thing
    # test calls ut, which is correct delegation (not duplicate)
    local test_output
    local ut_output
    test_output=$(make -n test 2>&1 | grep -v "^echo" | head -1)
    ut_output=$(make -n ut 2>&1 | head -1)
    
    if [[ "$test_output" == "$ut_output" ]]; then
        test_warn "test and ut targets may be redundant (both run ut)"
        ((duplicates_found++))
    else
        # test calls ut, which is fine
        test_pass "test delegates to ut (correct pattern)"
    fi
    
    # Check docker-build vs docker-rebuild
    # They should be different (rebuild should clean first)
    local build_output rebuild_output
    build_output=$(make -n docker-build 2>&1 | head -1)
    rebuild_output=$(make -n docker-rebuild 2>&1 | head -1)
    if [[ "$build_output" == "$rebuild_output" ]]; then
        test_warn "docker-build and docker-rebuild may be duplicates"
        ((duplicates_found++))
    else
        test_pass "docker-build vs docker-rebuild (different functionality)"
    fi
    
    # Check clean vs clean-all
    # clean-all should include clean, which is correct hierarchy
    local clean_output clean_all_output
    clean_output=$(make -n clean 2>&1 | grep "clean.sh" | wc -l)
    clean_all_output=$(make -n clean-all 2>&1 | grep "clean.sh" | wc -l)
    if [[ $clean_all_output -gt $clean_output ]]; then
        test_pass "clean-all includes clean (correct hierarchy)"
    else
        test_warn "clean-all may not include clean"
        ((duplicates_found++))
    fi
    
    if [[ $duplicates_found -eq 0 ]]; then
        test_pass "No duplicate functionality found"
    else
        test_warn "Found $duplicates_found potential duplicate(s)"
    fi
}

# Test script paths exist
test_script_paths() {
    echo ""
    echo "=== Testing Script Paths ==="
    
    local script_paths=(
        "scripts/dev/test.sh"
        "scripts/dev/lint.sh"
        "scripts/dev/clean.sh"
        "scripts/analysis/dcf.sh"
        "scripts/analysis/pe.sh"
        "scripts/utils/get_version.sh"
        "scripts/git.sh"
        "scripts/docker.sh"
        "scripts/version/docker_version.sh"
        "scripts/docker/build_base.sh"
    )
    
    for script in "${script_paths[@]}"; do
        if [[ -f "$PROJECT_ROOT/$script" ]]; then
            test_pass "Script exists: $script"
        else
            test_fail "Script missing: $script"
        fi
    done
}

# Test error handling
test_error_handling() {
    echo ""
    echo "=== Testing Error Handling ==="
    
    # Test dcf without TICKER
    if make -n dcf 2>&1 | grep -q "Usage\|TICKER"; then
        test_pass "dcf shows usage when TICKER missing"
    else
        test_fail "dcf doesn't show usage when TICKER missing"
    fi
    
    # Test pe without TICKER
    if make -n pe 2>&1 | grep -q "Usage\|TICKER"; then
        test_pass "pe shows usage when TICKER missing"
    else
        test_fail "pe doesn't show usage when TICKER missing"
    fi
    
    # Test git-tag without VERSION
    if make -n git-tag 2>&1 | grep -q "Usage\|VERSION"; then
        test_pass "git-tag shows usage when VERSION missing"
    else
        test_fail "git-tag doesn't show usage when VERSION missing"
    fi
    
    # Test docker-clean-old without KEEP
    if make -n docker-clean-old 2>&1 | grep -q "Usage\|KEEP"; then
        test_pass "docker-clean-old shows usage when KEEP missing"
    else
        test_fail "docker-clean-old doesn't show usage when KEEP missing"
    fi
}

# Main test runner
main() {
    echo "=========================================="
    echo "  Makefile Commands Test Suite"
    echo "=========================================="
    
    test_makefile_syntax
    test_help_command
    test_version_commands
    test_test_commands
    test_analysis_commands
    test_lint_commands
    test_clean_commands
    test_docker_commands
    test_web_commands
    test_backend_commands
    test_script_paths
    test_error_handling
    check_duplicates
    
    echo ""
    echo "=========================================="
    echo "  Test Summary"
    echo "=========================================="
    echo -e "${GREEN}Passed:${NC} $PASSED"
    echo -e "${RED}Failed:${NC} $FAILED"
    echo -e "${YELLOW}Skipped:${NC} $SKIPPED"
    echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
    echo ""
    
    if [[ $FAILED -eq 0 ]]; then
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}Some tests failed!${NC}"
        exit 1
    fi
}

# Run tests
main "$@"

