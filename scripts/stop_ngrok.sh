#!/bin/bash
# Script để dừng ngrok

PORT=${1:-8081}

echo "Đang dừng ngrok cho port $PORT..."

# Kiểm tra ngrok có đang chạy không (qua API)
if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
    echo "✅ Phát hiện ngrok đang chạy, đang dừng..."
    # Kill chỉ process ngrok, không phải script này
    pkill -f "^ngrok http" 2>/dev/null || pkill ngrok 2>/dev/null || true
    sleep 2
    
    # Kiểm tra lại
    if ! curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
        echo "✅ Đã dừng ngrok thành công!"
    else
        echo "⚠️  Ngrok vẫn đang chạy, thử kill force..."
        pkill -9 -f "^ngrok http" 2>/dev/null || pkill -9 ngrok 2>/dev/null || true
        sleep 1
        echo "✅ Đã dừng ngrok (force)"
    fi
elif pgrep -f "ngrok.*$PORT" > /dev/null || pgrep ngrok > /dev/null; then
    # Có process nhưng API không phản hồi
    echo "⚠️  Phát hiện process ngrok cũ, đang dọn dẹp..."
    pkill -f "^ngrok http" 2>/dev/null || pkill ngrok 2>/dev/null || true
    sleep 1
    echo "✅ Đã dọn dẹp process ngrok"
else
    echo "ℹ️  Không tìm thấy ngrok đang chạy cho port $PORT"
fi

