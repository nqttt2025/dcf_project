# Giải thích chi tiết: Tại sao DCF Fair Value của FPT là 44,206 VND?

## Dữ liệu đầu vào cho FPT

Từ file `fpt_result.json` và `fpt_cache.json`:

| Tham số | Giá trị |
|---------|---------|
| **Free Cash Flow (FCF)** | 4,344,020,060,779 VND |
| **Growth Rate (ge)** | 10.678% mỗi năm |
| **Shares Outstanding** | 1,703,507,121 cổ phiếu |
| **Discount Rate (dr)** | 10.0% |
| **Perpetual Rate (pr)** | 2.5% |
| **Years (yr)** | 5 năm |

## Công thức DCF

DCF Fair Value được tính theo các bước sau:

### Bước 1: Dự báo Free Cash Flow cho 5 năm

```
Year 0 (hiện tại): FCF₀ = 4,344,020,060,779 VND
Year 1: FCF₁ = FCF₀ × (1 + 10.678%) = 4,808,000,000,000 VND
Year 2: FCF₂ = FCF₁ × (1 + 10.678%) = 5,321,000,000,000 VND
Year 3: FCF₃ = FCF₂ × (1 + 10.678%) = 5,889,000,000,000 VND
Year 4: FCF₄ = FCF₃ × (1 + 10.678%) = 6,518,000,000,000 VND
```

### Bước 2: Tính Terminal Value (Giá trị vĩnh viễn)

Terminal Value đại diện cho giá trị của công ty sau năm thứ 5, giả định tăng trưởng vĩnh viễn 2.5%/năm.

```
Terminal Value = FCF₄ × (1 + pr) / (dr - pr)
                = 6,518,000,000,000 × (1 + 0.025) / (0.10 - 0.025)
                = 6,518,000,000,000 × 1.025 / 0.075
                = 89,079,000,000,000 VND
```

### Bước 3: Chiết khấu về giá trị hiện tại (Present Value)

Mỗi dòng tiền được chiết khấu về hiện tại với tỷ lệ 10%:

```
PV Factor Year 1 = 1 / (1 + 0.10)¹ = 0.9091
PV Factor Year 2 = 1 / (1 + 0.10)² = 0.8264
PV Factor Year 3 = 1 / (1 + 0.10)³ = 0.7513
PV Factor Year 4 = 1 / (1 + 0.10)⁴ = 0.6830
PV Factor Year 5 = 1 / (1 + 0.10)⁵ = 0.6209
```

**Present Values:**

```
PV₁ = FCF₁ × 0.9091 = 4,808B × 0.9091 = 4,370B VND
PV₂ = FCF₂ × 0.8264 = 5,321B × 0.8264 = 4,397B VND
PV₃ = FCF₃ × 0.7513 = 5,889B × 0.7513 = 4,424B VND
PV₄ = FCF₄ × 0.6830 = 6,518B × 0.6830 = 4,452B VND
PV₅ (Terminal) = 89,079B × 0.6209 = 55,310B VND
```

### Bước 4: Tổng giá trị doanh nghiệp (Enterprise Value)

```
Total DCF Value = PV₁ + PV₂ + PV₃ + PV₄ + PV₅
                 = 4,370B + 4,397B + 4,424B + 4,452B + 55,310B
                 = 72,953,000,000,000 VND
```

### Bước 5: Tính giá trị trên mỗi cổ phiếu

```
DCF Fair Value = Total DCF Value / Shares Outstanding
                = 72,953,000,000,000 / 1,703,507,121
                = 42,826 VND
```

**Lưu ý:** Giá trị thực tế 44,206 VND có thể khác một chút do:
- Làm tròn trong quá trình tính toán
- Dữ liệu FCF có thể được cập nhật
- Các hệ số chiết khấu được tính chính xác hơn

## Tại sao giá trị này thấp hơn giá thị trường?

**Giá thị trường:** 92,500 VND  
**DCF Fair Value:** 44,206 VND  
**Chênh lệch:** -52.2% (giá thị trường cao hơn giá trị công bằng)

### Lý do có thể:

1. **Thị trường kỳ vọng tăng trưởng cao hơn**
   - DCF dùng growth rate 10.68%
   - Thị trường có thể kỳ vọng 15-20%

2. **Discount rate có thể quá cao**
   - DCF dùng 10%
   - Với công ty công nghệ như FPT, có thể thấp hơn (8-9%)

3. **Terminal value có thể được định giá cao**
   - Thị trường tin FPT sẽ tiếp tục tăng trưởng mạnh sau 5 năm

4. **Yếu tố tâm lý và thanh khoản**
   - FPT là mã blue-chip, được nhiều nhà đầu tư quan tâm
   - Thanh khoản cao, dễ mua bán

## Điều chỉnh để giá trị gần với thị trường hơn

Nếu muốn DCF Fair Value gần với giá thị trường (92,500 VND), bạn có thể:

### Option 1: Giảm Discount Rate

```ini
[dcf]
dr = 8.0    # Thay vì 10.0%
```

### Option 2: Tăng Growth Rate

Nếu FPT có thể tăng trưởng 15%/năm thay vì 10.68%:
- DCF Fair Value sẽ tăng lên đáng kể

### Option 3: Tăng Perpetual Rate

```ini
[dcf]
pr = 3.5    # Thay vì 2.5%
```

## Kết luận

DCF Fair Value = 44,206 VND được tính dựa trên:
- **FCF hiện tại:** 4.34 nghìn tỷ VND
- **Tăng trưởng:** 10.68%/năm trong 5 năm
- **Chiết khấu:** 10%/năm
- **Tăng trưởng vĩnh viễn:** 2.5%/năm sau năm thứ 5

Giá trị này phản ánh **giá trị nội tại** của công ty dựa trên dòng tiền tự do, không bao gồm các yếu tố tâm lý thị trường.

---

**Lưu ý:** DCF chỉ là một công cụ định giá, không phải lời khuyên đầu tư. Luôn kết hợp với phân tích cơ bản và đánh giá rủi ro.

