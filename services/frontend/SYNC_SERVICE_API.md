# Sync Service API Endpoints

Tài liệu này mô tả các API endpoints của Sync Service có thể truy cập từ frontend qua Gateway.

## Base URL

Tất cả các endpoints được truy cập qua Gateway tại: `/api/sync`

## Endpoints

### 1. List All Jobs
**GET** `/api/sync/jobs`

Lấy danh sách tất cả sync jobs.

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "sync_market_data",
      "name": "Sync Market Data",
      "description": "Sync market data for all stocks",
      "job_type": "market_data",
      "schedule_type": "daily",
      "enabled": true,
      "status": "idle",
      "last_execution": {
        "execution_id": "exec_123",
        "status": "completed",
        "started_at": "2025-12-30T10:00:00Z",
        "completed_at": "2025-12-30T10:05:00Z"
      }
    }
  ],
  "total": 1
}
```

### 2. Get Job Details
**GET** `/api/sync/jobs/{job_id}`

Lấy thông tin chi tiết của một job bao gồm các executions.

**Response:**
```json
{
  "job": {
    "job_id": "sync_market_data",
    "name": "Sync Market Data",
    "description": "Sync market data for all stocks",
    "job_type": "market_data",
    "schedule_type": "daily",
    "enabled": true,
    "created_at": "2025-12-30T10:00:00Z",
    "updated_at": "2025-12-30T10:00:00Z"
  },
  "executions": [
    {
      "execution_id": "exec_123",
      "status": "completed",
      "started_at": "2025-12-30T10:00:00Z",
      "completed_at": "2025-12-30T10:05:00Z"
    }
  ],
  "total_executions": 1
}
```

### 3. Create Job
**POST** `/api/sync/jobs`

Tạo một sync job mới.

**Request Body:**
```json
{
  "job_id": "sync_market_data",
  "name": "Sync Market Data",
  "description": "Sync market data for all stocks",
  "job_type": "market_data",
  "schedule_type": "daily",
  "enabled": true
}
```

**Response:**
```json
{
  "message": "Job 'sync_market_data' created successfully",
  "job": {
    "job_id": "sync_market_data",
    "name": "Sync Market Data",
    ...
  }
}
```

### 4. Run Job
**POST** `/api/sync/jobs/{job_id}/run`

Chạy một job thủ công.

**Response:**
```json
{
  "message": "Job 'sync_market_data' started",
  "execution_id": "exec_123"
}
```

### 5. Stop Job
**POST** `/api/sync/jobs/{job_id}/stop?execution_id={execution_id}`

Dừng một job đang chạy.

**Query Parameters:**
- `execution_id` (optional): ID của execution cần dừng. Nếu không có, sẽ dừng execution đang chạy.

**Response:**
```json
{
  "message": "Job 'sync_market_data' stopped",
  "execution_id": "exec_123"
}
```

### 6. Get Execution Details
**GET** `/api/sync/jobs/{job_id}/executions/{execution_id}`

Lấy thông tin chi tiết của một execution bao gồm logs.

**Response:**
```json
{
  "execution": {
    "execution_id": "exec_123",
    "status": "completed",
    "started_at": "2025-12-30T10:00:00Z",
    "completed_at": "2025-12-30T10:05:00Z",
    "result": {...},
    "error_message": null
  },
  "logs": [
    {
      "level": "info",
      "message": "Starting sync...",
      "timestamp": "2025-12-30T10:00:00Z"
    }
  ]
}
```

### 7. Get Execution Logs (SSE Stream)
**GET** `/api/sync/jobs/{job_id}/executions/{execution_id}/logs`

Lấy logs của một execution dưới dạng Server-Sent Events (SSE) stream. Endpoint này sẽ stream logs real-time khi execution đang chạy.

**Response:** SSE stream với format:
```
data: {"level":"info","message":"Starting sync...","timestamp":"2025-12-30T10:00:00Z"}

data: {"level":"info","message":"Sync completed","timestamp":"2025-12-30T10:05:00Z"}

```

**Usage trong JavaScript:**
```javascript
const eventSource = new EventSource(`/api/sync/jobs/${jobId}/executions/${executionId}/logs`);
eventSource.onmessage = (event) => {
  const log = JSON.parse(event.data);
  console.log(log);
};
```

## Ví dụ sử dụng trong Frontend

### JavaScript Fetch API
```javascript
// List all jobs
const response = await fetch('/api/sync/jobs');
const data = await response.json();
console.log(data.jobs);

// Run a job
const runResponse = await fetch(`/api/sync/jobs/${jobId}/run`, {
  method: 'POST'
});
const runData = await runResponse.json();
console.log(runData.execution_id);

// Stop a job
const stopResponse = await fetch(`/api/sync/jobs/${jobId}/stop?execution_id=${executionId}`, {
  method: 'POST'
});
```

### Sử dụng trong các file HTML

Tất cả các file HTML trong `services/frontend/static/` có thể sử dụng các endpoints này với base URL `/api/sync`.

Ví dụ trong `jobs.html`:
```javascript
const SYNC_SERVICE_URL = '/api/sync';

// List jobs
const response = await fetch(`${SYNC_SERVICE_URL}/jobs`);

// Run job
const runResponse = await fetch(`${SYNC_SERVICE_URL}/jobs/${jobId}/run`, {
  method: 'POST'
});
```

## Lưu ý

1. Tất cả các requests được proxy qua Gateway, không cần chỉ định host/port cụ thể
2. Sử dụng relative paths (`/api/sync/...`) thay vì absolute URLs
3. Gateway sẽ tự động forward requests đến Sync Service
4. CORS đã được cấu hình sẵn trong Gateway

