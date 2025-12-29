# Vấn đề với cách tính Free Cash Flow (FCF)

## Vấn đề phát hiện

**Code hiện tại đang tính SAI Free Cash Flow!**

### Cách tính hiện tại (SAI):

Code trong `src/core/fcfs.py` chỉ lấy:
```python
fcf = latest_row['Net cash inflows/outflows from operating activities']
```

Đây chỉ là **Operating Cash Flow (OCF)**, không phải **Free Cash Flow (FCF)**!

### Công thức đúng của Free Cash Flow:

```
Free Cash Flow (FCF) = Operating Cash Flow - Capital Expenditures (CapEx)
```

Hoặc chi tiết hơn:

```
FCF = Operating Cash Flow 
    - Capital Expenditures (CapEx)
    - Changes in Working Capital (nếu chưa được tính trong OCF)
```

## Tác động đến kết quả DCF

### Ví dụ với FPT:

**Hiện tại (SAI):**
- "FCF" = Operating Cash Flow = 4,344,020,060,779 VND
- DCF Fair Value = 44,206 VND

**Nếu tính đúng:**
- Operating Cash Flow = 4,344,020,060,779 VND
- Capital Expenditures (CapEx) = ? (cần lấy từ cash flow statement)
- **FCF thực tế** = OCF - CapEx = **NHỎ HƠN** giá trị hiện tại
- **DCF Fair Value sẽ THẤP HƠN** 44,206 VND

## Tại sao điều này quan trọng?

1. **FCF thấp hơn** → DCF Fair Value thấp hơn
2. **Định giá sai** → Quyết định đầu tư sai
3. **So sánh không chính xác** giữa các công ty

## Cách sửa

Cần cập nhật hàm `get_free_cash_flow()` để:

1. Lấy Operating Cash Flow
2. Lấy Capital Expenditures từ cash flow statement
3. Tính FCF = OCF - CapEx

### Các cột cần tìm trong Cash Flow Statement:

- `Capital Expenditures`
- `Purchase of fixed assets`
- `Investments in fixed assets`
- `Cash flows from investing activities` (một phần)
- Hoặc các tên tương tự trong tiếng Việt

## Khuyến nghị

**Tùy chọn 1: Sửa code để tính đúng FCF**
- Cập nhật `get_free_cash_flow()` để trừ CapEx
- Cần kiểm tra cấu trúc dữ liệu từ vnstock

**Tùy chọn 2: Đổi tên cho đúng**
- Nếu không thể lấy CapEx, đổi tên hàm thành `get_operating_cash_flow()`
- Thêm cảnh báo trong documentation

**Tùy chọn 3: Sử dụng proxy**
- Nếu CapEx không có sẵn, có thể ước tính dựa trên:
  - Tỷ lệ CapEx/Revenue trung bình ngành
  - Hoặc CapEx/Operating Cash Flow trung bình

## Kết luận

**Free Cash Flow hiện tại KHÔNG được tính đúng** vì chỉ lấy Operating Cash Flow mà không trừ Capital Expenditures. Điều này làm cho DCF Fair Value bị **CAO HƠN** giá trị thực tế.

Cần sửa code để tính đúng FCF = OCF - CapEx.

