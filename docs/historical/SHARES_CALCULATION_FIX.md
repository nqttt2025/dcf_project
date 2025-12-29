# Sửa Lỗi Tính Toán Shares Outstanding

## Vấn Đề Phát Hiện

### Mô Tả
Một số mã cổ phiếu (đặc biệt là ngân hàng như VCB, ACB, MBB, HDB) có shares outstanding **quá lớn**, không hợp lý:
- VCB: 83,556 tỷ cổ phiếu (sai)
- ACB: 51,366 tỷ cổ phiếu (sai)
- MBB: 80,549 tỷ cổ phiếu (sai)

Trong khi một số mã khác có giá trị hợp lý:
- FPT: 1.7 tỷ cổ phiếu (đúng)
- VNM: 2.1 tỷ cổ phiếu (đúng)

### Nguyên Nhân

#### 1. Format Dữ Liệu Từ vnstock

**Dữ liệu từ vnstock:**
- Cột `Common shares (Bn. VND)`: Giá trị là **VND** (không phải tỷ VND), mặc dù tên có "(Bn. VND)"
- Cột `Paid-in capital (Bn. VND)`: Cũng là **VND** (không phải tỷ VND)

**Ví dụ:**
- FPT: `Common shares (Bn. VND)` = 17,035,071,210,000 VND
  - Thực tế: 17,035.07 tỷ VND
  - Chia cho par_value (10,000) → 1.7 tỷ cổ phiếu ✅

- VCB: `Paid-in capital (Bn. VND)` = 83,556,751,000,000 VND
  - Thực tế: 83,556.75 tỷ VND
  - **Code cũ**: Dùng trực tiếp → 83,556 tỷ cổ phiếu ❌
  - **Code mới**: Chia cho par_value (10,000) → 8.36 tỷ cổ phiếu ✅

#### 2. Logic Code Cũ

**Code cũ có 2 nhánh:**

1. **Nhánh 1**: Nếu có `Common shares (Bn. VND)`
   ```python
   shares_count = float(shares_capital) / par_value  # ✅ ĐÚNG
   ```

2. **Nhánh 2**: Nếu có `Paid-in capital (Bn. VND)`
   ```python
   shares_value = float(shares)  # ❌ SAI - Không chia cho par_value!
   ```

**Vấn đề**: Code chỉ chia cho par_value khi có `Common shares`, nhưng không chia khi có `Paid-in capital`.

#### 3. Sự Khác Biệt Giữa Các Mã

- **FPT, VNM**: Có cột `Common shares (Bn. VND)` → Code chia cho par_value → Đúng ✅
- **VCB, ACB, MBB, HDB**: Chỉ có `Paid-in capital (Bn. VND)` → Code dùng trực tiếp → Sai ❌

## Giải Pháp

### Sửa Logic Tính Toán

**Code mới:**

```python
# Check for capital columns that need conversion
alt_names_capital = [
    'Paid-in capital (Bn. VND)',
]

for col_name in alt_names_capital:
    if col_name in latest_row.index:
        capital_value = latest_row[col_name]
        if capital_valid and capital_value > 0:
            # Convert from capital (VND) to number of shares
            par_value = 10000
            shares_count = float(capital_value) / par_value  # ✅ Chia cho par_value
            return shares_count

# Check for direct shares outstanding (already in number of shares)
alt_names_shares = [
    'Shares Outstanding'
]

for col_name in alt_names_shares:
    if col_name in latest_row.index:
        shares = latest_row[col_name]
        if shares_valid and shares > 0:
            shares_value = float(shares)  # ✅ Dùng trực tiếp (đã là số cổ phiếu)
            return shares_value
```

### Thay Đổi Chính

1. **Tách riêng** các cột cần convert (capital) và các cột đã là số cổ phiếu
2. **Chia cho par_value** khi dùng `Paid-in capital (Bn. VND)`
3. **Dùng trực tiếp** khi có `Shares Outstanding` (nếu có)

## Kết Quả Sau Khi Sửa

### Trước Khi Sửa:
- VCB: 83,556 tỷ cổ phiếu ❌
- ACB: 51,366 tỷ cổ phiếu ❌
- MBB: 80,549 tỷ cổ phiếu ❌

### Sau Khi Sửa:
- VCB: ~8.36 tỷ cổ phiếu ✅
- ACB: ~5.14 tỷ cổ phiếu ✅
- MBB: ~8.05 tỷ cổ phiếu ✅

## Cách Kiểm Tra

### 1. Xóa Cache và Test Lại

```bash
# Xóa cache của các mã có vấn đề
rm data/cache/vcb_cache.json
rm data/cache/acb_cache.json
rm data/cache/mbb_cache.json

# Test lại
python3 << 'EOF'
from src.core.fcfs import get_shares_outstanding
shares = get_shares_outstanding('VCB')
print(f"VCB shares: {shares:,.0f}")
EOF
```

### 2. Chạy Lại DCF Analysis

```bash
# Chạy lại DCF để cập nhật shares
make dcf TICKER=VCB
make dcf TICKER=ACB
make dcf TICKER=MBB

# Kiểm tra kết quả
cat data/results/vcb_result.json | jq '.shares'
```

### 3. So Sánh Với Dữ Liệu Thực Tế

**Nguồn tham khảo:**
- Website công ty (báo cáo tài chính)
- HOSE/HNX (sàn giao dịch)
- Cafef, Vietstock

**Ví dụ VCB:**
- Theo báo cáo tài chính: ~8.3-8.4 tỷ cổ phiếu
- Code sau khi sửa: ~8.36 tỷ cổ phiếu ✅

## Lưu Ý Quan Trọng

### 1. Đơn Vị Dữ Liệu

- **vnstock trả về**: VND (không phải tỷ VND), mặc dù tên cột có "(Bn. VND)"
- **Cần chia**: Cho par_value (10,000) để có số cổ phiếu
- **Ngoại lệ**: Nếu có cột `Shares Outstanding` trực tiếp, dùng luôn

### 2. Par Value

- **Mặc định**: 10,000 VND/cổ phiếu (chuẩn Việt Nam)
- **Ngoại lệ**: Một số mã có par value khác (cần điều chỉnh riêng)

### 3. Cache

- **Sau khi sửa code**: Cần xóa cache để fetch lại dữ liệu mới
- **Cache cũ**: Có thể chứa giá trị sai

## Tóm Tắt

✅ **Đã sửa**: Logic tính toán để chia `Paid-in capital` cho par_value  
✅ **Kết quả**: Shares outstanding của các mã ngân hàng đã hợp lý  
✅ **Cần làm**: Xóa cache và chạy lại DCF analysis cho các mã có vấn đề  

---

**Version:** 1.0  
**Date:** 2025-12-29  
**Status:** Fixed

