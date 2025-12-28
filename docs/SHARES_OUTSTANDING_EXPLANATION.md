# Giải Thích Về Số Lượng Cổ Phiếu Đang Lưu Hành (Shares Outstanding)

## Tổng Quan

Hệ thống hiển thị **30 mã cổ phiếu** trong rổ VN30 trên web service tại `http://localhost:8080/`. Đây là số lượng **mã cổ phiếu**, không phải số lượng cổ phiếu đang lưu hành.

## Phân Biệt

### 1. Số Lượng Mã Cổ Phiếu (30 mã)
- **Định nghĩa**: Số lượng công ty trong rổ VN30
- **Hiển thị trên web**: 30 mã cổ phiếu
- **Nguồn**: Config files trong `config/` directory
- **Danh sách**: ACB, BID, CTG, FPT, GAS, GVR, HDB, HPG, KDH, MBB, MSN, MWG, NVL, PDR, PLX, PNJ, REE, SAB, SSB, SSI, STB, TPB, VCB, VHM, VIB, VIC, VJC, VNM, VPB, VRE

### 2. Số Lượng Cổ Phiếu Đang Lưu Hành (Shares Outstanding)
- **Định nghĩa**: Tổng số cổ phiếu của một công ty đang được lưu hành trên thị trường
- **Đơn vị**: Cổ phiếu (shares)
- **Ví dụ**: FPT có khoảng 1.7 tỷ cổ phiếu đang lưu hành

## Cách Tính Shares Outstanding

### Nguồn Dữ Liệu
- **Library**: `vnstock`
- **Source**: VCI (Vietnam)
- **Dữ liệu**: Bảng cân đối kế toán (Balance Sheet)

### Công Thức
```python
Shares Outstanding = Common shares (Bn. VND) / Par value (10,000 VND)
```

### Ví Dụ: FPT
1. **Lấy từ Balance Sheet**: "Common shares (Bn. VND)" = 17,035.07 tỷ VND
2. **Par value**: 10,000 VND/cổ phiếu (mệnh giá chuẩn)
3. **Tính toán**: 
   ```
   Shares = 17,035.07 tỷ VND / 10,000 VND
         = 1,703,507,000 cổ phiếu
         ≈ 1.7 tỷ cổ phiếu
   ```

## Tại Sao Có Thể Có Sự Khác Biệt?

### 1. Dữ Liệu Không Cập Nhật
- **Nguyên nhân**: Dữ liệu từ `vnstock` có thể không phản ánh các thay đổi gần đây
- **Giải pháp**: 
  - Xóa cache: `rm data/cache/{ticker}_cache.json`
  - Chạy lại DCF: `make dcf TICKER={ticker}`

### 2. Par Value Khác 10,000 VND
- **Nguyên nhân**: Một số công ty có mệnh giá khác (ví dụ: 1,000 VND, 100,000 VND)
- **Giải pháp**: Cần điều chỉnh `par_value` trong code `src/core/fcfs.py`

### 3. Thay Đổi Vốn Điều Lệ
- **Nguyên nhân**: Công ty có thể:
  - Phát hành thêm cổ phiếu
  - Mua lại cổ phiếu
  - Chia tách/gộp cổ phiếu
- **Giải pháp**: Cập nhật dữ liệu từ nguồn chính thức

### 4. Dữ Liệu Cache Cũ
- **Nguyên nhân**: Hệ thống cache dữ liệu để tránh gọi API nhiều lần
- **Giải pháp**: Xóa cache và fetch lại dữ liệu mới

## Kiểm Tra Shares Outstanding

### Trên Web Service
```bash
# Xem danh sách cổ phiếu
curl http://localhost:8080/api/stocks | jq '.stocks[] | {ticker, shares_outstanding}'
```

### Trong Result Files
```bash
# Xem shares outstanding của một mã
cat data/results/fpt_result.json | jq '.shares'
```

### Trong Code
```python
from src.core.fcfs import get_shares_outstanding

shares = get_shares_outstanding('FPT')
print(f"FPT shares outstanding: {shares:,.0f}")
```

## So Sánh Với Dữ Liệu Thực Tế

### Nguồn Dữ Liệu Tham Khảo
1. **Website công ty**: Báo cáo tài chính chính thức
2. **HOSE/HNX**: Sàn giao dịch chứng khoán
3. **Các công ty chứng khoán**: VCI, SSI, VNDirect, etc.
4. **Cafef, Vietstock**: Cổng thông tin tài chính

### Cách Kiểm Tra
```bash
# 1. Xem shares trong result file
python3 << 'EOF'
import json
from pathlib import Path

result_file = Path('data/results/fpt_result.json')
if result_file.exists():
    with open(result_file, 'r') as f:
        data = json.load(f)
    print(f"FPT Shares Outstanding: {data.get('shares', 'N/A'):,.0f}")
EOF

# 2. Fetch lại từ API
python3 << 'EOF'
from src.core.fcfs import get_shares_outstanding
shares = get_shares_outstanding('FPT')
print(f"FPT Shares Outstanding (fresh): {shares:,.0f}")
EOF
```

## Lưu Ý Quan Trọng

### 1. Shares Outstanding vs Free Float
- **Shares Outstanding**: Tổng số cổ phiếu đang lưu hành
- **Free Float**: Số cổ phiếu có thể giao dịch tự do (loại trừ cổ đông lớn, cổ phiếu quỹ)
- **VN30**: Dựa trên Free Float, không phải Shares Outstanding

### 2. Đơn Vị Tính
- **Trong code**: Shares (số cổ phiếu)
- **Trên web**: Có thể hiển thị dạng triệu/tỷ cổ phiếu
- **Trong báo cáo**: Thường dùng tỷ VND (charter capital)

### 3. Cập Nhật Dữ Liệu
- **Tần suất**: Sau mỗi quý (khi công ty công bố báo cáo tài chính)
- **Tự động**: Hệ thống cache dữ liệu, cần xóa cache để cập nhật
- **Thủ công**: Chạy lại DCF analysis để fetch dữ liệu mới

## Troubleshooting

### Vấn Đề: Shares Outstanding Không Đúng

**Kiểm tra:**
```bash
# 1. Xem cache
cat data/cache/fpt_cache.json | jq '.shares'

# 2. Xóa cache và fetch lại
rm data/cache/fpt_cache.json
make dcf TICKER=FPT

# 3. Kiểm tra log
tail -50 logs/app/dcf_fpt.log | grep -i share
```

### Vấn Đề: Par Value Khác

**Giải pháp**: Cập nhật `par_value` trong `src/core/fcfs.py`:
```python
# Thay đổi từ
par_value = 10000

# Thành giá trị đúng cho từng mã
par_value = get_par_value(ticker)  # Cần implement function này
```

## Kết Luận

- **Số lượng mã cổ phiếu**: 30 mã (đúng với VN30)
- **Shares Outstanding**: Khác nhau cho mỗi mã, được tính từ Balance Sheet
- **Sự khác biệt**: Có thể do dữ liệu cache, par value, hoặc thay đổi vốn điều lệ
- **Giải pháp**: Xóa cache và fetch lại dữ liệu mới từ `vnstock`

---

**Version:** 1.0  
**Last Updated:** 2025-12-29  
**Maintainer:** DCF Project Team

