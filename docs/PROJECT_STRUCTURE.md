# DCF Project - Reorganized Structure

## Project Layout

```
dcf_project/
├── src/                          # Source code
│   ├── core/                     # Core business logic modules
│   │   ├── dcf_calculator.py     # Main DCF calculation engine
│   │   ├── fcfs.py               # Free Cash Flow calculations
│   │   ├── ge.py                 # Growth Estimate module
│   │   ├── company.py            # Company data structures
│   │   ├── fpt_database.py        # FPT specific database functions
│   │   ├── value_estimator.py     # Valuation estimation
│   │   ├── value_estimator_async.py # Async valuation
│   │   └── __init__.py
│   │
│   └── utils/                    # Utility modules
│       ├── logger.py             # Logging configuration
│       ├── cache_manager.py       # Cache management
│       ├── result_manager.py      # Result file saving
│       ├── config_manager.py      # Configuration management
│       ├── common.py              # Common utilities
│       ├── constants.py           # Project constants
│       └── __init__.py
│
├── config/                       # Configuration files
│   ├── BID.cfg                   # BID stock configuration
│   ├── DCF.cfg                   # DCF stock configuration
│   ├── FPT.cfg                   # FPT stock configuration
│   └── VNM.cfg                   # VNM stock configuration
│
├── data/                         # Data directory
│   ├── cache/                    # Cached data (gitignored)
│   │   ├── bid_cache.json
│   │   ├── dcf_cache.json
│   │   ├── fpt_cache.json
│   │   └── vnm_cache.json
│   │
│   └── results/                  # Valuation results (gitignored)
│       ├── bid_result.json
│       ├── bid_result.text
│       ├── fpt_result.json
│       ├── fpt_result.text
│       ├── vcb_result.json
│       ├── vcb_result.text
│       ├── vnm_result.json
│       └── vnm_result.text
│
├── docs/                         # Documentation
│   ├── README.md                 # Main project README
│   ├── README_DCF_CALCULATOR.md
│   ├── IMPLEMENTATION_SUMMARY.md
│   ├── LOGGING_AND_RESULTS_GUIDE.md
│   └── PROJECT_COMPLETION_REPORT.md
│
├── scripts/                      # Standalone scripts
│   ├── run_all_dcf.py           # Run all stocks (async)
│   └── run_all_dcf.sh           # Run all stocks (shell)
│
├── examples/                     # Example scripts
│   └── example_multi_stocks.py   # Multi-stock analysis example
│
├── tests/                        # Test files
│   └── test_dcf_complete.py      # Complete test suite
│
├── run_dcf.py                    # Quick runner (single stock)
├── run_all_dcf_main.py           # Main runner (all stocks)
├── .gitignore                    # Git ignore configuration
└── log/                          # Log files directory
```

## Running the Project

### Option 1: Run Single Stock Analysis
```bash
python3 run_dcf.py FPT.cfg
```

### Option 2: Run All Stocks Analysis
```bash
python3 run_all_dcf_main.py
```

### Option 3: Use Script from Scripts Directory
```bash
python3 scripts/run_all_dcf.py
# or
./scripts/run_all_dcf.sh
```

## Results

- Valuation results are saved to `data/results/`
- Cache data is saved to `data/cache/`
- Both are automatically gitignored
- Results include both `.json` and `.text` formats

## Module Organization

### Core Modules (`src/core/`)
- **dcf_calculator.py**: Main DCF analysis calculation
- **fcfs.py**: Financial data fetching (Free Cash Flows)
- **ge.py**: Growth Estimate calculations
- **company.py**: Company data structures
- **value_estimator.py**: Stock valuation calculations

### Utility Modules (`src/utils/`)
- **logger.py**: Centralized logging configuration
- **cache_manager.py**: Cache file management
- **result_manager.py**: Result file saving and formatting
- **config_manager.py**: Configuration file parsing
- **common.py**: Common utilities
- **constants.py**: Project constants

## Key Features

✅ Clean modular structure  
✅ Separated concerns (core logic vs utilities)  
✅ Centralized configuration  
✅ Organized documentation  
✅ Easy to test and extend  
✅ Git-safe (results and cache ignored)  

## Import Examples

```python
# From root directory scripts
from src.core.dcf_calculator import calculate_dcf_from_config
from src.utils.logger import get_logger

# From within src/core modules
from .fcfs import get_free_cash_flow
from ..utils.logger import get_logger
```
