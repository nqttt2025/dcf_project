# Sửa Lỗi Shares Outstanding - Tài Liệu Kỹ Thuật

## 1. Script Thuộc Nhóm Nào?

### **Database Service** (`services/database/`)

Script `sync_service.py` thuộc **Database Service** - một microservice trong kiến trúc microservices của dự án:

```
services/
├── database/           ← Database Service
│   ├── main.py        ← API endpoints
│   └── sync_service.py ← Sync logic (script này)
├── dcf/               ← DCF Analysis Service
├── stock/             ← Stock Service
├── gateway/           ← API Gateway
└── frontend/          ← Frontend Service
```

**Chức năng của Database Service:**
- Quản lý dữ liệu trong PostgreSQL
- Sync dữ liệu từ vnstock API vào database
- Cung cấp API endpoints để query dữ liệu
- Quản lý cache và Redis

**File liên quan:**
- `services/database/sync_service.py` - Logic sync dữ liệu
- `services/database/main.py` - API endpoints cho sync

## 2. Nguyên Nhân Sai

### Vấn Đề Trong Code Cũ

**File:** `services/database/sync_service.py` (dòng 557-562)

**Code cũ (SAI):**
```python
elif 'Paid-in capital (Bn. VND)' in latest_row.index:
    capital = safe_get_value(latest_row, 'Paid-in capital (Bn. VND)')
    if capital and capital > 0:
        shares_outstanding = capital * 1000000 / par_value  # ❌ SAI: Nhân với 1,000,000
        calculation_method = 'paid_in_capital'
        source_column = 'Paid-in capital (Bn. VND)'
```

**Code mới (ĐÚNG):**
```python
elif 'Paid-in capital (Bn. VND)' in latest_row.index:
    capital = safe_get_value(latest_row, 'Paid-in capital (Bn. VND)')
    if capital and capital > 0:
        # Note: Despite the name "(Bn. VND)", the value is actually in VND (not billions)
        # So we only divide by par_value, not multiply by 1,000,000
        shares_outstanding = capital / par_value  # ✅ ĐÚNG: Chỉ chia cho par_value
        calculation_method = 'paid_in_capital'
        source_column = 'Paid-in capital (Bn. VND)'
```

### Giải Thích Chi Tiết

1. **Tên cột gây hiểu lầm:**
   - Tên cột: `Paid-in capital (Bn. VND)` → Gợi ý là "tỷ VND"
   - Thực tế: Giá trị là **VND trực tiếp** (không phải tỷ VND)

2. **Ví dụ cụ thể:**
   - ACB: `Paid-in capital (Bn. VND)` = 51,366,566,000,000 VND
   - Code cũ: `51,366,566,000,000 * 1,000,000 / 10,000` = 5,136,656,600,000,000 shares ❌
   - Code mới: `51,366,566,000,000 / 10,000` = 5,136,656,600 shares ✅

3. **Hậu quả:**
   - Shares sai → EPS sai (EPS = Net Profit / Shares)
   - Shares sai → DCF Fair Value sai (Fair Value = DCF Value / Shares)
   - Shares sai → Tất cả các tính toán liên quan đều sai

## 3. Liệu Có Tiếp Tục Sai Nếu Không Sửa Source Code?

### ❌ **CÓ, sẽ tiếp tục sai!**

### Lý Do:

1. **Code đã được sửa trong source:**
   - File `sync_service.py` đã được sửa
   - Code mới đã được build vào Docker image

2. **Nhưng dữ liệu cũ trong database vẫn sai:**
   - Database chứa dữ liệu cũ được sync với code cũ
   - Dữ liệu này không tự động cập nhật

3. **Khi nào sẽ đúng:**
   - ✅ Khi sync lại dữ liệu với code mới
   - ✅ Khi xóa dữ liệu cũ và sync lại
   - ❌ Nếu không làm gì → Dữ liệu vẫn sai mãi mãi

### Quy Trình Sync:

```
vnstock API → sync_service.py → Database → DCF Analysis
                ↑
            Code đã sửa ✅
                ↓
            Database vẫn có dữ liệu cũ ❌
```

### Giải Pháp:

1. **Xóa dữ liệu cũ** trong database
2. **Sync lại** với code mới đã sửa
3. **Chạy lại DCF analysis** để cập nhật kết quả

## 4. Các Mã Bị Ảnh Hưởng

Tất cả các mã sử dụng cột `Paid-in capital (Bn. VND)` thay vì `Common shares`:

- **Ngân hàng:** ACB, BID, CTG, HDB, MBB, TCB, VCB, VPB
- **Bất động sản:** VHM, VIC, VRE
- **Công nghiệp:** HPG, PLX, POW
- **Bán lẻ:** MWG, PNJ
- **Năng lượng:** GAS, PLX
- **Công nghệ:** FPT
- **Khác:** BVH, GVR, MSN, SAB, SSI, VJC, VNM, VSH, VTO

**Tổng cộng:** ~25 mã cổ phiếu

## 5. Cách Sửa

### Tự Động (Khuyến nghị):

```bash
# Chạy script tự động
./scripts/fix_shares_outstanding.sh
```

### Thủ Công:

```bash
# 1. Xóa dữ liệu cũ của một mã
docker-compose exec -T postgres psql -U dcf_user -d dcf_db -c \
    "DELETE FROM shares_outstanding WHERE stock_id IN (SELECT id FROM stocks WHERE ticker = 'ACB');"

# 2. Sync lại với code mới
curl -X POST http://localhost:8003/api/database/sync/shares_outstanding?ticker=ACB

# 3. Chạy lại DCF analysis
curl -X POST http://localhost:8000/api/stocks/ACB/run
```

## 6. Kiểm Tra Sau Khi Sửa

```bash
# Kiểm tra shares trong database
docker-compose exec -T postgres psql -U dcf_user -d dcf_db -c \
    "SELECT s.ticker, so.shares_outstanding FROM stocks s JOIN shares_outstanding so ON s.id = so.stock_id WHERE s.ticker = 'ACB';"

# Kiểm tra kết quả DCF
curl http://localhost:8000/api/stocks/ACB | jq '.result.dcf_fair_value'
```

## 7. Phòng Ngừa Trong Tương Lai

1. **Unit tests:** Thêm test cases cho sync logic
2. **Validation:** Kiểm tra giá trị shares hợp lý (ví dụ: < 100 tỷ)
3. **Monitoring:** Cảnh báo khi shares quá lớn
4. **Documentation:** Ghi chú rõ ràng về đơn vị dữ liệu từ vnstock

---

**Version:** 1.0  
**Date:** 2025-12-30  
**Status:** Fixed in source code, requires data sync

