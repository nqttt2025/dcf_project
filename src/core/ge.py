import requests
from lxml import html
import sys
from io import StringIO

try:
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = StringIO()
    sys.stderr = StringIO()
    try:
        from vnstock import Vnstock
        HAS_VNSTOCK = True
    except ImportError:
        HAS_VNSTOCK = False
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
except:
    HAS_VNSTOCK = False
    sys.stdout = old_stdout
    sys.stderr = old_stderr

from ..utils.cache_manager import get_cache_manager

cache_manager = get_cache_manager()

FPT_VN_GE = {"2023": 19.6,
          "2024": 19.4,
          "2025": 22.4,
          "2026": 21.1,
          "2027": 15.4}


def get_growth_estimate(ticker):
    """
    Get growth estimate for a ticker using vnstock data.
    Returns the next 5 years (5-10 years) growth estimate based on:
    1. Current YoY net profit growth
    2. Current YoY revenue growth
    3. Historical average of recent growth rates (last 2 years)
    
    Calculation:
    - Net Profit Growth: 50% weight (most important)
    - Revenue Growth: 30% weight
    - Historical Average: 20% weight
    
    Result is capped between 2% and 50% to avoid outliers.
    """
    
    if not HAS_VNSTOCK:
        # Fallback to hardcoded value if vnstock is not available
        return float("16")
    
    try:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            stock = Vnstock().stock(symbol=ticker.upper(), source="VCI")
            # Get income statement and ratio summary for growth data
            income = stock.finance.income_statement()
            ratio_df = stock.company.ratio_summary()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        
        growth_rates = []
        
        # 1. Get current YoY net profit growth from ratio_summary
        net_profit_growth_yoy = ratio_df['net_profit_growth'].iloc[0] * 100
        growth_rates.append(net_profit_growth_yoy)
        
        # 2. Get current YoY revenue growth
        revenue_growth_yoy = ratio_df['revenue_growth'].iloc[0] * 100
        growth_rates.append(revenue_growth_yoy)
        
        # 3. Calculate average growth from last 2 years of income statement
        # income statement has column: 'Attribute to parent company YoY (%)'
        if 'Attribute to parent company YoY (%)' in income.columns:
            # Get last 8 quarters (~2 years)
            recent_growth_rates = income['Attribute to parent company YoY (%)'].head(8).values
            # Filter outliers (keep values between -50% and 200%)
            recent_growth_rates = [g for g in recent_growth_rates if g > -50 and g < 200]
            if len(recent_growth_rates) > 0:
                avg_growth = sum(recent_growth_rates) / len(recent_growth_rates)
                growth_rates.append(avg_growth)
        
        # Calculate weighted average
        if len(growth_rates) >= 2:
            # Weight: net profit growth 50%, revenue growth 30%, historical average 20%
            if len(growth_rates) == 3:
                growth_estimate = growth_rates[0] * 0.5 + growth_rates[1] * 0.3 + growth_rates[2] * 0.2
            else:
                growth_estimate = growth_rates[0] * 0.6 + growth_rates[1] * 0.4
        else:
            growth_estimate = growth_rates[0] if growth_rates else 16.0
        
        # Cap the growth estimate between 2% and 50%
        growth_estimate = max(2.0, min(50.0, growth_estimate))
        
        # Cache the growth estimate
        cache_manager.set_with_timestamp(ticker, "growth_estimate", growth_estimate)
        
        return float(growth_estimate)
    
    except Exception as e:
        # Fallback to hardcoded value if there's any error
        return float("16")


if __name__ == "__main__":
    ticker = "FPT"
    try:
        ge = get_growth_estimate(ticker)
        print(f"Growth Estimate for {ticker}: {ge:.2f}%")
    except Exception as e:
        print(f"Error: {e}")