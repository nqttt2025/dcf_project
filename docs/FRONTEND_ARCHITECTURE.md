# 🎨 Frontend Architecture - Stock Analysis Platform

**Version:** 1.0  
**Target:** Thiết kế frontend có thể chứa nhiều tools phân tích

---

## 📊 Tổng quan Cấu trúc

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              NAVIGATION BAR                                   │
│  Logo │ Dashboard │ Analysis │ Screener │ Watchlist │ Reports │ Settings    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         STOCK HEADER                                    │ │
│  │  [Search Bar] │ FPT - FPT Corporation │ Price: 92,500 │ +2.5% │ ⭐      │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────┐ ┌────────────────────────────────┐  │
│  │         MAIN CHART                 │ │      INFO PANEL                │  │
│  │  [Candlestick + Indicators]        │ │  ┌────────────────────────┐    │  │
│  │  ┌──────────────────────────────┐  │ │  │ Company Info           │    │  │
│  │  │                              │  │ │  │ - Market Cap           │    │  │
│  │  │     TradingView Chart        │  │ │  │ - P/E Ratio            │    │  │
│  │  │     + MA/Bollinger/Ichimoku  │  │ │  │ - EPS                  │    │  │
│  │  │                              │  │ │  └────────────────────────┘    │  │
│  │  └──────────────────────────────┘  │ │  ┌────────────────────────┐    │  │
│  │  ┌──────────────────────────────┐  │ │  │ Analysis Summary       │    │  │
│  │  │  RSI Panel                   │  │ │  │ - DCF Fair Value       │    │  │
│  │  └──────────────────────────────┘  │ │  │ - Graham Value         │    │  │
│  │  ┌──────────────────────────────┐  │ │  │ - Upside/Downside      │    │  │
│  │  │  MACD Panel                  │  │ │  └────────────────────────┘    │  │
│  │  └──────────────────────────────┘  │ │  ┌────────────────────────┐    │  │
│  │  ┌──────────────────────────────┐  │ │  │ Technical Signals      │    │  │
│  │  │  Volume Panel                │  │ │  │ - RSI: 65 (Neutral)    │    │  │
│  │  └──────────────────────────────┘  │ │  │ - MACD: Buy            │    │  │
│  └────────────────────────────────────┘ │  │ - MA Cross: Bullish    │    │  │
│                                         │  └────────────────────────┘    │  │
│                                         └────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         TOOLS TABS                                    │   │
│  │  [DCF] [Graham] [PE Analysis] [Technical] [Financials] [News]        │   │
│  │  ─────────────────────────────────────────────────────────────────── │   │
│  │  │                      Selected Tool Content                      │ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Cấu trúc Thư mục Frontend

```
services/frontend/
├── index.html                    # Main dashboard
├── nginx.conf                    # Nginx config
├── Dockerfile.frontend
│
├── pages/                        # HTML Pages
│   ├── dashboard.html            # Overview dashboard
│   ├── stock-analysis.html       # Single stock analysis (all tools)
│   ├── screener.html             # Stock screener
│   ├── watchlist.html            # User watchlist
│   ├── reports.html              # Generated reports
│   └── settings.html             # User settings
│
├── static/
│   ├── css/
│   │   ├── main.css              # Global styles
│   │   ├── variables.css         # CSS Variables (colors, fonts)
│   │   ├── components/
│   │   │   ├── navbar.css
│   │   │   ├── sidebar.css
│   │   │   ├── cards.css
│   │   │   ├── charts.css
│   │   │   ├── tables.css
│   │   │   ├── forms.css
│   │   │   └── modals.css
│   │   └── pages/
│   │       ├── dashboard.css
│   │       ├── analysis.css
│   │       └── screener.css
│   │
│   ├── js/
│   │   ├── app.js                # Main app initialization
│   │   ├── api.js                # API client
│   │   ├── utils.js              # Utility functions
│   │   ├── state.js              # State management
│   │   │
│   │   ├── components/           # Reusable UI components
│   │   │   ├── navbar.js
│   │   │   ├── stock-card.js
│   │   │   ├── indicator-panel.js
│   │   │   └── data-table.js
│   │   │
│   │   ├── charts/               # Chart modules
│   │   │   ├── chart-manager.js  # Main chart controller
│   │   │   ├── candlestick.js    # Candlestick chart
│   │   │   ├── indicators/
│   │   │   │   ├── ma.js         # Moving Averages
│   │   │   │   ├── bollinger.js  # Bollinger Bands
│   │   │   │   ├── ichimoku.js   # Ichimoku Cloud
│   │   │   │   ├── rsi.js        # RSI panel
│   │   │   │   ├── macd.js       # MACD panel
│   │   │   │   └── volume.js     # Volume panel
│   │   │   └── drawing-tools.js  # Trendlines, Fibonacci
│   │   │
│   │   ├── tools/                # Analysis tools
│   │   │   ├── dcf-tool.js       # DCF Calculator UI
│   │   │   ├── graham-tool.js    # Graham Valuation UI
│   │   │   ├── pe-tool.js        # PE Analysis UI
│   │   │   ├── technical-tool.js # Technical Summary
│   │   │   └── financial-tool.js # Financial Statements
│   │   │
│   │   └── pages/                # Page controllers
│   │       ├── dashboard.js
│   │       ├── stock-analysis.js
│   │       ├── screener.js
│   │       └── watchlist.js
│   │
│   └── assets/
│       ├── icons/
│       ├── images/
│       └── fonts/
│
└── templates/                    # HTML templates (for HTMX)
    ├── partials/
    │   ├── stock-card.html
    │   ├── indicator-row.html
    │   └── analysis-result.html
    └── modals/
        ├── dcf-config.html
        └── alert-settings.html
```

