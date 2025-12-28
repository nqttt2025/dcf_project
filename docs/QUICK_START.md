# Quick Start Guide - Chạy DCF Analysis

## Cách nhanh nhất để chạy DCF

### Chạy cho một mã cổ phiếu

```bash
make dcf TICKER=VNM
```

Thay `VNM` bằng mã cổ phiếu bạn muốn phân tích (VCB, FPT, BID, ...)

### Chạy cho tất cả mã VN30

```bash
make dcf-all
```

## Ví dụ đầy đủ

### 1. Phân tích VNM (Vinamilk)

```bash
# Chạy DCF
make dcf TICKER=VNM

# Xem kết quả
cat data/results/vnm_result.text
```

### 2. Phân tích VCB (Vietcombank)

```bash
make dcf TICKER=VCB
cat data/results/vcb_result.text
```

### 3. Phân tích nhiều mã

```bash
for ticker in VNM VCB FPT; do
    echo "=== Analyzing $ticker ==="
    make dcf TICKER=$ticker
    echo ""
done
```

## Xem kết quả

Sau khi chạy, kết quả được lưu tại:

- **JSON**: `data/results/{ticker}_result.json`
- **Text**: `data/results/{ticker}_result.text`
- **Cache**: `data/cache/{ticker}_cache.json`
- **Log**: `src/utils/log/dcf_{ticker}.log`

## Các lệnh hữu ích khác

```bash
# Xem hướng dẫn DCF
make dcf-help

# Tính PE cho một mã
make pe TICKER=VNM

# Xem tất cả lệnh
make help
```

## Danh sách mã VN30

Tất cả 30 mã VN30 đã có sẵn config:

**Ngân hàng:** VCB, BID, CTG, MBB, HDB, ACB, VIB, VPB, STB, TPB, SSB

**Bất động sản:** VHM, VIC, VRE, NVL, PDR, KDH

**Công nghệ:** FPT, SSI

**Tiêu dùng:** VNM, MSN, MWG, SAB, PNJ

**Năng lượng:** GAS, PLX

**Công nghiệp:** HPG, REE, GVR

**Hàng không:** VJC

---

Xem hướng dẫn chi tiết tại: [HOW_TO_RUN_DCF.md](HOW_TO_RUN_DCF.md)

