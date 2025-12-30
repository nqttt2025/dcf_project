"""
Data Sync Service - Chuyên biệt cho việc sync dữ liệu chứng khoán
"""
import sys
from pathlib import Path

# Setup project path
if Path('/app').exists():
    project_root = Path('/app')
else:
    project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict
from datetime import datetime, timezone
import asyncio
import logging
import json
import uuid
import os
from pydantic import BaseModel

# Import common utilities
from services.common import create_health_response, get_service_urls
from src.utils.service_logger import setup_service_logger

logger = setup_service_logger('sync-service', level=logging.INFO)

app = FastAPI(title="Data Sync Service", version="1.0.0")

# Get service URLs
service_urls = get_service_urls()
DATABASE_SERVICE_URL = service_urls.get("database", "http://database:8003")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Note: Database connection will be added later when implementing persistent storage
# For now, using in-memory storage

# Job storage (in-memory for now, will move to database)
jobs_store = {}
executions_store = {}
logs_store = {}

# Pydantic models
class JobConfig(BaseModel):
    ticker: Optional[str] = None
    days: Optional[int] = None
    other: Optional[Dict] = None

class JobCreate(BaseModel):
    job_id: str
    name: str
    description: Optional[str] = None
    job_type: str
    schedule_type: str  # 'cron', 'interval', 'manual'
    schedule_config: Optional[Dict] = None
    config: Optional[JobConfig] = None
    enabled: bool = True
    max_retries: int = 3
    retry_delay: int = 60
    timeout: int = 3600

class JobResponse(BaseModel):
    job_id: str
    name: str
    description: Optional[str]
    job_type: str
    schedule_type: str
    schedule_config: Optional[Dict]
    config: Optional[Dict]
    enabled: bool
    status: str
    last_execution: Optional[Dict] = None

class ExecutionResponse(BaseModel):
    execution_id: str
    job_id: str
    status: str
    started_at: Optional[str]
    completed_at: Optional[str]
    duration: Optional[int]
    progress_percent: int
    result: Optional[Dict]
    error_message: Optional[str]

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "Data Sync Service",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return create_health_response("sync-service", include_database=True)

