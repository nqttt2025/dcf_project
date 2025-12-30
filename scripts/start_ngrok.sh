#!/bin/bash
# Script để khởi động ngrok cho port 8081

PORT=${1:-8081}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
NGROK_LOG_DIR="$PROJECT_ROOT/logs/ngrok"
NGROK_LOG="$NGROK_LOG_DIR/ngrok_${PORT}.log"

# Tạo thư mục log nếu chưa có
mkdir -p "$NGROK_LOG_DIR"

echo "=========================================="
echo "Khởi động ngrok cho port $PORT"
echo "=========================================="
echo ""

# Kiểm tra ngrok đã cài đặt chưa
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok chưa được cài đặt!"
    echo ""
    echo "Cài đặt ngrok:"
    echo "  curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null"
    echo "  echo 'deb https://ngrok-agent.s3.amazonaws.com buster main' | sudo tee /etc/apt/sources.list.d/ngrok.list"
    echo "  sudo apt update && sudo apt install ngrok"
    exit 1
fi

# Kiểm tra port có đang được sử dụng không
if ! netstat -tln 2>/dev/null | grep -q ":$PORT " && ! ss -tln 2>/dev/null | grep -q ":$PORT "; then
    echo "⚠️  Cảnh báo: Port $PORT có vẻ không đang listen!"
    echo "   Đảm bảo Docker container đang chạy: docker-compose up -d frontend"
    echo ""
fi

# Kiểm tra ngrok đã chạy chưa (kiểm tra API thay vì process)
if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
    echo "⚠️  ngrok đã đang chạy"
    echo ""
    
    # Lấy URL hiện tại
    CURRENT_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['tunnels'][0]['public_url'] if d.get('tunnels') else '')" 2>/dev/null)
    if [ -n "$CURRENT_URL" ]; then
        echo "URL hiện tại: $CURRENT_URL"
        echo ""
    fi
    
    echo "Để xem URL hiện tại:"
    echo "  make ngrok-status"
    echo ""
    echo "Để dừng ngrok:"
    echo "  make ngrok-stop"
    echo ""
    read -p "Bạn có muốn dừng và khởi động lại? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill ngrok 2>/dev/null
        sleep 2
    else
        exit 0
    fi
elif pgrep -f "ngrok.*$PORT" > /dev/null; then
    # Có process nhưng API không phản hồi - dọn dẹp
    echo "⚠️  Phát hiện process ngrok cũ nhưng không hoạt động"
    echo "   Đang dọn dẹp..."
    # Kill chỉ các process ngrok thực sự, không phải script này
    pkill -f "^ngrok http" 2>/dev/null || true
    sleep 2
fi

# Khởi động ngrok
echo "🚀 Đang khởi động ngrok..."
echo "   Log file: $NGROK_LOG"
echo ""

# Chạy ngrok trong background
ngrok http $PORT --log=stdout > "$NGROK_LOG" 2>&1 &
NGROK_PID=$!

# Đợi ngrok khởi động
sleep 3

# Kiểm tra ngrok đã chạy thành công chưa
if ! ps -p $NGROK_PID > /dev/null; then
    echo "❌ Không thể khởi động ngrok!"
    echo "   Kiểm tra log: $NGROK_LOG"
    cat "$NGROK_LOG"
    exit 1
fi

# Lấy URL từ ngrok API
sleep 2
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['tunnels'][0]['public_url'] if d.get('tunnels') else '')" 2>/dev/null)

if [ -z "$NGROK_URL" ]; then
    echo "⚠️  Không thể lấy URL từ ngrok API"
    echo "   Ngrok đang chạy nhưng có thể cần đợi thêm vài giây"
    echo "   Kiểm tra tại: http://localhost:4040"
    echo ""
    echo "PID: $NGROK_PID"
    echo "Log: $NGROK_LOG"
else
    echo "✅ ngrok đã khởi động thành công!"
    echo ""
    echo "=========================================="
    echo "🌐 URL công khai:"
    echo "=========================================="
    echo "$NGROK_URL"
    echo ""
    echo "=========================================="
    echo "Thông tin khác:"
    echo "=========================================="
    echo "PID: $NGROK_PID"
    echo "Log: $NGROK_LOG"
    echo "Web UI: http://localhost:4040"
    echo ""
    echo "Để dừng ngrok:"
    echo "  pkill -f \"ngrok.*$PORT\""
    echo "  hoặc: kill $NGROK_PID"
    echo ""
fi

