# API Reference

**API endpoints của DCF Valuation Project**

## 🌐 Base URLs

- **Production**: `http://localhost:8000` (Gateway)
- **DCF Service**: `http://localhost:8001`
- **Stock Service**: `http://localhost:8002`

## 📚 Gateway API

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "dcf": "healthy",
    "stock": "healthy"
  }
}
```

### List Stocks
```http
GET /api/stocks
```

**Response:**
```json
[
  {
    "ticker": "FPT",
    "name": "FPT Corporation",
    "status": "completed",
    "has_result": true
  }
]
```

### Get Stock Detail
```http
GET /api/stocks/{ticker}
```

**Response:**
```json
{
  "ticker": "FPT",
  "name": "FPT Corporation",
  "status": {
    "status": "completed",
    "progress": "Analysis completed!",
    "progress_percent": 100
  },
  "result": {
    "dcf_value": 150000,
    "graham_value": 145000,
    "market_price": 140000
  }
}
```

### Run DCF Analysis
```http
POST /api/stocks/{ticker}/run
```

**Response:**
```json
{
  "message": "Analysis started",
  "ticker": "FPT"
}
```

### Get Analysis Result
```http
GET /api/analysis/{ticker}
```

**Response:**
```json
{
  "ticker": "FPT",
  "status": "completed",
  "dcf_value": 150000,
  "graham_value": 145000,
  "market_price": 140000,
  "margin_of_safety": 7.14
}
```

## 🔧 DCF Service API

### Health Check
```http
GET /health
```

### Run Analysis
```http
POST /analyze/{ticker}
```

### Get Analysis Result
```http
GET /analysis/{ticker}
```

### Service Status
```http
GET /status
```

## 📊 Stock Service API

### Health Check
```http
GET /health
```

### List Stocks
```http
GET /stocks
```

### Get Stock Detail
```http
GET /stocks/{ticker}
```

### Get Stock Status
```http
GET /stocks/{ticker}/status
```

### Service Status
```http
GET /status
```

## 📖 API Documentation

Swagger UI: http://localhost:8000/docs  
ReDoc: http://localhost:8000/redoc

---

**Back to:** [Reference README](README.md)

