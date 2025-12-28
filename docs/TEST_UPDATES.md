# Cập nhật Test Cases

## Tổng quan

Đã kiểm tra và cập nhật test cases sau khi loại bỏ option `use_stockanalysis` và thêm hỗ trợ TTM mặc định.

## Thay đổi chính

### 1. Loại bỏ option `use_stockanalysis`

**Lý do:**
- stockanalysis.com đang chặn scraping với Cloudflare (403 Forbidden)
- Không thể lấy dữ liệu từ nguồn này
- Code trở nên đơn giản và dễ bảo trì hơn

**Thay đổi trong code:**
```python
# Trước đây
def get_free_cash_flow(ticker, use_ttm=True, use_stockanalysis=False):
    if use_stockanalysis:
        # Try stockanalysis.com...
    
# Bây giờ
def get_free_cash_flow(ticker, use_ttm=True):
    # Chỉ sử dụng vnstock với TTM
```

### 2. Test Cases mới

Đã tạo file `tests/ut/test_fcfs_ttm.py` với các test case:

#### Test Cases cho TTM Calculation:

1. **`test_get_free_cash_flow_ttm_success`**
   - Test tính TTM thành công với 4 quý
   - Verify công thức tính đúng: Sum(OCF) - Sum(CapEx)

2. **`test_get_free_cash_flow_ttm_with_cache`**
   - Test sử dụng cached value
   - Verify cache được check và sử dụng đúng

3. **`test_get_free_cash_flow_ttm_insufficient_quarters`**
   - Test với dữ liệu không đủ 4 quý
   - Verify vẫn trả về giá trị (sum của các quý có sẵn)

4. **`test_get_free_cash_flow_default_uses_ttm`**
   - Test mặc định sử dụng TTM
   - Verify `get_free_cash_flow()` mặc định gọi TTM

5. **`test_get_free_cash_flow_with_ttm_false`**
   - Test với `use_ttm=False`
   - Verify chỉ lấy quý gần nhất

6. **`test_get_free_cash_flow_ttm_empty_dataframe`**
   - Test với DataFrame rỗng
   - Verify trả về None

7. **`test_get_free_cash_flow_ttm_no_valid_data`**
   - Test với dữ liệu không hợp lệ
   - Verify trả về None

## Kết quả test

### Test FCF TTM:
```
tests/ut/test_fcfs_ttm.py::TestFCFTTM::test_get_free_cash_flow_default_uses_ttm PASSED
tests/ut/test_fcfs_ttm.py::TestFCFTTM::test_get_free_cash_flow_ttm_empty_dataframe PASSED
tests/ut/test_fcfs_ttm.py::TestFCFTTM::test_get_free_cash_flow_ttm_insufficient_quarters PASSED
tests/ut/test_fcfs_ttm.py::TestFCFTTM::test_get_free_cash_flow_ttm_no_valid_data PASSED
tests/ut/test_fcfs_ttm.py::TestFCFTTM::test_get_free_cash_flow_ttm_success PASSED
tests/ut/test_fcfs_ttm.py::TestFCFTTM::test_get_free_cash_flow_ttm_with_cache PASSED
tests/ut/test_fcfs_ttm.py::TestFCFTTM::test_get_free_cash_flow_with_ttm_false PASSED

7 passed in 2.02s
```

### Test DCF Calculator:
Tất cả test cases hiện tại vẫn pass sau khi loại bỏ `use_stockanalysis`.

## Test Coverage

### Đã cover:
- ✅ TTM calculation với 4 quý
- ✅ TTM calculation với cache
- ✅ TTM calculation với dữ liệu không đủ
- ✅ Default behavior (sử dụng TTM)
- ✅ Single quarter fallback
- ✅ Error handling (empty DataFrame, invalid data)

### Cần bổ sung (nếu cần):
- ⚠️ Integration test với real vnstock data (optional)
- ⚠️ Performance test cho TTM calculation (optional)

## Chạy test

### Chạy tất cả test:
```bash
cd tests
make ut
```

### Chạy test TTM riêng:
```bash
python3 -m pytest tests/ut/test_fcfs_ttm.py -v
```

### Chạy test DCF Calculator:
```bash
python3 -m pytest tests/ut/test_dcf_calculator.py -v
```

## Files đã thay đổi

1. **`src/core/fcfs.py`**
   - Loại bỏ parameter `use_stockanalysis`
   - Loại bỏ code liên quan đến stockanalysis.com
   - Cập nhật docstring

2. **`tests/ut/test_fcfs_ttm.py`** (mới)
   - 7 test cases cho TTM calculation
   - Cover các edge cases và error handling

## Lưu ý

- Tất cả test cases đều sử dụng mock để tránh phụ thuộc vào external API
- Test cases không cần internet connection
- Test cases chạy nhanh (< 3 giây)

---

**Cập nhật:** 2025-12-28  
**Phiên bản:** 2.0 (TTM mặc định, loại bỏ stockanalysis)

