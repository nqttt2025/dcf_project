# Configuration Files

## Tổng quan

Thư mục này chứa các file cấu hình cho từng mã cổ phiếu trong rổ VN30. Mỗi file `.cfg` định nghĩa các tham số cho phân tích DCF và Graham valuation.

## Cấu trúc file config

Mỗi file config bao gồm các section sau:

### [dcf]
Tham số cho mô hình DCF (Discounted Cash Flow):
- `yr`: Số năm dự báo (thường 5-7 năm)
- `dr`: Discount Rate (%) - Tỷ lệ chiết khấu, phản ánh rủi ro của cổ phiếu
- `pr`: Perpetual Growth Rate (%) - Tỷ lệ tăng trưởng vĩnh viễn sau giai đoạn dự báo

### [graham]
Tham số cho phương pháp định giá Graham:
- `base_pe`: Hệ số PE cơ bản (mặc định 8.5 theo Benjamin Graham)
- `growth_multiplier`: Hệ số nhân với tốc độ tăng trưởng (mặc định 2)

### [ticker]
- `ticker`: Mã cổ phiếu cần phân tích

### [data_source]
Thông tin về nguồn dữ liệu:
- `source`: Nguồn dữ liệu (VCI - mặc định)
- `note`: Ghi chú về nguồn dữ liệu

### [fcf_calculation]
**Thông tin về cách tính Free Cash Flow:**

- `data_source`: Nguồn dữ liệu (vnstock)
- `method`: Phương pháp tính (TTM - Trailing Twelve Months)
- `description`: Mô tả cách tính
- `formula`: Công thức tính toán
- `note`: Ghi chú về lợi ích của phương pháp

## Free Cash Flow Calculation

### Phương pháp: TTM (Trailing Twelve Months)

**Free Cash Flow được tính bằng cách cộng dồn 4 quý gần nhất từ vnstock.**

**Công thức:**
```
FCF TTM = Sum(Operating Cash Flow - Capital Expenditures) của 4 quý gần nhất
```

### Tại sao sử dụng TTM?

1. **Phản ánh tốt hơn tình hình hiện tại**
   - TTM bao gồm 12 tháng gần nhất, không chỉ một quý
   - Tránh biến động theo mùa của từng quý riêng lẻ

2. **Chuẩn trong phân tích tài chính**
   - Được sử dụng rộng rãi trong định giá DCF
   - Nhất quán với các nguồn dữ liệu khác (stockanalysis.com, Bloomberg, etc.)

3. **Giá trị chính xác hơn cho DCF**
   - DCF model dựa trên dòng tiền dài hạn
   - TTM phản ánh tốt hơn khả năng tạo dòng tiền của công ty

### Nguồn dữ liệu

- **Library:** vnstock
- **Source:** VCI (Vietnam)
- **Dữ liệu:** Báo cáo tài chính chính thức từ công ty

## Danh sách các mã cổ phiếu

Tổng cộng có **30 mã cổ phiếu** trong rổ VN30:

- ACB, BID, CTG, FPT, GAS, GVR, HDB, HPG, KDH, MBB
- MSN, MWG, NVL, PDR, PLX, PNJ, REE, SAB, SSB, SSI
- STB, TPB, VCB, VHM, VIB, VIC, VJC, VNM, VPB, VRE

## Sử dụng

Để chạy phân tích DCF cho một mã cổ phiếu:

```bash
make dcf TICKER=FPT
```

Hoặc:

```bash
python3 run_dcf.py FPT.cfg
```

## Cập nhật

- **Cập nhật cuối:** 2025-12-28
- **Phiên bản:** 2.0 (TTM mặc định)
- **Thay đổi:** Tất cả config files đã được cập nhật với thông tin về TTM calculation
