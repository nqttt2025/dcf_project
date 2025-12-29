# Cập nhật: Sử dụng TTM (Trailing Twelve Months) mặc định

## Tổng quan

Code đã được cập nhật để **mặc định sử dụng TTM (Trailing Twelve Months)** thay vì chỉ một quý khi tính Free Cash Flow cho phân tích DCF.

## Thay đổi chính

### 1. Hàm `get_free_cash_flow()`

**Trước đây:**
```python
def get_free_cash_flow(ticker, use_ttm=False, use_stockanalysis=False):
    # Mặc định chỉ lấy quý gần nhất
```

**Bây giờ:**
```python
def get_free_cash_flow(ticker, use_ttm=True, use_stockanalysis=False):
    # Mặc định sử dụng TTM (cộng 4 quý gần nhất)
```

### 2. Hàm `get_free_cash_flow_ttm()`

Đã được thêm với comment đầy đủ giải thích:
- TTM là gì và tại sao sử dụng
- Cách tính toán chi tiết
- Ví dụ cụ thể

## Tại sao sử dụng TTM?

### Ưu điểm của TTM:

1. **Phản ánh tốt hơn tình hình hiện tại**
   - TTM bao gồm 12 tháng gần nhất, không chỉ một quý
   - Tránh biến động theo mùa của từng quý riêng lẻ

2. **Chuẩn trong phân tích tài chính**
   - Được sử dụng rộng rãi trong định giá DCF
   - Nhất quán với các nguồn dữ liệu khác (stockanalysis.com, Bloomberg, etc.)

3. **Giá trị chính xác hơn cho DCF**
   - DCF model dựa trên dòng tiền dài hạn
   - TTM phản ánh tốt hơn khả năng tạo dòng tiền của công ty

### So sánh với quý đơn:

**Ví dụ với FPT:**
- **Quý đơn (Q3 2025):** FCF = 3,514 tỷ VND
- **TTM (4 quý gần nhất):** FCF = 13,934 tỷ VND
- **Chênh lệch:** +297% (TTM cao hơn đáng kể)

## Cách sử dụng

### Mặc định (khuyến nghị):
```python
from src.core.fcfs import get_free_cash_flow

# Sử dụng TTM (mặc định)
fcf = get_free_cash_flow('FPT')
# → Tính TTM từ 4 quý gần nhất
```

### Chỉ lấy quý gần nhất (không khuyến nghị):
```python
# Chỉ lấy quý gần nhất
fcf_quarter = get_free_cash_flow('FPT', use_ttm=False)
# → Chỉ lấy dữ liệu từ quý gần nhất
```

### Sử dụng trực tiếp hàm TTM:
```python
from src.core.fcfs import get_free_cash_flow_ttm

# Tính TTM trực tiếp
fcf_ttm = get_free_cash_flow_ttm('FPT')
```

## Tác động đến DCF Valuation

### Với giá trị TTM:

**FPT:**
- FCF TTM: 13,934 tỷ VND
- DCF Fair Value sẽ **CAO HƠN** đáng kể so với khi dùng quý đơn
- Phản ánh đúng giá trị nội tại của công ty

### Ví dụ tính toán:

**Với quý đơn (cũ):**
- FCF = 3,514 tỷ VND
- DCF Fair Value ≈ 35,756 VND

**Với TTM (mới):**
- FCF = 13,934 tỷ VND
- DCF Fair Value ≈ **142,000 VND** (ước tính, cần tính lại với growth rate)

## Cache và Performance

- Kết quả TTM được cache tự động
- Cache key: `{ticker}_fcf_ttm`
- Tránh tính toán lại khi gọi nhiều lần

## Backward Compatibility

Code vẫn hỗ trợ lấy quý đơn bằng cách:
```python
get_free_cash_flow(ticker, use_ttm=False)
```

Tuy nhiên, **không khuyến nghị** cho phân tích DCF.

## Files đã cập nhật

1. **`src/core/fcfs.py`**
   - Cập nhật `get_free_cash_flow()` với `use_ttm=True` mặc định
   - Thêm comment đầy đủ cho `get_free_cash_flow_ttm()`
   - Thêm comment giải thích trong logic tính toán

2. **`src/core/dcf_calculator.py`**
   - Cập nhật comment trong `fetch_data_async()`
   - Ghi chú rõ ràng về việc sử dụng TTM

## Khuyến nghị

✅ **Nên:**
- Sử dụng TTM mặc định cho tất cả phân tích DCF
- Xem xét giá trị TTM khi đánh giá công ty
- So sánh với các nguồn dữ liệu khác (nếu có)

❌ **Không nên:**
- Sử dụng quý đơn cho phân tích DCF (trừ khi có lý do đặc biệt)
- So sánh trực tiếp giá trị quý đơn với TTM

## Tài liệu liên quan

- `docs/FCF_DISCREPANCY_EXPLANATION.md` - Giải thích về sự khác biệt giữa các nguồn dữ liệu
- `docs/STOCKANALYSIS_SCRAPER.md` - Thông tin về scraping từ stockanalysis.com

---

**Cập nhật:** 2025-12-28  
**Phiên bản:** 2.0 (TTM mặc định)

