# Vnstock API Data Format Documentation

## Quan Trọng: Đơn Vị Dữ Liệu

### ⚠️ Cảnh Báo Quan Trọng

**Tên cột có thể gây hiểu lầm về đơn vị!**

Mặc dù tên cột có chứa `(Bn. VND)` (tỷ VND), nhưng **giá trị thực tế từ vnstock API là VND trực tiếp**, không phải tỷ VND.

## 1. Balance Sheet Columns

### 1.1. Common shares (Bn. VND)

**Tên cột:** `Common shares (Bn. VND)`  
**Đơn vị thực tế:** VND (không phải tỷ VND)  
**Cách tính shares:** `capital_value / par_value`

**Ví dụ FPT:**
```python
# Từ vnstock API
capital = 17035071210000  # VND (không phải tỷ VND!)
par_value = 10000  # VND per share
shares = capital / par_value  # = 1,703,507,121 shares ✅
```

**Lưu ý:** 
- ❌ KHÔNG nhân với 1,000,000
- ✅ Chỉ chia cho par_value (10,000)

### 1.2. Paid-in capital (Bn. VND)

**Tên cột:** `Paid-in capital (Bn. VND)`  
**Đơn vị thực tế:** VND (không phải tỷ VND)  
**Cách tính shares:** `capital_value / par_value`

**Ví dụ ACB:**
```python
# Từ vnstock API
capital = 51366566000000  # VND (không phải tỷ VND!)
par_value = 10000  # VND per share
shares = capital / par_value  # = 5,136,656,600 shares ✅
```

**Lưu ý:**
- ❌ KHÔNG nhân với 1,000,000
- ✅ Chỉ chia cho par_value (10,000)
- Logic giống hệt `Common shares`

### 1.3. Shares Outstanding

**Tên cột:** `Shares Outstanding`  
**Đơn vị thực tế:** Số cổ phiếu (đã là số cổ phiếu, không cần convert)  
**Cách sử dụng:** Dùng trực tiếp

**Ví dụ:**
```python
# Nếu có cột này, dùng trực tiếp
shares = latest_row['Shares Outstanding']  # Đã là số cổ phiếu
```

## 2. Par Value (Mệnh Giá)

### Giá Trị Mặc Định

**Par value chuẩn Việt Nam:** 10,000 VND per share

Hầu hết các công ty niêm yết tại Việt Nam sử dụng mệnh giá 10,000 VND/cổ phiếu.

### Công Thức Chuyển Đổi

```
Shares Outstanding = Capital (VND) / Par Value (VND per share)
```

**Ví dụ:**
- Capital: 51,366,566,000,000 VND
- Par value: 10,000 VND/share
- Shares: 51,366,566,000,000 / 10,000 = 5,136,656,600 shares

## 3. Các Cột Khác Trong Balance Sheet

### 3.1. Operating Cash Flow

**Đơn vị:** VND  
**Không có vấn đề về đơn vị**

### 3.2. Capital Expenditures

**Đơn vị:** VND  
**Lưu ý:** Thường là số âm trong báo cáo (dòng tiền ra)

### 3.3. Market Cap

**Đơn vị:** VND  
**Công thức:** `Market Cap = Shares Outstanding × Current Price`

## 4. Validation Rules

### 4.1. Shares Outstanding Validation

**Giá trị hợp lý:**
- Tối thiểu: > 0
- Tối đa hợp lý: < 50 tỷ shares (5e10)
- Cảnh báo: > 1 tỷ shares (1e9) - cần kiểm tra
- Lỗi: > 1 nghìn tỷ shares (1e12) - chắc chắn sai

**Ví dụ:**
```python
# Hợp lý
shares = 5136656600  # ACB: ~5.1 tỷ shares ✅

# Cần kiểm tra
shares = 50000000000  # 50 tỷ shares ⚠️

# Chắc chắn sai
shares = 5136656600000000  # 5.1 triệu tỷ shares ❌
```

### 4.2. Cross-Validation với Market Cap

**Công thức kiểm tra:**
```
|shares × price - market_cap| / market_cap < tolerance (15%)
```

**Ví dụ:**
```python
shares = 5136656600
price = 24000.0
market_cap = 123279758376000  # Từ vnstock

calculated_market_cap = shares * price  # = 123,279,758,400,000
difference = abs(calculated_market_cap - market_cap) / market_cap
# Should be < 15%
```

## 5. Code Examples

### 5.1. Tính Shares từ Common shares

```python
if 'Common shares (Bn. VND)' in latest_row.index:
    capital = latest_row['Common shares (Bn. VND)']  # VND
    par_value = 10000
    shares = capital / par_value  # ✅ Đúng
```

### 5.2. Tính Shares từ Paid-in capital

```python
if 'Paid-in capital (Bn. VND)' in latest_row.index:
    capital = latest_row['Paid-in capital (Bn. VND)']  # VND
    par_value = 10000
    shares = capital / par_value  # ✅ Đúng
    # ❌ SAI: shares = capital * 1000000 / par_value
```

### 5.3. Validation

```python
from src.utils.shares_validator import validate_shares, validate_and_cross_check

# Basic validation
validate_shares(shares, ticker, raise_error=True)

# Comprehensive validation with cross-check
validate_and_cross_check(
    shares=shares,
    ticker=ticker,
    price=price,
    market_cap=market_cap,
    raise_error=True
)
```

## 6. Common Mistakes

### ❌ Mistake 1: Nhân với 1,000,000

```python
# SAI
shares = capital * 1000000 / par_value  # ❌
```

**Lý do:** Nghĩ rằng `(Bn. VND)` nghĩa là tỷ VND, nhưng thực tế vnstock đã trả về VND.

### ❌ Mistake 2: Xử lý khác nhau giữa Common shares và Paid-in capital

```python
# SAI - Logic không nhất quán
if 'Common shares':
    shares = capital / par_value  # ✅
elif 'Paid-in capital':
    shares = capital * 1000000 / par_value  # ❌ Khác nhau!
```

**Đúng:** Cả hai đều dùng cùng logic: `capital / par_value`

### ❌ Mistake 3: Không validate

```python
# SAI - Không kiểm tra giá trị hợp lý
shares = capital / par_value
# Lưu vào database mà không validate
```

**Đúng:** Luôn validate trước khi lưu

## 7. Testing

### Unit Tests

Xem `tests/ut/test_shares_validator.py` cho các test cases:
- Validation với giá trị hợp lý
- Validation với giá trị sai
- Cross-validation với market cap
- Test logic tính toán từ capital values

### Manual Testing

```python
# Test với ACB
from src.core.fcfs import get_shares_outstanding
shares = get_shares_outstanding('ACB')
print(f"ACB shares: {shares:,.0f}")  # Should be ~5.1 billion

# Test với FPT
shares = get_shares_outstanding('FPT')
print(f"FPT shares: {shares:,.0f}")  # Should be ~1.7 billion
```

## 8. References

- [Root Cause Analysis](ROOT_CAUSE_ANALYSIS.md)
- [Shares Calculation Fix](historical/SHARES_CALCULATION_FIX.md)
- [Shares Validator Tests](../tests/ut/test_shares_validator.py)

---

**Version:** 1.0  
**Last Updated:** 2025-12-30  
**Status:** Active Documentation

