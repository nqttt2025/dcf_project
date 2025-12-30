# Data Sync Service - Architecture Design

## Tổng Quan

Tạo một service chuyên biệt để sync dữ liệu chứng khoán theo thời gian thực với:
- Job scheduler đáng tin cậy
- Retry mechanism
- Error handling tốt
- UI quản lý jobs (Jenkins-style)
- Logs và monitoring

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Data Sync Service                       │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Job Scheduler│  │ Job Executor │  │ Job Manager  │  │
│  │              │  │              │  │              │  │
│  │ - Cron jobs  │  │ - Run jobs   │  │ - CRUD jobs  │  │
│  │ - One-time   │  │ - Retry      │  │ - Status     │  │
│  │ - Manual     │  │ - Logs       │  │ - History    │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                  │                  │          │
│         └──────────────────┴──────────────────┘         │
│                          │                               │
│         ┌────────────────┴────────────────┐             │
│         │     Job Storage (PostgreSQL)    │             │
│         │  - jobs table                   │             │
│         │  - job_executions table         │             │
│         │  - job_logs table               │             │
│         └─────────────────────────────────┘             │
└─────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
    ┌─────────┐         ┌─────────┐         ┌─────────┐
    │ vnstock │         │Database │         │ Redis   │
    │   API   │         │ Service │         │ Cache   │
    └─────────┘         └─────────┘         └─────────┘
```

## Components

### 1. Job Scheduler
- Sử dụng APScheduler (Advanced Python Scheduler)
- Hỗ trợ cron expressions
- Persistent storage trong database
- Auto-recovery khi restart

### 2. Job Executor
- Chạy jobs trong background threads/processes
- Retry mechanism với exponential backoff
- Timeout handling
- Progress tracking

### 3. Job Manager
- CRUD operations cho jobs
- Job status tracking
- Execution history
- Logs management

### 4. Database Schema

```sql
-- Jobs definition
CREATE TABLE sync_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    job_type VARCHAR(50) NOT NULL, -- 'current_price', 'market_data', etc.
    schedule_type VARCHAR(50) NOT NULL, -- 'cron', 'interval', 'manual'
    schedule_config JSONB, -- cron expression or interval config
    config JSONB, -- job-specific config (ticker, days, etc.)
    enabled BOOLEAN DEFAULT TRUE,
    max_retries INTEGER DEFAULT 3,
    retry_delay INTEGER DEFAULT 60, -- seconds
    timeout INTEGER DEFAULT 3600, -- seconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job executions
CREATE TABLE job_executions (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) REFERENCES sync_jobs(job_id),
    execution_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration INTEGER, -- seconds
    progress_percent INTEGER DEFAULT 0,
    result JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job logs
CREATE TABLE job_logs (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(255) REFERENCES job_executions(execution_id),
    log_level VARCHAR(20) NOT NULL, -- 'DEBUG', 'INFO', 'WARNING', 'ERROR'
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_job_executions_job_id ON job_executions(job_id);
CREATE INDEX idx_job_executions_status ON job_executions(status);
CREATE INDEX idx_job_executions_started_at ON job_executions(started_at DESC);
CREATE INDEX idx_job_logs_execution_id ON job_logs(execution_id);
CREATE INDEX idx_job_logs_timestamp ON job_logs(timestamp DESC);
```

## API Endpoints

### Job Management
- `GET /api/jobs` - List all jobs
- `GET /api/jobs/{job_id}` - Get job details
- `POST /api/jobs` - Create new job
- `PUT /api/jobs/{job_id}` - Update job
- `DELETE /api/jobs/{job_id}` - Delete job

### Job Execution
- `POST /api/jobs/{job_id}/run` - Run job manually
- `POST /api/jobs/{job_id}/stop` - Stop running job
- `GET /api/jobs/{job_id}/executions` - Get execution history
- `GET /api/jobs/{job_id}/executions/{execution_id}` - Get execution details
- `GET /api/jobs/{job_id}/executions/{execution_id}/logs` - Get execution logs

### Status & Monitoring
- `GET /api/status` - Service status
- `GET /api/metrics` - Job metrics

## Job Types

1. **current_price_sync** - Sync current price
2. **market_data_sync** - Sync historical market data
3. **financial_data_sync** - Sync financial statements
4. **shares_outstanding_sync** - Sync shares outstanding
5. **base_pe_update** - Update base PE ratios

## Frontend Page (Jenkins-style)

### Features:
- Job list với status indicators
- Job details với configuration
- Execution history table
- Real-time logs viewer
- Run/Stop buttons
- Progress bars
- Error messages
- Filtering và search

### UI Components:
- Job cards với status badges
- Execution timeline
- Logs viewer với auto-scroll
- Configuration editor
- Schedule editor (cron builder)

