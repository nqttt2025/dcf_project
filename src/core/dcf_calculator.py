"""
DCF Calculator Module

Tính toán DCF valuation dựa trên config file.
Ví dụ:
    result = await calculate_dcf_from_config("FPT.cfg")
    print(result['dcf_fair_value'])
"""

import asyncio
import os
from pathlib import Path
from .fcfs import (
    get_free_cash_flow,
    get_shares_outstanding,
    get_earnings_per_share_Diluted,
    price_board_stock,
    get_market_cap
)
from .ge import get_growth_estimate
from .industry_pe import get_industry_pe, get_current_pe, suggest_base_pe, get_pe_analysis
from .advanced_analysis import generate_advanced_analysis
from ..utils.logger import get_logger, get_stock_logger
from ..utils.result_manager import get_result_manager
import configparser
import json
from datetime import datetime, timezone

# Import cache utilities
try:
    from ..utils.cache_utils import (
        get_cache_service, 
        CacheKey, 
        CacheTTL,
    )
    HAS_CACHE = True
except ImportError:
    HAS_CACHE = False
    get_cache_service = None

# Import error handler
try:
    from ..utils.error_handler import (
        DCFErrorHandler,
        analyze_calculation_viability,
        with_error_recovery,
    )
    HAS_ERROR_HANDLER = True
except ImportError:
    HAS_ERROR_HANDLER = False
    DCFErrorHandler = None

# Import shares validator
try:
    from ..utils.shares_validator import SharesValidator, ValidationConfidence
    HAS_SHARES_VALIDATOR = True
except ImportError:
    HAS_SHARES_VALIDATOR = False
    SharesValidator = None

logger = get_logger()


