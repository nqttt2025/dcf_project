# DCF Analysis Web Service

Web service để hiển thị báo cáo DCF analysis với giao diện đẹp và dễ sử dụng.

## Tính năng

- 📊 **Dashboard**: Hiển thị danh sách tất cả cổ phiếu VN30 với trạng thái
- 📈 **Chi tiết cổ phiếu**: Xem thông tin chi tiết về phân tích DCF của từng cổ phiếu
- ⚙️ **Config Viewer**: Xem và chỉnh sửa config của từng cổ phiếu
- 🔄 **Real-time Status**: Theo dõi trạng thái khi đang chạy phân tích
- 🔍 **Tìm kiếm & Lọc**: Tìm kiếm và lọc cổ phiếu theo trạng thái
- 📱 **Responsive**: Giao diện đẹp trên cả desktop và mobile

## Cài đặt

### 1. Cài đặt dependencies

```bash
make web-install
```

Hoặc thủ công:

```bash
pip install -r web/requirements.txt
```

### 2. Chạy web service

```bash
make web
```

Hoặc thủ công:

```bash
cd web
python3 app.py
```

### 3. Mở trình duyệt

Mở trình duyệt và truy cập: **http://localhost:5000**

## API Endpoints

### GET `/api/stocks`
Lấy danh sách tất cả cổ phiếu với trạng thái

**Response:**
```json
{
  "stocks": [
    {
      "ticker": "FPT",
      "has_result": true,
      "is_running": false,
      "current_price": 92500.0,
      "dcf_fair_value": 141794.43,
      "graham_fair_value": 42674.55,
      "average_fair_value": 92234.49,
      "upside_downside": 53.29,
      "saved_at": "2025-12-28 16:37:02 UTC"
    }
  ],
  "total": 30,
  "with_results": 5,
  "running": 0
}
```

### GET `/api/stocks/<ticker>`
Lấy thông tin chi tiết của một cổ phiếu

**Response:**
```json
{
  "ticker": "FPT",
  "result": {
    "ticker": "FPT",
    "price": 92500.0,
    "dcf_fair_value": 141794.43,
    ...
  },
  "config": {
    "dcf": {...},
    "graham": {...},
    ...
  }
}
```

### GET `/api/stocks/<ticker>/config`
Lấy config của một cổ phiếu

### GET `/api/stocks/<ticker>/status`
Lấy trạng thái chạy của một cổ phiếu

### GET `/api/status`
Lấy trạng thái tổng thể của hệ thống

### POST `/api/stocks/<ticker>/run`
Khởi chạy phân tích DCF cho một cổ phiếu (async)

## Cấu trúc thư mục

```
web/
├── app.py                 # Flask backend application
├── requirements.txt       # Python dependencies
├── README.md             # Documentation
├── templates/
│   └── index.html        # Dashboard HTML template
└── static/
    ├── css/
    │   └── style.css     # Stylesheet
    └── js/
        └── app.js        # Frontend JavaScript
```

## Tính năng chi tiết

### Dashboard
- Hiển thị tất cả cổ phiếu VN30 trong grid layout
- Màu sắc phân biệt:
  - 🟢 Xanh lá: Đã có kết quả phân tích
  - 🟡 Vàng: Đang chạy phân tích
  - ⚪ Xám: Chưa có kết quả

### Chi tiết cổ phiếu
- Thông số đầu vào (Price, EPS, FCF, Shares, Market Cap, Growth)
- Kết quả định giá (DCF, Graham, Average)
- Phân tích tiềm năng (Upside/Downside)
- Thông tin advanced analysis

### Config Viewer
- Hiển thị tất cả sections trong config file
- Format dễ đọc với grid layout

### Real-time Updates
- Tự động refresh mỗi 30 giây
- Hiển thị trạng thái đang chạy với animation
- Cập nhật số liệu thống kê real-time

## Troubleshooting

### Lỗi: ModuleNotFoundError
```bash
# Đảm bảo đã cài đặt dependencies
make web-install
```

### Lỗi: Port 5000 đã được sử dụng
Sửa port trong `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Đổi port
```

### Không thấy dữ liệu
- Đảm bảo đã chạy DCF analysis cho ít nhất một cổ phiếu
- Kiểm tra file `data/results/` có tồn tại không

## Development

### Thêm tính năng mới

1. **Backend (Flask)**: Thêm route mới trong `app.py`
2. **Frontend (JS)**: Thêm function mới trong `app.js`
3. **Styling**: Cập nhật `style.css` nếu cần

### Debug mode

Web service chạy ở debug mode mặc định, sẽ tự động reload khi code thay đổi.

## Tương lai

- [ ] WebSocket cho real-time updates
- [ ] Export PDF báo cáo
- [ ] So sánh nhiều cổ phiếu
- [ ] Charts và graphs
- [ ] Authentication
- [ ] Admin panel để trigger analysis

---

**Version:** 1.0  
**Last Updated:** 2025-12-28

