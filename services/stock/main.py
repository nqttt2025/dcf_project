"""
Stock Service - Microservice quản lý thông tin cổ phiếu
"""
import sys
from pathlib import Path

# Setup project path first (before importing services.common)
if Path('/app').exists():
    project_root = Path('/app')
else:
    project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
import json
import os
import logging
import asyncio

# Try to import httpx for syncing with DCF service
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

# Import common utilities after path setup
from services.common import create_health_response, get_service_urls

from src.utils.result_manager import get_result_manager

# Setup service-specific logger với rotation và tối ưu hiệu năng
from src.utils.service_logger import setup_service_logger
logger = setup_service_logger('stock', level=logging.INFO)

app = FastAPI(title="Stock Service")

# Initialize managers
result_manager = get_result_manager()

# Get service URLs
service_urls = get_service_urls()
DATABASE_SERVICE_URL = service_urls.get("database", "http://database:8003")

# Initialize paths
config_dir = project_root / 'config'
results_dir = project_root / 'data' / 'results'

# Debug: Log paths on startup
print(f"Stock Service initialized:")
print(f"  Project root: {project_root}")
print(f"  Config dir: {config_dir} (exists: {config_dir.exists()})")
print(f"  Results dir: {results_dir} (exists: {results_dir.exists()})")
if config_dir.exists():
    config_files = list(config_dir.glob('*.cfg'))
    print(f"  Found {len(config_files)} config files")

# Track running processes - sync with DCF service
running_processes = {}

def sync_running_status():
    """Sync running status with Redis"""
    try:
        # Try Redis first with timeout
        from src.utils.redis_client import get_redis_client
        redis_client = get_redis_client()
        # Use a quick timeout to avoid blocking
        redis_analyses = redis_client.get_all_running_analyses()
        
        # Update running_processes from Redis
        running_processes.clear()
        for ticker, analysis_info in redis_analyses.items():
            if analysis_info.get('status') in ['running', 'processing']:
                running_processes[ticker] = {
                    'status': analysis_info.get('status'),
                    'started_at': analysis_info.get('started_at'),
                    'progress': analysis_info.get('progress'),
                    'progress_percent': analysis_info.get('progress_percent')
                }
    except Exception as e:
        # Fallback to HTTP sync if Redis fails - use shorter timeout
        if HAS_HTTPX:
            try:
                dcf_service_url = os.getenv('DCF_SERVICE_URL', 'http://dcf:8001')
                # Use shorter timeout to avoid blocking the request
                response = httpx.get(f"{dcf_service_url}/status", timeout=2.0)
                if response.status_code == 200:
                    dcf_status = response.json()
                    # Update running_processes from DCF service
                    for ticker, analysis_info in dcf_status.get('analyses', {}).items():
                        if analysis_info.get('status') in ['running', 'processing']:
                            running_processes[ticker] = {
                                'status': analysis_info.get('status'),
                                'started_at': analysis_info.get('started_at'),
                                'progress': analysis_info.get('progress'),
                                'progress_percent': analysis_info.get('progress_percent')
                            }
            except:
                # If sync fails, just continue with empty running_processes
                pass

@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "Stock Service", "version": "1.0"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return create_health_response("stock-service", include_database=True)