class DCFCalculator:
    """
    DCF Calculator - Tính toán DCF valuation từ config file
    Hỗ trợ async execution và custom cache per config file
    """

    def __init__(self, config_file):
        """
        Initialize DCF Calculator với config file

        Args:
            config_file: Đường dẫn đến file config (ví dụ: "FPT.cfg")
        """
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.ticker = None
        self.dcf_params = {}
        self.graham_params = {}
        self.cache_file = None
        self.result_manager = get_result_manager()

        self._load_config()

        # Get stock-specific logger
        self.logger = get_stock_logger(self.ticker)

    def _load_config(self):
        """Load config từ file"""
        # Tìm config file từ database folder, thư mục hiện tại, hoặc thư mục script
        config_paths = [
            self.config_file,
            os.path.join(os.path.dirname(__file__), 'database', self.config_file),
            os.path.join(os.path.dirname(__file__), self.config_file),
            os.path.join(os.getcwd(), self.config_file),
            os.path.join(os.getcwd(), 'database', self.config_file),
        ]

        found_config = None
        for path in config_paths:
            if os.path.exists(path):
                found_config = path
                break

        if not found_config:
            raise FileNotFoundError(f"Config file not found: {self.config_file}\nSearched in: {config_paths}")

        self.config_file = found_config
        self.config.read(self.config_file)

        # Get ticker từ config hoặc từ tên file
        try:
            self.ticker = self.config.get('ticker', 'ticker')
        except:
            # Nếu không có, lấy từ tên file (ví dụ: FPT.cfg -> FPT)
            self.ticker = Path(self.config_file).stem.upper()

        # Load DCF parameters
        self.dcf_params = {
            'yr': self.config.getint('dcf', 'yr', fallback=5),
            'dr': self.config.getfloat('dcf', 'dr', fallback=10.0),
            'pr': self.config.getfloat('dcf', 'pr', fallback=2.5),
        }

        # Load Graham parameters
        self.graham_params = {
            'base_pe': self.config.getfloat('graham', 'base_pe', fallback=8.5),
            'growth_multiplier': self.config.getfloat('graham', 'growth_multiplier', fallback=2.0),
        }
        
        # Load report language (default: Vietnamese)
        try:
            if 'report' in self.config:
                self.report_language = self.config.get('report', 'language', fallback='vi')
            else:
                self.report_language = 'vi'
        except:
            self.report_language = 'vi'
        
        # Ensure language is valid
        if self.report_language.lower() not in ['vi', 'en']:
            self.report_language = 'vi'

        # Set cache file: FPT.cfg -> fpt_cache.json
        # Cache dir is at project_root/data/cache
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cache_dir = os.path.join(project_root, 'data', 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        cache_name = f"{Path(self.config_file).stem.lower()}_cache.json"
        self.cache_file = os.path.join(cache_dir, cache_name)

        logger.info(f"Loaded config from {self.config_file}")
        logger.info(f"Ticker: {self.ticker}")
        logger.info(f"Cache file: {self.cache_file}")
        logger.info(f"DCF params: yr={self.dcf_params['yr']}, dr={self.dcf_params['dr']}%, pr={self.dcf_params['pr']}%")

    async def fetch_data_async(self):
        """
        Fetch financial data asynchronously (parallel execution) with error recovery.
        
        Uses error handler for graceful degradation when data fetch fails.
        """
        self.logger.info(f"Starting async data fetch for {self.ticker}...")
        
        # Initialize error handler if available
        if HAS_ERROR_HANDLER:
            self.error_handler = DCFErrorHandler(self.ticker)
        else:
            self.error_handler = None

        async def fetch_with_timeout(func, *args, timeout=60.0, task_name="Unknown"):
            """Wrapper để thêm timeout cho mỗi API call với error recovery"""
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(func, *args),
                    timeout=timeout
                )
                return result
            except asyncio.TimeoutError as e:
                self.logger.error(f"Timeout fetching {task_name} for {self.ticker} after {timeout}s")
                # Record error in error handler
                if self.error_handler:
                    self.error_handler.handle_fetch_error(task_name, e)
                return None
            except Exception as e:
                self.logger.error(f"Error fetching {task_name} for {self.ticker}: {e}")
                if self.error_handler:
                    self.error_handler.handle_fetch_error(task_name, e)
                return None

        # Tạo các task với timeout riêng
        tasks = [
            fetch_with_timeout(get_free_cash_flow, self.ticker, timeout=60.0, task_name="FCF"),
            fetch_with_timeout(get_growth_estimate, self.ticker, timeout=60.0, task_name="Growth"),
            fetch_with_timeout(get_shares_outstanding, self.ticker, timeout=60.0, task_name="Shares"),
            fetch_with_timeout(get_earnings_per_share_Diluted, self.ticker, timeout=60.0, task_name="EPS"),
            fetch_with_timeout(price_board_stock, self.ticker, timeout=60.0, task_name="Price"),
            fetch_with_timeout(lambda: get_market_cap(self.ticker)[0], timeout=60.0, task_name="Market Cap"),
            fetch_with_timeout(get_industry_pe, self.ticker, timeout=60.0, task_name="Industry PE"),
        ]

        self.logger.info("Fetching: FCF (TTM), Growth, Shares, EPS, Price, Market Cap, Industry PE (in parallel with 60s timeout each)...")
        
        # Gather all tasks with overall timeout (5 minutes max)
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=300.0  # 5 minutes total timeout
            )
        except asyncio.TimeoutError:
            self.logger.error(f"Overall timeout fetching financial data for {self.ticker} after 5 minutes")
            results = [None] * len(tasks)

        # Check for errors and log warnings
        task_names = ['FCF', 'Growth', 'Shares', 'EPS', 'Price', 'Market Cap', 'Industry PE']
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error in task {i} ({task_names[i] if i < len(task_names) else 'Unknown'}): {result}")
                results[i] = None  # Convert exception to None
            elif result is None:
                self.logger.warning(f"Task {i} ({task_names[i] if i < len(task_names) else 'Unknown'}) returned None for {self.ticker}")

        data = {
            'fcf': results[0],
            'ge': results[1],
            'shares': results[2],
            'eps': results[3],
            'price': results[4],
            'market_cap': results[5],
            'industry_pe': results[6] if results[6] is not None else None,
        }
        
        # Cross-validate shares using SharesValidator if available
        if HAS_SHARES_VALIDATOR and data['shares'] is not None:
            try:
                validator = SharesValidator(self.ticker)
                validator.add_source("vnstock_api", data['shares'], priority=2)
                
                # Add market cap calculation as second source
                if data['market_cap'] and data['price'] and data['price'] > 0:
                    validator.add_from_market_cap(data['market_cap'], data['price'])
                
                validation_result = validator.validate()
                
                if validation_result.is_valid:
                    data['shares'] = validation_result.value
                    data['shares_confidence'] = validation_result.confidence.value
                    data['shares_sources'] = validation_result.sources_used
                    
                    if validation_result.discrepancies:
                        self.logger.warning(f"Shares discrepancies: {validation_result.discrepancies}")
                else:
                    self.logger.warning(f"Shares validation failed, using original value")
            except Exception as e:
                self.logger.debug(f"Shares validation error: {e}")
        
        # Log error summary if error handler is active
        if self.error_handler and self.error_handler.errors:
            summary = self.error_handler.get_error_summary()
            self.logger.warning(f"Data fetch completed with {summary['total_errors']} errors")
            data['_fetch_errors'] = summary
        
        return data

    def calculate_dcf(self, data):
        """Calculate DCF valuation"""
        # Validate input data
        if data['fcf'] is None:
            raise ValueError(f"FCF is None for {self.ticker}. Cannot calculate DCF.")
        
        if data['shares'] is None or data['shares'] <= 0:
            raise ValueError(f"Shares is None or invalid ({data['shares']}) for {self.ticker}. Cannot calculate DCF.")
        
        # Validation using shares_validator
        try:
            from src.utils.shares_validator import validate_and_cross_check
            validate_and_cross_check(
                shares=data['shares'],
                ticker=self.ticker,
                price=data.get('price'),
                market_cap=data.get('market_cap'),
                raise_error=True
            )
        except ImportError:
            # Fallback validation if validator not available
            if data['shares'] > 1e12:  # More than 1 trillion shares
                error_msg = (
                    f"Shares outstanding validation failed for {self.ticker}: {data['shares']:,.0f}. "
                    f"This value is unreasonably large (>1 trillion shares) and likely indicates a unit error. "
                    f"Please check the shares calculation logic in sync_service.py or fcfs.py."
                )
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Additional validation: Check reasonable range
            if data['shares'] > 5e10:  # More than 50 billion shares
                self.logger.warning(
                    f"Shares outstanding seems large for {self.ticker}: {data['shares']:,.0f}. "
                    f"Please verify this value is correct."
                )
        
        # Warn if FCF is negative
        if data['fcf'] < 0:
            self.logger.warning(f"FCF is negative for {self.ticker}: {data['fcf']:,.0f} VND. DCF calculation may produce negative fair value.")
        
        if data['ge'] is None or data['ge'] == []:
            raise ValueError("Growth rate not available")
        
        forecast = [data['fcf']]

        # Forecast cash flows
        for _ in range(1, self.dcf_params['yr']):
            forecast.append(round(forecast[-1] + (data['ge'] / 100) * forecast[-1], 2))

        # Terminal value
        terminal_value = round(
            forecast[-1] * (1 + (self.dcf_params['pr'] / 100)) / 
            (self.dcf_params['dr'] / 100 - self.dcf_params['pr'] / 100),
            2
        )
        forecast.append(terminal_value)

        # Discount factors
        discount_factors = [1 / (1 + (self.dcf_params['dr'] / 100))**(i + 1) 
                           for i in range(len(forecast) - 1)]

        # Present values
        pvs = [round(f * d, 2) for f, d in zip(forecast[:-1], discount_factors)]
        pvs.append(round(discount_factors[-1] * forecast[-1], 2))

        # DCF value
        dcf_value = sum(pvs)
        fair_value = dcf_value / data['shares']

        self.logger.info(f"DCF calculation completed for {self.ticker}")
        self.logger.info(f"Fair value: {fair_value:,.2f}")

        return {
            'forecast': forecast,
            'pvs': pvs,
            'dcf_value': dcf_value,
            'fair_value': fair_value,
        }

    def calculate_graham(self, data):
        """Calculate Graham valuation"""
        if data['eps'] <= 0:
            self.logger.warning(f"Cannot calculate Graham valuation for {self.ticker} (EPS <= 0)")
            return None

        base_pe = self.graham_params['base_pe']
        multiplier = self.graham_params['growth_multiplier']

        fair_value = data['eps'] * (base_pe + multiplier * data['ge'])
        ge_priced_in = (data['price'] / data['eps'] - base_pe) / multiplier

        self.logger.info(f"Graham valuation for {self.ticker}: {fair_value:,.2f}")

        return {
            'fair_value': fair_value,
            'ge_priced_in': ge_priced_in,
        }

    def _save_cache(self, data):
        """Save data to cache file (JSON format)"""
        try:
            cache_data = {
                f"{self.ticker}_fcf": data['fcf'],
                f"{self.ticker}_fcf_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                f"{self.ticker}_growth_estimate": data['ge'],
                f"{self.ticker}_growth_estimate_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                f"{self.ticker}_shares": data['shares'],
                f"{self.ticker}_shares_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                f"{self.ticker}_eps": data['eps'],
                f"{self.ticker}_eps_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                f"{self.ticker}_price": data['price'],
                f"{self.ticker}_price_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                f"{self.ticker}_market_cap": data['market_cap'],
                f"{self.ticker}_market_cap_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            }

            # Read existing cache if file exists
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    existing_data = json.load(f)
                    cache_data.update(existing_data)

            # Write cache file
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=4)

            self.logger.info(f"Cache saved to {self.cache_file}")
        except Exception as e:
            self.logger.error(f"Error saving cache: {e}")

    async def calculate(self, progress_callback=None):
        """
        Main calculation method - Tính toán DCF và Graham valuation

        Returns:
            dict: Kết quả valuation
                {
                    'ticker': 'FPT',
                    'config_file': 'FPT.cfg',
                    'price': 92500.0,
                    'market_cap': 157574408692500.0,
                    'eps': 1429.31,
                    'shares': 1703507121,
                    'growth_estimate': 10.68,
                    'dcf_fair_value': 44206.13,
                    'graham_fair_value': 42674.55,
                    'average_fair_value': 43440.34,
                    'cache_file': 'data/fpt_cache.json',
                    'result_file': 'data/results/fpt_result.json'
                }
        """
        self.logger.info("=" * 80)
        self.logger.info(f"DCF Analysis for {self.ticker}")
        self.logger.info("=" * 80)

        if progress_callback:
            progress_callback(5.0, "Initializing calculation...")

        # Fetch data
        if progress_callback:
            progress_callback(15.0, "Fetching financial data...")
        data = await self.fetch_data_async()

        # Calculate DCF
        if progress_callback:
            progress_callback(50.0, "Calculating DCF valuation...")
        dcf_result = self.calculate_dcf(data)
        dcf_fair_value = dcf_result['fair_value']

        # Calculate Graham
        if progress_callback:
            progress_callback(70.0, "Calculating Graham valuation...")
        graham_result = self.calculate_graham(data)
        graham_fair_value = graham_result['fair_value'] if graham_result else None

        # Calculate average
        if graham_fair_value:
            avg_fair_value = (dcf_fair_value + graham_fair_value) / 2
        else:
            avg_fair_value = dcf_fair_value

        result = {
            'ticker': self.ticker,
            'config_file': self.config_file,
            'price': data['price'],
            'market_cap': data['market_cap'],
            'eps': data['eps'],
            'shares': data['shares'],
            'fcf': data['fcf'],  # Thêm FCF vào result
            'growth_estimate': data['ge'],
            'dcf_params': self.dcf_params,
            'graham_params': self.graham_params,  # Thêm graham_params vào result
            'dcf_fair_value': dcf_fair_value,
            'graham_fair_value': graham_fair_value,
            'average_fair_value': avg_fair_value,
            'cache_file': self.cache_file,
            'dcf_result': dcf_result,  # Thêm chi tiết DCF result
            'report_language': self.report_language,  # Thêm ngôn ngữ báo cáo
        }
        
        # Generate advanced analysis
        if progress_callback:
            progress_callback(85.0, "Generating advanced analysis...")
        advanced_analysis = generate_advanced_analysis(result, dcf_result)
        result['advanced_analysis'] = advanced_analysis
        
        # Add PE analysis (current PE, industry PE, suggested base PE)
        if progress_callback:
            progress_callback(90.0, "Calculating PE analysis...")
        try:
            pe_analysis = get_pe_analysis(self.ticker)
            result['pe_analysis'] = pe_analysis
            self.logger.info(f"PE Analysis for {self.ticker}: Current={pe_analysis.get('current_pe')}, Industry={pe_analysis.get('industry_pe')}, Suggested Base={pe_analysis.get('suggested_base_pe')}")
        except Exception as e:
            self.logger.debug(f"Could not get PE analysis: {e}")
            result['pe_analysis'] = None

        self.logger.info("=" * 80)
        self.logger.info("Valuation Summary")
        self.logger.info("=" * 80)
        self.logger.info(f"Current Price: {data['price']:,.2f}")
        self.logger.info(f"DCF Fair Value: {dcf_fair_value:,.2f}")
        if graham_fair_value:
            self.logger.info(f"Graham Fair Value: {graham_fair_value:,.2f}")
            self.logger.info(f"Average Fair Value: {avg_fair_value:,.2f}")
        self.logger.info("=" * 80)

        # Save cache
        self._save_cache(data)

        # Save result to results directory
        if progress_callback:
            progress_callback(95.0, "Saving results...")
        result_file, log_file = self.result_manager.save_result(self.ticker, result, self.report_language)
        result['result_file'] = result_file
        result['log_file'] = log_file
        self.logger.info(f"Result saved to {result_file}")

        if progress_callback:
            progress_callback(100.0, "Analysis completed!")

        return result


async def calculate_dcf_from_config(config_file, progress_callback=None):
    """
    Main function - Tính DCF từ config file

    Args:
        config_file: Đường dẫn đến file config (ví dụ: "FPT.cfg")

    Returns:
        dict: Kết quả valuation

    Example:
        result = await calculate_dcf_from_config("FPT.cfg")
        print(f"DCF Fair Value: {result['dcf_fair_value']}")
        print(f"Cache saved to: {result['cache_file']}")
    """
    calculator = DCFCalculator(config_file)
    result = await calculator.calculate(progress_callback=progress_callback)
    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 dcf_calculator.py <config_file>")
        print("Example: python3 dcf_calculator.py FPT.cfg")
        sys.exit(1)

    config_file = sys.argv[1]

    try:
        result = asyncio.run(calculate_dcf_from_config(config_file))
        print(f"\n✓ Analysis completed for {result['ticker']}")
        print(f"  DCF Fair Value: {result['dcf_fair_value']:,.2f}")
        print(f"  Cache saved to: {result['cache_file']}")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
