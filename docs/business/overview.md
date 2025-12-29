# Business Overview

**Tổng quan về DCF Valuation Project**

## 🎯 Dự Án Là Gì?

**DCF Valuation Project** là một hệ thống phân tích và định giá cổ phiếu tự động sử dụng các mô hình tài chính chuẩn. Dự án cung cấp công cụ để:

- Tính toán giá trị hợp lý của cổ phiếu
- Phân tích tài chính tự động
- So sánh với giá thị trường
- Đưa ra khuyến nghị đầu tư

## 💼 Business Model

### Core Business
Phân tích và định giá cổ phiếu Việt Nam sử dụng:
- **DCF Model** (Discounted Cash Flow)
- **Graham Valuation Model**
- Dữ liệu tài chính từ vnstock

### Value Proposition
1. **Chính Xác**: Sử dụng các mô hình tài chính chuẩn
2. **Tự Động**: Tự động lấy dữ liệu và tính toán
3. **Dễ Sử Dụng**: Web interface đơn giản, trực quan
4. **Real-time**: Cập nhật dữ liệu và progress theo thời gian thực
5. **Mở Rộng**: Kiến trúc microservices dễ mở rộng

## 🎯 Mục Đích

### Primary Purpose
Cung cấp công cụ phân tích định giá cổ phiếu cho:
- **Nhà đầu tư cá nhân**: Đánh giá giá trị cổ phiếu trước khi đầu tư
- **Phân tích tài chính**: Hỗ trợ phân tích và nghiên cứu
- **Sinh viên/Học viên**: Học tập về định giá cổ phiếu

### Use Cases
1. **Đánh Giá Đầu Tư**: Xác định giá trị hợp lý của cổ phiếu
2. **So Sánh**: So sánh giá trị tính toán với giá thị trường
3. **Nghiên Cứu**: Phân tích và nghiên cứu các mã cổ phiếu
4. **Học Tập**: Học về các mô hình định giá

## 🏗️ Kiến Trúc

### Microservices Architecture
- **Frontend**: Web interface (Nginx)
- **Gateway**: API Gateway (FastAPI)
- **DCF Service**: Tính toán DCF
- **Stock Service**: Quản lý dữ liệu cổ phiếu
- **Redis**: Cache và status tracking

### Technology Stack
- **Backend**: Python 3.11, FastAPI
- **Frontend**: HTML, CSS, JavaScript
- **Cache**: Redis
- **Containerization**: Docker
- **Data Source**: vnstock library

## 📊 Dữ Liệu

### Data Sources
- **vnstock**: Thư viện Python để lấy dữ liệu từ các sàn chứng khoán Việt Nam
- **Financial Data**: Balance sheet, income statement, cash flow
- **Market Data**: Giá cổ phiếu, market cap, PE ratio

### Data Processing
- Tự động lấy dữ liệu từ vnstock
- Cache dữ liệu để tối ưu hiệu suất
- Xử lý và tính toán tự động

## 🎨 User Experience

### Web Interface
- **Danh sách cổ phiếu**: Xem tất cả mã có sẵn
- **Chi tiết cổ phiếu**: Thông tin và kết quả phân tích
- **Progress Tracking**: Theo dõi tiến độ tính toán
- **Kết quả**: Hiển thị giá trị hợp lý và khuyến nghị

### Command Line
- Chạy phân tích từ command line
- Batch processing cho nhiều mã
- Tùy chỉnh parameters

## 🔄 Workflow

1. **User** chọn mã cổ phiếu
2. **System** lấy dữ liệu tài chính từ vnstock
3. **DCF Service** tính toán giá trị hợp lý
4. **System** hiển thị kết quả và khuyến nghị
5. **User** xem và phân tích kết quả

## 📈 Metrics & KPIs

### Performance Metrics
- **Accuracy**: Độ chính xác của tính toán
- **Speed**: Thời gian tính toán
- **Reliability**: Độ tin cậy của hệ thống

### User Metrics
- **Usage**: Số lượng phân tích được chạy
- **Stocks Analyzed**: Số mã cổ phiếu được phân tích
- **User Satisfaction**: Mức độ hài lòng của người dùng

## 🎯 Success Criteria

### Technical Success
- ✅ Hệ thống chạy ổn định
- ✅ Tính toán chính xác
- ✅ Performance tốt
- ✅ Dễ sử dụng

### Business Success
- ✅ Người dùng sử dụng thành công
- ✅ Kết quả hữu ích cho quyết định đầu tư
- ✅ Hệ thống mở rộng được

## 🔗 Related Documents

- [Goals & Objectives](goals.md) - Mục tiêu chi tiết
- [Vision](vision.md) - Tầm nhìn
- [Features](features.md) - Các tính năng
- [Value Proposition](value-proposition.md) - Giá trị cung cấp

---

**Next:** [Goals & Objectives](goals.md) →

