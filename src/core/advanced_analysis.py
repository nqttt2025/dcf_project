"""
Advanced Analysis Module - Phân tích chuyên sâu cho DCF valuation
"""
from typing import Dict, List, Tuple
import math


def calculate_yearly_growth(forecast: List[float]) -> List[Tuple[float, float]]:
    """
    Tính tỷ lệ tăng trưởng theo từng năm
    
    Args:
        forecast: Danh sách FCF forecast (bao gồm terminal value ở cuối)
    
    Returns:
        List các tuple (yearly_growth, cumulative_growth) theo % cho mỗi năm
        Year 1 sẽ có yearly_growth = 0 (base year)
    """
    growth_data = []
    base_fcf = forecast[0] if forecast else 0
    
    for i in range(len(forecast) - 1):  # Bỏ qua terminal value
        if i == 0:
            # Year 1: base year, no growth
            growth_data.append((0.0, 0.0))
        else:
            # Yearly growth từ năm trước
            if forecast[i-1] > 0:
                yearly_growth = ((forecast[i] - forecast[i-1]) / forecast[i-1]) * 100
            else:
                yearly_growth = 0.0
            
            # Cumulative growth từ base year
            if base_fcf > 0:
                cumulative_growth = ((forecast[i] - base_fcf) / base_fcf) * 100
            else:
                cumulative_growth = 0.0
            
            growth_data.append((yearly_growth, cumulative_growth))
    
    return growth_data


def calculate_yearly_price_forecast(
    forecast: List[float],
    shares: float,
    discount_rate: float,
    years: int,
    current_price: float = 0
) -> List[Dict[str, float]]:
    """
    Tính giá cổ phiếu dự kiến sau mỗi năm dựa trên DCF model
    
    Args:
        forecast: Danh sách FCF forecast
        shares: Số cổ phiếu đang lưu hành
        discount_rate: Tỷ lệ chiết khấu (%)
        years: Số năm forecast
        current_price: Giá cổ phiếu hiện tại (để tính % thay đổi)
    
    Returns:
        List các dict chứa thông tin giá cổ phiếu theo từng năm
    """
    yearly_prices = []
    
    # Tính giá trị hiện tại của các năm còn lại từ mỗi năm
    for year in range(years):
        # Lấy các FCF từ năm hiện tại đến cuối
        remaining_forecast = forecast[year:]
        
        # Tính discount factors từ năm hiện tại
        discount_factors = [
            1 / (1 + (discount_rate / 100)) ** (i + 1)
            for i in range(len(remaining_forecast) - 1)
        ]
        
        # Tính present values
        pvs = [
            f * d for f, d in zip(remaining_forecast[:-1], discount_factors)
        ]
        # Terminal value
        pvs.append(discount_factors[-1] * remaining_forecast[-1])
        
        # Tổng giá trị công ty tại năm đó
        total_value = sum(pvs)
        
        # Giá cổ phiếu
        price_per_share = total_value / shares
        
        # Tính % thay đổi và multiplier so với giá hiện tại
        if current_price > 0:
            price_change_pct = ((price_per_share - current_price) / current_price) * 100
            price_multiplier = price_per_share / current_price
        else:
            price_change_pct = 0.0
            price_multiplier = 1.0
        
        # Tính % tăng trưởng so với năm trước
        if year == 0:
            # Year 1: so với giá hiện tại
            if current_price > 0:
                year_over_year_growth = price_change_pct
            else:
                year_over_year_growth = 0.0
        else:
            # So với năm trước
            prev_price = yearly_prices[year - 1]['price_per_share']
            if prev_price > 0:
                year_over_year_growth = ((price_per_share - prev_price) / prev_price) * 100
            else:
                year_over_year_growth = 0.0
        
        yearly_prices.append({
            'year': year + 1,
            'fcf': forecast[year],
            'company_value': total_value,
            'price_per_share': price_per_share,
            'price_change_pct': price_change_pct,
            'price_multiplier': price_multiplier,
            'year_over_year_growth_pct': year_over_year_growth
        })
    
    return yearly_prices


