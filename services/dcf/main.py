"""
DCF Service - Microservice xử lý phân tích DCF
"""
import sys
from pathlib import Path

# Setup project path first (before importing services.common)
if Path('/app').exists():
    project_root = Path('/app')
else:
    project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import asyncio
from datetime import datetime

# Import common utilities after path setup
from services.common import create_health_response

from src.core.dcf_calculator import calculate_dcf_from_config
from src.utils.result_manager import get_result_manager
from src.utils.redis_client import get_redis_client

app = FastAPI(title="DCF Analysis Service")

# Initialize managers
result_manager = get_result_manager()
redis_client = get_redis_client()
config_dir = project_root / 'config'
results_dir = project_root / 'data' / 'results'

class AnalysisRequest(BaseModel):
    ticker: str
    config_file: Optional[str] = None

@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "DCF Analysis Service", "version": "1.0"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return create_health_response("dcf-service", include_database=True)

# Semaphore to limit concurrent analyses
_analysis_semaphore = asyncio.Semaphore(10)  # Max 10 concurrent analyses

@app.post("/analyze/{ticker}")
async def run_analysis(ticker: str, background_tasks: BackgroundTasks):
    """Chạy phân tích DCF cho một cổ phiếu"""
    ticker = ticker.upper()
    
    # Check if already running (from Redis)
    existing_status = redis_client.get_analysis_status(ticker)
    if existing_status and existing_status.get('status') in ['running', 'processing']:
        raise HTTPException(status_code=400, detail=f'Analysis already running for {ticker}')
    
    # Check concurrent limit
    running_count = len(redis_client.get_all_running_analyses())
    if running_count >= 10:
        raise HTTPException(
            status_code=503, 
            detail=f'Service busy: Maximum 10 concurrent analyses allowed. Currently running: {running_count}'
        )
    
    # Check if config exists
    config_file = config_dir / f'{ticker}.cfg'
    if not config_file.exists():
        raise HTTPException(status_code=404, detail=f'Config file not found for {ticker}')
    
    # Mark as running in Redis
    started_at = datetime.now().isoformat()
    redis_client.set_analysis_status(
        ticker,
        'running',
        progress='Initializing...',
        progress_percent=0.0,
        started_at=started_at
    )
    
    # Run analysis in background (semaphore is handled in perform_analysis)
    background_tasks.add_task(perform_analysis, ticker, str(config_file), started_at)
    
    return {
        'message': f'Analysis started for {ticker}',
        'ticker': ticker,
        'status': 'running',
        'queue_position': running_count
    }

async def perform_analysis(ticker: str, config_file: str, started_at: str):
    """Perform DCF analysis with progress tracking"""
    # Use semaphore to limit concurrent analyses
    async with _analysis_semaphore:
        try:
            # Update status to processing
            redis_client.set_analysis_status(
                ticker,
                'processing',
                progress='Fetching financial data...',
                progress_percent=10.0,
                started_at=started_at
            )
            
            # Run DCF calculation with progress callbacks
            result = await calculate_dcf_from_config(config_file, progress_callback=lambda p, msg: 
                redis_client.set_analysis_status(
                    ticker,
                    'processing',
                    progress=msg,
                    progress_percent=p,
                    started_at=started_at
                )
            )
            
            # Mark as completed
            redis_client.set_analysis_status(
                ticker,
                'completed',
                progress='Analysis completed',
                progress_percent=100.0,
                started_at=started_at,
                completed_at=datetime.now().isoformat(),
                result=result
            )
            
            # Remove from Redis after 5 minutes (cleanup)
            await asyncio.sleep(300)  # 5 minutes
            redis_client.delete_analysis_status(ticker)
        except Exception as e:
            # Mark as failed
            redis_client.set_analysis_status(
                ticker,
                'failed',
                progress=f'Error: {str(e)}',
                progress_percent=0.0,
                started_at=started_at,
                failed_at=datetime.now().isoformat(),
                error=str(e)
            )
            
            # Remove from Redis after 1 minute (cleanup)
            await asyncio.sleep(60)  # 1 minute
            redis_client.delete_analysis_status(ticker)

@app.get("/analysis/{ticker}")
def get_analysis_result(ticker: str):
    """Lấy kết quả phân tích DCF"""
    ticker = ticker.upper()
    
    # Check Redis first
    redis_status = redis_client.get_analysis_status(ticker)
    if redis_status:
        return {
            'ticker': ticker,
            'status': redis_status.get('status'),
            'analysis': redis_status
        }
    
    # Check if result exists in file
    result_file = results_dir / f'{ticker.lower()}_result.json'
    if result_file.exists():
        try:
            import json
            with open(result_file, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            return {
                'ticker': ticker,
                'status': 'completed',
                'result': result_data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    raise HTTPException(status_code=404, detail=f'No analysis result found for {ticker}')

@app.get("/status")
def get_service_status():
    """Lấy trạng thái của service"""
    running_analyses = redis_client.get_all_running_analyses()
    return {
        'status': 'healthy',
        'running_analyses': len(running_analyses),
        'analyses': running_analyses
    }

