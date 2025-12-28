"""
Results Manager - Lưu lại kết quả DCF cho từng mã cổ phiếu
"""

import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from .translations import get_translation

class ResultManager:
    """
    Quản lý lưu trữ kết quả DCF valuation
    Format: data/results/{stock_name}_result.json
            data/results/{stock_name}_result.text
    """

    def __init__(self):
        # Get project root (go up 2 levels from src/utils/)
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.results_dir = os.path.join(self.project_root, 'data', 'results')
        os.makedirs(self.results_dir, exist_ok=True)

    def save_result(self, stock_name, valuation_result):
        """
        Lưu kết quả DCF cho một mã cổ phiếu

        Args:
            stock_name: Mã cổ phiếu (ví dụ: FPT, VNM, BID)
            valuation_result: Dictionary chứa kết quả định giá

        Returns:
            Tuple của (đường dẫn JSON, đường dẫn LOG)
        """
        stock_name_lower = stock_name.lower()
        result_file = os.path.join(self.results_dir, f'{stock_name_lower}_result.json')
        log_file = os.path.join(self.results_dir, f'{stock_name_lower}_result.text')

        # Thêm timestamp
        result_with_timestamp = valuation_result.copy()
        result_with_timestamp['saved_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        result_with_timestamp['stock_name'] = stock_name

        # Chuyển đổi các giá trị không thể serialize
        result_with_timestamp = self._serialize_result(result_with_timestamp)

        # Lưu lên file JSON
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_with_timestamp, f, indent=2, ensure_ascii=False)

        # Lưu lên file LOG
        self._save_as_log(log_file, result_with_timestamp)

        return result_file, log_file

    def _save_as_log(self, log_file, data):
        """
        Lưu kết quả dưới dạng text log file với phân tích chuyên sâu

        Args:
            log_file: Đường dẫn file log
            data: Dictionary chứa kết quả
        """
        # Lấy ngôn ngữ từ data hoặc mặc định là tiếng Việt
        language = data.get('report_language', 'vi')
        if language.lower() not in ['vi', 'en']:
            language = 'vi'
        
        # Helper function để lấy translation
        def t(key: str) -> str:
            return get_translation(language, key)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write(f"{t('DCF_VALUATION_ANALYSIS')} - {data.get('ticker', 'N/A').upper()}\n")
            f.write("=" * 80 + "\n\n")
            
            # Main valuation parameters
            f.write(f"{t('INPUT_PARAMETERS')}\n")
            f.write("-" * 80 + "\n")
            if 'price' in data:
                f.write(f"{t('MARKET_PRICE')}: {data['price']:,.2f} VND\n")
            if 'eps' in data:
                f.write(f"{t('EPS')}: {data['eps']:,.2f} VND\n")
            if 'fcf' in data:
                f.write(f"{t('FREE_CASH_FLOW_TTM')}: {data['fcf']:,.0f} VND\n")
            if 'shares' in data:
                f.write(f"{t('SHARES_OUTSTANDING')}: {data['shares']:,.0f}\n")
            if 'market_cap' in data:
                f.write(f"{t('MARKET_CAP')}: {data['market_cap']:,.0f} VND\n")
            if 'growth_estimate' in data:
                f.write(f"{t('GROWTH_ESTIMATE')}: {data['growth_estimate']:.2f}%\n")
            if 'dcf_params' in data and isinstance(data['dcf_params'], dict):
                years = data['dcf_params'].get('yr', 5)
                f.write(f"{t('FORECAST_TERM')}: {years} {t('YEARS')}\n")
                f.write(f"{t('DISCOUNT_RATE')}: {data['dcf_params'].get('dr', 10)}%\n")
                f.write(f"{t('PERPETUAL_RATE')}: {data['dcf_params'].get('pr', 2.5)}%\n")
            f.write("\n")
            
            # Valuation Results
            f.write("=" * 80 + "\n")
            f.write(f"{t('VALUATION_RESULTS')}\n")
            f.write("=" * 80 + "\n")
            f.write(f"{t('DCF_FAIR_VALUE')}: {data.get('dcf_fair_value', 'N/A'):,.2f} VND\n")
            if data.get('graham_fair_value'):
                f.write(f"{t('GRAHAM_FAIR_VALUE')}: {data['graham_fair_value']:,.2f} VND\n")
                f.write(f"{t('AVERAGE_FAIR_VALUE')}: {data.get('average_fair_value', 'N/A'):,.2f} VND\n")
            f.write("\n")
            
            # Upside/Downside Analysis
            advanced = data.get('advanced_analysis', {})
            upside = advanced.get('upside_downside', {})
            if upside:
                f.write(f"{t('UPSIDE_DOWNSIDE_ANALYSIS')}\n")
                f.write("-" * 80 + "\n")
                if 'dcf_upside_pct' in upside:
                    f.write(f"{t('DCF_UPSIDE_DOWNSIDE')}: {upside['dcf_upside_pct']:+.2f}%\n")
                if 'graham_upside_pct' in upside:
                    f.write(f"{t('GRAHAM_UPSIDE_DOWNSIDE')}: {upside['graham_upside_pct']:+.2f}%\n")
                if 'average_upside_pct' in upside:
                    f.write(f"{t('AVERAGE_UPSIDE_DOWNSIDE')}: {upside['average_upside_pct']:+.2f}%\n")
                f.write("\n")
            
            # Valuation Metrics
            metrics = advanced.get('valuation_metrics', {})
            if metrics:
                f.write(f"{t('VALUATION_METRICS')}\n")
                f.write("-" * 80 + "\n")
                if metrics.get('pe_ratio'):
                    f.write(f"{t('PE_RATIO')}: {metrics['pe_ratio']:.2f}\n")
                if metrics.get('pfcf_ratio'):
                    f.write(f"{t('PFCF_RATIO')}: {metrics['pfcf_ratio']:.2f}\n")
                if metrics.get('fcf_yield'):
                    f.write(f"{t('FCF_YIELD')}: {metrics['fcf_yield']:.2f}%\n")
                if metrics.get('earnings_yield'):
                    f.write(f"{t('EARNINGS_YIELD')}: {metrics['earnings_yield']:.2f}%\n")
                f.write("\n")
            
            # Yearly FCF Growth Forecast
            growth_data = advanced.get('yearly_growth', [])
            forecast_details = advanced.get('forecast_details', {})
            fcf_forecast = forecast_details.get('fcf_forecast', [])
            
            if growth_data and fcf_forecast:
                f.write("=" * 80 + "\n")
                f.write(f"{t('YEARLY_FCF_GROWTH_FORECAST')}\n")
                f.write("=" * 80 + "\n")
                f.write(f"{t('YEAR'):<6} {t('FCF_VND'):<20} {t('YOY_GROWTH'):<15} {t('CUMULATIVE_GROWTH'):<20}\n")
                f.write("-" * 80 + "\n")
                
                for i, (fcf, (yearly_growth, cumulative_growth)) in enumerate(zip(fcf_forecast, growth_data)):
                    year_label = f"{t('YEAR')} {i+1}" if language == 'en' else f"Năm {i+1}"
                    f.write(f"{year_label:<6} {fcf:>18,.0f}  {yearly_growth:>13.2f}%  {cumulative_growth:>18.2f}%\n")
                
                f.write("\n")
            
            # Yearly Price Forecast
            yearly_prices = advanced.get('yearly_price_forecast', [])
            if yearly_prices:
                f.write("=" * 80 + "\n")
                f.write(f"{t('YEARLY_PRICE_FORECAST')}\n")
                f.write("=" * 80 + "\n")
                f.write(f"{t('YEAR'):<6} {t('FCF_VND'):<20} {t('COMPANY_VALUE_VND'):<25} {t('PRICE_PER_SHARE_VND'):<20}\n")
                f.write("-" * 80 + "\n")
                
                current_price = data.get('price', 0)
                for year_data in yearly_prices:
                    year = year_data['year']
                    fcf = year_data['fcf']
                    company_value = year_data['company_value']
                    price = year_data['price_per_share']
                    price_change = year_data.get('price_change_pct', 0)
                    
                    year_label = f"{t('YEAR')} {year}" if language == 'en' else f"Năm {year}"
                    f.write(f"{year_label:<6} {fcf:>18,.0f}  {company_value:>23,.0f}  {price:>18,.2f} ({price_change:+.2f}%)\n")
                
                f.write("\n")
                
                # Thêm phần Performance Analysis
                f.write("=" * 80 + "\n")
                f.write(f"{t('YEARLY_PERFORMANCE_ANALYSIS')}\n")
                f.write("=" * 80 + "\n")
                f.write(f"{t('PERFORMANCE_DESCRIPTION')}\n")
                f.write("-" * 80 + "\n")
                f.write(f"{t('YEAR'):<6} {t('PRICE_VND'):<18} {t('YOY_GROWTH'):<15} {t('VS_CURRENT_PRICE'):<20} {t('MULTIPLIER'):<12}\n")
                f.write("-" * 80 + "\n")
                
                # Current price row
                current_label = t('CURRENT')
                base_label = t('BASE')
                base_100_label = t('BASE_100_PCT')
                f.write(f"{current_label:<6} {current_price:>16,.2f}  {base_label:<15}  {base_100_label:<20}  {'1.00x':<12}\n")
                
                for year_data in yearly_prices:
                    year = year_data['year']
                    price = year_data['price_per_share']
                    yoy_growth = year_data.get('year_over_year_growth_pct', 0)
                    price_change = year_data.get('price_change_pct', 0)
                    multiplier = year_data.get('price_multiplier', 1.0)
                    
                    vs_current = f"{price_change:+.2f}%"
                    multiplier_str = f"{multiplier:.2f}x"
                    
                    # Year 1: YoY Growth là so với giá hiện tại
                    if year == 1:
                        yoy_display = f"{price_change:+.2f}%"
                    else:
                        yoy_display = f"{yoy_growth:+.2f}%"
                    
                    year_label = f"{t('YEAR')} {year}" if language == 'en' else f"Năm {year}"
                    f.write(f"{year_label:<6} {price:>16,.2f}  {yoy_display:<15}  {vs_current:<20}  {multiplier_str:<12}\n")
                
                f.write("\n")
                f.write(f"{t('EXPLANATION')}:\n")
                f.write(f"  - {t('YOY_GROWTH_EXPLANATION')}\n")
                f.write(f"  - {t('VS_CURRENT_EXPLANATION')}\n")
                f.write(f"  - {t('MULTIPLIER_EXPLANATION')}\n")
                f.write("\n")
            
            # Graham Valuation Details
            if data.get('graham_fair_value'):
                f.write("=" * 80 + "\n")
                f.write(f"{t('GRAHAM_VALUATION_DETAILS')}\n")
                f.write("=" * 80 + "\n")
                f.write(f"{t('GRAHAM_FORMULA')}: {t('GRAHAM_FORMULA_DETAIL')}\n")
                if 'eps' in data and 'growth_estimate' in data:
                    base_pe = 8.5  # Default, có thể lấy từ config
                    calc_label = t('GRAHAM_CALCULATION')
                    f.write(f"{calc_label}: {data['eps']:,.2f} × ({base_pe} + 2 × {data['growth_estimate']:.2f}%)\n")
                f.write("\n")
            
            f.write("=" * 80 + "\n")
            f.write(f"{t('ANALYSIS_DATE')}: {data.get('saved_at', 'N/A')}\n")
            f.write("=" * 80 + "\n")

    def _format_key(self, key):
        """
        Chuyển đổi key thành readable format
        Ví dụ: 'valuation_price' -> 'Valuation Price'
        """
        return ' '.join(word.capitalize() for word in key.split('_'))

    def _serialize_result(self, data):
        """
        Chuyển đổi dữ liệu để có thể serialize thành JSON
        """
        serialized = {}
        for key, value in data.items():
            if isinstance(value, (int, float, str, bool, type(None))):
                serialized[key] = value
            elif isinstance(value, dict):
                serialized[key] = self._serialize_result(value)
            elif isinstance(value, (list, tuple)):
                serialized[key] = [self._serialize_result(v) if isinstance(v, dict) else v for v in value]
            else:
                # Chuyển đổi các loại khác sang string
                serialized[key] = str(value)
        return serialized

    def load_result(self, stock_name):
        """
        Tải kết quả DCF của một mã cổ phiếu từ file

        Args:
            stock_name: Mã cổ phiếu

        Returns:
            Dictionary chứa kết quả, hoặc None nếu file không tồn tại
        """
        stock_name_lower = stock_name.lower()
        result_file = os.path.join(self.results_dir, f'{stock_name_lower}_result.json')

        if not os.path.exists(result_file):
            return None

        with open(result_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_results(self):
        """
        Liệt kê tất cả các file kết quả đã lưu

        Returns:
            List các file kết quả
        """
        results = []
        if os.path.exists(self.results_dir):
            for file in os.listdir(self.results_dir):
                if file.endswith('_result.json'):
                    file_path = os.path.join(self.results_dir, file)
                    results.append({
                        'file': file,
                        'path': file_path,
                        'size': os.path.getsize(file_path)
                    })
        return results

    def get_results_dir(self):
        """Lấy đường dẫn thư mục results"""
        return self.results_dir

    def delete_result(self, stock_name):
        """
        Xóa file kết quả của một mã cổ phiếu

        Args:
            stock_name: Mã cổ phiếu

        Returns:
            True nếu xóa thành công, False nếu file không tồn tại
        """
        stock_name_lower = stock_name.lower()
        result_file = os.path.join(self.results_dir, f'{stock_name_lower}_result.json')
        log_file = os.path.join(self.results_dir, f'{stock_name_lower}_result.text')

        deleted = False
        if os.path.exists(result_file):
            os.remove(result_file)
            deleted = True
        if os.path.exists(log_file):
            os.remove(log_file)
            deleted = True

        return deleted

    def clear_all_results(self):
        """
        Xóa tất cả các file kết quả
        """
        if os.path.exists(self.results_dir):
            for file in os.listdir(self.results_dir):
                if file.endswith('_result.json') or file.endswith('_result.text'):
                    os.remove(os.path.join(self.results_dir, file))


# Singleton instance
_result_manager = None

def get_result_manager():
    """Lấy singleton instance của ResultManager"""
    global _result_manager
    if _result_manager is None:
        _result_manager = ResultManager()
    return _result_manager
