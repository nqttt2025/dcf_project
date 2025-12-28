# Docker Version Management

Hệ thống quản lý version cho Docker images, bao gồm base image với khả năng tự động phát hiện thay đổi.

## Tổng Quan

Hệ thống quản lý version tự động:
- **Base Image**: Version riêng, chỉ rebuild khi `requirements.txt` thay đổi
- **Service Images**: Version đồng bộ với git tag
- **Auto-detection**: Tự động phát hiện khi base image cần rebuild

## File Cấu Hình

### `docker-versions.json`

File JSON quản lý tất cả versions:

```json
{
  "base": {
    "current": "v1.0.0",
    "last_requirements_hash": "...",
    "last_updated": "2025-12-29 10:00:00"
  },
  "services": {
    "gateway": {
      "current": "v1.0.0",
      "depends_on_base": true
    },
    "dcf": {
      "current": "v1.0.0",
      "depends_on_base": true
    },
    ...
  }
}
```

## Cách Hoạt Động

### 1. Base Image Versioning

Base image có version riêng và chỉ rebuild khi:
- `requirements.txt` thay đổi (detected bằng SHA256 hash)
- Base image chưa tồn tại

**Lợi ích:**
- Không rebuild base image không cần thiết
- Tiết kiệm thời gian build
- Base image được cache và reuse

### 2. Service Image Versioning

Service images đồng bộ với git tag:
- Khi tạo git tag → tự động sync versions
- Tất cả services có cùng version với git tag

### 3. Auto-Detection

Hệ thống tự động:
- Check hash của `requirements.txt`
- So sánh với hash đã lưu
- Quyết định có cần rebuild base image không

## Commands

### Xem Versions

```bash
# Xem tất cả versions
make docker-versions
# hoặc
./scripts/docker_version.sh get

# Xem version của base
./scripts/docker_version.sh get base

# Xem version của service
./scripts/docker_version.sh get gateway
```

### Check Base Image

```bash
# Check xem base image có cần rebuild không
make docker-version-check-base
# hoặc
./scripts/docker_version.sh check-base
```

Output:
- `rebuild` - Cần rebuild (requirements.txt thay đổi)
- `no-rebuild` - Không cần rebuild

### Sync với Git Tag

```bash
# Sync tất cả versions với git tag hiện tại
./scripts/docker_version.sh sync-git
```

Khi tạo git tag, versions tự động sync:
```bash
make git-tag VERSION=v1.0.0
# Tự động sync Docker versions
```

### Set Version Thủ Công

```bash
# Set version cho base image
./scripts/docker_version.sh set base v1.1.0

# Set version cho service
./scripts/docker_version.sh set gateway v1.0.0
```

## Workflow

### 1. Development Normal

```bash
# Build images (tự động check base image)
make docker-build

# Nếu requirements.txt không đổi:
# - Base image không rebuild (dùng cache)
# - Chỉ rebuild service images
```

### 2. Thay Đổi Dependencies

```bash
# 1. Sửa requirements.txt
vim services/common/requirements.txt

# 2. Build (tự động detect và rebuild base)
make docker-build

# Base image sẽ được rebuild và version được update
```

### 3. Tạo Git Tag

```bash
# Tạo git tag (tự động sync Docker versions)
make git-tag VERSION=v1.0.0

# Hoặc auto-increment
make git-tag-patch  # v1.0.1
make git-tag-minor  # v1.1.0
make git-tag-major  # v2.0.0
```

### 4. Rebuild Hoàn Toàn

```bash
# Rebuild tất cả (bao gồm base image)
make docker-rebuild
```

## Version Strategy

### Base Image Version

- **Format**: `vX.Y.Z` (semantic versioning)
- **Increment**: Khi `requirements.txt` thay đổi
- **Auto-increment**: Patch version (+0.0.1)

### Service Image Version

- **Format**: `vX.Y.Z` (semantic versioning)
- **Source**: Git tag
- **Sync**: Tự động khi tạo git tag

## Examples

### Example 1: Normal Build

```bash
# Check base image
$ make docker-version-check-base
no-rebuild

# Build (base image không rebuild)
$ make docker-build
Building images...
Base image unchanged (version: v1.0.0), using cached version
Building service images...
```

### Example 2: Requirements Changed

```bash
# Sửa requirements.txt
$ echo "new-package==1.0.0" >> services/common/requirements.txt

# Check base image
$ make docker-version-check-base
rebuild

# Build (base image sẽ rebuild)
$ make docker-build
Building images...
Base image needs rebuild (requirements.txt changed)
Building base image (version: v1.0.1)...
Building service images...
```

### Example 3: Create Git Tag

```bash
# Tạo git tag
$ make git-tag VERSION=v1.0.0
Tag created: v1.0.0
Docker versions synced

# Check versions
$ make docker-versions
Base Image:
  Version: v1.0.0
  Last Updated: 2025-12-29 10:00:00
  Requirements Hash: abc123...

Services:
  gateway      Version: v1.0.0    Depends on base: ✓
  dcf          Version: v1.0.0    Depends on base: ✓
  stock        Version: v1.0.0    Depends on base: ✓
  frontend     Version: v1.0.0    Depends on base: ✗
```

## Integration với Git

### Auto Sync khi Tạo Tag

Khi tạo git tag bằng các commands:
- `make git-tag VERSION=v1.0.0`
- `make git-tag-patch`
- `make git-tag-minor`
- `make git-tag-major`

Docker versions tự động sync với git tag.

### Manual Sync

```bash
# Sync với git tag hiện tại
./scripts/docker_version.sh sync-git
```

## Troubleshooting

### Base Image Không Rebuild Khi Cần

```bash
# Force rebuild base image
./scripts/docker_version.sh set base v1.0.1
make docker-rebuild
```

### Versions Không Sync

```bash
# Manual sync
./scripts/docker_version.sh sync-git
```

### Check Requirements Hash

```bash
# Xem hash hiện tại
sha256sum services/common/requirements.txt

# Xem hash đã lưu
python3 -c "import json; print(json.load(open('docker-versions.json'))['base']['last_requirements_hash'])"
```

## Best Practices

1. **Luôn sync versions sau khi tạo git tag**
   - Tự động khi dùng `make git-tag`
   - Manual: `./scripts/docker_version.sh sync-git`

2. **Check base image trước khi build**
   ```bash
   make docker-version-check-base
   ```

3. **Increment base version khi thay đổi dependencies**
   - Tự động khi rebuild base image
   - Manual: `./scripts/docker_version.sh update base`

4. **Commit `docker-versions.json` vào git**
   - Track version history
   - Team members có cùng versions

---

**Version:** 1.0  
**Last Updated:** 2025-12-29

