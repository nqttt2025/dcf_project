#!/usr/bin/env python3
"""
Script để cập nhật tất cả các file config với thông tin về TTM và nguồn dữ liệu
"""
import os
import configparser
from pathlib import Path

def update_config_file(config_path):
    """Cập nhật một file config với thông tin về TTM và nguồn dữ liệu"""
    config = configparser.ConfigParser()
    config.read(config_path)
    
    # Thêm section [fcf_calculation] nếu chưa có
    if 'fcf_calculation' not in config:
        config.add_section('fcf_calculation')
    
    # Thêm các thông tin về FCF calculation
    config['fcf_calculation']['data_source'] = 'vnstock'
    config['fcf_calculation']['method'] = 'TTM (Trailing Twelve Months)'
    config['fcf_calculation']['description'] = 'Free Cash Flow được tính bằng cách cộng dồn 4 quý gần nhất từ vnstock'
    config['fcf_calculation']['formula'] = 'FCF TTM = Sum(OCF - CapEx) của 4 quý gần nhất'
    config['fcf_calculation']['note'] = 'TTM phản ánh tốt hơn tình hình hiện tại và chuẩn trong phân tích DCF'
    
    # Cập nhật section [data_source] nếu có
    if 'data_source' in config:
        if 'note' not in config['data_source']:
            config['data_source']['note'] = 'Dữ liệu được lấy từ vnstock library, source VCI'
    
    # Ghi lại file
    with open(config_path, 'w') as configfile:
        config.write(configfile)
    
    return True

def main():
    """Cập nhật tất cả các file config"""
    project_root = Path(__file__).parent.parent
    config_dir = project_root / 'config'
    
    config_files = sorted(config_dir.glob('*.cfg'))
    
    # Bỏ qua README.md nếu có
    config_files = [f for f in config_files if f.name != 'README.md']
    
    print(f"Tìm thấy {len(config_files)} file config")
    print("="*80)
    
    updated = 0
    failed = 0
    
    for config_file in config_files:
        try:
            if update_config_file(config_file):
                print(f"✓ Đã cập nhật: {config_file.name}")
                updated += 1
            else:
                print(f"✗ Lỗi khi cập nhật: {config_file.name}")
                failed += 1
        except Exception as e:
            print(f"✗ Lỗi khi cập nhật {config_file.name}: {e}")
            failed += 1
    
    print("="*80)
    print(f"Hoàn thành: {updated} file đã cập nhật, {failed} file lỗi")

if __name__ == "__main__":
    main()

