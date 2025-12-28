"""
Translation module - Hỗ trợ đa ngôn ngữ cho báo cáo
"""
from typing import Dict

# Translation dictionaries
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    'vi': {
        # Headers
        'DCF_VALUATION_ANALYSIS': 'PHÂN TÍCH ĐỊNH GIÁ DCF',
        'INPUT_PARAMETERS': 'THÔNG SỐ ĐẦU VÀO',
        'VALUATION_RESULTS': 'KẾT QUẢ ĐỊNH GIÁ',
        'UPSIDE_DOWNSIDE_ANALYSIS': 'PHÂN TÍCH TIỀM NĂNG TĂNG/GIẢM GIÁ',
        'VALUATION_METRICS': 'CHỈ SỐ ĐỊNH GIÁ',
        'YEARLY_FCF_GROWTH_FORECAST': 'DỰ BÁO TĂNG TRƯỞNG FCF THEO NĂM',
        'YEARLY_PRICE_FORECAST': 'DỰ BÁO GIÁ CỔ PHIẾU THEO NĂM',
        'YEARLY_PERFORMANCE_ANALYSIS': 'PHÂN TÍCH HIỆU SUẤT THEO NĂM',
        'GRAHAM_VALUATION_DETAILS': 'CHI TIẾT ĐỊNH GIÁ GRAHAM',
        
        # Labels
        'MARKET_PRICE': 'Giá thị trường',
        'EPS': 'EPS',
        'FREE_CASH_FLOW_TTM': 'Dòng tiền tự do (TTM)',
        'SHARES_OUTSTANDING': 'Số cổ phiếu đang lưu hành',
        'MARKET_CAP': 'Vốn hóa thị trường',
        'GROWTH_ESTIMATE': 'Tỷ lệ tăng trưởng ước tính',
        'FORECAST_TERM': 'Thời gian dự báo',
        'DISCOUNT_RATE': 'Tỷ lệ chiết khấu',
        'PERPETUAL_RATE': 'Tỷ lệ tăng trưởng vĩnh viễn',
        'YEARS': 'năm',
        
        'DCF_FAIR_VALUE': 'Giá trị công bằng DCF',
        'GRAHAM_FAIR_VALUE': 'Giá trị công bằng Graham',
        'AVERAGE_FAIR_VALUE': 'Giá trị công bằng trung bình',
        
        'DCF_UPSIDE_DOWNSIDE': 'DCF Tiềm năng tăng/giảm',
        'GRAHAM_UPSIDE_DOWNSIDE': 'Graham Tiềm năng tăng/giảm',
        'AVERAGE_UPSIDE_DOWNSIDE': 'Trung bình Tiềm năng tăng/giảm',
        
        'PE_RATIO': 'Tỷ số P/E',
        'PFCF_RATIO': 'Tỷ số P/FCF',
        'FCF_YIELD': 'Tỷ suất FCF',
        'EARNINGS_YIELD': 'Tỷ suất lợi nhuận',
        
        'YEAR': 'Năm',
        'FCF_VND': 'FCF (VND)',
        'YOY_GROWTH': 'Tăng trưởng YoY %',
        'CUMULATIVE_GROWTH': 'Tăng trưởng tích lũy %',
        'COMPANY_VALUE_VND': 'Giá trị công ty (VND)',
        'PRICE_PER_SHARE_VND': 'Giá/cổ phiếu (VND)',
        'PRICE_VND': 'Giá (VND)',
        'VS_CURRENT_PRICE': 'So với giá hiện tại',
        'MULTIPLIER': 'Số lần',
        
        'PERFORMANCE_DESCRIPTION': 'Hiệu suất tăng trưởng giá cổ phiếu theo từng năm',
        'CURRENT': 'Hiện tại',
        'BASE': 'Cơ sở',
        'BASE_100_PCT': 'Cơ sở (100%)',
        
        'EXPLANATION': 'Giải thích',
        'YOY_GROWTH_EXPLANATION': 'YoY Growth %: Tăng trưởng năm-over-year (Năm 1 so với giá hiện tại)',
        'VS_CURRENT_EXPLANATION': 'vs Current Price: % thay đổi so với giá hiện tại',
        'MULTIPLIER_EXPLANATION': 'Multiplier: Số lần tăng giá trị so với giá hiện tại (ví dụ: 1.53x = tăng 53%)',
        
        'GRAHAM_FORMULA': 'Công thức',
        'GRAHAM_FORMULA_DETAIL': 'EPS × (Base PE + 2 × Growth Rate)',
        'GRAHAM_CALCULATION': 'Tính toán',
        
        'ANALYSIS_DATE': 'Ngày phân tích',
    },
    'en': {
        # Headers
        'DCF_VALUATION_ANALYSIS': 'DCF VALUATION ANALYSIS',
        'INPUT_PARAMETERS': 'INPUT PARAMETERS',
        'VALUATION_RESULTS': 'VALUATION RESULTS',
        'UPSIDE_DOWNSIDE_ANALYSIS': 'UPSIDE/DOWNSIDE ANALYSIS',
        'VALUATION_METRICS': 'VALUATION METRICS',
        'YEARLY_FCF_GROWTH_FORECAST': 'YEARLY FCF GROWTH FORECAST',
        'YEARLY_PRICE_FORECAST': 'YEARLY PRICE FORECAST (Based on DCF Model)',
        'YEARLY_PERFORMANCE_ANALYSIS': 'YEARLY PERFORMANCE ANALYSIS',
        'GRAHAM_VALUATION_DETAILS': 'GRAHAM VALUATION DETAILS',
        
        # Labels
        'MARKET_PRICE': 'Market Price',
        'EPS': 'EPS',
        'FREE_CASH_FLOW_TTM': 'Free Cash Flow (TTM)',
        'SHARES_OUTSTANDING': 'Shares Outstanding',
        'MARKET_CAP': 'Market Cap',
        'GROWTH_ESTIMATE': 'Growth Estimate',
        'FORECAST_TERM': 'Forecast Term',
        'DISCOUNT_RATE': 'Discount Rate',
        'PERPETUAL_RATE': 'Perpetual Rate',
        'YEARS': 'years',
        
        'DCF_FAIR_VALUE': 'DCF Fair Value',
        'GRAHAM_FAIR_VALUE': 'Graham Fair Value',
        'AVERAGE_FAIR_VALUE': 'Average Fair Value',
        
        'DCF_UPSIDE_DOWNSIDE': 'DCF Upside/Downside',
        'GRAHAM_UPSIDE_DOWNSIDE': 'Graham Upside/Downside',
        'AVERAGE_UPSIDE_DOWNSIDE': 'Average Upside/Downside',
        
        'PE_RATIO': 'P/E Ratio',
        'PFCF_RATIO': 'P/FCF Ratio',
        'FCF_YIELD': 'FCF Yield',
        'EARNINGS_YIELD': 'Earnings Yield',
        
        'YEAR': 'Year',
        'FCF_VND': 'FCF (VND)',
        'YOY_GROWTH': 'YoY Growth %',
        'CUMULATIVE_GROWTH': 'Cumulative Growth %',
        'COMPANY_VALUE_VND': 'Company Value (VND)',
        'PRICE_PER_SHARE_VND': 'Price/Share (VND)',
        'PRICE_VND': 'Price (VND)',
        'VS_CURRENT_PRICE': 'vs Current Price',
        'MULTIPLIER': 'Multiplier',
        
        'PERFORMANCE_DESCRIPTION': 'Stock price growth performance by year',
        'CURRENT': 'Current',
        'BASE': 'Base',
        'BASE_100_PCT': 'Base (100%)',
        
        'EXPLANATION': 'Explanation',
        'YOY_GROWTH_EXPLANATION': 'YoY Growth %: Year-over-year growth (Year 1 vs current price)',
        'VS_CURRENT_EXPLANATION': 'vs Current Price: % change vs current price',
        'MULTIPLIER_EXPLANATION': 'Multiplier: Value multiplier vs current price (e.g., 1.53x = 53% increase)',
        
        'GRAHAM_FORMULA': 'Formula',
        'GRAHAM_FORMULA_DETAIL': 'EPS × (Base PE + 2 × Growth Rate)',
        'GRAHAM_CALCULATION': 'Calculation',
        
        'ANALYSIS_DATE': 'Analysis Date',
    }
}


def get_translation(language: str = 'en', key: str = '') -> str:
    """
    Lấy bản dịch theo ngôn ngữ
    
    Args:
        language: Ngôn ngữ ('vi' hoặc 'en')
        key: Key của text cần dịch
    
    Returns:
        Text đã dịch hoặc key nếu không tìm thấy
    """
    lang = language.lower() if language else 'en'
    if lang not in TRANSLATIONS:
        lang = 'en'
    
    return TRANSLATIONS.get(lang, {}).get(key, key)


def get_language_from_config(config) -> str:
    """
    Lấy ngôn ngữ từ config file
    
    Args:
        config: ConfigParser object
    
    Returns:
        'vi' hoặc 'en' (mặc định 'vi')
    """
    try:
        if 'report' in config:
            language = config.get('report', 'language', fallback='vi')
            return language.lower() if language.lower() in ['vi', 'en'] else 'vi'
    except:
        pass
    
    return 'vi'  # Mặc định tiếng Việt

