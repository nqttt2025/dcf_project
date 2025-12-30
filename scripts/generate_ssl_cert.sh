#!/bin/bash
# Script để tạo SSL certificate tự ký cho gateway

SSL_DIR="${1:-config/ssl}"
DOMAIN="${2:-gateway}"

echo "=========================================="
echo "Tạo SSL Certificate cho Gateway"
echo "=========================================="
echo ""

# Tạo thư mục nếu chưa có
mkdir -p "$SSL_DIR"

# Kiểm tra openssl
if ! command -v openssl &> /dev/null; then
    echo "❌ openssl chưa được cài đặt!"
    echo "   Cài đặt: sudo apt-get install openssl"
    exit 1
fi

# Tạo private key
echo "📝 Đang tạo private key..."
openssl genrsa -out "$SSL_DIR/${DOMAIN}.key" 2048

# Tạo certificate signing request
echo "📝 Đang tạo certificate signing request..."
openssl req -new -key "$SSL_DIR/${DOMAIN}.key" -out "$SSL_DIR/${DOMAIN}.csr" \
    -subj "/C=VN/ST=HoChiMinh/L=HoChiMinh/O=DCF Project/OU=IT Department/CN=${DOMAIN}"

# Tạo self-signed certificate (valid for 365 days)
echo "📝 Đang tạo self-signed certificate..."
openssl x509 -req -days 365 -in "$SSL_DIR/${DOMAIN}.csr" \
    -signkey "$SSL_DIR/${DOMAIN}.key" \
    -out "$SSL_DIR/${DOMAIN}.crt" \
    -extensions v3_req -extfile <(
        echo "[v3_req]"
        echo "keyUsage = keyEncipherment, dataEncipherment"
        echo "extendedKeyUsage = serverAuth"
        echo "subjectAltName = @alt_names"
        echo "[alt_names]"
        echo "DNS.1 = ${DOMAIN}"
        echo "DNS.2 = localhost"
        echo "IP.1 = 127.0.0.1"
    )

# Xóa CSR file (không cần thiết)
rm "$SSL_DIR/${DOMAIN}.csr"

# Set permissions
chmod 600 "$SSL_DIR/${DOMAIN}.key"
chmod 644 "$SSL_DIR/${DOMAIN}.crt"

echo ""
echo "✅ SSL Certificate đã được tạo thành công!"
echo ""
echo "Files:"
echo "  - Private Key: $SSL_DIR/${DOMAIN}.key"
echo "  - Certificate: $SSL_DIR/${DOMAIN}.crt"
echo ""
echo "Lưu ý: Đây là self-signed certificate, trình duyệt sẽ cảnh báo."
echo "       Để sử dụng trong production, cần certificate từ CA hợp lệ."
echo ""

