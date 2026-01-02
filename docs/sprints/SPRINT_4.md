# 🏃 Sprint 4: Momentum & Volume Indicators

**Phase:** 2 - Technical Analysis  
**Thời gian:** Tuần 7-8 (13/02/2026 - 26/02/2026)  
**Mục tiêu:** Implement momentum và volume indicators, buy/sell signals

---

## 📊 Sprint Overview

| Metric | Target |
|--------|--------|
| Indicators | RSI, Stochastic, Williams %R, OBV, VWAP, ATR |
| Signals | Buy/Sell signal endpoint |
| Tests | Unit tests for all indicators |

---

## 📋 Task Breakdown

### S4.1 - RSI (Relative Strength Index)
**Priority:** 🔴 High | **Estimate:** 1 day | **Status:** ⬜ Pending

**Tasks:**
- [ ] Implement RSI (default period: 14)
- [ ] Detect overbought (>70) / oversold (<30)
- [ ] Return signal: buy/sell/neutral

**API:**
```
GET /api/ta/{ticker}/rsi?period=14
Response: {
    "values": [...],
    "current": 65.4,
    "signal": "neutral",
    "zones": {
        "overbought": 70,
        "oversold": 30
    }
}
```

---

### S4.2 - Stochastic Oscillator
**Priority:** 🔴 High | **Estimate:** 1 day | **Status:** ⬜ Pending

**Tasks:**
- [ ] Implement Stochastic (14, 3, 3)
- [ ] Return %K and %D lines
- [ ] Detect crossovers

**API:**
```
GET /api/ta/{ticker}/stochastic
Response: {
    "k": [...],
    "d": [...],
    "signal": "buy" | "sell" | "neutral"
}
```

---

### S4.3 - Williams %R
**Priority:** 🟡 Medium | **Estimate:** 0.5 day | **Status:** ⬜ Pending

**Tasks:**
- [ ] Implement Williams %R (14)
- [ ] Similar to Stochastic but inverted scale

---

### S4.4 - OBV (On-Balance Volume)
**Priority:** 🔴 High | **Estimate:** 1 day | **Status:** ⬜ Pending

**Tasks:**
- [ ] Implement OBV calculation
- [ ] Detect divergences với price

**API:**
```
GET /api/ta/{ticker}/volume
Response: {
    "obv": [...],
    "obv_trend": "bullish" | "bearish",
    "divergence": null | "bullish_divergence" | "bearish_divergence"
}
```

---

### S4.5 - VWAP (Volume Weighted Average Price)
**Priority:** 🔴 High | **Estimate:** 1 day | **Status:** ⬜ Pending

**Tasks:**
- [ ] Implement VWAP
- [ ] Reset daily (intraday indicator)

---

### S4.6 - ATR (Average True Range)
**Priority:** 🟡 Medium | **Estimate:** 1 day | **Status:** ⬜ Pending

**Tasks:**
- [ ] Implement ATR (14)
- [ ] Useful for volatility và stop-loss calculation

---

### S4.7 - Buy/Sell Signals Endpoint
**Priority:** 🔴 High | **Estimate:** 2 days | **Status:** ⬜ Pending

**Mô tả:**
Aggregate signals từ tất cả indicators để đưa ra recommendation.

**Tasks:**
- [ ] Collect signals từ all indicators
- [ ] Weight-based scoring system
- [ ] Return overall recommendation

**API:**
```
GET /api/ta/signals/{ticker}
Response: {
    "ticker": "FPT",
    "timestamp": "2026-02-20T10:00:00",
    "overall_signal": "buy",
    "confidence": 0.72,
    "breakdown": {
        "trend_indicators": {
            "ma_cross": "buy",
            "macd": "buy",
            "ichimoku": "neutral"
        },
        "momentum_indicators": {
            "rsi": "neutral",
            "stochastic": "buy"
        },
        "volume_indicators": {
            "obv": "bullish"
        }
    },
    "summary": "7/10 indicators bullish"
}
```

**Scoring Logic:**
```python
INDICATOR_WEIGHTS = {
    'ma_cross': 1.5,
    'macd': 1.5,
    'rsi': 1.0,
    'stochastic': 1.0,
    'obv': 1.0,
    'bollinger': 1.0,
}

def calculate_signal_score(signals: dict) -> tuple[str, float]:
    total_weight = sum(INDICATOR_WEIGHTS.values())
    bullish_score = 0
    
    for indicator, signal in signals.items():
        weight = INDICATOR_WEIGHTS.get(indicator, 1.0)
        if signal == 'buy':
            bullish_score += weight
        elif signal == 'neutral':
            bullish_score += weight * 0.5
    
    confidence = bullish_score / total_weight
    
    if confidence > 0.65:
        return 'buy', confidence
    elif confidence < 0.35:
        return 'sell', 1 - confidence
    else:
        return 'neutral', 0.5
```

---

### S4.8 - Unit Tests for All Indicators
**Priority:** 🟡 Medium | **Estimate:** 1.5 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Test RSI calculation
- [ ] Test Stochastic
- [ ] Test OBV
- [ ] Test signal aggregation
- [ ] Mock data fixtures

**Test Files:**
```
tests/
├── test_ta_rsi.py
├── test_ta_stochastic.py
├── test_ta_volume.py
└── test_ta_signals.py
```

---

## 📅 Daily Plan

### Week 1 (13/02 - 19/02)
| Day | Tasks |
|-----|-------|
| 1 | S4.1 - RSI |
| 2 | S4.2 - Stochastic |
| 3 | S4.3 - Williams %R + S4.4 OBV |
| 4 | S4.5 - VWAP |
| 5 | S4.6 - ATR |

### Week 2 (20/02 - 26/02)
| Day | Tasks |
|-----|-------|
| 6 | S4.7 - Signals endpoint (part 1) |
| 7 | S4.7 - Signals endpoint (part 2) |
| 8 | S4.8 - Unit tests (part 1) |
| 9 | S4.8 - Unit tests (part 2) |
| 10 | Review, fixes, documentation |

---

## ✅ Definition of Done

- [ ] 6 new indicators implemented
- [ ] `/api/ta/signals/{ticker}` working
- [ ] All indicator tests passing
- [ ] API documentation updated

---

**Previous Sprint:** [Sprint 3 - Trend Indicators](./SPRINT_3.md)  
**Next Sprint:** [Sprint 5 - Charts & Visualization](./SPRINT_5.md)

