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

// Load stocks from API
async function loadStocks() {
    try {
        const response = await fetch('/api/stocks');
        const data = await response.json();
        
        allStocks = data.stocks;
        filteredStocks = [...allStocks];
        
        // Update status bar
        document.getElementById('total-stocks').textContent = data.total;
        document.getElementById('analyzed-stocks').textContent = data.with_results;
        document.getElementById('running-stocks').textContent = data.running;
        
        renderStocks();
    } catch (error) {
        console.error('Error loading stocks:', error);
        document.getElementById('stocks-grid').innerHTML = 
            '<div class="loading">❌ Lỗi khi tải dữ liệu. Vui lòng thử lại.</div>';
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
                        Cập nhật: ${new Date(stock.saved_at).toLocaleString('vi-VN')}
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
                        <div class="detail-label">Số cổ phiếu</div>
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
            
            ${advanced.upside_downside ? `
            <div class="section">
                <h3 class="section-title">Phân tích tiềm năng</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <div class="detail-label">DCF Upside/Downside</div>
                        <div class="detail-value ${advanced.upside_downside.dcf_upside_pct >= 0 ? 'positive' : 'negative'}">
                            ${formatPercent(advanced.upside_downside.dcf_upside_pct)}
                        </div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Graham Upside/Downside</div>
                        <div class="detail-value ${advanced.upside_downside.graham_upside_pct >= 0 ? 'positive' : 'negative'}">
                            ${formatPercent(advanced.upside_downside.graham_upside_pct)}
                        </div>
                    </div>
                </div>
            </div>
            ` : ''}
            
            ${result.saved_at ? `
            <div class="section">
                <div class="detail-label">Thời gian phân tích</div>
                <div class="detail-value">${new Date(result.saved_at).toLocaleString('vi-VN')}</div>
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

// Auto-refresh every 30 seconds
setInterval(loadStocks, 30000);

// Initial load
loadStocks();

