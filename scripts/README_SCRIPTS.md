# Scripts Organization and Testing

## Python Scripts Organization

All Python scripts have been organized into appropriate directories:

### Analysis Scripts (`scripts/analysis/`)
- `calculate_pe.py` - Calculate PE ratios for stocks
- `run_all_dcf.py` - Run DCF analysis for all stocks (fast mode)
- `run_all_dcf_with_retry.py` - Run DCF analysis with retry logic

### Utils Scripts (`scripts/utils/`)
- `update_configs_with_ttm_info.py` - Update config files with TTM information

## Path Resolution

All Python scripts have been updated to:
1. **Resolve project root correctly** - Works regardless of where script is called from
2. **Handle relative paths properly** - Config and data directories are resolved relative to project root
3. **Maintain compatibility** - Scripts can be run directly or via bash wrappers

### Example Path Resolution Pattern

```python
# Get script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get project root (2 levels up from scripts/analysis/)
project_root = os.path.dirname(os.path.dirname(script_dir))
# Add to Python path
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))
```

## Testing

### Running Tests

```bash
# Test all scripts (bash + Python)
make test-scripts

# Test only bash scripts
make test-scripts-bash
# or
./tests/scripts/test_bash_scripts.sh

# Test only Python scripts
make test-scripts-python
# or
python3 tests/scripts/test_python_scripts.py
```

### Test Coverage

#### Bash Script Tests
- ✅ Script existence
- ✅ Syntax validation
- ✅ Executability
- ✅ Help/usage functionality
- ✅ Module loading

#### Python Script Tests
- ✅ File existence
- ✅ Syntax validation
- ✅ Import checks
- ✅ Shebang presence
- ✅ Help/docstring presence
- ✅ Path resolution

## Script Usage

### Analysis Scripts

```bash
# PE calculation
./scripts/analysis/pe.sh single VNM
./scripts/analysis/pe.sh all

# DCF analysis
./scripts/analysis/dcf.sh single VNM
./scripts/analysis/dcf.sh all          # With retry
./scripts/analysis/dcf.sh all-fast     # Fast mode
```

### Python Scripts (Direct)

```bash
# Calculate PE
python3 scripts/analysis/calculate_pe.py VNM
python3 scripts/analysis/calculate_pe.py  # All VN30

# Run DCF
python3 scripts/analysis/run_all_dcf.py
python3 scripts/analysis/run_all_dcf_with_retry.py

# Update configs
python3 scripts/utils/update_configs_with_ttm_info.py
```

## Stability Improvements

1. **Absolute Path Resolution**: All scripts resolve paths relative to project root
2. **Error Handling**: Improved error handling in Python scripts
3. **Path Independence**: Scripts work regardless of current working directory
4. **Consistent Structure**: All scripts follow the same path resolution pattern

## Maintenance

When adding new Python scripts:

1. Place in appropriate directory (`analysis/`, `utils/`, etc.)
2. Use the standard path resolution pattern
3. Add tests to `tests/scripts/test_python_scripts.py`
4. Update this documentation

