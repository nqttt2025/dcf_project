#!/bin/bash
# Script để kiểm tra trạng thái ngrok

PORT=${1:-8081}

echo "=========================================="
echo "Trạng thái ngrok cho port $PORT"
echo "=========================================="
echo ""

# Kiểm tra process
if pgrep -f "ngrok.*$PORT" > /dev/null; then
    echo "✅ ngrok đang chạy"
    echo ""
    
    # Lấy URL từ ngrok API
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['tunnels'][0]['public_url'] if d.get('tunnels') else '')" 2>/dev/null)
    
    if [ -n "$NGROK_URL" ]; then
        echo "🌐 URL công khai:"
        echo "$NGROK_URL"
        echo ""
    else
        echo "⚠️  Không thể lấy URL (có thể đang khởi động)"
        echo "   Kiểm tra tại: http://localhost:4040"
        echo ""
    fi
    
    # Hiển thị thông tin chi tiết
    echo "Thông tin chi tiết:"
    curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -m json.tool 2>/dev/null || curl -s http://localhost:4040/api/tunnels 2>/dev/null
    
    echo ""
    echo "Web UI: http://localhost:4040"
else
    echo "❌ ngrok không đang chạy"
    echo ""
    echo "Để khởi động:"
    echo "  ./scripts/start_ngrok.sh $PORT"
fi