---

## 🎯 Layout Design Patterns

### Pattern 1: Dashboard Layout (Grid-based)
```
┌────────────────────────────────────────────────────────────┐
│ NAVBAR                                                      │
├──────────┬─────────────────────────────────────────────────┤
│          │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │
│          │  │ Summary │ │ Summary │ │ Summary │ │ Summary│ │
│          │  │  Card   │ │  Card   │ │  Card   │ │  Card  │ │
│ SIDEBAR  │  └─────────┘ └─────────┘ └─────────┘ └────────┘ │
│          │  ┌──────────────────────┐ ┌──────────────────┐  │
│ - Home   │  │                      │ │                  │  │
│ - Stocks │  │    Market Overview   │ │   Top Movers     │  │
│ - Tools  │  │       Chart          │ │     Table        │  │
│ - Reports│  │                      │ │                  │  │
│          │  └──────────────────────┘ └──────────────────┘  │
│          │  ┌──────────────────────────────────────────┐   │
│          │  │           Watchlist / Recent             │   │
│          │  └──────────────────────────────────────────┘   │
└──────────┴─────────────────────────────────────────────────┘
```

### Pattern 2: Stock Analysis Layout (Tool-focused)
```
┌────────────────────────────────────────────────────────────┐
│ NAVBAR   │ Search: [FPT________] │ FPT - 92,500 (+2.5%)    │
├──────────┴─────────────────────────────────────────────────┤
│ TABS: [Chart] [DCF] [Graham] [Technical] [Financials]      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                                                      │  │
│  │           MAIN CONTENT AREA (Based on Tab)           │  │
│  │                                                      │  │
│  │   - Chart Tab: TradingView + Indicators              │  │
│  │   - DCF Tab: DCF Calculator + Results                │  │
│  │   - Graham Tab: Graham Form + Valuation              │  │
│  │   - Technical Tab: All TA Indicators Summary         │  │
│  │   - Financials Tab: Income, Balance, Cash Flow       │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌────────────────────┐ ┌────────────────────────────────┐ │
│  │  Quick Actions     │ │     Analysis History           │ │
│  │  [Run DCF] [Alert] │ │  Date | Type | Result          │ │
│  └────────────────────┘ └────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

---

## 🧩 Component Design

### 1. Tool Panel Component
```html
<!-- templates/components/tool-panel.html -->
<div class="tool-panel" data-tool="dcf">
  <div class="tool-header">
    <h3 class="tool-title">
      <span class="tool-icon">📊</span>
      DCF Valuation
    </h3>
    <div class="tool-actions">
      <button class="btn-icon" title="Settings">⚙️</button>
      <button class="btn-icon" title="Expand">⬜</button>
    </div>
  </div>
  
  <div class="tool-body">
    <!-- Tool specific content -->
  </div>
  
  <div class="tool-footer">
    <span class="last-updated">Updated: 2 mins ago</span>
    <button class="btn-primary">Run Analysis</button>
  </div>
