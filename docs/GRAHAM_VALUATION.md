# Phương pháp định giá Graham (Graham Valuation)

## Graham là gì?

**Graham** là phương pháp định giá cổ phiếu được phát triển bởi **Benjamin Graham** (1894-1976), được mệnh danh là "cha đẻ của đầu tư giá trị" (value investing). Ông là thầy của Warren Buffett và là tác giả của cuốn sách nổi tiếng "The Intelligent Investor".

## Công thức Graham trong dự án

Trong dự án này, chúng ta sử dụng công thức Graham cải tiến để định giá cổ phiếu:

```
Graham Fair Value = EPS × (Base PE + Growth Multiplier × Growth Rate)
```

### Công thức chi tiết:

```
Fair Value = EPS × (8.5 + 2 × Growth Rate %)
```

Trong đó:
- **EPS** (Earnings Per Share): Lợi nhuận trên mỗi cổ phiếu
- **Base PE = 8.5**: Hệ số PE cơ bản (từ sách "The Intelligent Investor", trang 295)
- **Growth Multiplier = 2**: Hệ số nhân cho tốc độ tăng trưởng
- **Growth Rate**: Tốc độ tăng trưởng kỳ vọng (%)

## Các tham số trong config file

Trong file config (ví dụ: `FPT.cfg`), bạn sẽ thấy:

```ini
[graham]
base_pe = 8.5           # Hệ số PE cơ bản
growth_multiplier = 2   # Hệ số nhân tăng trưởng
```

### Giải thích các tham số:

1. **base_pe (8.5)**: 
   - Đây là hệ số PE cơ bản cho một công ty không tăng trưởng
   - Giá trị 8.5 được Benjamin Graham đề xuất trong "The Intelligent Investor"
   - Đại diện cho mức định giá hợp lý cho một công ty ổn định

2. **growth_multiplier (2)**: 
   - Hệ số này nhân với tốc độ tăng trưởng để điều chỉnh giá trị
   - Công ty tăng trưởng 10%/năm sẽ được cộng thêm: 2 × 10 = 20 điểm PE
   - PE hợp lý = 8.5 + 20 = 28.5

## Ví dụ tính toán

Giả sử một cổ phiếu có:
- **EPS** = 1,000 VND
- **Growth Rate** = 10% mỗi năm
- **Base PE** = 8.5
- **Growth Multiplier** = 2

**Tính toán:**
```
Graham Fair Value = 1,000 × (8.5 + 2 × 10)
                  = 1,000 × (8.5 + 20)
                  = 1,000 × 28.5
                  = 28,500 VND
```

## Cách sử dụng trong dự án

### 1. Trong code Python:

```python
from src.core.dcf_calculator import calculate_dcf_from_config

result = await calculate_dcf_from_config('config/FPT.cfg')

print(f"DCF Fair Value: {result['dcf_fair_value']:,.2f}")
print(f"Graham Fair Value: {result['graham_fair_value']:,.2f}")
print(f"Average Fair Value: {result['average_fair_value']:,.2f}")
```

### 2. Kết quả trong file JSON:

```json
{
  "ticker": "VNM",
  "dcf_fair_value": 19435.99,
  "graham_fair_value": 23110.72,
  "average_fair_value": 21273.36
}
```

### 3. Cách dự án sử dụng:

Dự án tính toán **cả DCF và Graham**, sau đó lấy **trung bình** của hai giá trị:

```
Average Fair Value = (DCF Fair Value + Graham Fair Value) / 2
```

## So sánh DCF vs Graham

| Phương pháp | Ưu điểm | Nhược điểm |
|------------|---------|------------|
| **DCF** | - Chi tiết, dựa trên dòng tiền<br>- Phù hợp cho công ty có dòng tiền ổn định | - Phức tạp, cần nhiều giả định<br>- Nhạy cảm với thay đổi tham số |
| **Graham** | - Đơn giản, dễ hiểu<br>- Nhanh chóng<br>- Phù hợp cho công ty có EPS ổn định | - Không xét đến dòng tiền<br>- Có thể không chính xác cho công ty tăng trưởng cao |

## Khi nào sử dụng Graham?

✅ **Phù hợp khi:**
- Công ty có EPS ổn định và dương
- Cần định giá nhanh
- Công ty có lịch sử tăng trưởng đều đặn
- Muốn có góc nhìn bổ sung cho DCF

❌ **Không phù hợp khi:**
- Công ty có EPS âm hoặc không ổn định
- Công ty mới thành lập, chưa có lịch sử
- Công ty có biến động lớn về lợi nhuận

## Tùy chỉnh tham số Graham

Bạn có thể điều chỉnh các tham số trong file config:

```ini
[graham]
base_pe = 8.5           # Có thể điều chỉnh 7-10 tùy ngành
growth_multiplier = 2   # Có thể điều chỉnh 1.5-2.5
```

### Gợi ý điều chỉnh:

- **Ngân hàng**: base_pe = 7-8 (rủi ro cao hơn)
- **Tiêu dùng**: base_pe = 8.5-9 (ổn định)
- **Công nghệ**: base_pe = 9-10 (tăng trưởng cao)
- **Năng lượng**: base_pe = 7-8.5 (biến động)

## Tài liệu tham khảo

- **"The Intelligent Investor"** - Benjamin Graham (1949)
- **Trang 295**: Công thức định giá cơ bản
- **"Security Analysis"** - Benjamin Graham & David Dodd (1934)

## Lưu ý quan trọng

⚠️ **Graham valuation chỉ là một công cụ tham khảo**, không phải lời khuyên đầu tư. Luôn kết hợp với:
- Phân tích cơ bản (fundamental analysis)
- Phân tích kỹ thuật (technical analysis)
- Hiểu biết về ngành và công ty
- Đánh giá rủi ro

---

**Tóm lại**: Graham là phương pháp định giá đơn giản, nhanh chóng dựa trên EPS và tốc độ tăng trưởng, giúp bạn có góc nhìn bổ sung cho phương pháp DCF phức tạp hơn.

