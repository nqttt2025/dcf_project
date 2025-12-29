# Cách tính Hệ số PE Cơ bản (Base PE) cho từng mã cổ phiếu

## 1. PE là gì?

**PE (Price-to-Earnings Ratio)** = Giá cổ phiếu / Lợi nhuận trên mỗi cổ phiếu

```
PE = Price / EPS
```

### Ví dụ với VNM:
- **Price** = 61,500 VND
- **EPS** = 1,209 VND
- **PE thực tế** = 61,500 / 1,209 = **50.87**

## 2. PE Cơ bản (Base PE) trong công thức Graham

Trong công thức Graham:
```
Graham Fair Value = EPS × (Base PE + 2 × Growth Rate)
```

**Base PE = 8.5** là giá trị mặc định từ Benjamin Graham, đại diện cho:
- PE hợp lý cho một công ty **không tăng trưởng**
- Công ty ổn định, trả cổ tức đều đặn
- Mức định giá an toàn

## 3. Cách tính PE Cơ bản phù hợp cho từng mã

### Phương pháp 1: Dựa trên PE trung bình ngành

#### Bước 1: Tính PE thực tế của công ty
```python
PE_thực_tế = Giá_cổ_phiếu / EPS
```

#### Bước 2: So sánh với PE trung bình ngành

| Ngành | PE Trung bình ngành | Base PE đề xuất |
|-------|---------------------|-----------------|
| **Ngân hàng** | 8-12 | 7-8 |
| **Bất động sản** | 10-15 | 8-9 |
| **Công nghệ** | 15-25 | 9-10 |
| **Tiêu dùng** | 12-18 | 8.5-9 |
| **Năng lượng** | 8-12 | 7.5-8.5 |
| **Công nghiệp** | 10-15 | 8-9 |
| **Hàng không** | 12-20 | 8.5-9.5 |

#### Bước 3: Điều chỉnh Base PE

```
Base PE = PE_trung_bình_ngành × (1 - Risk_factor)
```

Trong đó:
- **Risk_factor** = 0.1-0.2 cho công ty ổn định
- **Risk_factor** = 0.2-0.3 cho công ty rủi ro cao

### Phương pháp 2: Dựa trên lịch sử PE của công ty

#### Bước 1: Thu thập PE lịch sử (5-10 năm)
```python
PE_lịch_sử = [PE_2023, PE_2022, PE_2021, PE_2020, PE_2019]
```

#### Bước 2: Tính PE trung bình
```python
PE_trung_bình = sum(PE_lịch_sử) / len(PE_lịch_sử)
```

#### Bước 3: Loại bỏ yếu tố tăng trưởng
```python
Base_PE = PE_trung_bình / (1 + Growth_rate_historical)
```

### Phương pháp 3: Dựa trên công thức nghịch đảo

Từ công thức Graham, ta có thể tính ngược:

```
PE_thực_tế = Price / EPS
Growth_priced_in = (PE_thực_tế - Base_PE) / 2
```

Nếu bạn biết **Growth rate hợp lý** của công ty, có thể tính:
```
Base_PE = PE_thực_tế - (2 × Growth_rate_hợp_lý)
```

## 4. Ví dụ cụ thể cho các mã VN30

### Ví dụ 1: VNM (Vinamilk) - Tiêu dùng

**Dữ liệu:**
- Price = 61,500 VND
- EPS = 1,209 VND
- PE thực tế = 50.87
- Growth rate = 5.31%

**Tính toán:**
```
# Nếu dùng Base PE = 8.5 (mặc định)
Graham Value = 1,209 × (8.5 + 2 × 5.31) = 23,110 VND

# Nếu điều chỉnh Base PE = 9 (cho ngành tiêu dùng)
Graham Value = 1,209 × (9 + 2 × 5.31) = 23,519 VND
```

**Đề xuất Base PE cho VNM:** 8.5-9.0 (ngành tiêu dùng ổn định)

### Ví dụ 2: VCB (Vietcombank) - Ngân hàng

**Đặc thù ngân hàng:**
- Rủi ro cao hơn
- PE thường thấp hơn (8-12)
- Base PE nên thấp hơn

**Đề xuất Base PE cho VCB:** 7-8

### Ví dụ 3: FPT - Công nghệ

**Đặc thù công nghệ:**
- Tăng trưởng cao
- PE thường cao (15-25)
- Base PE có thể cao hơn

**Đề xuất Base PE cho FPT:** 9-10

## 5. Bảng đề xuất Base PE cho VN30