</div>
```

### 2. Indicator Card Component
```html
<!-- templates/components/indicator-card.html -->
<div class="indicator-card" data-indicator="rsi">
  <div class="indicator-header">
    <span class="indicator-name">RSI (14)</span>
    <span class="indicator-value" data-signal="neutral">65.4</span>
  </div>
  <div class="indicator-visual">
    <div class="rsi-gauge">
      <div class="gauge-fill" style="width: 65.4%"></div>
      <div class="gauge-zones">
        <span class="zone-oversold">30</span>
        <span class="zone-overbought">70</span>
      </div>
    </div>
  </div>
  <div class="indicator-signal">
    <span class="signal-badge neutral">Neutral</span>
  </div>
</div>
```

### 3. Chart Container Component
```html
<!-- templates/components/chart-container.html -->
<div class="chart-container">
  <div class="chart-toolbar">
    <div class="timeframe-buttons">
      <button class="tf-btn" data-tf="1D">1D</button>
      <button class="tf-btn active" data-tf="1W">1W</button>
      <button class="tf-btn" data-tf="1M">1M</button>
      <button class="tf-btn" data-tf="3M">3M</button>
      <button class="tf-btn" data-tf="1Y">1Y</button>
    </div>
    <div class="indicator-toggles">
      <button class="ind-btn active" data-ind="ma">MA</button>
      <button class="ind-btn" data-ind="bollinger">BB</button>
      <button class="ind-btn" data-ind="ichimoku">Ichimoku</button>
    </div>
    <div class="chart-tools">
      <button class="tool-btn" data-tool="trendline">📐</button>
      <button class="tool-btn" data-tool="fibonacci">🔢</button>
      <button class="tool-btn" data-tool="screenshot">📷</button>
    </div>
  </div>
  
  <div class="chart-main" id="main-chart">
    <!-- TradingView Lightweight Charts renders here -->
  </div>
  
  <div class="chart-panels">
    <div class="sub-panel" id="rsi-panel"></div>
    <div class="sub-panel" id="macd-panel"></div>
    <div class="sub-panel" id="volume-panel"></div>
  </div>
</div>
```

---

## 🎨 CSS Variables & Theme

```css
/* static/css/variables.css */
:root {
  /* Colors */
  --primary: #667eea;
  --primary-dark: #5a67d8;
  --secondary: #764ba2;
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
  --info: #3b82f6;
  
  /* Stock Colors */
  --stock-up: #10b981;
  --stock-down: #ef4444;
  --stock-neutral: #6b7280;
  
  /* Chart Colors */
  --chart-candle-up: #26a69a;
  --chart-candle-down: #ef5350;
  --chart-ma-20: #2196f3;
  --chart-ma-50: #ff9800;
  --chart-ma-200: #9c27b0;
  --chart-bollinger: rgba(33, 150, 243, 0.2);
  
  /* Layout */
  --sidebar-width: 250px;
  --navbar-height: 64px;
  --panel-gap: 16px;
  --border-radius: 12px;
  
  /* Typography */
  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
}

/* Dark Theme */
[data-theme="dark"] {
  --bg-primary: #1a1a2e;
  --bg-secondary: #16213e;
  --bg-card: #0f3460;
  --text-primary: #e4e4e7;
  --text-secondary: #a1a1aa;
  --border-color: #374151;
}
```

---

## 📱 Responsive Design

```css
/* Mobile First Approach */

/* Base: Mobile */
.tool-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--panel-gap);
}

/* Tablet: 768px+ */
@media (min-width: 768px) {
  .tool-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .chart-container {
    grid-column: span 2;
  }
}

