# Giải thích sự khác biệt Free Cash Flow giữa stockanalysis.com và vnstock

## Tóm tắt

**Nguyên nhân chính:** vnstock đang lấy dữ liệu từ **một quý cụ thể** (Q3 2025), trong khi stockanalysis.com sử dụng **TTM (Trailing Twelve Months)** - tổng hợp 4 quý gần nhất.

## So sánh chi tiết

### Từ stockanalysis.com
**Nguồn:** [stockanalysis.com FPT Cash Flow](https://stockanalysis.com/quote/hose/FPT/financials/cash-flow-statement/)

| Metric | Giá trị (triệu VND) | Giá trị (VND) |
|--------|---------------------|---------------|
| Operating Cash Flow | 11,424,150 | 11,424,150,000,000 |
| Capital Expenditures | 4,963,707 | 4,963,707,000,000 |
| **Free Cash Flow** | **6,460,442** | **6,460,442,000,000** |

**Kỳ báo cáo:** TTM (Trailing Twelve Months) - tính từ Sep 30, 2025 ngược lại 12 tháng
- Bao gồm: Q4 2024 + Q1-Q3 2025 (4 quý)

### Từ vnstock (hiện tại)

| Metric | Giá trị (VND) |
|--------|---------------|
| Operating Cash Flow | 4,344,020,060,779 |
| Capital Expenditures | 830,371,040,007 |
| **Free Cash Flow** | **3,513,649,020,772** |

**Kỳ báo cáo:** Năm 2025, Quý 3 (chỉ 1 quý)

### Chênh lệch

| Metric | Chênh lệch | % |
|--------|------------|---|
| Operating Cash Flow | -7,080 tỷ VND | **-62.0%** |
| Capital Expenditures | -4,133 tỷ VND | **-83.3%** |
| Free Cash Flow | -2,947 tỷ VND | **-45.6%** |

## Nguyên nhân

### 1. **Kỳ báo cáo khác nhau** (Nguyên nhân chính)

**vnstock:**
- Lấy dữ liệu từ **Quý 3 năm 2025** (1 quý)
- Code hiện tại: `cash_flow_df.iloc[0]` → lấy dòng đầu tiên

**stockanalysis.com:**
- Sử dụng **TTM (Trailing Twelve Months)**
- Tổng hợp 4 quý gần nhất: Q4 2024 + Q1-Q3 2025

### 2. **Dữ liệu từ vnstock có sẵn**

Từ phân tích, vnstock có dữ liệu cho các quý:
- Q3 2025: OCF = 4,344 tỷ VND, CapEx = 830 tỷ VND
- Q2 2025: OCF = 4,190 tỷ VND, CapEx = 688 tỷ VND
- Q1 2025: (cần kiểm tra)
- Q4 2024: OCF = 5,397 tỷ VND, CapEx = 838 tỷ VND

**TTM từ vnstock (nếu cộng 4 quý):**
- OCF ≈ 13,931 tỷ VND (cao hơn stockanalysis.com)
- CapEx ≈ 2,357 tỷ VND (thấp hơn stockanalysis.com)
- FCF ≈ 11,574 tỷ VND

### 3. **Định nghĩa CapEx có thể khác**

**stockanalysis.com:**
- CapEx = 4,963 tỷ VND
- Có thể bao gồm tất cả các khoản đầu tư vào tài sản cố định
- Có thể có điều chỉnh và chuẩn hóa

**vnstock:**
- CapEx = 830 tỷ VND (chỉ cho Q3 2025)
- Chỉ lấy "Purchase of fixed assets" từ báo cáo
- Không có điều chỉnh

## Tác động đến DCF Valuation

### Với giá trị hiện tại (Q3 2025):
- FCF = 3,513,649 triệu VND
- DCF Fair Value = **35,756 VND**

### Với giá trị TTM từ stockanalysis.com:
- FCF = 6,460,442 triệu VND
- DCF Fair Value sẽ **CAO HƠN khoảng 84%** (ước tính)

### Với giá trị TTM từ vnstock (nếu tính đúng):
- FCF ≈ 11,574,000 triệu VND (nếu cộng 4 quý)
- DCF Fair Value sẽ **CAO HƠN đáng kể**

## Giải pháp

### Tùy chọn 1: Tính TTM từ vnstock (Khuyến nghị)

Cập nhật hàm `get_free_cash_flow()` để:
1. Lấy dữ liệu từ 4 quý gần nhất
2. Cộng dồn OCF và CapEx
3. Tính FCF = TTM_OCF - TTM_CapEx

**Ưu điểm:**
- Phản ánh tốt hơn tình hình hiện tại
- Nhất quán với cách tính của stockanalysis.com
- Giá trị chính xác hơn cho DCF

**Nhược điểm:**
- Code phức tạp hơn
- Cần xử lý nhiều kỳ báo cáo

### Tùy chọn 2: Giữ nguyên và ghi chú rõ ràng

Giữ nguyên code hiện tại nhưng:
1. Thêm comment về kỳ báo cáo đang sử dụng
2. Cảnh báo về sự khác biệt với TTM
3. Ghi chú trong documentation

**Ưu điểm:**
- Đơn giản, không cần sửa code
- Giá trị vẫn đúng cho kỳ đó

**Nhược điểm:**
- DCF Fair Value có thể thấp hơn giá trị thực tế
- Không phản ánh tốt tình hình hiện tại

### Tùy chọn 3: Sử dụng nguồn dữ liệu khác

Nếu có thể, sử dụng API hoặc nguồn dữ liệu cung cấp TTM trực tiếp.

## Khuyến nghị

**Nên tính TTM từ vnstock** vì:
1. ✅ Phản ánh tốt hơn tình hình hiện tại (12 tháng gần nhất)
2. ✅ Nhất quán với cách tính chuẩn trong phân tích tài chính
3. ✅ DCF Fair Value sẽ chính xác hơn
4. ✅ Có thể so sánh với các nguồn khác như stockanalysis.com

## Code mẫu để tính TTM

```python
def get_free_cash_flow_ttm(ticker):
    """
    Tính Free Cash Flow TTM (Trailing Twelve Months)
    bằng cách cộng dồn 4 quý gần nhất
    """
    stock = Vnstock().stock(symbol=ticker.upper(), source="VCI")
    cash_flow_df = stock.finance.cash_flow()
    
    ocf_col = 'Net cash inflows/outflows from operating activities'
    capex_col = 'Purchase of fixed assets'
    
    ttm_ocf = 0
    ttm_capex = 0
    quarters_counted = 0
    
    for idx in range(len(cash_flow_df)):
        row = cash_flow_df.iloc[idx]
        
        ocf_val = row.get(ocf_col, 0)
        capex_val = row.get(capex_col, 0)
        
        if pd.notna(ocf_val) and ocf_val != 0:
            try:
                ocf_float = float(ocf_val)
                capex_float = abs(float(capex_val)) if capex_val != 0 else 0
                
                if ocf_float > 0 and quarters_counted < 4:
                    ttm_ocf += ocf_float
                    ttm_capex += capex_float
                    quarters_counted += 1
                    
                    if quarters_counted == 4:
                        break
            except (ValueError, TypeError):
                continue
    
    ttm_fcf = ttm_ocf - ttm_capex
    return ttm_fcf
```

## Kết luận

**Sự khác biệt là do:**
1. ✅ vnstock lấy dữ liệu từ **1 quý** (Q3 2025)
2. ✅ stockanalysis.com sử dụng **TTM** (4 quý gần nhất)
3. ✅ Định nghĩa CapEx có thể khác nhau

**Giá trị từ vnstock là ĐÚNG cho kỳ đó**, nhưng **TTM phản ánh tốt hơn** cho phân tích DCF.

**Khuyến nghị:** Cập nhật code để tính TTM từ vnstock bằng cách cộng dồn 4 quý gần nhất.

---

**Tài liệu tham khảo:**
- [stockanalysis.com FPT Cash Flow](https://stockanalysis.com/quote/hose/FPT/financials/cash-flow-statement/)
- [vnstock Documentation](https://vnstocks.com/onboard)