def calculate_valuation_metrics(
    price: float,
    eps: float,
    fcf: float,
    shares: float,
    market_cap: float,
    industry_pe: float = None
) -> Dict[str, float]:
    """
    Tính các chỉ số định giá
    
    Args:
        price: Giá cổ phiếu hiện tại
        eps: Earnings per share
        fcf: Free Cash Flow (TTM)
        shares: Số cổ phiếu đang lưu hành
        market_cap: Vốn hóa thị trường
        industry_pe: PE trung bình của ngành (optional)
    
    Returns:
        Dict chứa các chỉ số định giá
    """
    metrics = {}
    
    # P/E Ratio của cổ phiếu
    if eps > 0:
        metrics['pe_ratio'] = price / eps
    else:
        metrics['pe_ratio'] = None
    
    # P/E Ratio của ngành
    metrics['industry_pe'] = industry_pe
    
    # P/FCF Ratio (Price to Free Cash Flow)
    fcf_per_share = fcf / shares if shares > 0 else 0
    if fcf_per_share > 0:
        metrics['pfcf_ratio'] = price / fcf_per_share
    else:
        metrics['pfcf_ratio'] = None
    
    # FCF Yield
    if market_cap > 0:
        metrics['fcf_yield'] = (fcf / market_cap) * 100
    else:
        metrics['fcf_yield'] = None
    
    # Earnings Yield
    if eps > 0:
        metrics['earnings_yield'] = (eps / price) * 100 if price > 0 else None
    else:
        metrics['earnings_yield'] = None
    
    return metrics


def calculate_upside_downside(
    current_price: float,
    dcf_fair_value: float,
    graham_fair_value: float = None,
    average_fair_value: float = None
) -> Dict[str, float]:
    """
    Tính upside/downside potential
    
    Args:
        current_price: Giá hiện tại
        dcf_fair_value: Giá trị công bằng theo DCF
        graham_fair_value: Giá trị công bằng theo Graham (optional)
        average_fair_value: Giá trị công bằng trung bình (optional)
    
    Returns:
        Dict chứa upside/downside percentages
    """
    results = {}
    
    if current_price > 0:
        # DCF Upside/Downside
        results['dcf_upside_pct'] = ((dcf_fair_value - current_price) / current_price) * 100
        
        # Graham Upside/Downside
        if graham_fair_value:
            results['graham_upside_pct'] = ((graham_fair_value - current_price) / current_price) * 100
        
        # Average Upside/Downside
        if average_fair_value:
            results['average_upside_pct'] = ((average_fair_value - current_price) / current_price) * 100
    
    return results


def generate_advanced_analysis(
    result: Dict,
    dcf_result: Dict
) -> Dict:
    """
    Tạo phân tích chuyên sâu từ kết quả DCF
    
    Args:
        result: Kết quả từ calculate() method
        dcf_result: Kết quả từ calculate_dcf() method
    
    Returns:
        Dict chứa các phân tích chuyên sâu
    """
    forecast = dcf_result.get('forecast', [])
    years = result.get('dcf_params', {}).get('yr', 5)
    discount_rate = result.get('dcf_params', {}).get('dr', 10)
    
    # Tính tăng trưởng theo từng năm
    growth_rates = calculate_yearly_growth(forecast)
    
    # Tính giá cổ phiếu theo từng năm (bao gồm current_price để tính % thay đổi)
    yearly_prices = calculate_yearly_price_forecast(
        forecast,
        result.get('shares', 1),
        discount_rate,
        years,
        result.get('price', 0)  # Thêm current_price để tính % thay đổi và multiplier
    )
    
    # Tính các chỉ số định giá (bao gồm industry PE)
    valuation_metrics = calculate_valuation_metrics(
        result.get('price', 0),
        result.get('eps', 0),
        result.get('fcf', 0) if 'fcf' in result else 0,
        result.get('shares', 1),
        result.get('market_cap', 0),
        result.get('industry_pe')  # Industry PE
    )
    
    # Tính upside/downside
    upside_downside = calculate_upside_downside(
        result.get('price', 0),
        result.get('dcf_fair_value', 0),
        result.get('graham_fair_value'),
        result.get('average_fair_value')
    )
    
    return {
        'yearly_growth': growth_rates,
        'yearly_price_forecast': yearly_prices,
        'valuation_metrics': valuation_metrics,
        'upside_downside': upside_downside,
        'forecast_details': {
            'fcf_forecast': forecast[:-1],  # Bỏ terminal value
            'terminal_value': forecast[-1] if forecast else 0,
            'present_values': dcf_result.get('pvs', [])
        }
    }

