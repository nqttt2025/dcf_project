// Global state
let allStocks = [];
let filteredStocks = [];

// Format number with Vietnamese locale
function formatNumber(num) {
    if (num === null || num === undefined) return '-';
    return new Intl.NumberFormat('vi-VN').format(num);
}

// Format currency
function formatCurrency(num) {
    if (num === null || num === undefined) return '-';
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND',
        minimumFractionDigits: 0
    }).format(num);
}

// Format percentage
function formatPercent(num) {
    if (num === null || num === undefined) return '-';
    return `${num >= 0 ? '+' : ''}${num.toFixed(2)}%`;
}

// Convert GMT timestamp to GMT+7 (Ho Chi Minh City time) and format for display
function formatTimestampGMT7(timestamp) {
    if (!timestamp) return 'N/A';
    
    try {
        // Parse the timestamp - handle various formats
        let date;
        if (typeof timestamp === 'string') {
            // Handle UTC format strings like "2024-01-01 12:00:00 UTC" or ISO format
            if (timestamp.includes('UTC')) {
                // Remove " UTC" suffix and parse
                const cleanTimestamp = timestamp.replace(' UTC', '');
                date = new Date(cleanTimestamp + 'Z'); // Add Z to indicate UTC
            } else if (timestamp.includes('T') || timestamp.includes('Z') || timestamp.includes('+')) {
                // ISO format
                date = new Date(timestamp);
            } else {
                // Try parsing as is
                date = new Date(timestamp);
            }
        } else {
            date = new Date(timestamp);
        }
        
        // Check if date is valid
        if (isNaN(date.getTime())) {
            return 'Invalid date';
        }
        
        // Convert to GMT+7 (HCM timezone)
        // Create a date in GMT+7 timezone
        const gmt7Offset = 7 * 60; // 7 hours in minutes
        const utcTime = date.getTime() + (date.getTimezoneOffset() * 60000);
        const gmt7Time = new Date(utcTime + (gmt7Offset * 60000));
        
        // Format as Vietnamese locale with GMT+7 timezone
        return gmt7Time.toLocaleString('vi-VN', {
            timeZone: 'Asia/Ho_Chi_Minh',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        }) + ' GMT+7';
    } catch (error) {
        console.error('Error formatting timestamp:', error, timestamp);
        return 'Invalid date';
    }
}

// Format timestamp for display (short format, no seconds)
function formatTimestampShort(timestamp) {
    if (!timestamp) return 'N/A';
    
    try {
        let date;
        if (typeof timestamp === 'string') {
            if (timestamp.includes('UTC')) {
                const cleanTimestamp = timestamp.replace(' UTC', '');
                date = new Date(cleanTimestamp + 'Z');
            } else if (timestamp.includes('T') || timestamp.includes('Z') || timestamp.includes('+')) {
                date = new Date(timestamp);
            } else {
                date = new Date(timestamp);
            }
        } else {
            date = new Date(timestamp);
        }
        
        if (isNaN(date.getTime())) {
            return 'Invalid date';
        }
        
        const gmt7Offset = 7 * 60;
        const utcTime = date.getTime() + (date.getTimezoneOffset() * 60000);
        const gmt7Time = new Date(utcTime + (gmt7Offset * 60000));
        
        return gmt7Time.toLocaleString('vi-VN', {
            timeZone: 'Asia/Ho_Chi_Minh',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        }) + ' GMT+7';
    } catch (error) {
        console.error('Error formatting timestamp:', error, timestamp);
        return 'Invalid date';
    }
}

// Real-time updates state
let eventSource = null;
let pollTimeout = null;
let lastDataHash = null;
let pollInterval = 5000; // Start with 5s, will adapt
let lastUpdateTime = Date.now();
let sseSupported = true;

