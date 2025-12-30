# Script PowerShell để cấu hình port forwarding cho WSL2
# Chạy script này trên Windows PowerShell (với quyền Administrator)

Write-Host "Cấu hình port forwarding cho WSL2..." -ForegroundColor Green

# Lấy IP của WSL2
$wslIP = (wsl hostname -I).Trim()
Write-Host "WSL2 IP: $wslIP" -ForegroundColor Yellow

# Port cần forward
$port = 8081

# Xóa rule cũ nếu có
Write-Host "Xóa rule cũ (nếu có)..." -ForegroundColor Yellow
netsh interface portproxy delete v4tov4 listenport=$port listenaddress=0.0.0.0 2>$null

# Tạo rule mới
Write-Host "Tạo rule port forwarding..." -ForegroundColor Yellow
netsh interface portproxy add v4tov4 listenport=$port listenaddress=0.0.0.0 connectport=$port connectaddress=$wslIP

# Kiểm tra firewall
Write-Host "Kiểm tra firewall rule..." -ForegroundColor Yellow
$firewallRule = Get-NetFirewallRule -DisplayName "WSL2 Port $port" -ErrorAction SilentlyContinue
if (-not $firewallRule) {
    Write-Host "Tạo firewall rule..." -ForegroundColor Yellow
    New-NetFirewallRule -DisplayName "WSL2 Port $port" -Direction Inbound -LocalPort $port -Protocol TCP -Action Allow
} else {
    Write-Host "Firewall rule đã tồn tại" -ForegroundColor Green
}

# Hiển thị kết quả
Write-Host "`nPort forwarding đã được cấu hình!" -ForegroundColor Green
Write-Host "Truy cập từ bên ngoài: http://YOUR_WINDOWS_IP:8081/" -ForegroundColor Cyan
Write-Host "Truy cập từ Windows host: http://localhost:8081/" -ForegroundColor Cyan

# Hiển thị IP của Windows
$windowsIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*"} | Select-Object -First 1).IPAddress
if ($windowsIP) {
    Write-Host "Windows IP: $windowsIP" -ForegroundColor Yellow
    Write-Host "URL: http://$windowsIP`:8081/" -ForegroundColor Cyan
}

# Hiển thị các rule hiện tại
Write-Host "`nCác port forwarding hiện tại:" -ForegroundColor Yellow
netsh interface portproxy show all

