#!/bin/bash
# Script để lấy thông tin IP và hướng dẫn cấu hình port forwarding trên Windows

echo "=========================================="
echo "Cấu hình Port Forwarding cho WSL2"
echo "=========================================="
echo ""

# Lấy IP của WSL2
WSL_IP=$(hostname -I | awk '{print $1}')
echo "WSL2 IP: $WSL_IP"
echo ""

# Lấy IP của Windows host (từ /etc/resolv.conf)
WINDOWS_IP=$(grep nameserver /etc/resolv.conf | awk '{print $2}' | head -1)
echo "Windows Host IP (từ WSL): $WINDOWS_IP"
echo ""

echo "=========================================="
echo "HƯỚNG DẪN CẤU HÌNH"
echo "=========================================="
echo ""
echo "1. Từ Windows Host (localhost):"
echo "   → http://localhost:8081/"
echo ""
echo "2. Từ máy khác trong cùng mạng LAN:"
echo "   → Cần chạy script PowerShell trên Windows (với quyền Admin):"
echo ""
echo "   Chạy lệnh sau trên Windows PowerShell (Admin):"
echo ""
echo "   \$wslIP = '$(hostname -I | awk '{print $1}')'"
echo "   netsh interface portproxy add v4tov4 listenport=8081 listenaddress=0.0.0.0 connectport=8081 connectaddress=\$wslIP"
echo "   New-NetFirewallRule -DisplayName \"WSL2 Port 8081\" -Direction Inbound -LocalPort 8081 -Protocol TCP -Action Allow"
echo ""
echo "3. Hoặc chạy script PowerShell đã tạo:"
echo "   .\scripts\setup_port_forwarding.ps1"
echo ""
echo "=========================================="
echo "KIỂM TRA"
echo "=========================================="
echo ""
echo "Kiểm tra port forwarding hiện tại trên Windows:"
echo "   netsh interface portproxy show all"
echo ""
echo "Kiểm tra firewall rules:"
echo "   Get-NetFirewallRule -DisplayName \"WSL2 Port 8081\""
echo ""
echo "Xóa port forwarding (nếu cần):"
echo "   netsh interface portproxy delete v4tov4 listenport=8081 listenaddress=0.0.0.0"
echo ""

