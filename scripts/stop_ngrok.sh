#!/bin/bash
# Script để dừng ngrok

PORT=${1:-8081}

echo "Đang dừng ngrok cho port $PORT..."

# Tìm và kill process ngrok
if pgrep -f "ngrok.*$PORT" > /dev/null; then
    pkill -f "ngrok.*$PORT"
    sleep 1
    
    if ! pgrep -f "ngrok.*$PORT" > /dev/null; then
        echo "✅ Đã dừng ngrok thành công!"
    else
        echo "⚠️  Có thể cần kill force:"
        echo "   pkill -9 -f 'ngrok.*$PORT'"
    fi
else
    echo "ℹ️  Không tìm thấy ngrok đang chạy cho port $PORT"
fi

