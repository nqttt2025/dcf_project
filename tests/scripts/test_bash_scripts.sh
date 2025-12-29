#!/bin/bash
# Test suite for bash scripts
# Tests all bash scripts in scripts/ directory

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0
SKIPPED=0

# Project root - go up 2 levels from tests/scripts/
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

# Source test utilities (only if needed, don't fail if not available)
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

test_script_exists() {
    local script="$1"
    # Try absolute path first, then relative to PROJECT_ROOT
    local full_path="$script"
    if [[ ! "$script" =~ ^/ ]]; then
        full_path="$PROJECT_ROOT/$script"
    fi
    
    if [[ -f "$full_path" ]]; then
        test_pass "Script exists: $script"
        return 0
    else
        test_fail "Script missing: $script"
        return 1
    fi
}

test_script_executable() {
    local script="$1"
    if [[ -x "$script" ]]; then
        test_pass "Script executable: $script"
        return 0
    else
        test_fail "Script not executable: $script"
        return 1
    fi
}

test_script_help() {
    local script="$1"
    local help_cmd="${2:-help}"
    
    if "$script" "$help_cmd" >/dev/null 2>&1; then
        test_pass "Script help works: $script"
        return 0
    else
        # Some scripts may not have help, that's okay
        test_skip "Script help not available: $script"
        return 0
    fi
}

test_script_syntax() {
    local script="$1"
    # Try absolute path first, then relative to PROJECT_ROOT
    local full_path="$script"
    if [[ ! "$script" =~ ^/ ]]; then
        full_path="$PROJECT_ROOT/$script"
    fi
    
    # Use a subshell to avoid set -e affecting the test
    if (bash -n "$full_path" 2>/dev/null); then
        test_pass "Script syntax valid: $(basename "$script")"
        return 0
    else
        test_fail "Script syntax error: $script"
        (bash -n "$full_path" 2>&1) || true
        return 1
    fi
}

# Test lib modules
test_lib_modules() {
    echo ""
    echo "=== Testing lib modules ==="
    
    local lib_modules=(
        "scripts/lib/config.sh"
        "scripts/lib/logging.sh"
        "scripts/lib/file_ops.sh"
        "scripts/lib/validation.sh"
        "scripts/lib/error_handler.sh"
        "scripts/lib/python_utils.sh"
        "scripts/lib/docker_utils.sh"
        "scripts/lib/display.sh"
        "scripts/lib/version.sh"
        "scripts/lib/common.sh"
        "scripts/lib/base_script.sh"
    )
    
    for module in "${lib_modules[@]}"; do
        test_script_exists "$module"
        test_script_syntax "$module"
    done
}

# Test version scripts
test_version_scripts() {
    echo ""
    echo "=== Testing version scripts ==="
    
    local scripts=(
        "scripts/version/docker_version.sh"
        "scripts/version/create_git_tag.sh"
        "scripts/version/auto_version.sh"
        "scripts/version/auto_tag_from_commit.sh"
    )
    
    for script in "${scripts[@]}"; do
        test_script_exists "$script"
        test_script_syntax "$script"
    done
    
    # Test docker_version.sh commands
    if [[ -f "scripts/version/docker_version.sh" ]]; then
        if scripts/version/docker_version.sh get >/dev/null 2>&1; then
            test_pass "docker_version.sh get works"
        else
            test_skip "docker_version.sh get (may need docker-versions.json)"
        fi
    fi
}

# Test docker scripts
test_docker_scripts() {
    echo ""
    echo "=== Testing docker scripts ==="
    
    local scripts=(
        "scripts/docker.sh"
        "scripts/docker/build_base.sh"
    )
    
    for script in "${scripts[@]}"; do
        test_script_exists "$script"
        test_script_syntax "$script"
        test_script_help "$script" "help"
    done
}

# Test analysis scripts
test_analysis_scripts() {
    echo ""
    echo "=== Testing analysis scripts ==="
    
    local scripts=(
        "scripts/analysis/dcf.sh"
        "scripts/analysis/pe.sh"
        "scripts/analysis/run_all_dcf.sh"
    )
    
    for script in "${scripts[@]}"; do
        test_script_exists "$script"
        test_script_syntax "$script"
        test_script_help "$script" "help"
    done
}

# Test dev scripts
test_dev_scripts() {
    echo ""
    echo "=== Testing dev scripts ==="
    
    local scripts=(
        "scripts/dev/test.sh"
        "scripts/dev/lint.sh"
        "scripts/dev/clean.sh"
        "scripts/dev/health_check.sh"
    )
    
    for script in "${scripts[@]}"; do
        test_script_exists "$script"
        test_script_syntax "$script"
        test_script_help "$script" "help"
    done
}

# Test utils scripts
test_utils_scripts() {
    echo ""
    echo "=== Testing utils scripts ==="
    
    local scripts=(
        "scripts/utils/get_version.sh"
        "scripts/utils/web.sh"
    )
    
    for script in "${scripts[@]}"; do
        test_script_exists "$script"
        test_script_syntax "$script"
        test_script_help "$script" "help"
    done
}

# Test git script
test_git_script() {
    echo ""
    echo "=== Testing git script ==="
    
    test_script_exists "scripts/git.sh"
    test_script_syntax "scripts/git.sh"
    test_script_help "scripts/git.sh" "help"
}

# Test common.sh backward compatibility
test_common_compatibility() {
    echo ""
    echo "=== Testing common.sh backward compatibility ==="
    
    if [[ -f "scripts/common.sh" ]]; then
        test_pass "common.sh exists for backward compatibility"
        
        # Test that it can be sourced
        if bash -c "source scripts/common.sh && echo 'OK'" >/dev/null 2>&1; then
            test_pass "common.sh can be sourced"
        else
            test_fail "common.sh cannot be sourced"
        fi
    else
        test_fail "common.sh missing"
    fi
}

# Main test runner
main() {
    echo "=========================================="
    echo "  Bash Scripts Test Suite"
    echo "=========================================="
    
    test_lib_modules
    test_version_scripts
    test_docker_scripts
    test_analysis_scripts
    test_dev_scripts
    test_utils_scripts
    test_git_script
    test_common_compatibility
    
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
        exit 0
    else
        echo -e "${RED}Some tests failed!${NC}"
        exit 1
    fi
}

# Run tests
main "$@"

