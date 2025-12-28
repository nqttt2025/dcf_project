# Hướng dẫn sử dụng Script tính PE (Price-to-Earnings)

## Mục đích

Script `calculate_pe.py` giúp bạn:
- Tính PE hiện tại của mã cổ phiếu
- Đề xuất Base PE phù hợp dựa trên ngành nghề
- Phân tích PE cho tất cả các mã VN30

## Cách sử dụng

### 1. Sử dụng trực tiếp với Python

#### Tính PE cho một mã cụ thể:
```bash
python3 scripts/calculate_pe.py VNM
```

#### Tính PE với đề xuất theo ngành:
```bash
python3 scripts/calculate_pe.py VNM consumer
python3 scripts/calculate_pe.py VCB banking
python3 scripts/calculate_pe.py FPT technology
```

#### Phân tích tất cả mã VN30:
```bash
python3 scripts/calculate_pe.py
```

### 2. Sử dụng qua Makefile (Khuyến nghị)

#### Tính PE cho một mã:
```bash
make pe TICKER=VNM
make pe TICKER=VCB INDUSTRY=banking
```

#### Phân tích tất cả VN30:
```bash
make pe-all
```

#### Xem danh sách ngành:
```bash
make pe-help
```

## Các ngành được hỗ trợ

- `banking` - Ngân hàng
- `real_estate` - Bất động sản
- `technology` - Công nghệ
- `consumer` - Tiêu dùng
- `energy` - Năng lượng
- `industrial` - Công nghiệp
- `aviation` - Hàng không

## Ví dụ kết quả

### Khi chạy cho một mã:
```
VNM:
  PE hiện tại: 50.87
  Base PE đề xuất: 8.75
```

### Khi phân tích tất cả VN30:
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

## Cách cập nhật Base PE vào config file

Sau khi có Base PE đề xuất, bạn có thể cập nhật vào file config:

### Ví dụ: Cập nhật cho VCB

1. Chạy script để lấy Base PE đề xuất:
```bash
make pe TICKER=VCB INDUSTRY=banking
```

2. Mở file config:
```bash
vi config/VCB.cfg
```

3. Cập nhật giá trị:
```ini
[graham]
base_pe = 7.5          # Thay đổi từ 8.5 thành 7.5
growth_multiplier = 2
```

## Lưu ý

- Script cần kết nối internet để lấy dữ liệu từ vnstock
- PE hiện tại thay đổi theo thời gian thực
- Base PE đề xuất chỉ là tham khảo, bạn nên điều chỉnh dựa trên:
  - Đặc thù của công ty
  - Điều kiện thị trường
  - Phân tích cơ bản

## Xử lý lỗi

Nếu gặp lỗi:
1. Kiểm tra kết nối internet
2. Kiểm tra mã cổ phiếu có đúng không
3. Kiểm tra vnstock đã được cài đặt: `pip install vnstock`
4. Xem log chi tiết trong file log

