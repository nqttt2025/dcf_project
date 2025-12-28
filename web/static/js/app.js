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
                
                <div class="stock-actions">
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

