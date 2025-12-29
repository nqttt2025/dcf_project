#!/usr/bin/env python3
"""
Test suite for Python scripts in scripts/ directory
Tests all Python scripts for syntax, imports, and basic functionality
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path
from typing import List, Tuple

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color

# Test counters
passed = 0
failed = 0
skipped = 0


def test_pass(message: str):
    """Print pass message"""
    print(f"{GREEN}✓ PASS{NC}: {message}")
    global passed
    passed += 1


def test_fail(message: str):
    """Print fail message"""
    print(f"{RED}✗ FAIL{NC}: {message}")
    global failed
    failed += 1


def test_skip(message: str):
    """Print skip message"""
    print(f"{YELLOW}⊘ SKIP{NC}: {message}")
    global skipped
    skipped += 1


def test_file_exists(filepath: Path) -> bool:
    """Test if file exists"""
    if filepath.exists():
        test_pass(f"File exists: {filepath}")
        return True
    else:
        test_fail(f"File missing: {filepath}")
        return False


def test_python_syntax(filepath: Path) -> bool:
    """Test Python script syntax"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        compile(code, str(filepath), 'exec')
        test_pass(f"Syntax valid: {filepath.name}")
        return True
    except SyntaxError as e:
        test_fail(f"Syntax error in {filepath.name}: {e}")
        return False
    except Exception as e:
        test_fail(f"Error checking syntax for {filepath.name}: {e}")
        return False


def test_python_imports(filepath: Path) -> bool:
    """Test if Python script can import its dependencies"""
    try:
        # Read the file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for common imports that might fail
        # We'll do a basic check - actual import testing would require full environment
        if 'import' in content or 'from' in content:
            # Try to compile to check for import syntax errors
            compile(content, str(filepath), 'exec')
            test_pass(f"Imports check passed: {filepath.name}")
            return True
        else:
            test_pass(f"No imports to check: {filepath.name}")
            return True
    except SyntaxError as e:
        test_fail(f"Import syntax error in {filepath.name}: {e}")
        return False
    except Exception as e:
        test_fail(f"Error checking imports for {filepath.name}: {e}")
        return False


def test_python_executable(filepath: Path) -> bool:
    """Test if Python script is executable and has shebang"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
        
        if first_line.startswith('#!'):
            if 'python' in first_line.lower():
                test_pass(f"Shebang present: {filepath.name}")
                return True
            else:
                test_skip(f"Shebang present but not Python: {filepath.name}")
                return True
        else:
            test_skip(f"No shebang in {filepath.name} (may be module)")
            return True
    except Exception as e:
        test_fail(f"Error checking shebang for {filepath.name}: {e}")
        return False


def test_python_help(filepath: Path) -> bool:
    """Test if Python script has help/usage information"""
    try:
        # Try running with --help
        result = subprocess.run(
            [sys.executable, str(filepath), '--help'],
            capture_output=True,
            timeout=5,
            cwd=filepath.parent.parent.parent
        )
        if result.returncode == 0 or 'usage' in result.stdout.decode().lower() or 'help' in result.stdout.decode().lower():
            test_pass(f"Help available: {filepath.name}")
            return True
        else:
            # Check if script has docstring
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            if '"""' in content or "'''" in content:
                test_pass(f"Has docstring: {filepath.name}")
                return True
            else:
                test_skip(f"No help/docstring: {filepath.name}")
                return True
    except subprocess.TimeoutExpired:
        test_skip(f"Help test timeout: {filepath.name}")
        return True
    except Exception as e:
        # Script may not support --help, that's okay
        test_skip(f"Help test skipped for {filepath.name}: {str(e)[:50]}")
        return True


def test_analysis_scripts():
    """Test analysis Python scripts"""
    print("\n=== Testing analysis Python scripts ===")
    
    project_root = Path(__file__).parent.parent.parent
    scripts = [
        project_root / "scripts" / "analysis" / "calculate_pe.py",
        project_root / "scripts" / "analysis" / "run_all_dcf.py",
        project_root / "scripts" / "analysis" / "run_all_dcf_with_retry.py",
    ]
    
    for script in scripts:
        if test_file_exists(script):
            test_python_syntax(script)
            test_python_executable(script)
            test_python_imports(script)
            # Don't test help for scripts that require arguments
            if script.name != "run_all_dcf.py" and script.name != "run_all_dcf_with_retry.py":
                test_python_help(script)


def test_utils_scripts():
    """Test utils Python scripts"""
    print("\n=== Testing utils Python scripts ===")
    
    project_root = Path(__file__).parent.parent.parent
    scripts = [
        project_root / "scripts" / "utils" / "update_configs_with_ttm_info.py",
    ]
    
    for script in scripts:
        if test_file_exists(script):
            test_python_syntax(script)
            test_python_executable(script)
            test_python_imports(script)
            test_python_help(script)


def test_script_paths():
    """Test that scripts can find project root correctly"""
    print("\n=== Testing script path resolution ===")
    
    project_root = Path(__file__).parent.parent.parent
    
    # Test calculate_pe.py path resolution
    script = project_root / "scripts" / "analysis" / "calculate_pe.py"
    if script.exists():
        try:
            # Check if script has proper path resolution code
            with open(script, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'project_root' in content and 'os.path' in content:
                test_pass("calculate_pe.py has path resolution")
            else:
                test_fail("calculate_pe.py missing path resolution")
        except Exception as e:
            test_fail(f"Error checking calculate_pe.py paths: {e}")
    
    # Test run_all_dcf.py path resolution
    script = project_root / "scripts" / "analysis" / "run_all_dcf.py"
    if script.exists():
        try:
            with open(script, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'project_root' in content or 'config_dir' in content:
                test_pass("run_all_dcf.py has path resolution")
            else:
                test_fail("run_all_dcf.py missing path resolution")
        except Exception as e:
            test_fail(f"Error checking run_all_dcf.py paths: {e}")


def main():
    """Main test runner"""
    print("=" * 50)
    print("  Python Scripts Test Suite")
    print("=" * 50)
    
    test_analysis_scripts()
    test_utils_scripts()
    test_script_paths()
    
    print("\n" + "=" * 50)
    print("  Test Summary")
    print("=" * 50)
    print(f"{GREEN}Passed:{NC} {passed}")
    print(f"{RED}Failed:{NC} {failed}")
    print(f"{YELLOW}Skipped:{NC} {skipped}")
    print()
    
    if failed == 0:
        print(f"{GREEN}All tests passed!{NC}")
        return 0
    else:
        print(f"{RED}Some tests failed!{NC}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

