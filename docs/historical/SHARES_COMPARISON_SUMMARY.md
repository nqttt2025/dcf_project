# Tóm Tắt So Sánh Shares Outstanding

## Ngày: 2025-12-30

## Vấn Đề Phát Hiện

Người dùng phát hiện số cổ phiếu trên trang web không khớp với tính toán từ market cap / price, dẫn đến tính toán giá trị bị sai lệch.

## Phương Pháp Validation

**Công thức:** `Shares Outstanding = Market Cap / Current Price`

## Kết Quả So Sánh

### Các Mã Đã Kiểm Tra

| Ticker | Price | Market Cap | Shares (MC/Price) | Shares (DB) | Shares (Result) | Diff % | Status |
|--------|-------|------------|-------------------|-------------|-----------------|--------|--------|
| ACB | 24,000 | 123,279,758,376,000 | 5,136,656,599 | 5,136,656,600 | 5,136,656,600 | 0.00% | ✓ |
| FPT | 94,300 | 160,640,721,510,300 | 1,703,507,121 | 1,703,507,121 | 1,703,507,121 | 0.00% | ✓ |
| VCB | 57,100 | 477,109,047,867,400 | 8,355,675,094 | 8,355,675,094 | 9,542,180,957 | 14.20% | ❌ |
| BID | 38,800 | 272,428,842,379,600 | 7,021,361,917 | 7,021,361,900 | 7,021,361,900 | 0.00% | ✓ |
| MBB | 24,850 | 200,166,747,738,650 | 8,054,999,909 | 8,054,999,900 | 8,054,999,900 | 0.00% | ✓ |
| STB | 59,900 | 112,924,421,388,400 | 1,885,215,716 | 1,885,215,700 | 1,885,215,700 | 0.00% | ✓ |
| TPB | 16,900 | 46,881,392,153,700 | 2,774,046,873 | 2,641,956,200 | 2,641,956,200 | 5.00% | ⚠️ |

## Vấn Đề Phát Hiện

### 1. Result Files Cũ Có Shares Sai

**Vấn đề:** Một số result files cũ vẫn chứa shares sai từ lần sync trước:
- FPT: 1,703,507,121,000,000 (sai - nhân với 1 triệu)
- VCB: 83,556,751,000,000 (sai - nhân với 1 triệu)
- BID: 7,021,361,900,000,000 (sai - nhân với 1 triệu)
- MBB: 80,549,999,000,000 (sai - nhân với 1 triệu)

**Giải pháp:** Chạy lại DCF analysis để cập nhật result files.

### 2. VCB Shares Không Khớp

**Vấn đề:** 
- Database có shares: 9,542,180,957 (tính từ market cap khi price = 50,000)
- Price hiện tại: 57,100
- Shares tính từ MC/Price hiện tại: 8,355,675,094
- **Khác biệt: 14.2%**

**Nguyên nhân:** Price thay đổi, nhưng shares trong database không được cập nhật.

**Giải pháp:** 
- Cập nhật shares trong database dựa trên price hiện tại
- Hoặc sử dụng shares từ balance sheet (không phụ thuộc vào price)

### 3. TPB Có Khác Biệt Nhỏ

**Vấn đề:** TPB có khác biệt 5% giữa shares từ market cap và shares trong database.

**Nguyên nhân:** Có thể do:
- Market cap không chính xác
- Hoặc shares trong database không chính xác

**Giải pháp:** Kiểm tra thủ công và quyết định nguồn nào đáng tin cậy hơn.

## Giải Pháp Đã Triển Khai

### 1. Cross-Validation Tự Động

**File:** `src/utils/data_fetcher.py`

Tự động so sánh shares từ database với shares tính từ market cap:
- Nếu khác biệt > 10%: Tự động dùng shares từ market cap
- Nếu khác biệt 5-10%: Cảnh báo
- Nếu khác biệt < 5%: OK

### 2. Fallback từ Market Cap

**File:** `src/core/fcfs.py`

Nếu không tìm thấy shares từ các nguồn khác, tự động tính từ market cap / price.

### 3. Script Tự Động Sửa

**File:** `scripts/fix_shares_from_market_cap.sh`

Script tự động:
- So sánh shares trong database với shares tính từ market cap
- Tự động cập nhật nếu khác biệt > 10%
- Log chi tiết cho từng ticker

## Khuyến Nghị

### 1. Chạy Script Validation Định Kỳ

```bash
./scripts/fix_shares_from_market_cap.sh
```

### 2. Ưu Tiên Nguồn Dữ Liệu

**Nên ưu tiên:**
1. Balance sheet từ vnstock (không phụ thuộc vào price)
2. Market cap calculation (chính xác nhưng phụ thuộc vào price)
3. Database (có thể cũ)

### 3. Cập Nhật Định Kỳ

- Chạy lại sync service định kỳ để cập nhật shares từ balance sheet
- Chạy script validation để kiểm tra và sửa shares sai

### 4. Monitoring

- Alert khi shares khác biệt > 10%
- Track shares values over time
- Compare với historical data

## Kết Luận

✅ **Đã sửa:** FPT, BID, MBB, ACB, STB  
⚠️ **Cần theo dõi:** VCB (price thay đổi), TPB (khác biệt 5%)  
❌ **Đã sửa nhưng cần re-run:** VCB (đã cập nhật database, cần chạy lại DCF)

---

**Version:** 1.0  
**Date:** 2025-12-30  
**Status:** Completed