| Mã | Ngành | Base PE đề xuất | Lý do |
|----|-------|----------------|-------|
| **VCB, BID, CTG** | Ngân hàng | 7-8 | Rủi ro cao, PE thấp |
| **MBB, HDB, ACB** | Ngân hàng | 7.5-8.5 | Ngân hàng nhỏ hơn, rủi ro cao |
| **VHM, VIC, VRE** | Bất động sản | 8-9 | Biến động theo chu kỳ |
| **NVL, PDR, KDH** | Bất động sản | 8-9 | Tương tự |
| **FPT** | Công nghệ | 9-10 | Tăng trưởng cao |
| **VNM, MSN, MWG** | Tiêu dùng | 8.5-9 | Ổn định, tăng trưởng đều |
| **SAB, PNJ** | Tiêu dùng | 8.5-9 | Tương tự |
| **GAS, PLX** | Năng lượng | 7.5-8.5 | Biến động theo giá dầu |
| **HPG, REE** | Công nghiệp | 8-9 | Phụ thuộc chu kỳ kinh tế |
| **VJC** | Hàng không | 8.5-9.5 | Rủi ro cao, biến động |

## 6. Cách cập nhật Base PE trong config file

### Ví dụ: Cập nhật cho VCB (Ngân hàng)

```ini
[graham]
base_pe = 7.5          # Điều chỉnh từ 8.5 xuống 7.5 cho ngân hàng
growth_multiplier = 2
```

### Ví dụ: Cập nhật cho FPT (Công nghệ)

```ini
[graham]
base_pe = 9.5           # Điều chỉnh từ 8.5 lên 9.5 cho công nghệ
growth_multiplier = 2
```

## 7. Script tính toán PE tự động

Bạn có thể tạo script để tính PE trung bình ngành:

```python
import pandas as pd
from src.core.fcfs import price_board_stock, get_earnings_per_share_Diluted

def calculate_current_pe(ticker):
    """Tính PE hiện tại của mã cổ phiếu"""
    price = price_board_stock(ticker)
    eps = get_earnings_per_share_Diluted(ticker)
    
    if eps > 0:
        pe = price / eps
        return pe
    return None

def suggest_base_pe(ticker, industry):
    """Đề xuất Base PE dựa trên ngành"""
    pe_current = calculate_current_pe(ticker)
    
    industry_pe_ranges = {
        'banking': (7, 8),
        'real_estate': (8, 9),
        'technology': (9, 10),
        'consumer': (8.5, 9),
        'energy': (7.5, 8.5),
        'industrial': (8, 9),
        'aviation': (8.5, 9.5)
    }
    
    if industry in industry_pe_ranges:
        base_pe_min, base_pe_max = industry_pe_ranges[industry]
        # Nếu PE hiện tại quá cao, dùng giá trị thấp hơn
        if pe_current and pe_current > 30:
            return base_pe_min
        return (base_pe_min + base_pe_max) / 2
    
    return 8.5  # Mặc định
```

## 8. Lưu ý quan trọng

⚠️ **Base PE không phải là PE thực tế của công ty**

- **PE thực tế** = Price / EPS (thay đổi theo thị trường)
- **Base PE** = Giá trị cố định trong công thức Graham (đại diện cho công ty không tăng trưởng)

⚠️ **Base PE nên điều chỉnh theo:**
- Đặc thù ngành nghề
- Mức độ rủi ro
- Lịch sử PE của công ty
- Điều kiện thị trường

⚠️ **Không nên thay đổi Base PE quá thường xuyên:**
- Base PE là giá trị cơ bản, ổn định
- Chỉ điều chỉnh khi có thay đổi lớn về ngành hoặc công ty

## 9. Kết luận

**Cách đơn giản nhất:**
1. Sử dụng **Base PE = 8.5** (mặc định từ Graham) cho tất cả các mã
2. Điều chỉnh theo ngành nếu cần:
   - Ngân hàng: 7-8
   - Công nghệ: 9-10
   - Tiêu dùng: 8.5-9
   - Các ngành khác: 8-9

**Cách chính xác hơn:**
1. Tính PE trung bình ngành
2. Tính PE lịch sử của công ty
3. Điều chỉnh Base PE dựa trên cả hai yếu tố

---

**Tóm lại**: Base PE trong công thức Graham là giá trị cơ bản (mặc định 8.5), nhưng bạn có thể điều chỉnh từ 7-10 tùy theo đặc thù ngành và công ty để có kết quả định giá chính xác hơn.

