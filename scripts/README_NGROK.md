# Hướng dẫn sử dụng ngrok để expose port 8081

## Tổng quan

Ngrok cho phép bạn expose localhost:8081 ra internet công khai, giúp truy cập ứng dụng từ bất kỳ đâu.

## Cài đặt ngrok

Nếu chưa có ngrok, cài đặt bằng:

```bash
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo 'deb https://ngrok-agent.s3.amazonaws.com buster main' | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
```

Hoặc tải từ: https://ngrok.com/download

## Sử dụng

### 1. Khởi động ngrok cho port 8081

```bash
./scripts/start_ngrok.sh 8081
```

Script sẽ:
- Kiểm tra ngrok đã cài đặt chưa
- Kiểm tra port 8081 có đang listen không
- Khởi động ngrok và hiển thị URL công khai

### 2. Xem trạng thái ngrok

```bash
./scripts/ngrok_status.sh 8081
```

### 3. Dừng ngrok

```bash
./scripts/stop_ngrok.sh 8081
```

Hoặc:

```bash
pkill -f "ngrok.*8081"
```

## Truy cập

Sau khi khởi động ngrok, bạn sẽ nhận được URL dạng:
```
https://xxxx-xxxx-xxxx.ngrok-free.app
```

URL này có thể truy cập từ bất kỳ đâu trên internet.

**Lưu ý:**
- URL sẽ thay đổi mỗi lần khởi động lại ngrok (trừ khi dùng ngrok account có tên miền cố định)
- Ngrok miễn phí có giới hạn về số lượng requests
- Web UI của ngrok: http://localhost:4040

## Web UI

Ngrok cung cấp web UI tại: http://localhost:4040

Tại đây bạn có thể:
- Xem các request đến tunnel
- Xem logs
- Xem thống kê

## Troubleshooting

### Port 8081 không listen
Đảm bảo Docker container đang chạy:
```bash
docker-compose up -d frontend
docker ps | grep frontend
```

### Ngrok không khởi động
Kiểm tra log:
```bash
cat logs/ngrok/ngrok_8081.log
# hoặc
tail -f logs/ngrok/ngrok_8081.log
```

### Không thể lấy URL
Đợi vài giây rồi kiểm tra lại:
```bash
curl http://localhost:4040/api/tunnels | python3 -m json.tool
```

