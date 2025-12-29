# Tùy chọn ngôn ngữ cho báo cáo

## Tổng quan

Dự án hỗ trợ **2 ngôn ngữ** cho file báo cáo kết quả:
- **Tiếng Việt (vi)** - Mặc định
- **Tiếng Anh (en)**

## Cách sử dụng

### 1. Cấu hình trong file config

Thêm section `[report]` vào file config của mã cổ phiếu:

```ini
[report]
# Ngôn ngữ cho báo cáo: vi (Tiếng Việt) hoặc en (Tiếng Anh)
# Language for report: vi (Vietnamese) or en (English)
language = vi
```

### 2. Các giá trị có thể

- `vi` hoặc `VI` - Tiếng Việt (mặc định)
- `en` hoặc `EN` - Tiếng Anh
- Nếu không có section `[report]` hoặc giá trị không hợp lệ, mặc định sẽ là **tiếng Việt**

### 3. Ví dụ

#### Tiếng Việt (mặc định):
```ini
[report]
language = vi
```

**Kết quả:**
```
================================================================================
PHÂN TÍCH ĐỊNH GIÁ DCF - FPT
================================================================================

THÔNG SỐ ĐẦU VÀO
--------------------------------------------------------------------------------
Giá thị trường: 92,500.00 VND
EPS: 1,429.31 VND
Dòng tiền tự do (TTM): 13,933,764,607,232 VND
...
```

#### Tiếng Anh:
```ini
[report]
language = en
```

**Kết quả:**
```
================================================================================
DCF VALUATION ANALYSIS - FPT
================================================================================

INPUT PARAMETERS
--------------------------------------------------------------------------------
Market Price: 92,500.00 VND
EPS: 1,429.31 VND
Free Cash Flow (TTM): 13,933,764,607,232 VND
...
```

## Các phần được dịch

Tất cả các phần trong báo cáo đều được dịch:

### Headers
- DCF VALUATION ANALYSIS → PHÂN TÍCH ĐỊNH GIÁ DCF
- INPUT PARAMETERS → THÔNG SỐ ĐẦU VÀO
- VALUATION RESULTS → KẾT QUẢ ĐỊNH GIÁ
- UPSIDE/DOWNSIDE ANALYSIS → PHÂN TÍCH TIỀM NĂNG TĂNG/GIẢM GIÁ
- VALUATION METRICS → CHỈ SỐ ĐỊNH GIÁ
- YEARLY FCF GROWTH FORECAST → DỰ BÁO TĂNG TRƯỞNG FCF THEO NĂM
- YEARLY PRICE FORECAST → DỰ BÁO GIÁ CỔ PHIẾU THEO NĂM
- YEARLY PERFORMANCE ANALYSIS → PHÂN TÍCH HIỆU SUẤT THEO NĂM
- GRAHAM VALUATION DETAILS → CHI TIẾT ĐỊNH GIÁ GRAHAM

### Labels
- Market Price → Giá thị trường
- Free Cash Flow (TTM) → Dòng tiền tự do (TTM)
- Shares Outstanding → Số cổ phiếu đang lưu hành
- Market Cap → Vốn hóa thị trường
- Growth Estimate → Tỷ lệ tăng trưởng ước tính
- Forecast Term → Thời gian dự báo
- Discount Rate → Tỷ lệ chiết khấu
- Perpetual Rate → Tỷ lệ tăng trưởng vĩnh viễn
- DCF Fair Value → Giá trị công bằng DCF
- Graham Fair Value → Giá trị công bằng Graham
- Average Fair Value → Giá trị công bằng trung bình
- P/E Ratio → Tỷ số P/E
- P/FCF Ratio → Tỷ số P/FCF
- FCF Yield → Tỷ suất FCF
- Earnings Yield → Tỷ suất lợi nhuận
- Year → Năm
- YoY Growth % → Tăng trưởng YoY %
- Cumulative Growth % → Tăng trưởng tích lũy %
- vs Current Price → So với giá hiện tại
- Multiplier → Số lần

## Cập nhật tất cả config files

Tất cả 30 file config đã được cập nhật với section `[report]` và mặc định là tiếng Việt.

## Thay đổi ngôn ngữ cho một mã cổ phiếu

### Cách 1: Sửa trực tiếp file config

```bash
# Mở file config
nano config/FPT.cfg

# Sửa dòng language
[report]
language = en  # Đổi sang tiếng Anh
```

### Cách 2: Sử dụng script

```bash
# Tạo script để đổi ngôn ngữ
python3 << 'EOF'
import configparser
from pathlib import Path

config_file = Path('config/FPT.cfg')
config = configparser.ConfigParser()
config.read(config_file)

if 'report' not in config:
    config.add_section('report')

config['report']['language'] = 'en'  # hoặc 'vi'

with open(config_file, 'w') as f:
    config.write(f)

print(f"✓ Đã đổi ngôn ngữ sang tiếng Anh trong {config_file}")
EOF
```

## Files liên quan

1. **`src/utils/translations.py`** - Module chứa các bản dịch
2. **`src/utils/result_manager.py`** - Sử dụng translations để tạo báo cáo
3. **`src/core/dcf_calculator.py`** - Đọc language từ config và truyền vào result

## Lưu ý

- Ngôn ngữ chỉ ảnh hưởng đến file `.text`, không ảnh hưởng đến file `.json`
- File JSON luôn giữ nguyên format và keys bằng tiếng Anh để dễ xử lý programmatically
- Mặc định là tiếng Việt để phù hợp với người dùng Việt Nam

## Ví dụ đầy đủ

### File config (FPT.cfg):
```ini
[dcf]
yr = 5
dr = 10
pr = 2.5

[graham]
base_pe = 8.5
growth_multiplier = 2

[ticker]
ticker = FPT

[report]
language = vi
```

### Chạy analysis:
```bash
make dcf TICKER=FPT
```

### Kết quả:
File `data/results/fpt_result.text` sẽ được tạo bằng **tiếng Việt**.

---

**Cập nhật:** 2025-12-28  
**Phiên bản:** 2.0 (Multi-language support)

