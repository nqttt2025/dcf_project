# Version Management System

Hệ thống quản lý version thống nhất cho toàn bộ project.

## Nguyên Tắc

**Git Tag là Single Source of Truth duy nhất cho project version**

- Tất cả scripts đều lấy project version từ git tag
- Docker service images đồng bộ với git tag
- Base image có version riêng, chỉ increment khi `requirements.txt` thay đổi

## Version Sources

### 1. Project Version (Git Tag) - Single Source of Truth

**Source:** Git tag  
**Script:** `scripts/utils/get_version.sh`  
**Usage:** Tất cả Docker service images

```bash
# Lấy project version
./scripts/utils/get_version.sh
# hoặc
make get-version
```

**Priority:**
1. Git tag (nếu có)
2. Git commit hash (nếu không có tag)
3. Timestamp (nếu không phải git repo)

### 2. Base Image Version (Independent)

**Source:** `docker-versions.json`  
**Script:** `scripts/version/docker_version.sh`  
**Usage:** Base Docker image

- Version riêng: `v1.0.0`, `v1.0.1`, ...
- Chỉ increment khi `requirements.txt` thay đổi
- Auto-detect bằng SHA256 hash

### 3. Service Image Versions (Sync với Git Tag)

**Source:** `docker-versions.json` (sync với git tag)  
**Script:** `scripts/version/docker_version.sh`  
**Usage:** Docker service images (gateway, dcf, stock, frontend)

- Đồng bộ với git tag
- Tự động sync khi tạo git tag

## File Cấu Hình

### `docker-versions.json`

Quản lý Docker-specific versions:

```json
{
  "base": {
    "current": "v1.0.0",
    "last_requirements_hash": "...",
    "last_updated": "2025-12-29 10:00:00"
  },
  "services": {
    "gateway": { "current": "v1.0.0", "depends_on_base": true },
    "dcf": { "current": "v1.0.0", "depends_on_base": true },
    ...
  }
}
```

**Lưu ý:** Service versions được sync với git tag, không cần maintain thủ công.

## Scripts và Chức Năng

### `scripts/utils/get_version.sh` ⭐ PRIMARY
**Chức năng:** Lấy project version từ git tag  
**Usage:** Tất cả scripts cần project version

```bash
./scripts/utils/get_version.sh
# Output: v1.0.0 hoặc dev-abc123 hoặc dev-20251229-001234
```

### `scripts/version/docker_version.sh`
**Chức năng:** Quản lý Docker-specific versions  
**Usage:** Base image version, sync service versions

```bash
# Get Docker versions
./scripts/version/docker_version.sh get              # All Docker versions
./scripts/version/docker_version.sh get base         # Base image version
./scripts/version/docker_version.sh get gateway      # Gateway version
./scripts/version/docker_version.sh get project      # Project version (from git tag)

# Check base image
./scripts/version/docker_version.sh check-base       # Check if rebuild needed

# Sync with git tag
./scripts/version/docker_version.sh sync-git         # Sync service versions
```

### `scripts/version/create_git_tag.sh`
**Chức năng:** Tạo git tag và sync Docker versions  
**Usage:** Tạo version mới

```bash
./scripts/version/create_git_tag.sh v1.0.0
# 1. Tạo git tag
# 2. Sync Docker service versions với git tag
```

### `scripts/version/auto_version.sh`
**Chức năng:** Auto-increment version và tạo git tag  
**Usage:** Tự động tăng version

```bash
./scripts/version/auto_version.sh patch   # v1.0.0 -> v1.0.1
./scripts/version/auto_version.sh minor   # v1.0.0 -> v1.1.0
./scripts/version/auto_version.sh major   # v1.0.0 -> v2.0.0
# Tự động sync Docker versions
```

### `scripts/version/auto_tag_from_commit.sh`
**Chức năng:** Tạo tag từ commit message  
**Usage:** Auto-tagging từ commit

