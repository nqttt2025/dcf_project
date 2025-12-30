#!/bin/bash
# Script để kiểm tra trạng thái ngrok

PORT=${1:-8081}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
NGROK_LOG_DIR="$PROJECT_ROOT/logs/ngrok"
NGROK_LOG="$NGROK_LOG_DIR/ngrok_${PORT}.log"

echo "=========================================="
echo "Trạng thái ngrok cho port $PORT"
echo "=========================================="
echo ""

# Kiểm tra ngrok API có phản hồi không (cách kiểm tra chính xác hơn)
if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
    echo "✅ ngrok đang chạy"
    echo ""
    
    # Lấy URL từ ngrok API
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['tunnels'][0]['public_url'] if d.get('tunnels') else '')" 2>/dev/null)
    
    if [ -n "$NGROK_URL" ]; then
        echo "🌐 URL công khai:"
        echo "$NGROK_URL"
        echo ""
    else
        echo "⚠️  Không thể lấy URL (có thể đang khởi động hoặc không có tunnel)"
        echo "   Kiểm tra tại: http://localhost:4040"
        echo ""
    fi
    
    # Hiển thị thông tin chi tiết
    echo "Thông tin chi tiết:"
    curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -m json.tool 2>/dev/null || curl -s http://localhost:4040/api/tunnels 2>/dev/null
    
    echo ""
    echo "Web UI: http://localhost:4040"
    if [ -f "$NGROK_LOG" ]; then
        echo "Log file: $NGROK_LOG"
    fi
else
    echo "❌ ngrok không đang chạy"
    echo ""
    
    # Kiểm tra xem có process zombie không
    if pgrep -f "ngrok.*$PORT" > /dev/null || pgrep ngrok > /dev/null; then
        echo "⚠️  Phát hiện process ngrok nhưng API không phản hồi"
        echo "   Có thể là process cũ hoặc zombie process"
        echo "   Chạy 'make ngrok-stop' để dọn dẹp"
        echo ""
    fi
    
    echo "Để khởi động:"
    echo "  make ngrok"
    echo "  hoặc: ./scripts/start_ngrok.sh $PORT"
fi

