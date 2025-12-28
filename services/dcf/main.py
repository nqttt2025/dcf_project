"""
DCF Service - Microservice xử lý phân tích DCF
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
# Handle both Docker (/app) and local development
if Path('/app').exists():
    project_root = Path('/app')
else:
    # Local development: go up from services/dcf/main.py to project root
    project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.dcf_calculator import calculate_dcf_from_config
from src.utils.result_manager import get_result_manager

app = FastAPI(title="DCF Analysis Service")

# Initialize managers
result_manager = get_result_manager()
config_dir = project_root / 'config'
results_dir = project_root / 'data' / 'results'

# Track running analyses
running_analyses = {}

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
    return {"status": "healthy", "service": "dcf-service"}

@app.post("/analyze/{ticker}")
async def run_analysis(ticker: str, background_tasks: BackgroundTasks):
    """Chạy phân tích DCF cho một cổ phiếu"""
    ticker = ticker.upper()
    
    # Check if already running
    if ticker in running_analyses:
        raise HTTPException(status_code=400, detail=f'Analysis already running for {ticker}')
    
    # Check if config exists
    config_file = config_dir / f'{ticker}.cfg'
    if not config_file.exists():
        raise HTTPException(status_code=404, detail=f'Config file not found for {ticker}')
    
    # Mark as running
    running_analyses[ticker] = {
        'started_at': datetime.now().isoformat(),
        'status': 'running'
    }
    
    # Run analysis in background
    background_tasks.add_task(perform_analysis, ticker, str(config_file))
    
    return {
        'message': f'Analysis started for {ticker}',
        'ticker': ticker,
        'status': 'running'
    }

async def perform_analysis(ticker: str, config_file: str):
    """Perform DCF analysis"""
    try:
        # Update status to processing
        running_analyses[ticker]['status'] = 'processing'
        running_analyses[ticker]['progress'] = 'Fetching data...'
        
        # Run DCF calculation
        result = await calculate_dcf_from_config(config_file)
        
        # Mark as completed
        running_analyses[ticker] = {
            'started_at': running_analyses[ticker]['started_at'],
            'completed_at': datetime.now().isoformat(),
            'status': 'completed',
            'result': result
        }
        
        # Remove from running after 5 minutes (cleanup)
        import asyncio
        await asyncio.sleep(300)  # 5 minutes
        if ticker in running_analyses and running_analyses[ticker]['status'] == 'completed':
            running_analyses.pop(ticker, None)
    except Exception as e:
        # Mark as failed
        running_analyses[ticker] = {
            'started_at': running_analyses[ticker]['started_at'],
            'failed_at': datetime.now().isoformat(),
            'status': 'failed',
            'error': str(e)
        }
        
        # Remove from running after 1 minute (cleanup)
        import asyncio
        await asyncio.sleep(60)  # 1 minute
        if ticker in running_analyses and running_analyses[ticker]['status'] == 'failed':
            running_analyses.pop(ticker, None)

@app.get("/analysis/{ticker}")
def get_analysis_result(ticker: str):
    """Lấy kết quả phân tích DCF"""
    ticker = ticker.upper()
    
    # Check if running
    if ticker in running_analyses:
        return {
            'ticker': ticker,
            'status': running_analyses[ticker]['status'],
            'analysis': running_analyses[ticker]
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
    return {
        'status': 'healthy',
        'running_analyses': len(running_analyses),
        'analyses': running_analyses
    }

