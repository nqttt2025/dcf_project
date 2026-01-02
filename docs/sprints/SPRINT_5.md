# 🏃 Sprint 5: Charts & Visualization

**Phase:** 2 - Technical Analysis  
**Thời gian:** Tuần 9-10 (27/02/2026 - 12/03/2026)  
**Mục tiêu:** Interactive charts với TradingView Lightweight Charts

---

## 📊 Sprint Overview

| Metric | Target |
|--------|--------|
| Chart | Candlestick + OHLC |
| Overlays | MA, Bollinger bands |
| Sub-panels | RSI, MACD, Volume |
| Timeframes | 1D, 1W, 1M, 3M, 1Y |

---

## 📋 Task Breakdown

### S5.1 - TradingView Lightweight Charts Setup
**Priority:** 🔴 High | **Estimate:** 2 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Install lightweight-charts via CDN
- [ ] Create chart-manager.js module
- [ ] Basic chart initialization
- [ ] Theme support (light/dark)

**CDN:**
```html
<script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
```

**Files:**
```
static/js/charts/
├── chart-manager.js      # Main controller
├── chart-config.js       # Chart options
└── chart-theme.js        # Theme settings
```

---

### S5.2 - Candlestick Chart with OHLC Data
**Priority:** 🔴 High | **Estimate:** 2 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Fetch OHLC data từ API
- [ ] Render candlestick series
- [ ] Add tooltip với price info
- [ ] Crosshair cursor

**API Endpoint:**
```
GET /api/stocks/{ticker}/ohlc?timeframe=1D&limit=100
Response: {
    "ticker": "FPT",
    "timeframe": "1D",
    "data": [
        {"time": "2026-01-02", "open": 92000, "high": 93500, "low": 91500, "close": 92500},
        ...
    ]
}
```

**Code:**
```javascript
// static/js/charts/candlestick.js
export function createCandlestickChart(containerId, ohlcData) {
    const chart = LightweightCharts.createChart(document.getElementById(containerId), {
        width: 800,
        height: 400,
        layout: {
            background: { type: 'solid', color: '#ffffff' },
            textColor: '#333',
        },
    });
    
    const candlestickSeries = chart.addCandlestickSeries({
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderVisible: false,
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
    });
    
    candlestickSeries.setData(ohlcData);
    return chart;
}
```

---

### S5.3 - Indicator Overlays (MA, Bollinger)
**Priority:** 🔴 High | **Estimate:** 2 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Add Moving Average lines (20, 50, 200)
- [ ] Add Bollinger Bands (upper, middle, lower)
- [ ] Toggle indicators on/off
- [ ] Color coding

**Code:**
```javascript
// static/js/charts/indicators/ma.js
export function addMovingAverages(chart, maData) {
    const colors = {
        ma20: '#2196f3',
        ma50: '#ff9800',
        ma200: '#9c27b0'
    };
    
    for (const [key, values] of Object.entries(maData)) {
        const series = chart.addLineSeries({
            color: colors[key],
            lineWidth: 2,
            title: key.toUpperCase(),
        });
        series.setData(values);
    }
}
```

---

### S5.4 - Sub-panels (RSI, MACD, Volume)
**Priority:** 🔴 High | **Estimate:** 2 days | **Status:** ⬜ Pending

**Tasks:**
- [ ] Create separate chart containers for sub-panels
- [ ] RSI panel với overbought/oversold zones
- [ ] MACD panel với histogram
- [ ] Volume panel với color coding (up/down)
- [ ] Sync crosshair across all panels

**Layout:**
```html
<div class="chart-area">
    <div id="main-chart" style="height: 400px"></div>
    <div id="rsi-chart" style="height: 100px"></div>
    <div id="macd-chart" style="height: 100px"></div>
    <div id="volume-chart" style="height: 80px"></div>
</div>
```

**Sync Crosshair:**
```javascript
function syncCrosshair(charts) {
    charts.forEach((chart, index) => {
        chart.subscribeCrosshairMove((param) => {
            charts.forEach((otherChart, otherIndex) => {
                if (index !== otherIndex && param.time) {
                    otherChart.setCrosshairPosition(param.point, param.time);
                }
            });
        });
    });
}
```