/* Desktop: 1024px+ */
@media (min-width: 1024px) {
  .main-layout {
    display: grid;
    grid-template-columns: var(--sidebar-width) 1fr;
  }
  
  .tool-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* Large Desktop: 1440px+ */
@media (min-width: 1440px) {
  .analysis-layout {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: var(--panel-gap);
  }
}
```

---

## 🔧 JavaScript Architecture

### State Management
```javascript
// static/js/state.js
class AppState {
  constructor() {
    this.state = {
      currentStock: null,
      watchlist: [],
      indicators: {
        ma: { enabled: true, periods: [20, 50, 200] },
        bollinger: { enabled: false, period: 20, std: 2 },
        rsi: { enabled: true, period: 14 },
        macd: { enabled: true, fast: 12, slow: 26, signal: 9 },
      },
      chartTimeframe: '1D',
      theme: 'light',
    };
    
    this.listeners = new Map();
  }
  
  subscribe(key, callback) {
    if (!this.listeners.has(key)) {
      this.listeners.set(key, []);
    }
    this.listeners.get(key).push(callback);
  }
  
  update(key, value) {
    this.state[key] = value;
    this.notify(key, value);
    this.persist();
  }
  
  notify(key, value) {
    const callbacks = this.listeners.get(key) || [];
    callbacks.forEach(cb => cb(value));
  }
  
  persist() {
    localStorage.setItem('appState', JSON.stringify(this.state));
  }
}

export const appState = new AppState();
```

### Tool Manager
```javascript
// static/js/tools/tool-manager.js
class ToolManager {
  constructor() {
    this.tools = new Map();
    this.activeTools = new Set();
  }
  
  register(name, toolClass) {
    this.tools.set(name, toolClass);
  }
  
  async activate(name, container) {
    const ToolClass = this.tools.get(name);
    if (!ToolClass) throw new Error(`Tool ${name} not found`);
    
    const tool = new ToolClass(container);
    await tool.init();
    this.activeTools.add(name);
    
    return tool;
  }
  
  deactivate(name) {
    this.activeTools.delete(name);
  }
}

// Usage
import { DCFTool } from './dcf-tool.js';
import { GrahamTool } from './graham-tool.js';
import { TechnicalTool } from './technical-tool.js';

const toolManager = new ToolManager();
toolManager.register('dcf', DCFTool);
toolManager.register('graham', GrahamTool);
toolManager.register('technical', TechnicalTool);

// Activate on tab click
document.querySelectorAll('.tool-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    const toolName = tab.dataset.tool;
    const container = document.getElementById('tool-content');
    toolManager.activate(toolName, container);
  });
});
```

### Chart Manager
```javascript
// static/js/charts/chart-manager.js
import { createChart } from 'lightweight-charts';

class ChartManager {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.chart = null;
    this.series = {};
    this.indicators = {};
  }
  
  init() {
    this.chart = createChart(this.container, {
      width: this.container.clientWidth,
      height: 400,
      layout: {
        background: { color: '#ffffff' },
        textColor: '#333',
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: '#ccc' },
      timeScale: { borderColor: '#ccc', timeVisible: true },
    });
    
    this.series.candles = this.chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderUpColor: '#26a69a',
      borderDownColor: '#ef5350',
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });
    
    window.addEventListener('resize', () => this.resize());
  }
  
  setData(ohlcData) {
    this.series.candles.setData(ohlcData);
  }
  
  addMA(period, color) {
    const maKey = `ma_${period}`;
    this.indicators[maKey] = this.chart.addLineSeries({
      color: color,
      lineWidth: 2,
      title: `MA ${period}`,
    });
    return this.indicators[maKey];
  }
  
  addBollinger(data, color) {
    this.indicators.bb_upper = this.chart.addLineSeries({
      color: color,
      lineWidth: 1,
      lineStyle: 2, // Dashed
    });
    this.indicators.bb_lower = this.chart.addLineSeries({
      color: color,
      lineWidth: 1,
      lineStyle: 2,
    });
    // Area between bands
    this.indicators.bb_area = this.chart.addAreaSeries({
      topColor: 'rgba(33, 150, 243, 0.1)',
      bottomColor: 'rgba(33, 150, 243, 0.1)',
      lineColor: 'transparent',
    });
  }
  
  resize() {
    this.chart.applyOptions({
      width: this.container.clientWidth,
    });
  }
}

export { ChartManager };
```

---

## 📄 Example: Stock Analysis Page

```html
<!-- pages/stock-analysis.html -->
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Stock Analysis - DCF Platform</title>
  <link rel="stylesheet" href="/static/css/main.css">
