# Getting Started

**Dành cho người mới bắt đầu với DCF Valuation Project**

## 🎯 Mục Đích

Phần này giúp bạn:
- Hiểu dự án làm gì
- Cài đặt và chạy dự án
- Thực hiện phân tích DCF đầu tiên
- Tìm hiểu các tính năng cơ bản

## 📚 Tài Liệu

### 1. [Quick Start Guide](quick-start.md) ⭐
Hướng dẫn nhanh để chạy dự án trong 5 phút.

### 2. [Installation Guide](installation.md)
Hướng dẫn chi tiết cài đặt và cấu hình.

### 3. [First Steps](first-steps.md)
Các bước đầu tiên sau khi cài đặt.

## 🚀 Quick Start (Tóm Tắt)

### Prerequisites
- Docker & Docker Compose
- Git

### 3 Bước Đơn Giản

```bash
# 1. Clone repository
git clone <repository-url>
cd dcf_project

# 2. Build và start services
make docker-build-base
make docker-build
make docker-up

# 3. Truy cập ứng dụng
# Frontend: http://localhost:8080
```

Xem chi tiết tại [Quick Start Guide](quick-start.md).

## 📖 Tiếp Theo

Sau khi đã chạy được dự án:
1. Đọc [Business Overview](../business/overview.md) để hiểu về dự án
2. Xem [Features](../business/features.md) để biết các tính năng
3. Tham khảo [Architecture](../architecture/README.md) để hiểu cấu trúc

## ❓ FAQ

### Q: Tôi cần biết gì trước khi bắt đầu?
A: Chỉ cần biết Docker cơ bản. Xem [Installation Guide](installation.md).

### Q: Làm sao để chạy phân tích DCF?
A: Xem [Quick Start Guide](quick-start.md) hoặc [First Steps](first-steps.md).

### Q: Tôi gặp lỗi khi build Docker?
A: Xem [Troubleshooting](../operations/troubleshooting.md).

---

**Next:** [Quick Start Guide](quick-start.md) →

