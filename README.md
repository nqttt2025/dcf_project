# DCF Valuation Project

## Cấu trúc dự án

### File Config
- **DCF.cfg** - File cấu hình chính
  - `[dcf]` - Các tham số DCF (yr, dr, pr)
  - `[graham]` - Các hệ số Graham (base_pe, growth_multiplier)
  - `[ticker]` - Mã cổ phiếu cần phân tích
  - `[data_source]` - Nguồn dữ liệu (VCI)

### Classes

#### ConfigManager (config_manager.py)
- Singleton class đọc config từ file
- Cung cấp các parameters cho ứng dụng
- Fallback values nếu config không tồn tại

**Các phương thức chính:**
- `get_dcf_params()` - Lấy yr, dr, pr
- `get_graham_params()` - Lấy base_pe, growth_multiplier
- `get_ticker()` - Lấy mã cổ phiếu
- `log_config()` - Log hiện tại config

#### CacheManager (cache_manager.py)
- Singleton cache manager với lazy save
- Lưu data với GMT/UTC timestamp

#### LoggerSingleton (logger.py)
- Singleton logger với file rotation
- Format: `YYYY-MM-DD HH:MM:SS - module - function (Line: X) - LEVEL - message`

### Các Script

#### value_estimator.py
- Version tuần tự (sequential)
- Lấy dữ liệu từng cái một
- Thích hợp cho debugging

**Chạy:**
```bash
python3 value_estimator.py
```

#### value_estimator_async.py
- **Version bất đồng bộ (async)** - RECOMMENDED
- Lấy dữ liệu song song để tăng hiệu suất
- ~60% nhanh hơn version tuần tự

**Chạy:**
```bash
python3 value_estimator_async.py
```

### Dữ liệu từ vnstock
Tất cả dữ liệu được lấy từ vnstock (không scraping):
- **Free Cash Flow** - từ balance sheet
- **Shares Outstanding** - từ charter capital ÷ 10,000
- **EPS** - tính từ net profit ÷ shares
- **Price** - từ price board (real-time)
- **Market Cap** - từ ratio summary (EV)
- **Growth Estimate** - weighted average của:
  - Net Profit Growth YoY (50%)
  - Revenue Growth YoY (30%)
  - Historical Average (20%)

### Cache System
- Singleton CacheManager
- Lazy save (chỉ lưu 1 lần khi chạy xong)
- GMT/UTC timestamps
- JSON format

**Cache file:** `data/fcf_cache.json`

### DCF Parameters Giải thích

| Tham số | Mặc định | Ý nghĩa |
|---------|----------|--------|
| `yr` | 5 | Số năm dự báo |
| `dr` | 10 | Discount Rate (%) |
| `pr` | 2.5 | Perpetual/Terminal Growth Rate (%) |
| `base_pe` | 8.5 | Base PE từ Graham |
| `growth_multiplier` | 2 | Growth multiplier từ Graham |

### Hiệu suất

**Benchmark lần chạy gần nhất:**
- Sequential: 16.59 giây
- Async: 6.36 giây
- **Cải thiện: 60.7% nhanh hơn** ⚡

### Logging
Tất cả output được log với thông tin chi tiết:
- Timestamp (GMT/UTC)
- Module name
- Function name & line number
- Log level (INFO, WARNING, ERROR)
- Message

**Log file:** `log/dcf_project.log`

## Cách sử dụng

### 1. Chạy phân tích DCF
```bash
# Async (nhanh hơn, recommended)
python3 value_estimator_async.py

# Sequential (chậm hơn, dùng để debug)
python3 value_estimator.py
```

### 2. Tùy chỉnh config
Edit `DCF.cfg`:
```ini
[dcf]
yr = 7              # Dự báo 7 năm
dr = 12             # Discount rate 12%
pr = 3              # Perpetual growth 3%

[ticker]
ticker = VNM        # Phân tích Vinamilk
```

### 3. Check config
```bash
python3 config_manager.py
```

### 4. View logs
```bash
tail -f log/dcf_project.log
```

## Công thức

### DCF Model
```
Fair Value = Σ(CF_t / (1 + DR)^t) + Terminal Value
Terminal Value = CF_n × (1 + PR) / (DR - PR)
```

### Graham Valuation
```
Fair Value = EPS × (8.5 + 2 × Growth Rate)
```

## Các tệp trong project
- `fcfs.py` - Hàm lấy financial data
- `ge.py` - Growth estimate
- `company.py` - Company-specific logic
- `value_estimator.py` - DCF sequential
- `value_estimator_async.py` - DCF async (RECOMMENDED)
- `cache_manager.py` - Cache singleton
- `config_manager.py` - Config singleton
- `logger.py` - Logger singleton
- `DCF.cfg` - Configuration file
- `log/dcf_project.log` - Log file
- `data/fcf_cache.json` - Cache data