@app.get("/stocks")
async def list_stocks():
    """Lấy danh sách tất cả cổ phiếu với trạng thái"""
    # Sync running status with DCF service
    sync_running_status()
    
    stocks = []
    
    # Get all config files
    config_files = sorted(config_dir.glob('*.cfg'))
    
    # Fetch prices from database for all tickers in parallel
    ticker_list = [config_file.stem.upper() for config_file in config_files if config_file.stem.upper() != 'README']
    price_map = {}
    
    if HAS_HTTPX and ticker_list:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Fetch prices for all tickers in parallel
                tasks = []
                for ticker in ticker_list:
                    tasks.append(client.get(f"{DATABASE_SERVICE_URL}/api/database/stocks/{ticker}"))
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                for ticker, response in zip(ticker_list, responses):
                    if isinstance(response, Exception):
                        logger.warning(f"Could not fetch price from database for {ticker}: {response}")
                        continue
                    if response.status_code == 200:
                        db_data = response.json()
                        # Try to get current_price from metrics first, then market_data
                        current_price = db_data.get('metrics', {}).get('current_price')
                        if current_price is None:
                            current_price = db_data.get('market_data', {}).get('close_price')
                        if current_price is None:
                            current_price = db_data.get('current_price')
                        if current_price:
                            price_map[ticker] = current_price
                            logger.info(f"Fetched price for {ticker} from database: {current_price}")
                    else:
                        logger.warning(f"Failed to fetch price for {ticker}: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching prices from database: {e}", exc_info=True)
    
    for config_file in config_files:
        ticker = config_file.stem.upper()
        if ticker == 'README':
            continue
        
        # Check if result exists
        result_file = results_dir / f'{ticker.lower()}_result.json'
        has_result = result_file.exists()
        
        # Load result if exists
        result_data = None
        if has_result:
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    result_data = json.load(f)
            except:
                pass
        
        # Use database price if available, otherwise fallback to result file price
        current_price = price_map.get(ticker) if ticker in price_map else None
        if current_price is None:
            current_price = result_data.get('price') if result_data else None
        
        # Check if running
        is_running = ticker in running_processes
        running_info = running_processes.get(ticker, {})
        
        stock_info = {
            'ticker': ticker,
            'has_result': has_result,
            'is_running': is_running,
            'progress': running_info.get('progress'),
            'progress_percent': running_info.get('progress_percent', 0),
            'current_price': current_price,
            'dcf_fair_value': result_data.get('dcf_fair_value') if result_data else None,
            'graham_fair_value': result_data.get('graham_fair_value') if result_data else None,
            'average_fair_value': result_data.get('average_fair_value') if result_data else None,
            'saved_at': result_data.get('saved_at') if result_data else None,
            'upside_downside': None
        }
        
        # Calculate upside/downside
        if current_price and result_data and result_data.get('dcf_fair_value'):
            dcf_fv = result_data['dcf_fair_value']
            upside = ((dcf_fv - current_price) / current_price) * 100
            stock_info['upside_downside'] = round(upside, 2)
        
        stocks.append(stock_info)
    
    return {
        'stocks': stocks,
        'total': len(stocks),
        'with_results': sum(1 for s in stocks if s['has_result']),
        'running': sum(1 for s in stocks if s['is_running'])
    }

@app.get("/stocks/{ticker}")
def get_stock_detail(ticker: str):
    """Lấy thông tin chi tiết của một cổ phiếu"""
    ticker = ticker.upper()
    result_file = results_dir / f'{ticker.lower()}_result.json'
    
    if not result_file.exists():
        raise HTTPException(status_code=404, detail=f'No result found for {ticker}')
    
    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        # Load config
        config_file = config_dir / f'{ticker}.cfg'
        config_data = None
        if config_file.exists():
            import configparser
            config = configparser.ConfigParser()
            config.read(config_file)
            config_data = {section: dict(config[section]) for section in config.sections()}
        
        return {
            'ticker': ticker,
            'result': result_data,
            'config': config_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stocks/{ticker}/config")
def get_stock_config(ticker: str):
    """Lấy config của một cổ phiếu"""
    ticker = ticker.upper()
    config_file = config_dir / f'{ticker}.cfg'
    
    if not config_file.exists():
        raise HTTPException(status_code=404, detail=f'Config file not found for {ticker}')
    
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read(config_file)
        
        config_data = {}
        for section in config.sections():
            config_data[section] = dict(config[section])
        
        return {
            'ticker': ticker,
            'config': config_data,
            'config_file': str(config_file)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stocks/{ticker}/status")
def get_stock_status(ticker: str):
    """Lấy trạng thái của một cổ phiếu"""
    ticker = ticker.upper()
    
    # Sync running status with DCF service
    sync_running_status()
    
    if ticker in running_processes:
        return {
            'ticker': ticker,
            'is_running': True,
            'status': running_processes[ticker]
        }
    
    # Check if result exists
    result_file = results_dir / f'{ticker.lower()}_result.json'
    if result_file.exists():
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            return {
                'ticker': ticker,
                'is_running': False,
                'has_result': True,
                'saved_at': result_data.get('saved_at')
            }
        except:
            pass
    
    return {
        'ticker': ticker,
        'is_running': False,
        'has_result': False
    }

@app.get("/status")
def get_system_status():
    """Lấy trạng thái tổng thể của hệ thống"""
    config_files = list(config_dir.glob('*.cfg'))
    result_files = list(results_dir.glob('*_result.json'))
    
    return {
        'status': 'healthy',
        'total_stocks': len([f for f in config_files if f.stem.upper() != 'README']),
        'analyzed_stocks': len(result_files),
        'running_processes': len(running_processes),
        'running_tickers': list(running_processes.keys())
    }

