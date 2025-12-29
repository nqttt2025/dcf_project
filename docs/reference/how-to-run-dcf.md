# Hướng dẫn chạy DCF Analysis cho một mã cổ phiếu

## Tổng quan

Dự án này cung cấp nhiều cách để chạy phân tích DCF (Discounted Cash Flow) cho các mã cổ phiếu VN30.

## Cách 1: Sử dụng Makefile (Khuyến nghị - Đơn giản nhất)

### Chạy DCF cho một mã cổ phiếu cụ thể

```bash
make dcf TICKER=VNM
make dcf TICKER=VCB
make dcf TICKER=FPT
```

**Ví dụ kết quả:**
```
Running DCF analysis for VNM...
[Logs...]
✓ Analysis completed for VNM
  DCF Fair Value: 19,435.99
  Cache saved to: /home/eenitug/dcf_project/data/cache/vnm_cache.json
```

### Chạy DCF cho tất cả mã VN30

```bash
make dcf-all
```

### Xem hướng dẫn

```bash
make dcf-help
```

## Cách 2: Sử dụng Python script trực tiếp

### Chạy với run_dcf.py

```bash
# Từ project root
python3 run_dcf.py VNM.cfg
python3 run_dcf.py VCB.cfg
python3 run_dcf.py FPT.cfg
```

### Chạy với dcf_calculator.py

```bash
# Từ project root
python3 src/core/dcf_calculator.py config/VNM.cfg
python3 src/core/dcf_calculator.py config/VCB.cfg
```

## Cách 3: Sử dụng Python API

### Trong Python script

```python
import asyncio
from src.core.dcf_calculator import calculate_dcf_from_config

async def analyze_stock():
    # Phân tích một mã cổ phiếu
    result = await calculate_dcf_from_config('config/VNM.cfg')
    
    print(f"Ticker: {result['ticker']}")
    print(f"Current Price: {result['price']:,.0f} VND")
    print(f"DCF Fair Value: {result['dcf_fair_value']:,.2f} VND")
    print(f"Graham Fair Value: {result['graham_fair_value']:,.2f} VND")
    print(f"Average Fair Value: {result['average_fair_value']:,.2f} VND")
    
    # Tính upside/downside
    upside = ((result['average_fair_value'] - result['price']) / result['price'] * 100)
    print(f"Upside/Downside: {upside:.1f}%")

# Chạy
asyncio.run(analyze_stock())
```

## Danh sách các mã VN30 có sẵn

Tất cả 30 mã VN30 đã có config files sẵn trong thư mục `config/`:

**Ngân hàng:** VCB, BID, CTG, MBB, HDB, ACB, VIB, VPB, STB, TPB, SSB

**Bất động sản:** VHM, VIC, VRE, NVL, PDR, KDH

**Công nghệ:** FPT, SSI

**Tiêu dùng:** VNM, MSN, MWG, SAB, PNJ

**Năng lượng:** GAS, PLX

**Công nghiệp:** HPG, REE, GVR

**Hàng không:** VJC

## Ví dụ sử dụng thực tế

### Ví dụ 1: Phân tích VNM (Vinamilk)

```bash
make dcf TICKER=VNM
```

**Kết quả sẽ được lưu tại:**
- JSON: `data/results/vnm_result.json`
- Text: `data/results/vnm_result.text`
- Cache: `data/cache/vnm_cache.json`
- Log: `src/utils/log/dcf_vnm.log`

### Ví dụ 2: Phân tích VCB (Vietcombank)

```bash
make dcf TICKER=VCB
```

### Ví dụ 3: Phân tích nhiều mã liên tiếp

```bash
for ticker in VNM VCB FPT; do
    make dcf TICKER=$ticker
    echo ""
done
```

### Ví dụ 4: Phân tích tất cả mã VN30

```bash
make dcf-all
```

## Kết quả và Output

### File kết quả JSON

Mỗi lần chạy sẽ tạo file `data/results/{ticker}_result.json`:

