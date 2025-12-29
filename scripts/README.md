# Scripts Directory

Scripts directory đã được refactor theo nguyên tắc SOLID để dễ bảo trì và tái sử dụng code.

## 📁 Cấu Trúc Thư Mục

```
scripts/
├── lib/              # Core library modules (Single Responsibility)
│   ├── common.sh     # Main entry point - loads all modules
│   ├── config.sh     # Configuration and constants
│   ├── logging.sh    # Logging functions
│   ├── file_ops.sh   # File/directory operations
│   ├── validation.sh # Input validation
│   ├── error_handler.sh # Error handling
│   ├── python_utils.sh # Python helpers
│   ├── docker_utils.sh # Docker helpers
│   ├── display.sh    # Display/formatting functions
│   ├── version.sh    # Version management
│   └── base_script.sh # Base script class
│
├── version/          # Version management scripts
│   ├── docker_version.sh
│   ├── create_git_tag.sh
│   ├── auto_version.sh
│   └── auto_tag_from_commit.sh
│
├── docker/           # Docker-related scripts
│   └── build_base.sh
│
├── analysis/         # Analysis scripts (DCF, PE)
│   ├── dcf.sh
│   ├── pe.sh
│   ├── run_all_dcf.sh
│   ├── calculate_pe.py
│   ├── run_all_dcf.py
│   └── run_all_dcf_with_retry.py
│
├── dev/              # Development tools
│   ├── test.sh
│   ├── lint.sh
│   ├── clean.sh
│   ├── health_check.sh
│   ├── run_backend_dev.sh
│   └── run_backend_local.sh
│
├── utils/            # Utility scripts
│   ├── get_version.sh
│   ├── web.sh
│   └── update_configs_with_ttm_info.py
│
├── common.sh         # Backward compatibility wrapper
├── docker.sh         # Main Docker management script
└── git.sh            # Git tag management script
```

## 🎯 SOLID Principles

### Single Responsibility Principle (SRP)
- Mỗi module trong `lib/` có một trách nhiệm rõ ràng
- Scripts được tổ chức theo chức năng (version, docker, analysis, dev, utils)

### Open/Closed Principle (OCP)
- Base script class (`lib/base_script.sh`) cung cấp foundation có thể mở rộng
- Scripts mới có thể mở rộng mà không cần sửa code cũ

### Dependency Inversion Principle (DIP)
- Scripts phụ thuộc vào abstractions (lib modules) không phải implementations cụ thể

## 📝 Sử Dụng

### Tạo Script Mới

```bash
#!/bin/bash
set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/scripts/lib/common.sh"

# Initialize script
init_script "$(basename "${BASH_SOURCE[0]}")"

# Your script logic here
```

### Backward Compatibility

File `scripts/common.sh` vẫn tồn tại như một wrapper để đảm bảo tương thích ngược. Nó tự động load `scripts/lib/common.sh`.

## 🔧 Analysis Scripts

### DCF Analysis

```bash
# Single stock
./scripts/analysis/dcf.sh single VNM

# All stocks (with retry)
./scripts/analysis/dcf.sh all

# All stocks (fast mode)
./scripts/analysis/dcf.sh all-fast
```

### PE Calculation

```bash
# Single stock
./scripts/analysis/pe.sh single VNM
./scripts/analysis/pe.sh single VCB banking

# All VN30 stocks
./scripts/analysis/pe.sh all
```

**Các ngành được hỗ trợ:**
- `banking` - Ngân hàng
- `real_estate` - Bất động sản
- `technology` - Công nghệ
- `consumer` - Tiêu dùng
- `energy` - Năng lượng
- `industrial` - Công nghiệp
- `aviation` - Hàng không

### Python Scripts (Direct)

```bash
# Calculate PE
python3 scripts/analysis/calculate_pe.py VNM
python3 scripts/analysis/calculate_pe.py  # All VN30

# Run DCF
python3 scripts/analysis/run_all_dcf.py
python3 scripts/analysis/run_all_dcf_with_retry.py

# Update configs
python3 scripts/utils/update_configs_with_ttm_info.py
```

## 🧪 Testing

### Run Script Tests

```bash
# Test all scripts (bash + Python)
make test-scripts

# Test only bash scripts
make test-scripts-bash

# Test only Python scripts
make test-scripts-python
```

### Test Coverage

#### Bash Script Tests
- ✅ Script existence
- ✅ Syntax validation
- ✅ Executability
- ✅ Help/usage functionality
- ✅ Module loading

#### Python Script Tests
- ✅ File existence
- ✅ Syntax validation
- ✅ Import checks
- ✅ Shebang presence
- ✅ Help/docstring presence
- ✅ Path resolution

Xem chi tiết: [tests/scripts/README.md](../tests/scripts/README.md)

## 📊 Path Resolution

Tất cả Python scripts đã được cập nhật để:
1. **Tự động tìm project root** - Hoạt động từ bất kỳ đâu
2. **Xử lý đường dẫn đúng cách** - Config và data directories được resolve relative to project root
3. **Giữ tương thích** - Scripts có thể chạy trực tiếp hoặc qua bash wrappers

### Pattern Chuẩn

```python
# Get script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get project root (2 levels up from scripts/analysis/)
project_root = os.path.dirname(os.path.dirname(script_dir))
# Add to Python path
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))
```

## ✅ Lợi Ích

1. **Code Reuse**: Chức năng chung được tập trung trong `lib/`
2. **Maintainability**: Thay đổi một module không ảnh hưởng module khác
3. **Testability**: Mỗi module có thể test độc lập
4. **Clarity**: Tổ chức rõ ràng, dễ tìm scripts
5. **Extensibility**: Dễ thêm scripts mới theo cùng pattern

## 🔄 Maintenance

Khi thêm scripts mới:

1. Đặt vào thư mục phù hợp (`analysis/`, `utils/`, etc.)
2. Sử dụng pattern path resolution chuẩn
3. Thêm tests vào `tests/scripts/`
4. Cập nhật documentation này
