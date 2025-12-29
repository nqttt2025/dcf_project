# So sánh kết quả DCF trước và sau khi sửa FCF

## Vấn đề đã sửa

**Trước đây:** Code chỉ lấy Operating Cash Flow, không trừ Capital Expenditures  
**Bây giờ:** Code tính đúng Free Cash Flow = Operating Cash Flow - Capital Expenditures

## So sánh kết quả cho FPT

### Dữ liệu đầu vào

| Tham số | Giá trị cũ (SAI) | Giá trị mới (ĐÚNG) | Chênh lệch |
|---------|------------------|-------------------|------------|
| **Free Cash Flow** | 4,344,020,060,779 VND | 3,513,649,020,772 VND | -830,371,040,007 VND (-19.1%) |
| Operating Cash Flow | 4,344,020,060,779 VND | 4,344,020,060,779 VND | - |
| Capital Expenditures | **Không được trừ** | 830,371,040,007 VND | - |

### Kết quả định giá

| Phương pháp | Giá trị cũ | Giá trị mới | Chênh lệch |
|------------|-----------|-------------|------------|
| **DCF Fair Value** | 44,206 VND | **35,756 VND** | -8,450 VND (-19.1%) |
| Graham Fair Value | 42,675 VND | 42,675 VND | Không đổi |
| **Average Fair Value** | 43,440 VND | **39,215 VND** | -4,225 VND (-9.7%) |

### So với giá thị trường

**Giá thị trường:** 92,500 VND

| Metric | Giá trị cũ | Giá trị mới |
|--------|-----------|-------------|
| **DCF Fair Value** | 44,206 VND | 35,756 VND |
| **Upside/Downside** | -52.2% | **-61.3%** |
| **Giá thị trường cao hơn** | 109% | **159%** |

## Phân tích

### Tại sao DCF Fair Value giảm?

1. **FCF giảm 19.1%** (từ 4.34 nghìn tỷ xuống 3.51 nghìn tỷ VND)
2. **DCF Fair Value giảm tương ứng 19.1%** (từ 44,206 xuống 35,756 VND)
3. Điều này hợp lý vì:
   - FCF thấp hơn → Dòng tiền tự do ít hơn → Giá trị công ty thấp hơn
   - Đã tính đúng chi phí đầu tư vào tài sản cố định

### Ý nghĩa

**Với giá trị mới (35,756 VND):**
- Giá thị trường (92,500 VND) cao hơn giá trị công bằng **159%**
- Điều này cho thấy FPT đang được định giá rất cao trên thị trường
- Có thể do:
  - Kỳ vọng tăng trưởng cao trong tương lai
  - Yếu tố tâm lý và thanh khoản
  - Định giá dựa trên tiềm năng công nghệ

## Kết luận

✅ **FCF đã được tính ĐÚNG**  
✅ **DCF Fair Value chính xác hơn** (35,756 VND thay vì 44,206 VND)  
✅ **Kết quả phản ánh đúng giá trị nội tại** của công ty

**Khuyến nghị:**
- Chạy lại DCF analysis cho tất cả các mã đã phân tích trước đó
- Xóa cache cũ để lấy FCF mới: `rm data/cache/*_cache.json`
- Chạy lại: `make dcf-all`

---

**Lưu ý:** Giá trị DCF chỉ là một công cụ định giá, không phải lời khuyên đầu tư. Luôn kết hợp với phân tích cơ bản và đánh giá rủi ro.

