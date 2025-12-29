# Phân tích chuyên sâu DCF Valuation

## Tổng quan

Module phân tích chuyên sâu cung cấp các thông tin chi tiết về định giá cổ phiếu, bao gồm:
- Tăng trưởng FCF theo từng năm
- Dự báo giá cổ phiếu theo từng năm
- Các chỉ số định giá (P/E, P/FCF, FCF Yield, etc.)
- Phân tích Upside/Downside potential

## Các thành phần phân tích

### 1. Yearly FCF Growth Forecast

**Mô tả:** Hiển thị tăng trưởng Free Cash Flow theo từng năm trong giai đoạn forecast.

**Bao gồm:**
- FCF của mỗi năm
- Tỷ lệ tăng trưởng năm-over-year (%)
- Tỷ lệ tăng trưởng tích lũy từ năm đầu (%)

**Ví dụ:**
```
Year   FCF (VND)            Growth %     Cumulative Growth % 
--------------------------------------------------------------------------------
Year 1    13,933,764,607,232        0.00%                0.00%
Year 2    15,421,662,643,240       10.68%               10.68%
Year 3    17,068,443,840,257       10.68%               22.50%
Year 4    18,891,074,319,779       10.68%               35.58%
```

### 2. Yearly Price Forecast

**Mô tả:** Dự báo giá cổ phiếu sau mỗi năm dựa trên DCF model.

**Cách tính:**
- Tính giá trị công ty tại mỗi năm (tổng PV của các FCF còn lại)
- Chia cho số cổ phiếu đang lưu hành
- So sánh với giá hiện tại để tính % thay đổi

**Ví dụ:**
```
Year   FCF (VND)            Company Value (VND)       Price/Share (VND)   
--------------------------------------------------------------------------------
Year 1    13,933,764,607,232      241,547,827,197,827          141,794.43 (+53.29%)
Year 2    15,421,662,643,240      251,768,845,310,378          147,794.42 (+59.78%)
Year 3    17,068,443,840,257      261,524,067,198,176          153,520.97 (+65.97%)
```

### 3. Valuation Metrics

**Các chỉ số được tính:**

#### P/E Ratio (Price-to-Earnings)
```
P/E = Current Price / EPS
```
- **Ý nghĩa:** Số năm cần để thu hồi vốn đầu tư dựa trên lợi nhuận
- **Giá trị tốt:** Thường < 20-25 cho thị trường phát triển

#### P/FCF Ratio (Price-to-Free Cash Flow)
```
P/FCF = Current Price / (FCF / Shares)
```
- **Ý nghĩa:** Số năm cần để thu hồi vốn đầu tư dựa trên dòng tiền tự do
- **Giá trị tốt:** Thường < 15-20

#### FCF Yield
```
FCF Yield = (FCF / Market Cap) × 100%
```
- **Ý nghĩa:** Tỷ suất sinh lời từ dòng tiền tự do
- **Giá trị tốt:** Thường > 5-8%

#### Earnings Yield
```
Earnings Yield = (EPS / Price) × 100%
```
- **Ý nghĩa:** Tỷ suất sinh lời từ lợi nhuận
- **Giá trị tốt:** Thường > 4-6%

### 4. Upside/Downside Analysis

**Mô tả:** Phân tích tiềm năng tăng/giảm giá so với giá trị công bằng.

**Bao gồm:**
- DCF Upside/Downside: So sánh giá hiện tại với DCF Fair Value
- Graham Upside/Downside: So sánh giá hiện tại với Graham Fair Value
- Average Upside/Downside: So sánh giá hiện tại với Average Fair Value

**Công thức:**
```
Upside/Downside % = ((Fair Value - Current Price) / Current Price) × 100%
```

**Giải thích:**
- **Upside (+):** Giá thị trường thấp hơn giá trị công bằng → Có tiềm năng tăng giá
- **Downside (-):** Giá thị trường cao hơn giá trị công bằng → Có thể bị định giá quá cao

## Cấu trúc file result

File result được lưu ở `data/results/{ticker}_result.text` với format:

```
================================================================================
DCF VALUATION ANALYSIS - {TICKER}
================================================================================

INPUT PARAMETERS
--------------------------------------------------------------------------------
Market Price: ...
EPS: ...
Free Cash Flow (TTM): ...
...

================================================================================
VALUATION RESULTS
================================================================================
DCF Fair Value: ...
Graham Fair Value: ...
Average Fair Value: ...

UPSIDE/DOWNSIDE ANALYSIS
--------------------------------------------------------------------------------
DCF Upside/Downside: ...
Graham Upside/Downside: ...
Average Upside/Downside: ...

VALUATION METRICS
--------------------------------------------------------------------------------
P/E Ratio: ...
P/FCF Ratio: ...
FCF Yield: ...
Earnings Yield: ...

================================================================================
YEARLY FCF GROWTH FORECAST
================================================================================
...

================================================================================
YEARLY PRICE FORECAST (Based on DCF Model)
================================================================================
...

================================================================================
GRAHAM VALUATION DETAILS
================================================================================
...
```

## Sử dụng

Phân tích chuyên sâu được tự động tạo khi chạy DCF analysis:

```bash
make dcf TICKER=FPT
```

Kết quả sẽ được lưu trong:
- `data/results/fpt_result.text` - File text với phân tích chi tiết
- `data/results/fpt_result.json` - File JSON với đầy đủ dữ liệu

## Lưu ý

1. **Yearly Price Forecast** là dự báo dựa trên DCF model, không phải dự đoán chính xác
2. **Growth rates** được giả định là không đổi trong suốt giai đoạn forecast
3. **Terminal value** được tính ở cuối giai đoạn forecast với perpetual growth rate
4. Các chỉ số định giá chỉ mang tính tham khảo, cần so sánh với industry average

## Tài liệu liên quan

- `docs/DCF_CALCULATION_EXPLAINED.md` - Giải thích về DCF model
- `docs/TTM_UPDATE.md` - Thông tin về TTM calculation
- `docs/GRAHAM_VALUATION.md` - Giải thích về Graham valuation

---

**Cập nhật:** 2025-12-28  
**Phiên bản:** 2.0 (Advanced Analysis)

