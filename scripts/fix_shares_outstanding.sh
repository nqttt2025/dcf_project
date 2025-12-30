#!/bin/bash
# Script để sửa shares outstanding cho tất cả các mã cổ phiếu bị ảnh hưởng
# Nguyên nhân: Code sync_service.py đã được sửa, nhưng dữ liệu cũ trong database vẫn sai
# Script này sẽ xóa dữ liệu cũ và sync lại với code đã sửa

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "Sửa Shares Outstanding cho tất cả các mã"
echo "=========================================="
echo ""

# Danh sách các mã cần sửa (có shares > 1 tỷ và sử dụng Paid-in capital)
TICKERS="BID BVH CTG FPT GAS GVR HDB HPG MBB MSN MWG PLX POW SAB SSI TCB VCB VHM VIC VJC VNM VPB VRE VSH VTO"

echo "Các mã sẽ được sửa:"
echo "$TICKERS" | tr ' ' '\n' | nl
echo ""

# Kiểm tra database service có đang chạy không
if ! docker-compose ps | grep -q "dcf-database.*Up"; then
    echo "❌ Database service chưa chạy. Vui lòng chạy: ./scripts/docker.sh up"
    exit 1
fi

# Xóa dữ liệu cũ
echo "Bước 1: Xóa dữ liệu shares cũ..."
for ticker in $TICKERS; do
    echo "  - Xóa shares cũ của $ticker..."
    docker-compose exec -T postgres psql -U dcf_user -d dcf_db -c \
        "DELETE FROM shares_outstanding WHERE stock_id IN (SELECT id FROM stocks WHERE ticker = '$ticker');" > /dev/null 2>&1 || true
done
echo "✓ Đã xóa dữ liệu cũ"
echo ""

# Sync lại với code đã sửa
echo "Bước 2: Sync lại dữ liệu với code đã sửa..."
for ticker in $TICKERS; do
    echo "  - Sync $ticker..."
    curl -s -X POST "http://localhost:8003/api/database/sync/shares_outstanding?ticker=$ticker" > /dev/null 2>&1 || true
    sleep 2  # Delay để tránh rate limit
done
echo "✓ Đã sync lại dữ liệu"
echo ""

# Đợi sync hoàn thành
echo "Bước 3: Đợi sync hoàn thành..."
sleep 10

# Kiểm tra kết quả
echo "Bước 4: Kiểm tra kết quả..."
echo ""
docker-compose exec -T postgres psql -U dcf_user -d dcf_db -c "
SELECT 
    s.ticker, 
    so.shares_outstanding,
    CASE 
        WHEN so.shares_outstanding > 1000000000000 THEN '❌ Vẫn sai'
        WHEN so.shares_outstanding > 1000000000 THEN '⚠️  Cần kiểm tra'
        ELSE '✓ Hợp lý'
    END as status
FROM stocks s 
JOIN shares_outstanding so ON s.id = so.stock_id 
WHERE s.ticker IN ($(echo $TICKERS | sed "s/ /','/g" | sed "s/^/'/" | sed "s/$/'/"))
ORDER BY s.ticker;
" | cat

echo ""
echo "=========================================="
echo "Hoàn thành!"
echo "=========================================="
echo ""
echo "Lưu ý: Bạn có thể cần chạy lại phân tích DCF cho các mã này:"
echo "  curl -X POST http://localhost:8000/api/stocks/{TICKER}/run"
echo ""