</head>
<body>
  <!-- Navbar -->
  <nav class="navbar" id="navbar"></nav>
  
  <main class="main-content">
    <!-- Stock Header -->
    <header class="stock-header">
      <div class="stock-search">
        <input type="text" id="stock-search" placeholder="Search stock..." 
               hx-get="/api/stocks/search" hx-trigger="keyup changed delay:300ms"
               hx-target="#search-results">
        <div id="search-results" class="search-dropdown"></div>
      </div>
      
      <div class="stock-info" id="stock-info">
        <h1 class="stock-ticker">FPT</h1>
        <span class="stock-name">FPT Corporation</span>
        <span class="stock-price">92,500</span>
        <span class="stock-change positive">+2,300 (+2.5%)</span>
        <button class="btn-watchlist" data-action="toggle-watchlist">⭐</button>
      </div>
    </header>
    
    <!-- Tool Tabs -->
    <div class="tool-tabs">
      <button class="tab-btn active" data-tool="chart">📈 Chart</button>
      <button class="tab-btn" data-tool="dcf">💰 DCF</button>
      <button class="tab-btn" data-tool="graham">📊 Graham</button>
      <button class="tab-btn" data-tool="technical">📉 Technical</button>
      <button class="tab-btn" data-tool="financials">📋 Financials</button>
    </div>
    
    <!-- Tool Content -->
    <div class="tool-content" id="tool-content">
      <!-- Chart Tool (Default) -->
      <div class="tool-panel" id="chart-tool">
        <div class="chart-toolbar">
          <div class="timeframe-group">
            <button class="tf-btn" data-tf="1D">1D</button>
            <button class="tf-btn active" data-tf="1W">1W</button>
            <button class="tf-btn" data-tf="1M">1M</button>
            <button class="tf-btn" data-tf="1Y">1Y</button>
          </div>
          <div class="indicator-group">
            <label><input type="checkbox" data-ind="ma" checked> MA</label>
            <label><input type="checkbox" data-ind="bollinger"> Bollinger</label>
            <label><input type="checkbox" data-ind="ichimoku"> Ichimoku</label>
          </div>
        </div>
        
        <div class="chart-area">
          <div id="main-chart"></div>
          <div id="rsi-chart" class="sub-chart"></div>
          <div id="macd-chart" class="sub-chart"></div>
          <div id="volume-chart" class="sub-chart"></div>
        </div>
      </div>
    </div>
    
    <!-- Side Panel -->
    <aside class="side-panel">
      <div class="panel-section">
        <h3>📊 Analysis Summary</h3>
        <div class="summary-grid" id="analysis-summary">
          <!-- Loaded via HTMX -->
        </div>
      </div>
      
      <div class="panel-section">
        <h3>📈 Technical Signals</h3>
        <div class="signals-list" id="technical-signals">
          <!-- Loaded via HTMX -->
        </div>
      </div>
      
      <div class="panel-section">
        <h3>⚡ Quick Actions</h3>
        <button class="btn-primary btn-full" 
                hx-post="/api/analysis/run/dcf" 
                hx-vals='{"ticker": "FPT"}'
                hx-target="#analysis-result">
          Run DCF Analysis
        </button>
        <button class="btn-secondary btn-full" onclick="setAlert()">
          Set Price Alert
        </button>
      </div>
    </aside>
  </main>
  
  <!-- Scripts -->
  <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
  <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
  <script type="module" src="/static/js/pages/stock-analysis.js"></script>
</body>
</html>
```

---

## 🔗 API Integration Pattern

```javascript
// static/js/api.js
const API_BASE = '/api';

class APIClient {
  async get(endpoint) {
    const response = await fetch(`${API_BASE}${endpoint}`);
    if (!response.ok) throw new Error(`API Error: ${response.status}`);
    return response.json();
  }
  
  async post(endpoint, data) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error(`API Error: ${response.status}`);
    return response.json();
  }
}

// Stock API
export const stockAPI = {
  getStock: (ticker) => api.get(`/stocks/${ticker}`),
  getOHLC: (ticker, tf) => api.get(`/stocks/${ticker}/ohlc?timeframe=${tf}`),
  runDCF: (ticker) => api.post(`/stocks/${ticker}/run`),
};

// Technical Analysis API
export const taAPI = {
  getIndicators: (ticker) => api.get(`/ta/all/${ticker}`),
  getMA: (ticker, periods) => api.get(`/ta/ma/${ticker}?periods=${periods.join(',')}`),
  getRSI: (ticker, period = 14) => api.get(`/ta/rsi/${ticker}?period=${period}`),
  getMACD: (ticker) => api.get(`/ta/macd/${ticker}`),
  getSignals: (ticker) => api.get(`/ta/signals/${ticker}`),
};

const api = new APIClient();
export default api;
```

---

## 📊 Summary: Tool Organization

| Page | Primary Tools | Secondary Tools |
|------|--------------|-----------------|
| **Dashboard** | Market Overview, Top Movers | Watchlist, Recent |
| **Stock Analysis** | Chart, DCF, Graham, Technical, Financials | Alerts, History |
| **Screener** | Filter Builder, Results Table | Save Screens |
| **Watchlist** | Stock List, Alerts | Price Tracker |
| **Reports** | PDF/Excel Generator | History |

---

**Last Updated:** 2026-01-02

