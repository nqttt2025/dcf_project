# First Steps

**Các bước đầu tiên sau khi cài đặt**

## ✅ Checklist

Sau khi cài đặt thành công, bạn đã có:
- [x] Docker và Docker Compose
- [x] Repository cloned
- [x] Base image built
- [x] Services running
- [x] Web interface accessible

## 🎯 Bước 1: Khám Phá Web Interface

1. Mở http://localhost:8080
2. Xem danh sách cổ phiếu có sẵn
3. Click vào một mã cổ phiếu để xem chi tiết
4. Xem kết quả phân tích (nếu có)

## 🔍 Bước 2: Chạy Phân Tích Đầu Tiên

### Qua Web Interface

1. Chọn mã cổ phiếu (ví dụ: FPT)
2. Click "Chạy DCF"
3. Theo dõi progress bar
4. Xem kết quả khi hoàn tất

### Qua Command Line

```bash
# Chạy DCF cho FPT
make dcf-single TICKER=FPT

# Xem kết quả
cat data/results/fpt_result.text
```

## 📊 Bước 3: Hiểu Kết Quả

Kết quả DCF bao gồm:

1. **DCF Valuation**
   - Fair Value per share
   - Discounted Cash Flows
   - Terminal Value

2. **Graham Valuation**
   - Fair Value per share
   - PE Ratio
   - Growth Rate

3. **Advanced Analysis**
   - Margin of Safety
   - Comparison với Market Price
   - Investment Recommendation

Xem chi tiết tại [DCF Calculation](../reference/dcf-calculation.md).

## ⚙️ Bước 4: Tùy Chỉnh Configuration

### Tạo Config Mới

```bash
# Copy template
cp config/FPT.cfg config/NEW_TICKER.cfg

# Edit config
nano config/NEW_TICKER.cfg
```

### Thay Đổi Parameters

```ini
[dcf]
yr = 7              # Forecast years
dr = 12             # Discount rate (%)
pr = 3              # Perpetual growth (%)

[graham]
base_pe = 8.5
growth_multiplier = 2
```

## 🔧 Bước 5: Development Mode

Để phát triển với hot reload:

```bash
# Start dev mode
make docker-dev

# Edit code trong services/*/main.py hoặc src/
# Changes sẽ tự động reload
```

## 📚 Bước 6: Đọc Documentation

### Essential Reading

1. **[Business Overview](../business/overview.md)** - Hiểu về dự án
2. **[Features](../business/features.md)** - Các tính năng
3. **[Architecture](../architecture/README.md)** - Cấu trúc hệ thống

### Technical Reading

1. **[DCF Calculation](../reference/dcf-calculation.md)** - Công thức DCF
2. **[Graham Valuation](../reference/graham-valuation.md)** - Công thức Graham
3. **[API Reference](../reference/api.md)** - API endpoints

## 🎓 Bước 7: Học Các Commands

### Docker Commands

```bash
make docker-build          # Build images
make docker-up             # Start services
make docker-down           # Stop services
make docker-logs           # View logs
make docker-ps             # List containers
```

### Analysis Commands

```bash
make dcf-single TICKER=FPT    # Run DCF
make dcf-all                  # Run all
make pe-single TICKER=FPT     # Run PE
```

### Maintenance Commands

```bash
make clean                    # Clean logs/cache
make lint                     # Run linters
make test                     # Run tests
```

## 🐛 Bước 8: Troubleshooting

### Kiểm Tra Logs

```bash
# All logs
make docker-logs

# Specific service
make docker-logs-dcf
make docker-logs-stock
make docker-logs-redis
```

### Kiểm Tra Status

```bash
# Service status
make docker-ps

# API health
curl http://localhost:8000/health
```

## 🚀 Tiếp Theo

Bây giờ bạn đã sẵn sàng:

1. **Sử dụng dự án**: Chạy phân tích DCF cho các mã cổ phiếu
2. **Phát triển**: Thêm tính năng mới hoặc cải thiện hiện có
3. **Tùy chỉnh**: Điều chỉnh parameters và configs
4. **Học hỏi**: Đọc thêm documentation

## 📖 Recommended Reading

- [Business Overview](../business/overview.md) - Hiểu về business
- [Architecture](../architecture/README.md) - Hiểu cấu trúc
- [Version Management](../operations/version-management.md) - Quản lý version
- [Development Guide](../architecture/development.md) - Phát triển

---

**Next:** [Business Overview](../business/overview.md) →

