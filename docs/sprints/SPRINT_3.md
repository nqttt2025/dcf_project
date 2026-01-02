# 🏃 Sprint 3: Trend Indicators & New Architecture Deploy

**Phase:** 2 - Technical Analysis  
**Thời gian:** Tuần 5-6 (30/01/2026 - 12/02/2026)  
**Mục tiêu:** Implement TA indicators + Deploy kiến trúc 4 containers

---

## 📊 Sprint Overview

| Metric | Target |
|--------|--------|
| Indicators | MA, MACD, Bollinger, Ichimoku |
| Architecture | Deploy 4 containers |
| API | `/api/ta/*` endpoints working |

---

## 📋 Task Breakdown

### S3.1 - Moving Averages (SMA, EMA)
**Priority:** 🔴 High | **Estimate:** 2 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Implement SMA (Simple Moving Average) - 20, 50, 200 periods
- [ ] Implement EMA (Exponential Moving Average)
- [ ] Create TA service module
- [ ] Add API endpoint

**Code:**
```python
# services/api/services/ta_service.py
import pandas_ta as ta

class TAService:
    def calculate_ma(self, df: pd.DataFrame, periods: list[int]) -> dict:
        result = {}
        for period in periods:
            result[f'sma_{period}'] = ta.sma(df['close'], length=period).tolist()
            result[f'ema_{period}'] = ta.ema(df['close'], length=period).tolist()
        return result
```

**API:**
```
GET /api/ta/{ticker}/ma?periods=20,50,200
```

---

### S3.2 - MACD Indicator
**Priority:** 🔴 High | **Estimate:** 1 day | **Status:** ⬜ Pending

**Tasks:**
- [ ] Implement MACD (12, 26, 9)
- [ ] Return: MACD line, Signal line, Histogram
- [ ] Add buy/sell signal detection

**API:**
```
GET /api/ta/{ticker}/macd
Response: {
    "macd": [...],
    "signal": [...],
    "histogram": [...],
    "current_signal": "buy" | "sell" | "neutral"
}
```

---

### S3.3 - Bollinger Bands
**Priority:** 🔴 High | **Estimate:** 1 day | **Status:** ⬜ Pending

**Tasks:**
- [ ] Implement Bollinger Bands (20, 2)
- [ ] Return: Upper, Middle, Lower bands
- [ ] Calculate %B and Bandwidth

**API:**
```
GET /api/ta/{ticker}/bollinger
Response: {
    "upper": [...],
    "middle": [...],
    "lower": [...],
    "percent_b": 0.65,
    "bandwidth": 0.08
}
```

---

### S3.4 - Ichimoku Cloud
**Priority:** 🟡 Medium | **Estimate:** 2 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Implement all 5 Ichimoku lines
- [ ] Tenkan-sen, Kijun-sen, Senkou Span A/B, Chikou Span
- [ ] Detect cloud color (bullish/bearish)

**API:**
```
GET /api/ta/{ticker}/ichimoku
```

---

### S3.5 - API: GET /api/ta/{ticker} Endpoint
**Priority:** 🔴 High | **Estimate:** 1 day | **Status:** ⬜ Pending

**Tasks:**
- [ ] Create unified endpoint for all indicators
- [ ] Support query params to select indicators
- [ ] Return summary signals

**API:**
```
GET /api/ta/{ticker}?indicators=ma,macd,bollinger
Response: {
    "ticker": "FPT",
    "timestamp": "2026-01-30T10:00:00",
    "indicators": {
        "ma": {...},
        "macd": {...},
        "bollinger": {...}
    },
    "summary": {
        "trend": "bullish",
        "strength": 0.7
    }
}
```

---

### S3.6 - Deploy New Docker Compose (4 Containers)
**Priority:** 🔴 High | **Estimate:** 2 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Finalize services/api/ code
- [ ] Finalize services/worker/ code
- [ ] Update docker-compose.yml
- [ ] Test full deployment
- [ ] Data migration (if needed)

**New docker-compose.yml:**
```yaml
services:
  postgres:
    image: postgres:15-alpine
  redis:
    image: redis:7-alpine
  api:
    build: ./services/api
    ports: ["8000:8000"]
  worker:
    build: ./services/worker
  frontend:
    build: ./services/frontend
    ports: ["80:80"]
```

---

### S3.7 - Remove Old Services
**Priority:** 🟡 Medium | **Estimate:** 1 day | **Status:** ⬜ Pending

**Tasks:**
- [ ] Remove old service folders (backup first)
- [ ] Remove redis-commander from compose
- [ ] Update documentation
- [ ] Clean up unused code

**Services to remove:**
- `services/gateway/` → merged into api
- `services/dcf/` → merged into api
- `services/stock/` → merged into api
- `services/database/` → merged into api
- `redis-commander` → dev tool only

---

## 📁 New API Structure

```
services/api/routers/
├── stocks.py       # GET /api/stocks/*
├── analysis.py     # POST /api/analysis/*
├── technical.py    # GET /api/ta/* (NEW)
└── health.py       # GET /health
```

---

## 📅 Daily Plan

### Week 1 (30/01 - 05/02)
| Day | Tasks |
|-----|-------|
| 1 | S3.1 - SMA implementation |
| 2 | S3.1 - EMA + API endpoint |
| 3 | S3.2 - MACD |
| 4 | S3.3 - Bollinger Bands |
| 5 | S3.4 - Ichimoku (part 1) |

### Week 2 (06/02 - 12/02)
| Day | Tasks |
|-----|-------|
| 6 | S3.4 - Ichimoku (part 2) |
| 7 | S3.5 - Unified /api/ta endpoint |
| 8 | S3.6 - Deploy new architecture |
| 9 | S3.6 - Testing & fixes |
| 10 | S3.7 - Cleanup old services |

---

## ✅ Definition of Done

- [ ] 4 trend indicators working
- [ ] `/api/ta/{ticker}` returns all indicators
- [ ] New 4-container architecture deployed
- [ ] Old services removed
- [ ] All tests passing

---

## 📦 Dependencies

```txt
pandas-ta>=0.3.14b      # Technical Analysis library
```

---

**Previous Sprint:** [Sprint 2 - Infrastructure](./SPRINT_2.md)  
**Next Sprint:** [Sprint 4 - Momentum Indicators](./SPRINT_4.md)

