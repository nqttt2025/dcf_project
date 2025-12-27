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
    Format: results/{stock_name}_result.json
           {project_root}/{stock_name}.text
    """

    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.results_dir = os.path.join(self.project_root, 'results')
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
        Lưu kết quả dưới dạng text log file

        Args:
            log_file: Đường dẫn file log
            data: Dictionary chứa kết quả
        """
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"DCF VALUATION RESULT - {data.get('stock_name', 'Unknown')}\n")
            f.write("=" * 80 + "\n")
            f.write(f"Saved at: {data.get('saved_at', 'N/A')}\n")
            f.write("-" * 80 + "\n\n")

            # Format kết quả một cách dễ đọc
            for key, value in data.items():
                if key not in ['stock_name', 'saved_at']:
                    # Định dạng key thành readable format
                    formatted_key = self._format_key(key)

                    if isinstance(value, dict):
                        f.write(f"\n{formatted_key}:\n")
                        for sub_key, sub_value in value.items():
                            formatted_sub_key = self._format_key(sub_key)
                            f.write(f"  {formatted_sub_key}: {sub_value}\n")
                    elif isinstance(value, (list, tuple)):
                        f.write(f"\n{formatted_key}:\n")
                        for i, item in enumerate(value):
                            f.write(f"  [{i}]: {item}\n")
                    else:
                        f.write(f"{formatted_key}: {value}\n")

            f.write("\n" + "=" * 80 + "\n")

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
