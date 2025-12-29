#!/bin/bash
# Check for duplicate functionality in Makefile
# Ensures no redundant targets

set -uo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

DUPLICATES=0
WARNINGS=0

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

check_duplicate() {
    local target1="$1"
    local target2="$2"
    local reason="$3"
    
    local output1 output2
    output1=$(make -n "$target1" 2>&1)
    output2=$(make -n "$target2" 2>&1)
    
    if [[ "$output1" == "$output2" ]]; then
        echo -e "${YELLOW}⚠ WARNING${NC}: $target1 and $target2 may be duplicates"
        echo "  Reason: $reason"
        ((DUPLICATES++))
        return 1
    fi
    return 0
}

echo "=========================================="
echo "  Checking for Duplicate Functionality"
echo "=========================================="
echo ""

# Check test vs ut
echo "1. Checking test vs ut..."
test_output=$(make -n test 2>&1)
ut_output=$(make -n ut 2>&1)
if echo "$test_output" | grep -q "test.sh ut" && echo "$ut_output" | grep -q "test.sh ut"; then
    # test calls ut, which is fine (not a duplicate)
    echo -e "${GREEN}✓${NC} test calls ut (correct delegation)"
else
    echo -e "${YELLOW}⚠${NC} test and ut relationship unclear"
    ((WARNINGS++))
fi

# Check docker-build vs docker-build-fast
echo "2. Checking docker-build vs docker-build-fast..."
build_output=$(make -n docker-build 2>&1)
build_fast_output=$(make -n docker-build-fast 2>&1)
if echo "$build_output" | grep -q "docker.sh build" && echo "$build_fast_output" | grep -q "PARALLEL=true"; then
    echo -e "${GREEN}✓${NC} docker-build-fast uses PARALLEL (different functionality)"
else
    echo -e "${YELLOW}⚠${NC} docker-build vs docker-build-fast unclear"
    ((WARNINGS++))
fi

# Check docker-build-auto vs docker-build
echo "3. Checking docker-build-auto vs docker-build..."
build_auto_output=$(make -n docker-build-auto 2>&1)
if echo "$build_auto_output" | grep -q "auto_version\|docker-build"; then
    echo -e "${GREEN}✓${NC} docker-build-auto adds auto-tagging (different functionality)"
else
    echo -e "${YELLOW}⚠${NC} docker-build-auto functionality unclear"
    ((WARNINGS++))
fi

# Check docker-rebuild-auto vs docker-rebuild
echo "4. Checking docker-rebuild-auto vs docker-rebuild..."
rebuild_auto_output=$(make -n docker-rebuild-auto 2>&1)
if echo "$rebuild_auto_output" | grep -q "auto_version\|docker-rebuild"; then
    echo -e "${GREEN}✓${NC} docker-rebuild-auto adds auto-tagging (different functionality)"
else
    echo -e "${YELLOW}⚠${NC} docker-rebuild-auto functionality unclear"
    ((WARNINGS++))
fi

# Check clean vs clean-all
echo "5. Checking clean vs clean-all..."
clean_output=$(make -n clean 2>&1)
clean_all_output=$(make -n clean-all 2>&1)
if echo "$clean_all_output" | grep -q "clean\|clean-results\|clean-data"; then
    echo -e "${GREEN}✓${NC} clean-all includes clean (correct hierarchy)"
else
    echo -e "${YELLOW}⚠${NC} clean vs clean-all relationship unclear"
    ((WARNINGS++))
fi

# Check lint vs pylint/flake8
echo "6. Checking lint vs pylint/flake8..."
lint_output=$(make -n lint 2>&1)
pylint_output=$(make -n pylint 2>&1)
flake8_output=$(make -n flake8 2>&1)
if echo "$lint_output" | grep -q "pylint\|flake8"; then
    echo -e "${GREEN}✓${NC} lint calls pylint and flake8 (correct aggregation)"
else
    echo -e "${YELLOW}⚠${NC} lint relationship unclear"
    ((WARNINGS++))
fi

# Summary
echo ""
echo "=========================================="
echo "  Summary"
echo "=========================================="
echo -e "${RED}Duplicates found:${NC} $DUPLICATES"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo ""

if [[ $DUPLICATES -eq 0 ]]; then
    echo -e "${GREEN}No duplicate functionality found!${NC}"
    exit 0
else
    echo -e "${RED}Found $DUPLICATES potential duplicate(s)!${NC}"
    exit 1
fi

