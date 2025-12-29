# Phân tích sự khác biệt Free Cash Flow giữa stockanalysis.com và vnstock

## Vấn đề

Có sự khác biệt lớn giữa giá trị Free Cash Flow của FPT từ:
- **stockanalysis.com**: 6,460,442 triệu VND (TTM)
- **vnstock**: 3,513,649 triệu VND

## So sánh chi tiết

### Từ stockanalysis.com (TTM - Trailing Twelve Months)
**Nguồn:** [stockanalysis.com FPT Cash Flow](https://stockanalysis.com/quote/hose/FPT/financials/cash-flow-statement/)

| Metric | Giá trị (triệu VND) | Giá trị (VND) |
|--------|---------------------|---------------|
| Operating Cash Flow | 11,424,150 | 11,424,150,000,000 |
| Capital Expenditures | 4,963,707 | 4,963,707,000,000 |
| **Free Cash Flow** | **6,460,442** | **6,460,442,000,000** |

**Kỳ báo cáo:** TTM (Trailing Twelve Months) - tính từ Sep 30, 2025 ngược lại 12 tháng

### Từ vnstock

| Metric | Giá trị (VND) |
|--------|---------------|
| Operating Cash Flow | 4,344,020,060,779 |
| Capital Expenditures | 830,371,040,007 |
| **Free Cash Flow** | **3,513,649,020,772** |

**Kỳ báo cáo:** Cần kiểm tra (có thể là năm tài chính 2024 hoặc quý gần nhất)

## Phân tích chênh lệch

| Metric | Chênh lệch (VND) | % chênh lệch |
|--------|------------------|--------------|
| Operating Cash Flow | 7,080,129,939,221 | **-62.0%** (vnstock thấp hơn) |
| Capital Expenditures | 4,133,335,959,993 | **-83.3%** (vnstock thấp hơn) |
| Free Cash Flow | 2,946,792,979,228 | **-45.6%** (vnstock thấp hơn) |

## Nguyên nhân có thể

### 1. **Khác biệt về kỳ báo cáo** (Nguyên nhân chính)

**stockanalysis.com:**
- Sử dụng **TTM (Trailing Twelve Months)**
- Tính từ Sep 30, 2025 ngược lại 12 tháng
- Bao gồm dữ liệu từ Q4 2024 + Q1-Q3 2025

**vnstock:**
- Có thể đang lấy dữ liệu từ:
  - **Năm tài chính 2024** (FY 2024: Jan-Dec 2024)
  - Hoặc **quý gần nhất** (Q3 2025)
- Không phải TTM

### 2. **Khác biệt về định nghĩa và cách tính**

**stockanalysis.com:**
- Có thể điều chỉnh và chuẩn hóa dữ liệu
- Tính toán FCF theo chuẩn quốc tế
- Có thể bao gồm các điều chỉnh khác

**vnstock:**
- Lấy trực tiếp từ báo cáo tài chính của công ty
- Có thể không điều chỉnh
- Phụ thuộc vào cách công ty báo cáo

### 3. **Khác biệt về nguồn dữ liệu**

**stockanalysis.com:**
- Sử dụng dữ liệu từ S&P Global Market Intelligence
- Có thể có điều chỉnh và chuẩn hóa

**vnstock:**
- Lấy từ nguồn VCI (Vietnam)
- Dữ liệu gốc từ báo cáo tài chính của công ty

### 4. **Khác biệt về cách xử lý CapEx**

**stockanalysis.com:**
- CapEx = 4,963,707 triệu VND
- Có thể bao gồm tất cả các khoản đầu tư vào tài sản cố định

**vnstock:**
- CapEx = 830,371 triệu VND (chỉ 17% so với stockanalysis)
- Có thể chỉ lấy một phần hoặc định nghĩa khác

## Tác động đến DCF Valuation

### Với giá trị từ stockanalysis.com:
- FCF = 6,460,442 triệu VND
- DCF Fair Value sẽ **CAO HƠN** đáng kể

### Với giá trị từ vnstock:
- FCF = 3,513,649 triệu VND  
- DCF Fair Value = 35,756 VND (hiện tại)

### Chênh lệch:
- Nếu dùng FCF từ stockanalysis.com, DCF Fair Value có thể tăng khoảng **45-60%**

## Khuyến nghị

### 1. **Kiểm tra kỳ báo cáo của vnstock**
```python
# Cần kiểm tra xem vnstock đang lấy dữ liệu từ kỳ nào
cash_flow_df = stock.finance.cash_flow()
print(cash_flow_df.index)  # Xem các kỳ có sẵn
print(cash_flow_df.iloc[0])  # Xem dữ liệu kỳ đầu tiên
```

### 2. **Sử dụng TTM nếu có thể**
- TTM (Trailing Twelve Months) phản ánh tốt hơn tình hình hiện tại
- Nếu vnstock không hỗ trợ TTM, có thể tính thủ công bằng cách:
  - Lấy dữ liệu từ 4 quý gần nhất
  - Cộng dồn các giá trị

### 3. **Xác nhận với báo cáo tài chính chính thức**
- Kiểm tra báo cáo tài chính của FPT trên website công ty
- So sánh với cả hai nguồn để xác định giá trị chính xác

### 4. **Ghi chú trong code**
- Thêm comment về kỳ báo cáo đang sử dụng
- Cảnh báo về sự khác biệt có thể có giữa các nguồn

## Kết luận

**Sự khác biệt chủ yếu do:**
1. ✅ **Kỳ báo cáo khác nhau** (TTM vs FY/Quý)
2. ✅ **Nguồn dữ liệu khác nhau** (S&P Global vs VCI)
3. ✅ **Cách tính và định nghĩa có thể khác nhau**

**Khuyến nghị:**
- Sử dụng TTM nếu có thể để phản ánh tốt hơn tình hình hiện tại
- Kiểm tra và xác nhận với báo cáo tài chính chính thức
- Ghi chú rõ ràng về kỳ báo cáo đang sử dụng trong code

---

**Lưu ý:** Giá trị từ stockanalysis.com (TTM) thường được coi là chuẩn hơn cho phân tích DCF vì phản ánh tình hình 12 tháng gần nhất, không chỉ một năm tài chính cụ thể.

