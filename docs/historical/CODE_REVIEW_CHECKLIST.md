# Code Review Checklist - Shares Outstanding

## Mục Đích

Checklist này đảm bảo code liên quan đến shares outstanding được review kỹ lưỡng và tránh các lỗi về đơn vị dữ liệu.

## Checklist Trước Khi Commit

### 1. Logic Tính Toán

- [ ] **Logic nhất quán:** Cả `Common shares` và `Paid-in capital` đều dùng cùng logic
- [ ] **Không nhân với 1,000,000:** Chỉ chia cho par_value, không nhân với 1 triệu
- [ ] **Par value đúng:** Sử dụng 10,000 VND (chuẩn Việt Nam)
- [ ] **Xử lý edge cases:** Có xử lý khi giá trị None, 0, hoặc âm

### 2. Validation

- [ ] **Validation cơ bản:** Kiểm tra shares > 0 và < 1e12
- [ ] **Cross-validation:** So sánh với market cap nếu có
- [ ] **Error handling:** Raise error thay vì chỉ warning khi giá trị sai
- [ ] **Logging:** Log đầy đủ thông tin để debug

### 3. Testing

- [ ] **Unit tests:** Có test cases cho logic tính shares
- [ ] **Edge cases:** Test với giá trị lớn, nhỏ, None, 0
- [ ] **Integration tests:** Test với dữ liệu thực từ vnstock
- [ ] **Regression tests:** Test các mã đã từng bị lỗi (ACB, VCB, MBB)

### 4. Documentation

- [ ] **Comments:** Có comment giải thích về đơn vị dữ liệu
- [ ] **Docstrings:** Có docstring mô tả input/output
- [ ] **Examples:** Có ví dụ cụ thể trong code hoặc docs
- [ ] **Warnings:** Có cảnh báo về tên cột gây hiểu lầm

### 5. Code Consistency

- [ ] **So sánh với fcfs.py:** Logic giống với `src/core/fcfs.py`
- [ ] **So sánh với sync_service.py:** Logic giống với `services/database/sync_service.py`
- [ ] **Naming convention:** Tên biến rõ ràng, không gây hiểu lầm
- [ ] **Code reuse:** Sử dụng `shares_validator` thay vì duplicate code

## Checklist Khi Review Code

### 1. Kiểm Tra Logic

```python
# ✅ ĐÚNG
shares = capital / par_value

# ❌ SAI
shares = capital * 1000000 / par_value
shares = capital  # Không chia cho par_value
```

### 2. Kiểm Tra Validation

```python
# ✅ ĐÚNG
from src.utils.shares_validator import validate_shares
validate_shares(shares, ticker, raise_error=True)

# ❌ SAI
if shares > 1e12:
    logger.warning("Too large")  # Chỉ warning, không ngăn chặn
```

### 3. Kiểm Tra Consistency

```python
# ✅ ĐÚNG - Logic nhất quán
if 'Common shares':
    shares = capital / par_value
elif 'Paid-in capital':
    shares = capital / par_value  # Cùng logic

# ❌ SAI - Logic khác nhau
if 'Common shares':
    shares = capital / par_value
elif 'Paid-in capital':
    shares = capital * 1000000 / par_value  # Khác nhau!
```

## Red Flags (Cảnh Báo)

Nếu thấy các dấu hiệu sau, cần review kỹ:

1. **Nhân với 1,000,000:** `capital * 1000000`
2. **Logic khác nhau:** Xử lý `Common shares` và `Paid-in capital` khác nhau
3. **Không validate:** Không có validation trước khi lưu
4. **Chỉ warning:** Chỉ warning mà không raise error khi giá trị sai
5. **Thiếu comments:** Không có comment về đơn vị dữ liệu

## Test Cases Bắt Buộc

### Test Case 1: ACB (Paid-in capital)

```python
capital = 51366566000000  # VND
par_value = 10000
expected_shares = 5136656600

shares = capital / par_value
assert shares == expected_shares
validate_shares(shares, "ACB")
```

### Test Case 2: FPT (Common shares)

```python
capital = 17035071210000  # VND
par_value = 10000
expected_shares = 1703507121

shares = capital / par_value
assert shares == expected_shares
validate_shares(shares, "FPT")
```

### Test Case 3: Validation với giá trị sai

```python
shares_wrong = 5136656600000000  # Old wrong value
with pytest.raises(ValueError):
    validate_shares(shares_wrong, "ACB")
```

### Test Case 4: Cross-validation

```python
shares = 5136656600
price = 24000.0
market_cap = shares * price

is_valid, error = cross_validate_shares_with_market_cap(
    shares, price, market_cap, "ACB"
)
assert is_valid
assert error is None
```

## Checklist Khi Sync Dữ Liệu

Trước khi sync shares vào database:

- [ ] **Validate trước:** Validate shares trước khi lưu vào database
- [ ] **Log giá trị:** Log capital value, par_value, và shares để debug
- [ ] **So sánh:** So sánh với giá trị cũ nếu có
- [ ] **Alert:** Alert nếu giá trị thay đổi đột ngột (>50%)

## Checklist Khi Chạy DCF Analysis

Trước khi tính DCF:

- [ ] **Validate shares:** Validate shares từ database
- [ ] **Cross-check:** Cross-check với market cap nếu có
- [ ] **Warning:** Warning nếu shares > 5e10 (50 tỷ)
- [ ] **Error:** Error nếu shares > 1e12 (1 nghìn tỷ)

## Automation

### Pre-commit Hook

Có thể tạo pre-commit hook để tự động kiểm tra:

```bash
# .git/hooks/pre-commit
#!/bin/bash
# Check for suspicious patterns
if git diff --cached | grep -E "capital.*\*.*1000000|capital.*\*.*1,000,000"; then
    echo "ERROR: Found suspicious multiplication by 1,000,000"
    echo "Please review: shares calculation should only divide by par_value"
    exit 1
fi
```

### CI/CD Checks

Thêm vào CI/CD pipeline:

1. Run unit tests: `pytest tests/ut/test_shares_validator.py`
2. Check for validation: Ensure all shares calculations have validation
3. Compare logic: Ensure consistency between files

## References

- [Vnstock Data Format](VNSTOCK_DATA_FORMAT.md)
- [Root Cause Analysis](ROOT_CAUSE_ANALYSIS.md)
- [Shares Validator](../src/utils/shares_validator.py)

---

**Version:** 1.0  
**Last Updated:** 2025-12-30  
**Status:** Active Checklist