@app.get("/api/jobs")
async def list_jobs():
    """List all sync jobs"""
    jobs = []
    for job_id, job in jobs_store.items():
        last_execution = None
        if job_id in executions_store and executions_store[job_id]:
            last_exec = max(executions_store[job_id], key=lambda x: x.get('started_at', ''))
            last_execution = {
                "execution_id": last_exec.get('execution_id'),
                "status": last_exec.get('status'),
                "started_at": last_exec.get('started_at'),
                "completed_at": last_exec.get('completed_at')
            }
        
        jobs.append({
            "job_id": job_id,
            "name": job.get('name'),
            "description": job.get('description'),
            "job_type": job.get('job_type'),
            "schedule_type": job.get('schedule_type'),
            "enabled": job.get('enabled', True),
            "status": "running" if last_execution and last_execution.get('status') == 'running' else "idle",
            "last_execution": last_execution
        })
    
    return {
        "jobs": jobs,
        "total": len(jobs)
    }

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job details"""
    if job_id not in jobs_store:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    
    job = jobs_store[job_id]
    executions = executions_store.get(job_id, [])
    
    return {
        "job": job,
        "executions": executions[-10:],  # Last 10 executions
        "total_executions": len(executions)
    }

@app.post("/api/jobs")
async def create_job(job: JobCreate):
    """Create a new sync job"""
    if job.job_id in jobs_store:
        raise HTTPException(status_code=400, detail=f"Job '{job.job_id}' already exists")
    
    job_dict = job.dict()
    job_dict['created_at'] = datetime.now(timezone.utc).isoformat()
    job_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    jobs_store[job.job_id] = job_dict
    executions_store[job.job_id] = []
    
    logger.info(f"Created job: {job.job_id} ({job.name})")
    
    return {
        "message": f"Job '{job.job_id}' created successfully",
        "job": job_dict
    }

@app.post("/api/jobs/{job_id}/run")
async def run_job(job_id: str, background_tasks: BackgroundTasks):
    """Run a job manually"""
    if job_id not in jobs_store:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    
    job = jobs_store[job_id]
    if not job.get('enabled', True):
        raise HTTPException(status_code=400, detail=f"Job '{job_id}' is disabled")
    
    # Check if job is already running
    if job_id in executions_store:
        running_executions = [e for e in executions_store[job_id] if e.get('status') == 'running']
        if running_executions:
            raise HTTPException(status_code=400, detail=f"Job '{job_id}' is already running")
    
    # Create execution
    execution_id = f"{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    execution = {
        "execution_id": execution_id,
        "job_id": job_id,
        "status": "pending",
        "started_at": None,
        "completed_at": None,
        "duration": None,
        "progress_percent": 0,
        "current_step": None,
        "step_message": None,
        "steps": [],
        "steps_detail": [],
        "result": None,
        "error_message": None,
        "retry_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    if job_id not in executions_store:
        executions_store[job_id] = []
    executions_store[job_id].append(execution)
    logs_store[execution_id] = []
    
    # Start job execution in background
    background_tasks.add_task(execute_job, job_id, execution_id)
    
    logger.info(f"Started execution: {execution_id} for job: {job_id}")
    
    return {
        "message": f"Job '{job_id}' started",
        "execution_id": execution_id,
        "status": "pending"
    }

def update_progress(execution_id: str, step: str, percent: int, message: str = ""):
    """Update execution progress"""
    # Find execution in all jobs
    for job_id, executions in executions_store.items():
        execution = next((e for e in executions if e['execution_id'] == execution_id), None)
        if execution:
            execution['progress_percent'] = percent
            execution['current_step'] = step
            execution['step_message'] = message
            if 'steps_detail' not in execution:
                execution['steps_detail'] = []
            execution['steps_detail'].append({
                'step': step,
                'percent': percent,
                'message': message,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            add_log(execution_id, "INFO", f"[{percent}%] {step}: {message}")
            break

async def update_redis_cache_after_sync(job_type: str, ticker: Optional[str], sync_result: Dict):
    """Update Redis cache after syncing data to database"""
    try:
        from src.utils.redis_client import get_redis_client
        redis_client = get_redis_client()
        
        if not redis_client or not redis_client._client:
            logger.warning("Redis client not available, skipping cache update")
            return
        
        # Get list of tickers that were synced
        tickers_to_update = []
        if ticker:
            tickers_to_update = [ticker.upper()]
        else:
            # If syncing all, get list from result or fetch from database
            if sync_result and 'processed' in sync_result:
                # Try to get tickers from result details
                details = sync_result.get('details', [])
                tickers_to_update = [d.get('ticker') for d in details if d.get('ticker')]
            else:
                # Fetch all active tickers from database
                import httpx
                async with httpx.AsyncClient(timeout=10.0) as client:
                    try:
                        response = await client.get(f"{DATABASE_SERVICE_URL}/api/database/stocks")
                        if response.status_code == 200:
                            stocks_data = response.json()
                            tickers_to_update = [s.get('ticker') for s in stocks_data.get('stocks', []) if s.get('ticker')]
                    except Exception as e:
                        logger.warning(f"Could not fetch tickers list: {e}")
        
        if not tickers_to_update:
            logger.warning("No tickers to update in Redis cache")
            return
        
        # Update cache for each ticker based on job type
        for ticker_item in tickers_to_update:
            try:
                # Fetch latest data from database for this ticker
                import httpx
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{DATABASE_SERVICE_URL}/api/database/stocks/{ticker_item}")
                    if response.status_code == 200:
                        stock_data = response.json()
                        
                        # Update Redis cache based on job type
                        if job_type == 'current_price' or job_type == 'market_data':
                            # Cache market data
                            market_data = stock_data.get('market_data', {})
                            if market_data:
                                redis_client.cache_market_data(ticker_item, {
                                    'current_price': market_data.get('close_price'),
                                    'market_cap': stock_data.get('metrics', {}).get('market_cap'),
                                    'pe_ratio': stock_data.get('metrics', {}).get('pe_ratio'),
                                    'source': 'sync_service',
                                    'updated_at': datetime.now(timezone.utc).isoformat()
                                })
                                logger.info(f"Updated Redis cache for {ticker_item}: market_data")
                        
                        elif job_type == 'financial_data':
                            # Cache financial TTM data
                            financial_data = stock_data.get('financial_data', {})
                            if financial_data:
                                redis_client.cache_financial_ttm(ticker_item, {
                                    'ttm_fcf': financial_data.get('ttm_fcf'),
                                    'ttm_ocf': financial_data.get('ttm_ocf'),
                                    'ttm_capex': financial_data.get('ttm_capex'),
                                    'source': 'sync_service',
                                    'updated_at': datetime.now(timezone.utc).isoformat()
                                })
                                logger.info(f"Updated Redis cache for {ticker_item}: financial_data")
                        
                        elif job_type == 'shares_outstanding':
                            # Cache shares outstanding
                            shares_data = stock_data.get('shares_outstanding', {})
                            if shares_data:
                                redis_client.cache_shares(
                                    ticker_item,
                                    shares_data.get('shares', 0),
                                    par_value=shares_data.get('par_value', 10000),
                                    calculation_method='sync_service'
                                )
                                logger.info(f"Updated Redis cache for {ticker_item}: shares_outstanding")
                        
                        elif job_type == 'base_pe':
                            # Cache stock info
                            stock_info = stock_data.get('stock', {})
                            metrics = stock_data.get('metrics', {})
                            if stock_info:
                                redis_client.cache_stock_info(ticker_item, {
                                    'base_pe': stock_info.get('base_pe'),
                                    'current_pe': metrics.get('pe_ratio'),
                                    'source': 'sync_service',
                                    'updated_at': datetime.now(timezone.utc).isoformat()
                                })
                                logger.info(f"Updated Redis cache for {ticker_item}: stock_info")
                        
            except Exception as e:
                logger.warning(f"Error updating Redis cache for {ticker_item}: {e}")
        
        logger.info(f"Redis cache update completed for {len(tickers_to_update)} ticker(s)")
        
    except Exception as e:
        logger.error(f"Error updating Redis cache: {e}", exc_info=True)

async def execute_job(job_id: str, execution_id: str):
    """Execute a job with detailed progress tracking"""
    try:
        # Update execution status
        execution = next((e for e in executions_store[job_id] if e['execution_id'] == execution_id), None)
        if not execution:
            logger.error(f"Execution {execution_id} not found")
            return
        
        execution['status'] = 'running'
        execution['started_at'] = datetime.now(timezone.utc).isoformat()
        execution['steps'] = []
        
        # Add log
        add_log(execution_id, "INFO", f"Starting job execution: {job_id}")
        update_progress(execution_id, "Initializing", 0, "Preparing job execution")
        
        # Get job config
        job = jobs_store[job_id]
        job_type = job.get('job_type')
        config = job.get('config', {})
        ticker = config.get('ticker') if isinstance(config, dict) else None
        
        # Define steps based on job type
        steps = []
        if job_type == 'current_price':
            steps = [
                {"name": "Fetching data from vnstock API", "percent": 20},
                {"name": "Updating database (market_data table)", "percent": 50},
                {"name": "Updating Redis cache (market data)", "percent": 80},
                {"name": "Finalizing", "percent": 100}
            ]
            result = await sync_current_price_with_progress(execution_id, ticker, steps)
        elif job_type == 'market_data':
            steps = [
                {"name": "Fetching historical data from vnstock API", "percent": 20},
                {"name": "Updating database (market_data table)", "percent": 60},
                {"name": "Updating Redis cache (market data)", "percent": 90},
                {"name": "Finalizing", "percent": 100}
            ]
            result = await sync_market_data_with_progress(execution_id, ticker, config.get('days', 7), steps)
        elif job_type == 'financial_data':
            steps = [
                {"name": "Fetching financial statements from vnstock API", "percent": 20},
                {"name": "Updating database (financial_data table)", "percent": 60},
                {"name": "Updating Redis cache (financial TTM)", "percent": 90},
                {"name": "Finalizing", "percent": 100}
            ]
            result = await sync_financial_data_with_progress(execution_id, ticker, steps)
        elif job_type == 'shares_outstanding':
            steps = [
                {"name": "Fetching shares data from vnstock API", "percent": 20},
                {"name": "Updating database (shares_outstanding table)", "percent": 60},
                {"name": "Updating Redis cache (shares)", "percent": 90},
                {"name": "Finalizing", "percent": 100}
            ]
            result = await sync_shares_outstanding_with_progress(execution_id, ticker, steps)
        elif job_type == 'base_pe':
            steps = [
                {"name": "Calculating base PE ratios", "percent": 30},
                {"name": "Updating database (stocks table)", "percent": 70},
                {"name": "Updating Redis cache (stock info)", "percent": 90},
                {"name": "Finalizing", "percent": 100}
            ]
            result = await sync_base_pe_with_progress(execution_id, ticker, steps)
        else:
            raise ValueError(f"Unknown job type: {job_type}")
        
        execution['steps'] = steps
        
        # Update execution
        execution['status'] = 'completed'
        execution['completed_at'] = datetime.now(timezone.utc).isoformat()
        execution['result'] = result
        execution['progress_percent'] = 100
        execution['current_step'] = "Completed"
        execution['step_message'] = "Job execution completed successfully"
        
        started = datetime.fromisoformat(execution['started_at'].replace('Z', '+00:00'))
        completed = datetime.fromisoformat(execution['completed_at'].replace('Z', '+00:00'))
        execution['duration'] = int((completed - started).total_seconds())
        
        add_log(execution_id, "INFO", f"Job execution completed successfully")
        
    except Exception as e:
        logger.error(f"Error executing job {job_id}: {e}", exc_info=True)
        execution = next((e for e in executions_store[job_id] if e['execution_id'] == execution_id), None)
        if execution:
            execution['status'] = 'failed'
            execution['completed_at'] = datetime.now(timezone.utc).isoformat()
            execution['error_message'] = str(e)
            execution['current_step'] = "Failed"
            execution['step_message'] = str(e)
            add_log(execution_id, "ERROR", f"Job execution failed: {str(e)}")

async def sync_current_price_with_progress(execution_id: str, ticker: Optional[str] = None, steps: List[Dict] = None):
    """Sync current price with progress tracking"""
    import httpx
    
    # Step 1: Fetching data from vnstock API
    if steps and len(steps) > 0:
        update_progress(execution_id, steps[0]["name"], steps[0]["percent"], "Connecting to vnstock API...")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        url = f"{DATABASE_SERVICE_URL}/api/database/sync/current-price"
        if ticker:
            url += f"?ticker={ticker}"
        response = await client.post(url)
        if response.status_code != 200:
            raise Exception(f"Failed to sync current price: {response.text}")
        
        result = response.json()
        
        # Step 2: Database updated (done by database service)
        if steps and len(steps) > 1:
            update_progress(execution_id, steps[1]["name"], steps[1]["percent"], "Database updated successfully")
        
        # Step 3: Update Redis cache
        if steps and len(steps) > 2:
            update_progress(execution_id, steps[2]["name"], steps[2]["percent"], "Updating Redis cache...")
            await update_redis_cache_after_sync("current_price", ticker, result)
        
        # Step 4: Finalizing
        if steps and len(steps) > 3:
            update_progress(execution_id, steps[3]["name"], steps[3]["percent"], "Sync completed")
        
        return result

async def sync_current_price(ticker: Optional[str] = None):
    """Sync current price (legacy, for backward compatibility)"""
    return await sync_current_price_with_progress("", ticker, [])

async def sync_market_data_with_progress(execution_id: str, ticker: Optional[str] = None, days: int = 7, steps: List[Dict] = None):
    """Sync market data with progress tracking"""
    import httpx
    
    # Step 1: Fetching historical data
    if steps and len(steps) > 0:
        update_progress(execution_id, steps[0]["name"], steps[0]["percent"], f"Fetching {days} days of data...")
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        url = f"{DATABASE_SERVICE_URL}/api/database/sync/market_data?days={days}"
        if ticker:
            url += f"&ticker={ticker}"
        response = await client.post(url)
        if response.status_code != 200:
            raise Exception(f"Failed to sync market data: {response.text}")
        
        result = response.json()
        
        # Step 2: Database updated
        if steps and len(steps) > 1:
            update_progress(execution_id, steps[1]["name"], steps[1]["percent"], "Database updated successfully")
        
        # Step 3: Update Redis cache
        if steps and len(steps) > 2:
            update_progress(execution_id, steps[2]["name"], steps[2]["percent"], "Updating Redis cache...")
            await update_redis_cache_after_sync("market_data", ticker, result)
        
        # Step 4: Finalizing
        if steps and len(steps) > 3:
            update_progress(execution_id, steps[3]["name"], steps[3]["percent"], "Sync completed")
        
        return result

async def sync_market_data(ticker: Optional[str] = None, days: int = 7):
    """Sync market data (legacy)"""
    return await sync_market_data_with_progress("", ticker, days, [])

async def sync_financial_data_with_progress(execution_id: str, ticker: Optional[str] = None, steps: List[Dict] = None):
    """Sync financial data with progress tracking"""
    import httpx
    
    if steps and len(steps) > 0:
        update_progress(execution_id, steps[0]["name"], steps[0]["percent"], "Fetching financial statements...")
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        url = f"{DATABASE_SERVICE_URL}/api/database/sync/financial_data"
        if ticker:
            url += f"?ticker={ticker}"
        response = await client.post(url)
        if response.status_code != 200:
            raise Exception(f"Failed to sync financial data: {response.text}")
        
        result = response.json()
        
        if steps and len(steps) > 1:
            update_progress(execution_id, steps[1]["name"], steps[1]["percent"], "Database updated successfully")
        
        if steps and len(steps) > 2:
            update_progress(execution_id, steps[2]["name"], steps[2]["percent"], "Updating Redis cache...")
            await update_redis_cache_after_sync("financial_data", ticker, result)
        
        if steps and len(steps) > 3:
            update_progress(execution_id, steps[3]["name"], steps[3]["percent"], "Sync completed")
        
        return result

async def sync_financial_data(ticker: Optional[str] = None):
    """Sync financial data (legacy)"""
    return await sync_financial_data_with_progress("", ticker, [])

async def sync_shares_outstanding_with_progress(execution_id: str, ticker: Optional[str] = None, steps: List[Dict] = None):
    """Sync shares outstanding with progress tracking"""
    import httpx
    
    if steps and len(steps) > 0:
        update_progress(execution_id, steps[0]["name"], steps[0]["percent"], "Fetching shares data...")
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        url = f"{DATABASE_SERVICE_URL}/api/database/sync/shares_outstanding"
        if ticker:
            url += f"?ticker={ticker}"
        response = await client.post(url)
        if response.status_code != 200:
            raise Exception(f"Failed to sync shares outstanding: {response.text}")
        
        result = response.json()
        
        if steps and len(steps) > 1:
            update_progress(execution_id, steps[1]["name"], steps[1]["percent"], "Database updated successfully")
        
        if steps and len(steps) > 2:
            update_progress(execution_id, steps[2]["name"], steps[2]["percent"], "Updating Redis cache...")
            await update_redis_cache_after_sync("shares_outstanding", ticker, result)
        
        if steps and len(steps) > 3:
            update_progress(execution_id, steps[3]["name"], steps[3]["percent"], "Sync completed")
        
        return result

async def sync_shares_outstanding(ticker: Optional[str] = None):
    """Sync shares outstanding (legacy)"""
    return await sync_shares_outstanding_with_progress("", ticker, [])

async def sync_base_pe_with_progress(execution_id: str, ticker: Optional[str] = None, steps: List[Dict] = None):
    """Sync base PE with progress tracking"""
    import httpx
    
    if steps and len(steps) > 0:
        update_progress(execution_id, steps[0]["name"], steps[0]["percent"], "Calculating PE ratios...")
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        url = f"{DATABASE_SERVICE_URL}/api/database/sync/base-pe"
        if ticker:
            url += f"?ticker={ticker}"
        response = await client.post(url)
        if response.status_code != 200:
            raise Exception(f"Failed to sync base PE: {response.text}")
        
        result = response.json()
        
        if steps and len(steps) > 1:
            update_progress(execution_id, steps[1]["name"], steps[1]["percent"], "Database updated successfully")
        
        if steps and len(steps) > 2:
            update_progress(execution_id, steps[2]["name"], steps[2]["percent"], "Updating Redis cache...")
            await update_redis_cache_after_sync("base_pe", ticker, result)
        
        if steps and len(steps) > 3:
            update_progress(execution_id, steps[3]["name"], steps[3]["percent"], "Sync completed")
        
        return result

async def sync_base_pe(ticker: Optional[str] = None):
    """Sync base PE (legacy)"""
    return await sync_base_pe_with_progress("", ticker, [])

def add_log(execution_id: str, level: str, message: str):
    """Add log entry"""
    if execution_id not in logs_store:
        logs_store[execution_id] = []
    
    logs_store[execution_id].append({
        "level": level,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.get("/api/jobs/{job_id}/executions/{execution_id}")
async def get_execution(job_id: str, execution_id: str):
    """Get execution details"""
    if job_id not in executions_store:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    
    execution = next((e for e in executions_store[job_id] if e['execution_id'] == execution_id), None)
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution '{execution_id}' not found")
    
    logs = logs_store.get(execution_id, [])
    
    return {
        "execution": execution,
        "logs": logs
    }

@app.get("/api/jobs/{job_id}/executions/{execution_id}/logs")
async def get_execution_logs(job_id: str, execution_id: str):
    """Get execution logs as SSE stream"""
    async def log_generator():
        logs = logs_store.get(execution_id, [])
        for log in logs:
            yield f"data: {json.dumps(log)}\n\n"
        
        # Keep connection alive and send new logs
        execution = next((e for e in executions_store.get(job_id, []) if e['execution_id'] == execution_id), None)
        if execution and execution.get('status') == 'running':
            # Poll for new logs
            last_count = len(logs)
            while True:
                await asyncio.sleep(1)
                current_logs = logs_store.get(execution_id, [])
                if len(current_logs) > last_count:
                    for log in current_logs[last_count:]:
                        yield f"data: {json.dumps(log)}\n\n"
                    last_count = len(current_logs)
                
                # Check if execution completed
                execution = next((e for e in executions_store.get(job_id, []) if e['execution_id'] == execution_id), None)
                if not execution or execution.get('status') != 'running':
                    break
    
    return StreamingResponse(
        log_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.post("/api/jobs/{job_id}/stop")
async def stop_job(job_id: str, execution_id: Optional[str] = None):
    """Stop a running job"""
    if job_id not in executions_store:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    
    if execution_id:
        execution = next((e for e in executions_store[job_id] if e['execution_id'] == execution_id), None)
        if not execution:
            raise HTTPException(status_code=404, detail=f"Execution '{execution_id}' not found")
        if execution.get('status') != 'running':
            raise HTTPException(status_code=400, detail=f"Execution '{execution_id}' is not running")
        
        execution['status'] = 'cancelled'
        execution['completed_at'] = datetime.now(timezone.utc).isoformat()
        add_log(execution_id, "INFO", "Job execution cancelled by user")
    else:
        # Stop all running executions for this job
        running_executions = [e for e in executions_store[job_id] if e.get('status') == 'running']
        if not running_executions:
            raise HTTPException(status_code=400, detail=f"No running executions for job '{job_id}'")
        
        for execution in running_executions:
            execution['status'] = 'cancelled'
            execution['completed_at'] = datetime.now(timezone.utc).isoformat()
            add_log(execution['execution_id'], "INFO", "Job execution cancelled by user")
    
    return {
        "message": f"Job '{job_id}' stopped",
        "execution_id": execution_id
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)