// Load stocks from API (used by both SSE and polling)
async function loadStocks() {
    try {
        const response = await fetch('/api/stocks');
        const data = await response.json();
        
        // Create hash to detect changes
        const dataHash = JSON.stringify(data.stocks.map(s => ({
            ticker: s.ticker,
            current_price: s.current_price,
            is_running: s.is_running,
            has_result: s.has_result
        })));
        
        // Update stocks
        allStocks = data.stocks;
        filteredStocks = [...allStocks];
        
        // Update status bar
        document.getElementById('total-stocks').textContent = data.total;
        document.getElementById('analyzed-stocks').textContent = data.with_results;
        document.getElementById('running-stocks').textContent = data.running;
        
        renderStocks();
        
        // Smart polling: adapt interval based on changes
        if (dataHash !== lastDataHash) {
            // Data changed - use faster polling
            pollInterval = 5000;
            lastUpdateTime = Date.now();
            lastDataHash = dataHash;
        } else {
            // No changes - gradually increase interval
            const timeSinceUpdate = Date.now() - lastUpdateTime;
            if (timeSinceUpdate > 60000) {
                pollInterval = Math.min(pollInterval * 1.2, 30000); // Max 30s
            }
        }
        
        return data;
    } catch (error) {
        console.error('Error loading stocks:', error);
        document.getElementById('stocks-grid').innerHTML = 
            '<div class="loading">❌ Lỗi khi tải dữ liệu. Vui lòng thử lại.</div>';
        throw error;
    }
}

// Initialize SSE connection for real-time updates
function initSSE() {
    if (!sseSupported || eventSource) {
        return;
    }
    
    try {
        eventSource = new EventSource('/api/stocks/stream');
        
        eventSource.onmessage = (event) => {
            if (event.data.startsWith(':')) {
                // Heartbeat, ignore
                return;
            }
            
            try {
                const data = JSON.parse(event.data);
                
                // Update stocks
                allStocks = data.stocks;
                filteredStocks = [...allStocks];
                
                // Update status bar
                document.getElementById('total-stocks').textContent = data.total;
                document.getElementById('analyzed-stocks').textContent = data.with_results;
                document.getElementById('running-stocks').textContent = data.running;
                
                renderStocks();
                
                // Reset polling interval since we got update via SSE
                pollInterval = 5000;
                lastUpdateTime = Date.now();
            } catch (error) {
                console.error('Error parsing SSE data:', error);
            }
        };
        
        eventSource.onerror = (error) => {
            console.warn('SSE connection error, falling back to polling:', error);
            sseSupported = false;
            if (eventSource) {
                eventSource.close();
                eventSource = null;
            }
            // Start polling as fallback
            startSmartPolling();
        };
        
        console.log('SSE connection established for real-time updates');
    } catch (error) {
        console.warn('SSE not supported, using polling:', error);
        sseSupported = false;
        startSmartPolling();
    }
}

// Smart polling with adaptive interval
function startSmartPolling() {
    if (pollTimeout) {
        clearTimeout(pollTimeout);
    }
    
    const poll = async () => {
        try {
            await loadStocks();
        } catch (error) {
            console.error('Polling error:', error);
        }
        
        // Schedule next poll with adaptive interval
        pollTimeout = setTimeout(poll, pollInterval);
    };
    
    poll();
}

// Cleanup function
function cleanupUpdates() {
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }
    if (pollTimeout) {
        clearTimeout(pollTimeout);
        pollTimeout = null;
    }
}

