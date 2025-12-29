# Hướng dẫn sử dụng Stockanalysis.com Scraper

## Tổng quan

Module `stockanalysis_scraper.py` được tạo để lấy dữ liệu Free Cash Flow từ stockanalysis.com, cung cấp giá trị **TTM (Trailing Twelve Months)** thay vì chỉ một quý như vnstock.

## Vấn đề hiện tại

**Stockanalysis.com đang chặn scraping** với Cloudflare protection (403 Forbidden). Điều này có nghĩa là:

- ❌ Không thể scrape trực tiếp bằng `requests` hoặc `cloudscraper`
- ❌ API endpoints cũng bị chặn
- ⚠️ Cần giải pháp khác

## Giải pháp

### Tùy chọn 1: Sử dụng Selenium (Khuyến nghị)

Selenium có thể bypass Cloudflare protection bằng cách sử dụng trình duyệt thật:

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_fcf_with_selenium(ticker):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Chạy không hiển thị browser
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    url = f"https://stockanalysis.com/quote/hose/{ticker}/financials/cash-flow-statement/"
    driver.get(url)
    
    # Đợi trang load
    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.presence_of_element_located((By.XPATH, "//tr[contains(.,'Free Cash Flow')]")))
    
    # Parse dữ liệu
    # ...
    
    driver.quit()
```

**Yêu cầu:**
- Cài đặt Selenium: `pip install selenium`
- Cài đặt ChromeDriver hoặc GeckoDriver

### Tùy chọn 2: Sử dụng API của bên thứ ba

Có thể sử dụng các dịch vụ API như:
- **RapidAPI** có thể có wrapper cho stockanalysis.com
- **ScraperAPI** hoặc **ScrapingBee** để bypass Cloudflare

### Tùy chọn 3: Tính TTM từ vnstock (Hiện tại)

**Giải pháp tốt nhất hiện tại:** Tính TTM bằng cách cộng dồn 4 quý gần nhất từ vnstock:

```python
def get_free_cash_flow_ttm(ticker):
    """
    Tính FCF TTM từ vnstock bằng cách cộng 4 quý gần nhất
    """
    stock = Vnstock().stock(symbol=ticker.upper(), source="VCI")
    cash_flow_df = stock.finance.cash_flow()
    
    ocf_col = 'Net cash inflows/outflows from operating activities'
    capex_col = 'Purchase of fixed assets'
    
    ttm_ocf = 0
    ttm_capex = 0
    quarters_counted = 0
    
    for idx in range(len(cash_flow_df)):
        row = cash_flow_df.iloc[idx]
        
        ocf_val = row.get(ocf_col, 0)
        capex_val = row.get(capex_col, 0)
        
        if pd.notna(ocf_val) and ocf_val != 0:
            try:
                ocf_float = float(ocf_val)
                capex_float = abs(float(capex_val)) if capex_val != 0 else 0
                
                if ocf_float > 0 and quarters_counted < 4:
                    ttm_ocf += ocf_float
                    ttm_capex += capex_float
                    quarters_counted += 1
                    
                    if quarters_counted == 4:
                        break
            except (ValueError, TypeError):
                continue
    
    ttm_fcf = ttm_ocf - ttm_capex
    return ttm_fcf
```

## So sánh các phương pháp

| Phương pháp | Ưu điểm | Nhược điểm | Khuyến nghị |
|------------|---------|------------|-------------|
| **stockanalysis.com scraping** | Dữ liệu TTM chuẩn, đã chuẩn hóa | Bị chặn bởi Cloudflare | ❌ Không khả thi |
| **Selenium** | Bypass được Cloudflare | Chậm, cần browser, phức tạp | ⚠️ Có thể thử |
| **Tính TTM từ vnstock** | Đơn giản, không bị chặn | Có thể khác với stockanalysis.com | ✅ **Khuyến nghị** |

## Khuyến nghị

**Hiện tại, nên sử dụng phương pháp tính TTM từ vnstock** vì:

1. ✅ Không bị chặn
2. ✅ Dữ liệu từ nguồn chính thức (VCI)
3. ✅ Có thể tính được TTM bằng cách cộng 4 quý
4. ✅ Đơn giản và ổn định

**Nếu muốn dùng stockanalysis.com:**

1. Cài đặt Selenium và ChromeDriver
2. Cập nhật `stockanalysis_scraper.py` để sử dụng Selenium
3. Hoặc sử dụng dịch vụ API của bên thứ ba

## Code mẫu để tính TTM từ vnstock

Xem file `docs/FCF_DISCREPANCY_EXPLANATION.md` để có code mẫu đầy đủ.

## Tài liệu tham khảo

- [stockanalysis.com FPT Cash Flow](https://stockanalysis.com/quote/hose/FPT/financials/cash-flow-statement/)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [Cloudflare Bypass Guide](https://github.com/VeNoMouS/cloudscraper)

