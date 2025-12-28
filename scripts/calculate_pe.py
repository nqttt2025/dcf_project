#!/usr/bin/env python3
"""
Script tính toán PE (Price-to-Earnings) cho các mã cổ phiếu
Giúp xác định Base PE phù hợp cho từng mã
"""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.core.fcfs import price_board_stock, get_earnings_per_share_Diluted
from src.utils.logger import get_logger

logger = get_logger()

def calculate_current_pe(ticker):
    """
    Tính PE hiện tại của mã cổ phiếu
    
    Args:
        ticker: Mã cổ phiếu (ví dụ: 'VNM', 'FPT')
    
    Returns:
        float: PE ratio, hoặc None nếu không tính được
    """
    try:
        price = price_board_stock(ticker.upper())
        eps = get_earnings_per_share_Diluted(ticker.upper())
        
        if eps and eps > 0:
            pe = price / eps
            logger.info(f"{ticker}: Price={price:,.0f}, EPS={eps:,.2f}, PE={pe:.2f}")
            return pe
        else:
            logger.warning(f"{ticker}: EPS <= 0, không thể tính PE")
            return None
    except Exception as e:
        logger.error(f"Lỗi khi tính PE cho {ticker}: {e}")
        return None

def suggest_base_pe(ticker, industry=None, current_pe=None):
    """
    Đề xuất Base PE dựa trên ngành và PE hiện tại
    
    Args:
        ticker: Mã cổ phiếu
        industry: Ngành nghề (banking, real_estate, technology, consumer, energy, industrial, aviation)
        current_pe: PE hiện tại (nếu None sẽ tự tính)
    
    Returns:
        float: Base PE đề xuất
    """
    # Tính PE hiện tại nếu chưa có
    if current_pe is None:
        current_pe = calculate_current_pe(ticker)
    
    # Bảng đề xuất Base PE theo ngành
    industry_base_pe = {
        'banking': (7.0, 8.0),
        'real_estate': (8.0, 9.0),
        'technology': (9.0, 10.0),
        'consumer': (8.5, 9.0),
        'energy': (7.5, 8.5),
        'industrial': (8.0, 9.0),
        'aviation': (8.5, 9.5),
    }
    
    # Nếu có thông tin ngành
    if industry and industry.lower() in industry_base_pe:
        base_pe_min, base_pe_max = industry_base_pe[industry.lower()]
        
        # Nếu PE hiện tại quá cao (>30), dùng giá trị thấp hơn
        if current_pe and current_pe > 30:
            suggested = base_pe_min
        else:
            suggested = (base_pe_min + base_pe_max) / 2
        
        logger.info(f"{ticker} ({industry}): Đề xuất Base PE = {suggested:.2f}")
        return suggested
    
    # Mặc định
    logger.info(f"{ticker}: Sử dụng Base PE mặc định = 8.5")
    return 8.5

def analyze_vn30_stocks():
    """Phân tích PE cho các mã VN30"""
    
    # Danh sách mã VN30 theo ngành
    vn30_stocks = {
        'banking': ['VCB', 'BID', 'CTG', 'MBB', 'HDB', 'ACB', 'VIB', 'VPB', 'STB', 'TPB', 'SSB'],
        'real_estate': ['VHM', 'VIC', 'VRE', 'NVL', 'PDR', 'KDH'],
        'technology': ['FPT', 'SSI'],
        'consumer': ['VNM', 'MSN', 'MWG', 'SAB', 'PNJ'],
        'energy': ['GAS', 'PLX'],
        'industrial': ['HPG', 'REE', 'GVR'],
        'aviation': ['VJC'],
    }
    
    print("\n" + "="*80)
    print("PHÂN TÍCH PE CHO CÁC MÃ VN30")
    print("="*80)
    
    results = []
    
    for industry, tickers in vn30_stocks.items():
        print(f"\n--- {industry.upper()} ---")
        for ticker in tickers:
            try:
                pe = calculate_current_pe(ticker)
                base_pe = suggest_base_pe(ticker, industry, pe)
                
                results.append({
                    'ticker': ticker,
                    'industry': industry,
                    'current_pe': pe,
                    'suggested_base_pe': base_pe
                })
                
                if pe:
                    print(f"{ticker:5} | PE hiện tại: {pe:6.2f} | Base PE đề xuất: {base_pe:.2f}")
                else:
                    print(f"{ticker:5} | Không tính được PE")
            except Exception as e:
                print(f"{ticker:5} | Lỗi: {e}")
    
    # Tóm tắt
    print("\n" + "="*80)
    print("TÓM TẮT")
    print("="*80)
    print(f"{'Mã':<6} {'Ngành':<15} {'PE hiện tại':<12} {'Base PE đề xuất':<15}")
    print("-" * 80)
    
    for r in sorted(results, key=lambda x: x['ticker']):
        pe_str = f"{r['current_pe']:.2f}" if r['current_pe'] else "N/A"
        print(f"{r['ticker']:<6} {r['industry']:<15} {pe_str:<12} {r['suggested_base_pe']:.2f}")
    
    return results

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Tính PE cho một mã cụ thể
        ticker = sys.argv[1].upper()
        industry = sys.argv[2] if len(sys.argv) > 2 else None
        
        pe = calculate_current_pe(ticker)
        base_pe = suggest_base_pe(ticker, industry, pe)
        
        print(f"\n{ticker}:")
        print(f"  PE hiện tại: {pe:.2f}" if pe else "  Không tính được PE")
        print(f"  Base PE đề xuất: {base_pe:.2f}")
    else:
        # Phân tích tất cả VN30
        analyze_vn30_stocks()

