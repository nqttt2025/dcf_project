# Hướng dẫn sử dụng Script tính PE và Base PE

## Tổng quan

Script `calculate_pe.py` giúp bạn tính toán PE (Price-to-Earnings) và đề xuất Base PE phù hợp cho từng mã cổ phiếu trong rổ VN30.

## Cách sử dụng qua Makefile (Khuyến nghị)

### 1. Tính PE cho một mã cổ phiếu

```bash
# Tính PE đơn giản
make pe TICKER=VNM

# Tính PE với đề xuất theo ngành
make pe TICKER=VNM INDUSTRY=consumer
make pe TICKER=VCB INDUSTRY=banking
make pe TICKER=FPT INDUSTRY=technology
```

**Kết quả:**
```
Calculating PE for VNM...
VNM: Price=61,500, EPS=1,209.00, PE=50.87
VNM (consumer): Đề xuất Base PE = 8.75

VNM:
  PE hiện tại: 50.87
  Base PE đề xuất: 8.75
```

### 2. Phân tích tất cả mã VN30

```bash
make pe-all
```

**Kết quả:** Hiển thị bảng phân tích PE cho tất cả 30 mã VN30, được nhóm theo ngành.

### 3. Xem hướng dẫn

```bash
make pe-help
```

## Các ngành được hỗ trợ

| Ngành | Tên trong script | Base PE đề xuất |
|-------|-----------------|-----------------|
| Ngân hàng | `banking` | 7.0 - 8.0 |
| Bất động sản | `real_estate` | 8.0 - 9.0 |
| Công nghệ | `technology` | 9.0 - 10.0 |
| Tiêu dùng | `consumer` | 8.5 - 9.0 |
| Năng lượng | `energy` | 7.5 - 8.5 |
| Công nghiệp | `industrial` | 8.0 - 9.0 |
| Hàng không | `aviation` | 8.5 - 9.5 |

## Ví dụ sử dụng thực tế

### Ví dụ 1: Tính PE cho VNM (Vinamilk)

```bash
make pe TICKER=VNM INDUSTRY=consumer
```

**Kết quả:**
- PE hiện tại: 50.87
- Base PE đề xuất: 8.75 (cho ngành tiêu dùng)

**Hành động tiếp theo:**
Cập nhật `config/VNM.cfg`:
```ini
[graham]
base_pe = 8.75          # Thay đổi từ 8.5
growth_multiplier = 2
```

### Ví dụ 2: Tính PE cho VCB (Vietcombank)

```bash
make pe TICKER=VCB INDUSTRY=banking
```

**Kết quả:**
- PE hiện tại: ~12-15 (tùy thời điểm)
- Base PE đề xuất: 7.5 (cho ngành ngân hàng)

**Hành động tiếp theo:**
Cập nhật `config/VCB.cfg`:
```ini
[graham]
base_pe = 7.5           # Thay đổi từ 8.5
growth_multiplier = 2
```

### Ví dụ 3: Phân tích toàn bộ VN30

```bash
make pe-all
```

Sẽ hiển thị bảng tổng hợp:
```
================================================================================
PHÂN TÍCH PE CHO CÁC MÃ VN30
================================================================================

--- BANKING ---
VCB   | PE hiện tại:  12.45 | Base PE đề xuất: 7.50
BID   | PE hiện tại:  10.23 | Base PE đề xuất: 7.50
...

--- CONSUMER ---
VNM   | PE hiện tại:  50.87 | Base PE đề xuất: 8.75
MSN   | PE hiện tại:  15.23 | Base PE đề xuất: 8.75
...

================================================================================
TÓM TẮT
================================================================================
Mã     Ngành           PE hiện tại  Base PE đề xuất
--------------------------------------------------------------------------------
ACB    banking         15.23        7.50
BID    banking         10.23        7.50
...
```

## Sử dụng trực tiếp với Python (Nếu không dùng Makefile)

### Tính PE cho một mã:

```bash
python3 scripts/calculate_pe.py VNM
python3 scripts/calculate_pe.py VCB banking
```

### Phân tích tất cả VN30:

```bash
python3 scripts/calculate_pe.py
```

## Quy trình đề xuất: Cập nhật Base PE cho các mã VN30

### Bước 1: Phân tích tất cả mã

```bash
make pe-all > pe_analysis.txt
```

### Bước 2: Xem kết quả và xác định Base PE cần điều chỉnh

```bash
cat pe_analysis.txt
```

### Bước 3: Cập nhật từng file config

Ví dụ cho VCB:
```bash
# Xem Base PE đề xuất
make pe TICKER=VCB INDUSTRY=banking

# Cập nhật config
vi config/VCB.cfg
# Thay đổi base_pe = 7.5
```

### Bước 4: (Tùy chọn) Tạo script tự động cập nhật

Bạn có thể tạo script để tự động cập nhật Base PE dựa trên kết quả phân tích.

## Lưu ý quan trọng

⚠️ **PE thay đổi theo thời gian thực**
- PE hiện tại phụ thuộc vào giá cổ phiếu và EPS hiện tại
- Nên chạy script định kỳ để cập nhật

⚠️ **Base PE đề xuất chỉ là tham khảo**
- Điều chỉnh dựa trên:
  - Đặc thù của công ty
  - Điều kiện thị trường
  - Phân tích cơ bản

⚠️ **Cần kết nối internet**
- Script sử dụng vnstock để lấy dữ liệu
- Đảm bảo đã cài đặt: `pip install vnstock`

## Xử lý lỗi

### Lỗi: "No module named 'vnstock'"
```bash
pip install vnstock
```

### Lỗi: "Cannot fetch data"
- Kiểm tra kết nối internet
- Kiểm tra mã cổ phiếu có đúng không
- Thử lại sau vài phút

### Lỗi: "EPS <= 0"
- Một số công ty có thể có EPS âm hoặc bằng 0
- Không thể tính PE cho các công ty này
- Bỏ qua hoặc sử dụng phương pháp định giá khác

## Tích hợp vào workflow

### 1. Trước khi chạy DCF analysis:

```bash
# Phân tích PE cho tất cả mã
make pe-all

# Xem kết quả và điều chỉnh Base PE trong config files
# Sau đó chạy DCF analysis
python3 run_all_dcf_main.py
```

### 2. Định kỳ cập nhật (hàng tháng):

```bash
# Chạy phân tích PE
make pe-all > pe_analysis_$(date +%Y%m%d).txt

# Xem và so sánh với lần trước
diff pe_analysis_previous.txt pe_analysis_$(date +%Y%m%d).txt
```

## Tóm tắt các lệnh

| Lệnh | Mô tả |
|------|-------|
| `make pe TICKER=VNM` | Tính PE cho VNM |
| `make pe TICKER=VCB INDUSTRY=banking` | Tính PE với đề xuất ngành |
| `make pe-all` | Phân tích tất cả VN30 |
| `make pe-help` | Xem hướng dẫn |
| `make help` | Xem tất cả lệnh Makefile |

---

**Tóm lại**: Sử dụng `make pe` để tính PE và đề xuất Base PE, sau đó cập nhật vào các file config để có kết quả định giá chính xác hơn.