---

### S5.5 - Timeframe Switching
**Priority:** 🟡 Medium | **Estimate:** 1 day | **Status:** ⬜ Pending

**Tasks:**
- [ ] UI buttons: 1D, 1W, 1M, 3M, 1Y
- [ ] Fetch data với selected timeframe
- [ ] Re-render chart
- [ ] Preserve indicator settings

**UI:**
```html
<div class="timeframe-buttons">
    <button class="tf-btn" data-tf="1D">1D</button>
    <button class="tf-btn active" data-tf="1W">1W</button>
    <button class="tf-btn" data-tf="1M">1M</button>
    <button class="tf-btn" data-tf="3M">3M</button>
    <button class="tf-btn" data-tf="1Y">1Y</button>
</div>
```

---

### S5.6 - Chart State Management
**Priority:** 🟡 Medium | **Estimate:** 1 day | **Status:** ⬜ Pending

**Tasks:**
- [ ] Save user preferences (indicators, timeframe)
- [ ] LocalStorage persistence
- [ ] Restore state on page load

**State:**
```javascript
const chartState = {
    ticker: 'FPT',
    timeframe: '1W',
    indicators: {
        ma: { enabled: true, periods: [20, 50, 200] },
        bollinger: { enabled: false },
        rsi: { enabled: true, period: 14 },
        macd: { enabled: true },
        volume: { enabled: true }
    }
};

// Save to localStorage
localStorage.setItem('chartState', JSON.stringify(chartState));
```

---

## 📁 Frontend Files

```
static/js/charts/
├── chart-manager.js        # Main controller
├── chart-config.js         # Default options
├── candlestick.js          # Candlestick chart
├── sub-panels.js           # RSI, MACD, Volume panels
└── indicators/
    ├── ma.js               # Moving Averages overlay
    ├── bollinger.js        # Bollinger Bands overlay
    ├── rsi.js              # RSI sub-panel
    ├── macd.js             # MACD sub-panel
    └── volume.js           # Volume sub-panel
```

---

## 📅 Daily Plan

### Week 1 (27/02 - 05/03)
| Day | Tasks |
|-----|-------|
| 1 | S5.1 - Chart setup (part 1) |
| 2 | S5.1 - Chart setup (part 2) |
| 3 | S5.2 - Candlestick (part 1) |
| 4 | S5.2 - Candlestick (part 2) |
| 5 | S5.3 - MA overlay |

### Week 2 (06/03 - 12/03)
| Day | Tasks |
|-----|-------|
| 6 | S5.3 - Bollinger overlay |
| 7 | S5.4 - RSI panel |
| 8 | S5.4 - MACD + Volume panels |
| 9 | S5.5 - Timeframe switching |
| 10 | S5.6 - State management + Polish |

---

## ✅ Definition of Done

- [ ] Interactive candlestick chart working
- [ ] MA và Bollinger overlays
- [ ] RSI, MACD, Volume sub-panels
- [ ] Timeframe switching works
- [ ] State persisted in localStorage
- [ ] Mobile responsive

---

## 🎨 UI Preview

```
┌──────────────────────────────────────────────────────────┐
│ FPT - 92,500 (+2.5%)  │  [1D] [1W] [1M] [3M] [1Y]        │
├──────────────────────────────────────────────────────────┤
│ Indicators: [✓MA] [✓BB] [✓RSI] [✓MACD] [✓Vol]            │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │         CANDLESTICK CHART + MA + BOLLINGER         │  │
│  │                    (400px)                         │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  RSI: 65.4   ═══════════════════●──────────        │  │
│  │              30                 70                 │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  MACD: ▄▄▄▂▂▂▁▁▂▂▃▃▄▅▆▇█▇▆▅▄▃▂▁                    │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Volume: ▃▅▂▇█▃▂▅▆▃▂▄▅▇▃▂                          │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

**Previous Sprint:** [Sprint 4 - Momentum Indicators](./SPRINT_4.md)  
**Next Sprint:** [Sprint 6 - Dashboard & User System](./SPRINT_6.md)