```json
{
  "ticker": "VNM",
  "config_file": "config/VNM.cfg",
  "price": 61500.0,
  "market_cap": 128532259867500.0,
  "eps": 1209.0,
  "shares": 2089955445.0,
  "growth_estimate": 5.31,
  "dcf_params": {
    "yr": 5,
    "dr": 11.0,
    "pr": 2.5
  },
  "dcf_fair_value": 19435.99,
  "graham_fair_value": 23110.72,
  "average_fair_value": 21273.36,
  "cache_file": "/path/to/vnm_cache.json",
  "saved_at": "2025-12-28 15:43:48 UTC",
  "stock_name": "VNM"
}
```

### File kết quả Text

File `data/results/{ticker}_result.text` chứa kết quả dạng text dễ đọc:

```
================================================================================
DCF model (basic)
================================================================================
Market price: 61500
EPS: 1209.00
Growth estimate: 5.31
Term: 5 years
Discount Rate: 11.0%
Perpetual Rate: 2.5%
================================================================================
DCF Fair Value: 19435.99
================================================================================
Graham style valuation basic (Page 295, The Intelligent Investor)
================================================================================
Expected value based on growth rate: 23110.72
================================================================================
```

## Tùy chỉnh tham số DCF

Bạn có thể chỉnh sửa file config để thay đổi tham số DCF:

```bash
# Mở file config
vi config/VNM.cfg
```

**Ví dụ điều chỉnh:**

```ini
[dcf]
yr = 5          # Số năm dự báo (có thể 5-7)
dr = 11.0       # Tỷ lệ chiết khấu (8-15% tùy rủi ro)
pr = 2.5        # Tỷ lệ tăng trưởng vĩnh viễn (2-3%)

[graham]
base_pe = 8.5           # Hệ số PE cơ bản (7-10 tùy ngành)
growth_multiplier = 2    # Hệ số nhân tăng trưởng
```

Sau đó chạy lại:
```bash
make dcf TICKER=VNM
```

## Xử lý lỗi

### Lỗi: "Config file not found"

```bash
# Kiểm tra file config có tồn tại không
ls config/VNM.cfg

# Xem danh sách các config có sẵn
ls config/*.cfg
```

### Lỗi: "Cannot fetch data"

- Kiểm tra kết nối internet
- Kiểm tra vnstock đã được cài đặt: `pip install vnstock`
- Thử lại sau vài phút

### Lỗi: "Growth rate not available"

- Một số mã có thể không có dữ liệu tăng trưởng
- Kiểm tra log file để xem chi tiết: `src/utils/log/dcf_{ticker}.log`

## Workflow đề xuất

### 1. Phân tích một mã mới

```bash
# Bước 1: Tính PE để đề xuất Base PE
make pe TICKER=VNM INDUSTRY=consumer

# Bước 2: (Tùy chọn) Điều chỉnh Base PE trong config
vi config/VNM.cfg

# Bước 3: Chạy DCF analysis
make dcf TICKER=VNM

# Bước 4: Xem kết quả
cat data/results/vnm_result.text
```

### 2. Phân tích định kỳ (hàng tuần/tháng)

```bash
# Chạy cho tất cả mã VN30
make dcf-all

# Xem tổng hợp kết quả
ls -lh data/results/*.json
```

### 3. So sánh các mã

```bash
# Chạy cho nhiều mã
for ticker in VNM VCB FPT; do
    make dcf TICKER=$ticker
done

# So sánh kết quả
grep "average_fair_value" data/results/*.json
```

## Tóm tắt các lệnh

| Lệnh | Mô tả |
|------|-------|
| `make dcf TICKER=VNM` | Chạy DCF cho VNM |
| `make dcf-all` | Chạy DCF cho tất cả VN30 |
| `make dcf-help` | Xem hướng dẫn |
| `python3 run_dcf.py VNM.cfg` | Chạy trực tiếp với Python |
| `make pe TICKER=VNM` | Tính PE trước khi chạy DCF |

---

**Lưu ý**: Kết quả DCF chỉ mang tính tham khảo, không phải lời khuyên đầu tư. Luôn kết hợp với phân tích cơ bản và đánh giá rủi ro.

