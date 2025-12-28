# VN30 Configuration Files

Thư mục này chứa các file cấu hình cho tất cả 30 mã cổ phiếu trong rổ VN30.

## Danh sách các mã VN30

### Ngân hàng (Banking)
1. **VCB** - Ngân hàng TMCP Ngoại thương Việt Nam (Vietcombank)
2. **BID** - Ngân hàng TMCP Đầu tư và Phát triển Việt Nam (BIDV)
3. **CTG** - Ngân hàng TMCP Công Thương Việt Nam (Vietinbank)
4. **MBB** - Ngân hàng TMCP Quân Đội (MB Bank)
5. **HDB** - Ngân hàng TMCP Phát triển Thành phố Hồ Chí Minh (HDBank)
6. **ACB** - Ngân hàng TMCP Á Châu (Asia Commercial Bank)
7. **VIB** - Ngân hàng TMCP Quốc tế Việt Nam (Vietnam International Bank)
8. **VPB** - Ngân hàng TMCP Việt Nam Thịnh Vượng (VPBank)
9. **STB** - Ngân hàng TMCP Sài Gòn Thương Tín (Sacombank)
10. **TPB** - Ngân hàng TMCP Tiên Phong (Tien Phong Bank)
11. **SSB** - Ngân hàng TMCP Đông Nam Á (Southeast Asia Bank)

### Bất động sản (Real Estate)
12. **VHM** - Công ty CP Vinhomes
13. **VIC** - Tập đoàn Vingroup
14. **VRE** - Công ty CP Vincom Retail
15. **NVL** - Công ty CP Tập đoàn Đầu tư Địa ốc No Va (Novaland)
16. **PDR** - Công ty CP Phát triển Bất động sản Phát Đạt
17. **KDH** - Công ty CP Đầu tư và Kinh doanh Nhà Khang Điền

### Công nghệ & Viễn thông (Technology & Telecom)
18. **FPT** - Công ty CP FPT
19. **SSI** - Công ty CP Chứng khoán SSI

### Tiêu dùng (Consumer)
20. **VNM** - Công ty CP Sữa Việt Nam (Vinamilk)
21. **MSN** - Công ty CP Tập đoàn Masan
22. **MWG** - Công ty CP Đầu tư Thế giới Di động (Mobile World)
23. **SAB** - Tổng Công ty CP Bia - Rượu - Nước giải khát Sài Gòn (Sabeco)
24. **PNJ** - Công ty CP Vàng bạc Đá quý Phú Nhuận

### Năng lượng (Energy)
25. **GAS** - Tổng Công ty Khí Việt Nam - CTCP (PetroVietnam Gas)
26. **PLX** - Tập đoàn Xăng dầu Việt Nam (Petrolimex)

### Công nghiệp (Industrial)
27. **REE** - Công ty CP Cơ điện lạnh
28. **HPG** - Công ty CP Tập đoàn Hòa Phát (Hoa Phat Group)
29. **GVR** - Tập đoàn Công nghiệp Cao su Việt Nam

### Hàng không (Aviation)
30. **VJC** - Công ty CP Hàng không VietJet

## Cấu trúc file config

Mỗi file `.cfg` có cấu trúc như sau:

```ini
[dcf]
yr = 5          # Số năm dự báo
dr = 10         # Tỷ lệ chiết khấu (%)
pr = 2.5        # Tỷ lệ tăng trưởng vĩnh viễn (%)

[graham]
base_pe = 8.5   # Hệ số PE cơ bản
growth_multiplier = 2  # Hệ số nhân tăng trưởng

[ticker]
ticker = XXX    # Mã cổ phiếu

[data_source]
source = VCI    # Nguồn dữ liệu
```

## Sử dụng

Để chạy phân tích DCF cho một mã cổ phiếu:

```bash
python3 run_dcf.py config/VCB.cfg
```

Hoặc sử dụng trong code:

```python
from src.core.dcf_calculator import calculate_dcf_from_config

result = await calculate_dcf_from_config('config/VCB.cfg')
```

## Tùy chỉnh tham số

Bạn có thể điều chỉnh các tham số DCF cho từng mã cổ phiếu dựa trên:
- **dr (Discount Rate)**: Tỷ lệ chiết khấu phù hợp với mức độ rủi ro của công ty
  - Ngân hàng: 10-12%
  - Bất động sản: 11-13%
  - Công nghệ: 9-11%
  - Tiêu dùng: 10-11%
  - Năng lượng: 10-12%

- **yr (Years)**: Số năm dự báo (thường 5-7 năm)
- **pr (Perpetual Rate)**: Tỷ lệ tăng trưởng vĩnh viễn (thường 2-3%)

## Ghi chú

- Tất cả các file config sử dụng giá trị mặc định ban đầu
- Bạn có thể tùy chỉnh từng file theo đặc thù của từng công ty
- File config có thể được cập nhật định kỳ khi có thay đổi về cấu trúc rổ VN30

