# Shares Validation từ Market Cap

## Tổng Quan

Để đảm bảo tính chính xác của shares outstanding, hệ thống hiện sử dụng **market cap / price** như một phương pháp validation và fallback.

## Công Thức

```
Shares Outstanding = Market Cap / Current Price
```

## Implementation

### 1. Cross-Validation trong `data_fetcher.py`

Khi lấy shares từ database, hệ thống tự động so sánh với shares tính từ market cap:

```python
# Cross-validation with market cap if available
market_cap, price = get_market_cap(ticker)
if market_cap and price and price > 0:
    shares_from_mc = market_cap / price
    diff_pct = abs(shares - shares_from_mc) / shares_from_mc * 100
    
    # If difference > 10%, use market cap calculation
    if diff_pct > 10:
        logger.warning("Using market cap calculation instead")
        shares = shares_from_mc
```

**Logic:**
- Nếu khác biệt > 10%: Tự động dùng shares từ market cap
- Nếu khác biệt 5-10%: Cảnh báo nhưng vẫn dùng shares từ database
- Nếu khác biệt < 5%: OK

### 2. Fallback trong `fcfs.py`

Nếu không tìm thấy shares từ các nguồn khác, hệ thống sẽ tính từ market cap:

```python
# Last resort: Calculate from market cap / price
try:
    market_cap, price = get_market_cap(ticker)
    if market_cap and price and price > 0:
        shares_from_mc = market_cap / price
        # Validate and return
        return shares_from_mc
except:
    pass
```

**Priority order:**
1. Database
2. Redis
3. File cache
4. vnstock API (balance sheet)
5. **Market cap calculation** (fallback)

## Script Tự Động Sửa

### `scripts/fix_shares_from_market_cap.sh`

Script tự động kiểm tra và sửa shares dựa trên market cap:

```bash
./scripts/fix_shares_from_market_cap.sh
```

**Chức năng:**
- So sánh shares trong database với shares tính từ market cap
- Tự động cập nhật nếu khác biệt > 10%
- Log chi tiết cho từng ticker

## Validation Rules

| Difference | Action |
|------------|--------|
| < 5% | ✓ OK - Không cần sửa |
| 5-10% | ⚠️ Warning - Nên kiểm tra |
| > 10% | ❌ Error - Tự động sửa |

## Ví Dụ

### VCB (Đã sửa)

**Trước:**
- Shares trong DB: 8,355,675,100
- Market Cap: 477,109,047,867,400
- Price: 50,000
- Shares từ MC: 9,542,180,957
- **Diff: 14.2%** ❌

**Sau:**
- Shares trong DB: 9,542,180,957 ✅
- **Diff: 0%** ✓

### FPT (Đã đúng)

- Shares trong DB: 1,703,507,121
- Market Cap: 160,640,721,510,300
- Price: 94,300
- Shares từ MC: 1,703,507,121
- **Diff: 0%** ✓

## Lưu Ý

1. **Market cap có thể thay đổi:** Giá cổ phiếu thay đổi liên tục, nên shares tính từ market cap cũng thay đổi theo.

2. **Độ chính xác:** Market cap từ vnstock có thể không hoàn toàn chính xác do:
   - Delay trong cập nhật giá
   - Rounding errors
   - Khác biệt về thời điểm lấy dữ liệu

3. **Tolerance:** Hệ thống cho phép sai lệch 5-10% để tránh sửa nhầm do market cap không chính xác.

## Best Practices

1. **Chạy script validation định kỳ:**
   ```bash
   ./scripts/fix_shares_from_market_cap.sh
   ```

2. **Kiểm tra logs:** Xem các cảnh báo về khác biệt > 5%

3. **Manual review:** Nếu khác biệt > 10%, nên kiểm tra thủ công

4. **Re-sync:** Nếu phát hiện nhiều mã sai, chạy lại sync service:
   ```bash
   docker-compose exec database python3 -m services.database.sync_service sync_shares_outstanding
   ```

---

**Version:** 1.0  
**Last Updated:** 2025-12-30  
**Status:** Active