```bash
# Commit message: "Fix bug [version: v1.0.1]"
./scripts/version/auto_tag_from_commit.sh
# Tự động tạo tag v1.0.1 và sync Docker versions
```

### `scripts/git.sh`
**Chức năng:** Wrapper cho git tag commands  
**Usage:** Quản lý git tags

```bash
./scripts/git.sh tag v1.0.0
./scripts/git.sh tag-patch
./scripts/git.sh version          # Show project version
```

## Workflow

### 1. Tạo Version Mới

```bash
# Option 1: Manual
make git-tag VERSION=v1.0.0
# → Tạo git tag
# → Sync Docker service versions

# Option 2: Auto-increment
make git-tag-patch
# → Increment patch version
# → Tạo git tag
# → Sync Docker service versions
```

### 2. Build Docker Images

```bash
make docker-build
# → Lấy project version từ git tag
# → Check base image (chỉ rebuild nếu requirements.txt thay đổi)
# → Build service images với project version
```

### 3. Check Versions

```bash
# Project version (from git tag)
make get-version

# All Docker versions
make docker-versions

# Check base image
make docker-version-check-base
```

## Version Strategy

### Project Version
- **Source:** Git tag
- **Format:** `vX.Y.Z` (semantic versioning)
- **Used by:** All Docker service images
- **Management:** Git tags only

### Base Image Version
- **Source:** `docker-versions.json`
- **Format:** `vX.Y.Z` (semantic versioning)
- **Increment:** Only when `requirements.txt` changes
- **Management:** Auto-increment on rebuild

### Service Image Versions
- **Source:** `docker-versions.json` (synced with git tag)
- **Format:** `vX.Y.Z` (semantic versioning)
- **Sync:** Automatic when creating git tag
- **Management:** Auto-sync, no manual update needed

## Commands Summary

### Project Version (Git Tag)
```bash
make get-version              # Get project version
make git-tag VERSION=v1.0.0  # Create git tag
make git-tag-patch           # Auto-increment patch
make git-tag-minor           # Auto-increment minor
make git-tag-major           # Auto-increment major
```

### Docker Versions
```bash
make docker-versions              # Show all Docker versions
make docker-version-check-base    # Check base image
```

### Docker Build
```bash
make docker-build        # Build (uses project version from git tag)
make docker-rebuild      # Rebuild (uses project version from git tag)
```

## Best Practices

1. **Luôn dùng git tag để quản lý project version**
   - Không set project version thủ công
   - Tất cả scripts đều lấy từ git tag

2. **Base image version độc lập**
   - Chỉ increment khi `requirements.txt` thay đổi
   - Không sync với git tag

3. **Service versions tự động sync**
   - Khi tạo git tag → tự động sync
   - Không cần maintain thủ công

4. **Commit `docker-versions.json`**
   - Track base image version history
   - Team members có cùng base version

## Troubleshooting

### Version không đồng bộ

```bash
# Sync service versions với git tag
./scripts/version/docker_version.sh sync-git
```

### Base image không rebuild khi cần

```bash
# Check base image
make docker-version-check-base

# Force rebuild base
./scripts/version/docker_version.sh update base
make docker-rebuild
```

### Project version không đúng

```bash
# Check git tag
git describe --tags --abbrev=0

# Tạo git tag nếu chưa có
make git-tag VERSION=v1.0.0
```

## 📚 Tài Liệu Liên Quan

- [Version Best Practices](./VERSION_BEST_PRACTICES.md) - Hướng dẫn sử dụng best practices
- [Docker Version Management](./DOCKER_VERSION_MANAGEMENT.md) - Quản lý Docker versions
- [Docker Build Optimization](./DOCKER_BUILD_OPTIMIZATION.md) - Tối ưu Docker builds

---

**Version:** 1.0  
**Last Updated:** 2025-12-29  
**Single Source of Truth:** Git Tag

