"""
Results Manager - Lưu lại kết quả DCF cho từng mã cổ phiếu
"""

import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

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
        with open(log_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write(f"DCF VALUATION ANALYSIS - {data.get('ticker', 'N/A').upper()}\n")
            f.write("=" * 80 + "\n\n")
            
            # Main valuation parameters
            f.write("INPUT PARAMETERS\n")
            f.write("-" * 80 + "\n")
            if 'price' in data:
                f.write(f"Market Price: {data['price']:,.2f} VND\n")
            if 'eps' in data:
                f.write(f"EPS: {data['eps']:,.2f} VND\n")
            if 'fcf' in data:
                f.write(f"Free Cash Flow (TTM): {data['fcf']:,.0f} VND\n")
            if 'shares' in data:
                f.write(f"Shares Outstanding: {data['shares']:,.0f}\n")
            if 'market_cap' in data:
                f.write(f"Market Cap: {data['market_cap']:,.0f} VND\n")
            if 'growth_estimate' in data:
                f.write(f"Growth Estimate: {data['growth_estimate']:.2f}%\n")
            if 'dcf_params' in data and isinstance(data['dcf_params'], dict):
                f.write(f"Forecast Term: {data['dcf_params'].get('yr', 5)} years\n")
                f.write(f"Discount Rate: {data['dcf_params'].get('dr', 10)}%\n")
                f.write(f"Perpetual Rate: {data['dcf_params'].get('pr', 2.5)}%\n")
            f.write("\n")
            
            # Valuation Results
            f.write("=" * 80 + "\n")
            f.write("VALUATION RESULTS\n")
            f.write("=" * 80 + "\n")
            f.write(f"DCF Fair Value: {data.get('dcf_fair_value', 'N/A'):,.2f} VND\n")
            if data.get('graham_fair_value'):
                f.write(f"Graham Fair Value: {data['graham_fair_value']:,.2f} VND\n")
                f.write(f"Average Fair Value: {data.get('average_fair_value', 'N/A'):,.2f} VND\n")
            f.write("\n")
            
            # Upside/Downside Analysis
            advanced = data.get('advanced_analysis', {})
            upside = advanced.get('upside_downside', {})
            if upside:
                f.write("UPSIDE/DOWNSIDE ANALYSIS\n")
                f.write("-" * 80 + "\n")
                if 'dcf_upside_pct' in upside:
                    f.write(f"DCF Upside/Downside: {upside['dcf_upside_pct']:+.2f}%\n")
                if 'graham_upside_pct' in upside:
                    f.write(f"Graham Upside/Downside: {upside['graham_upside_pct']:+.2f}%\n")
                if 'average_upside_pct' in upside:
                    f.write(f"Average Upside/Downside: {upside['average_upside_pct']:+.2f}%\n")
                f.write("\n")
            
            # Valuation Metrics
            metrics = advanced.get('valuation_metrics', {})
            if metrics:
                f.write("VALUATION METRICS\n")
                f.write("-" * 80 + "\n")
                if metrics.get('pe_ratio'):
                    f.write(f"P/E Ratio: {metrics['pe_ratio']:.2f}\n")
                if metrics.get('pfcf_ratio'):
                    f.write(f"P/FCF Ratio: {metrics['pfcf_ratio']:.2f}\n")
                if metrics.get('fcf_yield'):
                    f.write(f"FCF Yield: {metrics['fcf_yield']:.2f}%\n")
                if metrics.get('earnings_yield'):
                    f.write(f"Earnings Yield: {metrics['earnings_yield']:.2f}%\n")
                f.write("\n")
            
            # Yearly FCF Growth Forecast
            growth_data = advanced.get('yearly_growth', [])
            forecast_details = advanced.get('forecast_details', {})
            fcf_forecast = forecast_details.get('fcf_forecast', [])
            
            if growth_data and fcf_forecast:
                f.write("=" * 80 + "\n")
                f.write("YEARLY FCF GROWTH FORECAST\n")
                f.write("=" * 80 + "\n")
                f.write(f"{'Year':<6} {'FCF (VND)':<20} {'YoY Growth %':<15} {'Cumulative Growth %':<20}\n")
                f.write("-" * 80 + "\n")
                
                for i, (fcf, (yearly_growth, cumulative_growth)) in enumerate(zip(fcf_forecast, growth_data)):
                    f.write(f"Year {i+1:<4} {fcf:>18,.0f}  {yearly_growth:>13.2f}%  {cumulative_growth:>18.2f}%\n")
                
                f.write("\n")
            
            # Yearly Price Forecast
            yearly_prices = advanced.get('yearly_price_forecast', [])
            if yearly_prices:
                f.write("=" * 80 + "\n")
                f.write("YEARLY PRICE FORECAST (Based on DCF Model)\n")
                f.write("=" * 80 + "\n")
                f.write(f"{'Year':<6} {'FCF (VND)':<20} {'Company Value (VND)':<25} {'Price/Share (VND)':<20}\n")
                f.write("-" * 80 + "\n")
                
                current_price = data.get('price', 0)
                for year_data in yearly_prices:
                    year = year_data['year']
                    fcf = year_data['fcf']
                    company_value = year_data['company_value']
                    price = year_data['price_per_share']
                    price_change = year_data.get('price_change_pct', 0)
                    
                    f.write(f"Year {year:<4} {fcf:>18,.0f}  {company_value:>23,.0f}  {price:>18,.2f} ({price_change:+.2f}%)\n")
                
                f.write("\n")
                
                # Thêm phần Performance Analysis
                f.write("=" * 80 + "\n")
                f.write("YEARLY PERFORMANCE ANALYSIS\n")
                f.write("=" * 80 + "\n")
                f.write("Hiệu suất tăng trưởng giá cổ phiếu theo từng năm\n")
                f.write("-" * 80 + "\n")
                f.write(f"{'Year':<6} {'Price (VND)':<18} {'YoY Growth %':<15} {'vs Current Price':<20} {'Multiplier':<12}\n")
                f.write("-" * 80 + "\n")
                
                # Current price row
                f.write(f"{'Current':<6} {current_price:>16,.2f}  {'Base':<15}  {'Base (100%)':<20}  {'1.00x':<12}\n")
                
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
                    
                    f.write(f"Year {year:<4} {price:>16,.2f}  {yoy_display:<15}  {vs_current:<20}  {multiplier_str:<12}\n")
                
                f.write("\n")
                f.write("Giải thích:\n")
                f.write("  - YoY Growth %: Tăng trưởng năm-over-year (Year 1 so với giá hiện tại)\n")
                f.write("  - vs Current Price: % thay đổi so với giá hiện tại\n")
                f.write("  - Multiplier: Số lần tăng giá trị so với giá hiện tại (ví dụ: 1.53x = tăng 53%)\n")
                f.write("\n")
            
            # Graham Valuation Details
            if data.get('graham_fair_value'):
                f.write("=" * 80 + "\n")
                f.write("GRAHAM VALUATION DETAILS\n")
                f.write("=" * 80 + "\n")
                f.write("Formula: EPS × (Base PE + 2 × Growth Rate)\n")
                if 'eps' in data and 'growth_estimate' in data:
                    base_pe = 8.5  # Default, có thể lấy từ config
                    f.write(f"Calculation: {data['eps']:,.2f} × ({base_pe} + 2 × {data['growth_estimate']:.2f}%)\n")
                f.write("\n")
            
            f.write("=" * 80 + "\n")
            f.write(f"Analysis Date: {data.get('saved_at', 'N/A')}\n")
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