// Run DCF analysis for a stock
async function runDCFAnalysis(ticker) {
    // Disable button immediately
    const button = event.target;
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '⏳ Đang khởi động...';
    
    try {
        const response = await fetch(`/api/stocks/${ticker}/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            button.disabled = false;
            button.innerHTML = originalText;
            alert(`Lỗi: ${error.detail || 'Không thể chạy phân tích DCF'}`);
            return;
        }
        
        const result = await response.json();
        
        // Update button state
        button.innerHTML = '🔄 Đang chạy...';
        
        // Show notification
        showNotification(`Đã bắt đầu phân tích DCF cho ${ticker}`, 'success');
        
        // Reload stocks to update status
        loadStocks();
        
        // Start polling for status updates
        pollStockStatus(ticker);
    } catch (error) {
        console.error('Error running DCF analysis:', error);
        button.disabled = false;
        button.innerHTML = originalText;
        showNotification(`Lỗi khi chạy phân tích DCF: ${error.message}`, 'error');
    }
}

// Poll stock status until analysis completes
async function pollStockStatus(ticker) {
    const maxAttempts = 120; // 10 minutes max (5s * 120)
    let attempts = 0;
    
    const poll = async () => {
        try {
            const response = await fetch(`/api/stocks/${ticker}/status`);
            const status = await response.json();
            
            if (!status.is_running) {
                // Analysis completed, reload stocks
                loadStocks();
                showNotification(`Phân tích DCF hoàn tất cho ${ticker}`, 'success');
                return;
            }
            
            attempts++;
            if (attempts < maxAttempts) {
                setTimeout(poll, 5000); // Poll every 5 seconds
            } else {
                console.warn(`Polling timeout for ${ticker}`);
                showNotification(`Phân tích DCF cho ${ticker} đang mất nhiều thời gian...`, 'warning');
            }
        } catch (error) {
            console.error('Error polling status:', error);
        }
    };
    
    setTimeout(poll, 5000); // Start polling after 5 seconds
}

// Show notification
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existing = document.querySelectorAll('.notification');
    existing.forEach(n => n.remove());
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add to body
    document.body.appendChild(notification);
    
    // Show with animation
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Render stocks grid
function renderStocks() {
    const grid = document.getElementById('stocks-grid');
    
    if (filteredStocks.length === 0) {
        grid.innerHTML = '<div class="loading">Không tìm thấy mã cổ phiếu nào.</div>';
        return;
    }
    
    grid.innerHTML = filteredStocks.map(stock => {
        const cardClass = stock.is_running ? 'running' : 
                         stock.has_result ? 'has-result' : 'no-result';
        
        const statusBadge = stock.is_running ? 
            '<span class="status-badge running">🔄 Đang chạy</span>' :
            stock.has_result ?
            '<span class="status-badge completed">✓ Đã phân tích</span>' :
            '<span class="status-badge pending">⏳ Chưa phân tích</span>';
        
        const upsideHtml = stock.upside_downside !== null ? `
            <div class="upside-badge ${stock.upside_downside >= 0 ? 'positive' : 'negative'}">
                ${formatPercent(stock.upside_downside)}
            </div>
        ` : '';
        
        return `
            <div class="stock-card ${cardClass}" onclick="showDetail('${stock.ticker}')">
                <div class="stock-header">
                    <div class="ticker">${stock.ticker}</div>
                    ${statusBadge}
                </div>
                
                ${stock.has_result ? `
                    <div class="stock-info">
                        <div class="info-item">
                            <span class="info-label">Giá hiện tại</span>
                            <span class="info-value">${formatCurrency(stock.current_price)}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">DCF Fair Value</span>
                            <span class="info-value">${formatCurrency(stock.dcf_fair_value)}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Graham Fair Value</span>
                            <span class="info-value">${formatCurrency(stock.graham_fair_value)}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Average Fair Value</span>
                            <span class="info-value">${formatCurrency(stock.average_fair_value)}</span>
                        </div>
                    </div>
                    ${upsideHtml}
                    ${stock.saved_at ? `<div style="margin-top: 10px; font-size: 0.85em; color: #6b7280;">
                        Cập nhật: ${formatTimestampShort(stock.saved_at)}
                    </div>` : ''}
                ` : `
                    <div style="text-align: center; padding: 20px; color: #6b7280;">
                        Chưa có dữ liệu phân tích
                    </div>
                `}
                
                ${stock.is_running ? `
                    <div class="progress-container">
                        <div class="progress-bar-wrapper">
                            <div class="progress-bar" style="width: ${stock.progress_percent || 0}%"></div>
                        </div>
                        <div class="progress-text">${stock.progress || 'Đang xử lý...'} (${Math.round(stock.progress_percent || 0)}%)</div>
                    </div>
                ` : ''}
                
                <div class="stock-actions">
                    <button class="btn-run-dcf" onclick="event.stopPropagation(); runDCFAnalysis('${stock.ticker}')" 
                            ${stock.is_running ? 'disabled' : ''}>
                        ${stock.is_running ? '🔄 Đang chạy...' : '▶️ Chạy DCF'}
                    </button>
                    <button class="btn btn-primary" onclick="event.stopPropagation(); showDetail('${stock.ticker}')">
                        Chi tiết
                    </button>
                    <button class="btn btn-secondary" onclick="event.stopPropagation(); showConfig('${stock.ticker}')">
                        Config
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Filter stocks
function filterStocks() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const statusFilter = document.getElementById('filter-status').value;
    
    filteredStocks = allStocks.filter(stock => {
        const matchesSearch = stock.ticker.toLowerCase().includes(searchTerm);
        
        let matchesStatus = true;
        if (statusFilter === 'has-result') {
            matchesStatus = stock.has_result;
        } else if (statusFilter === 'no-result') {
            matchesStatus = !stock.has_result;
        } else if (statusFilter === 'running') {
            matchesStatus = stock.is_running;
        }
        
        return matchesSearch && matchesStatus;
    });
    
    renderStocks();
}

// Show stock detail
async function showDetail(ticker) {
    try {
        const response = await fetch(`/api/stocks/${ticker}`);
        const data = await response.json();
        
        if (data.error) {
            alert(data.error);
            return;
        }
        
        const result = data.result;
        const advanced = result.advanced_analysis || {};
        
        // Build comprehensive detail view
        const dcfParams = result.dcf_params || {};
        const grahamParams = result.graham_params || {};
        const metrics = advanced.valuation_metrics || {};
        const upside = advanced.upside_downside || {};
        const forecast = advanced.forecast_details || {};
        const yearlyPrice = advanced.yearly_price_forecast || [];
        const peAnalysis = result.pe_analysis || {};
        
        const modalContent = `
            <div class="modal-header">
                <h2 class="modal-title">${ticker} - Chi tiết phân tích DCF</h2>
                <span class="close" onclick="closeModal()">&times;</span>
            </div>
            
            <div class="section">
                <h3 class="section-title">Thông số đầu vào</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <div class="detail-label">Giá thị trường</div>
                        <div class="detail-value">${formatCurrency(result.price)}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">EPS</div>
                        <div class="detail-value">${formatCurrency(result.eps)}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Free Cash Flow (TTM)</div>
                        <div class="detail-value">${formatNumber(result.fcf)} VND</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Số cổ phiếu đang lưu hành</div>
                        <div class="detail-value">${formatNumber(result.shares)}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Vốn hóa thị trường</div>
                        <div class="detail-value">${formatNumber(result.market_cap)} VND</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Tỷ lệ tăng trưởng ước tính</div>
                        <div class="detail-value">${result.growth_estimate.toFixed(2)}%</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Thời gian dự báo</div>
                        <div class="detail-value">${dcfParams.yr || 5} năm</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Tỷ lệ chiết khấu</div>
                        <div class="detail-value">${dcfParams.dr || 10}%</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Tỷ lệ tăng trưởng vĩnh viễn</div>
                        <div class="detail-value">${dcfParams.pr || 2.5}%</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h3 class="section-title">Kết quả định giá</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <div class="detail-label">DCF Fair Value</div>
                        <div class="detail-value">${formatCurrency(result.dcf_fair_value)}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Graham Fair Value</div>
                        <div class="detail-value">${formatCurrency(result.graham_fair_value)}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Average Fair Value</div>
                        <div class="detail-value">${formatCurrency(result.average_fair_value)}</div>
                    </div>
                </div>
            </div>
            
            ${upside.dcf_upside_pct !== undefined ? `
            <div class="section">
                <h3 class="section-title">Phân tích tiềm năng tăng/giảm giá</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <div class="detail-label">DCF Tiềm năng tăng/giảm</div>
                        <div class="detail-value ${upside.dcf_upside_pct >= 0 ? 'positive' : 'negative'}">
                            ${formatPercent(upside.dcf_upside_pct)}
                        </div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Graham Tiềm năng tăng/giảm</div>
                        <div class="detail-value ${upside.graham_upside_pct >= 0 ? 'positive' : 'negative'}">
                            ${formatPercent(upside.graham_upside_pct)}
                        </div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Trung bình Tiềm năng tăng/giảm</div>
                        <div class="detail-value ${upside.average_upside_pct >= 0 ? 'positive' : 'negative'}">
                            ${formatPercent(upside.average_upside_pct)}
                        </div>
                    </div>
                </div>
            </div>
            ` : ''}
            
            ${metrics.pe_ratio !== undefined ? `
            <div class="section">
                <h3 class="section-title">Chỉ số định giá</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <div class="detail-label">Tỷ số P/E (cổ phiếu)</div>
                        <div class="detail-value">${metrics.pe_ratio.toFixed(2)}</div>
                    </div>
                    ${metrics.industry_pe !== undefined && metrics.industry_pe !== null ? `
                    <div class="detail-item">
                        <div class="detail-label">Tỷ số P/E (ngành)</div>
                        <div class="detail-value">${metrics.industry_pe.toFixed(2)}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">So sánh P/E</div>
                        <div class="detail-value ${metrics.pe_ratio <= metrics.industry_pe ? 'positive' : 'negative'}">
                            ${metrics.pe_ratio <= metrics.industry_pe ? 'Thấp hơn ngành' : 'Cao hơn ngành'}
                            ${metrics.industry_pe > 0 ? ` (${((metrics.pe_ratio / metrics.industry_pe - 1) * 100).toFixed(1)}%)` : ''}
                        </div>
                    </div>
                    ` : ''}
                    ${peAnalysis && peAnalysis.suggested_base_pe ? `
                    <div class="detail-item">
                        <div class="detail-label">Base PE đề xuất (Graham)</div>
                        <div class="detail-value">
                            ${peAnalysis.suggested_base_pe.toFixed(2)}
                            ${peAnalysis.industry ? ` <span style="font-size: 0.8em; color: #666;">(${peAnalysis.industry})</span>` : ''}
                        </div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Base PE hiện tại (config)</div>
                        <div class="detail-value ${Math.abs((grahamParams.base_pe || 8.5) - peAnalysis.suggested_base_pe) > 0.5 ? 'negative' : 'positive'}">
                            ${grahamParams.base_pe || 8.5}
                            ${Math.abs((grahamParams.base_pe || 8.5) - peAnalysis.suggested_base_pe) > 0.5 ? 
                                ` <span style="font-size: 0.8em; color: #ef4444;">(Khác ${((grahamParams.base_pe || 8.5) - peAnalysis.suggested_base_pe).toFixed(2)})</span>` : 
                                ` <span style="font-size: 0.8em; color: #10b981;">(Phù hợp)</span>`}
                        </div>
                    </div>
                    ` : ''}
                    <div class="detail-item">
                        <div class="detail-label">Tỷ số P/FCF</div>
                        <div class="detail-value">${metrics.pfcf_ratio.toFixed(2)}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Tỷ suất FCF</div>
                        <div class="detail-value">${metrics.fcf_yield.toFixed(2)}%</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Tỷ suất lợi nhuận</div>
                        <div class="detail-value">${metrics.earnings_yield.toFixed(2)}%</div>
                    </div>
                </div>
            </div>
            ` : ''}
            
            ${forecast.fcf_forecast && forecast.fcf_forecast.length > 0 ? `
            <div class="section">
                <h3 class="section-title">Dự báo tăng trưởng FCF theo năm</h3>
                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Năm</th>
                                <th>FCF (VND)</th>
                                <th>Tăng trưởng YoY %</th>
                                <th>Tăng trưởng tích lũy %</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${advanced.yearly_growth ? advanced.yearly_growth.map((growth, idx) => `
                                <tr>
                                    <td>Năm ${idx + 1}</td>
                                    <td>${formatNumber(forecast.fcf_forecast[idx] || 0)}</td>
                                    <td>${growth[0].toFixed(2)}%</td>
                                    <td>${growth[1].toFixed(2)}%</td>
                                </tr>
                            `).join('') : forecast.fcf_forecast.map((fcf, idx) => `
                                <tr>
                                    <td>Năm ${idx + 1}</td>
                                    <td>${formatNumber(fcf)}</td>
                                    <td>-</td>
                                    <td>-</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
            ` : ''}
            
            ${yearlyPrice && yearlyPrice.length > 0 ? `
            <div class="section">
                <h3 class="section-title">Dự báo giá cổ phiếu theo năm</h3>
                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Năm</th>
                                <th>FCF (VND)</th>
                                <th>Giá trị công ty (VND)</th>
                                <th>Giá/cổ phiếu (VND)</th>
                                <th>Thay đổi</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${yearlyPrice.map(year => `
                                <tr>
                                    <td>Năm ${year.year}</td>
                                    <td>${formatNumber(year.fcf)}</td>
                                    <td>${formatNumber(year.company_value)}</td>
                                    <td><strong>${formatCurrency(year.price_per_share)}</strong></td>
                                    <td class="${year.price_change_pct >= 0 ? 'positive' : 'negative'}">
                                        ${formatPercent(year.price_change_pct)}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h3 class="section-title">Phân tích hiệu suất theo năm</h3>
                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Năm</th>
                                <th>Giá (VND)</th>
                                <th>Tăng trưởng YoY %</th>
                                <th>So với giá hiện tại</th>
                                <th>Số lần</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><strong>Hiện tại</strong></td>
                                <td><strong>${formatCurrency(result.price)}</strong></td>
                                <td>Cơ sở</td>
                                <td>Cơ sở (100%)</td>
                                <td>1.00x</td>
                            </tr>
                            ${yearlyPrice.map(year => `
                                <tr>
                                    <td>Năm ${year.year}</td>
                                    <td><strong>${formatCurrency(year.price_per_share)}</strong></td>
                                    <td class="${year.year_over_year_growth_pct >= 0 ? 'positive' : 'negative'}">
                                        ${formatPercent(year.year_over_year_growth_pct)}
                                    </td>
                                    <td class="${year.price_change_pct >= 0 ? 'positive' : 'negative'}">
                                        ${formatPercent(year.price_change_pct)}
                                    </td>
                                    <td>${year.price_multiplier.toFixed(2)}x</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                <div style="margin-top: 15px; padding: 12px; background: #f9fafb; border-radius: 8px; font-size: 0.9em; color: #666;">
                    <strong>Giải thích:</strong><br>
                    - YoY Growth %: Tăng trưởng năm-over-year (Năm 1 so với giá hiện tại)<br>
                    - vs Current Price: % thay đổi so với giá hiện tại<br>
                    - Multiplier: Số lần tăng giá trị so với giá hiện tại (ví dụ: 1.50x = tăng 50%)
                </div>
            </div>
            ` : ''}
            
            ${result.saved_at ? `
            <div class="section">
                <div class="detail-item">
                    <div class="detail-label">Ngày phân tích</div>
                    <div class="detail-value">${formatTimestampGMT7(result.saved_at)}</div>
                </div>
            </div>
            ` : ''}
        `;
        
        showModal(modalContent);
    } catch (error) {
        console.error('Error loading detail:', error);
        alert('Lỗi khi tải chi tiết. Vui lòng thử lại.');
    }
}

// Show config
async function showConfig(ticker) {
    try {
        const response = await fetch(`/api/stocks/${ticker}/config`);
        const data = await response.json();
        
        if (data.error) {
            alert(data.error);
            return;
        }
        
        const config = data.config;
        const configHtml = Object.entries(config).map(([section, values]) => `
            <div class="section">
                <h3 class="section-title">[${section}]</h3>
                <div class="detail-grid">
                    ${Object.entries(values).map(([key, value]) => `
                        <div class="detail-item">
                            <div class="detail-label">${key}</div>
                            <div class="detail-value">${value}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');
        
        const modalContent = `
            <div class="modal-header">
                <h2 class="modal-title">${ticker} - Cấu hình</h2>
                <span class="close" onclick="closeModal()">&times;</span>
            </div>
            ${configHtml}
        `;
        
        showModal(modalContent);
    } catch (error) {
        console.error('Error loading config:', error);
        alert('Lỗi khi tải config. Vui lòng thử lại.');
    }
}

// Modal functions
function showModal(content) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'detail-modal';
    modal.innerHTML = `<div class="modal-content">${content}</div>`;
    document.body.appendChild(modal);
    modal.style.display = 'block';
}

function closeModal() {
    const modal = document.getElementById('detail-modal');
    if (modal) {
        modal.style.display = 'none';
        modal.remove();
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('detail-modal');
    if (event.target === modal) {
        closeModal();
    }
}

// Initialize real-time updates
// Try SSE first, fallback to smart polling
initSSE();

// If SSE not supported or failed, start smart polling
if (!sseSupported) {
    startSmartPolling();
}

// Initial load
loadStocks();

// Cleanup on page unload
window.addEventListener('beforeunload', cleanupUpdates);

