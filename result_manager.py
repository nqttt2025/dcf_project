"""
Results Manager - Lưu lại kết quả DCF cho từng mã cổ phiếu
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path

class ResultManager:
    """
    Quản lý lưu trữ kết quả DCF valuation
    Format: results/{stock_name}_result.json
    """
    
    def __init__(self):
        self.results_dir = os.path.join(os.path.dirname(__file__), 'results')
        os.makedirs(self.results_dir, exist_ok=True)
    
    def save_result(self, stock_name, valuation_result):
        """
        Lưu kết quả DCF cho một mã cổ phiếu
        
        Args:
            stock_name: Mã cổ phiếu (ví dụ: FPT, VNM, BID)
            valuation_result: Dictionary chứa kết quả định giá
        
        Returns:
            Đường dẫn tới file kết quả
        """
        stock_name_lower = stock_name.lower()
        result_file = os.path.join(self.results_dir, f'{stock_name_lower}_result.json')
        
        # Thêm timestamp
        result_with_timestamp = valuation_result.copy()
        result_with_timestamp['saved_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        result_with_timestamp['stock_name'] = stock_name
        
        # Chuyển đổi các giá trị không thể serialize
        result_with_timestamp = self._serialize_result(result_with_timestamp)
        
        # Lưu lên file
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_with_timestamp, f, indent=2, ensure_ascii=False)
        
        return result_file
    
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
        
        if os.path.exists(result_file):
            os.remove(result_file)
            return True
        return False
    
    def clear_all_results(self):
        """
        Xóa tất cả các file kết quả
        """
        if os.path.exists(self.results_dir):
            for file in os.listdir(self.results_dir):
                if file.endswith('_result.json'):
                    os.remove(os.path.join(self.results_dir, file))


# Singleton instance
_result_manager = None

def get_result_manager():
    """Lấy singleton instance của ResultManager"""
    global _result_manager
    if _result_manager is None:
        _result_manager = ResultManager()
    return _result_manager
