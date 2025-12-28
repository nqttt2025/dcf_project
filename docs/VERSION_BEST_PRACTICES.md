# Version Management - Best Practices

Hướng dẫn sử dụng hệ thống quản lý version theo best practices.

## 📋 Tổng Quan

Hệ thống quản lý version sử dụng **Git Tag làm Single Source of Truth** cho project version. Tất cả Docker service images đồng bộ với git tag, trong khi base image có version riêng và chỉ increment khi `requirements.txt` thay đổi.

## 🎯 Nguyên Tắc Cơ Bản

### 1. Git Tag là Single Source of Truth
- ✅ **Luôn** tạo git tag trước khi build Docker images
- ✅ **Không** set project version thủ công
- ✅ **Không** commit Docker service versions vào git (tự động sync)

### 2. Base Image Version Độc Lập
- ✅ Base image có version riêng (`v1.0.0`, `v1.0.1`, ...)
- ✅ Chỉ increment khi `requirements.txt` thay đổi
- ✅ Tự động detect bằng SHA256 hash

### 3. Service Versions Tự Động Sync
- ✅ Service versions tự động sync với git tag
- ✅ Không cần maintain thủ công
- ✅ Đảm bảo consistency

## 🚀 Workflow Hàng Ngày

### Scenario 1: Development Normal (Không thay đổi dependencies)

```bash
# 1. Làm việc với code
git add .
git commit -m "Fix bug in DCF calculation"

# 2. Tạo git tag (nếu cần release)
make git-tag-patch
# → Tự động increment patch version (v1.0.0 → v1.0.1)
# → Tự động sync Docker service versions

# 3. Build Docker images
make docker-build
# → Lấy project version từ git tag
# → Base image không rebuild (requirements.txt không đổi)
# → Chỉ build service images

# 4. Deploy
make docker-up
```

**Kết quả:**
- Project version: `v1.0.1` (từ git tag)
- Base image version: `v1.0.0` (không đổi)
- Service versions: `v1.0.1` (sync với git tag)

### Scenario 2: Thay Đổi Dependencies

```bash
# 1. Sửa requirements.txt
vim services/common/requirements.txt
# Thêm: pandas==2.1.4

# 2. Commit changes
git add services/common/requirements.txt
git commit -m "Add pandas dependency"

# 3. Tạo git tag
make git-tag-patch
# → v1.0.0 → v1.0.1

# 4. Build Docker images
make docker-build
# → Detect requirements.txt thay đổi
# → Base image sẽ rebuild và increment version (v1.0.0 → v1.0.1)
# → Service images build với project version (v1.0.1)

# 5. Check versions
make docker-versions
```

**Kết quả:**
- Project version: `v1.0.1` (từ git tag)
- Base image version: `v1.0.1` (increment vì requirements.txt đổi)
- Service versions: `v1.0.1` (sync với git tag)

### Scenario 3: Major Release

```bash
# 1. Chuẩn bị release
git add .
git commit -m "Major refactoring: new architecture"

# 2. Tạo major version tag
make git-tag-major
# → v1.0.0 → v2.0.0

# 3. Build và deploy
make docker-build
make docker-up
```

**Kết quả:**
- Project version: `v2.0.0` (từ git tag)
- Base image version: `v1.0.0` (không đổi nếu requirements.txt không đổi)
- Service versions: `v2.0.0` (sync với git tag)

## 📝 Best Practices Chi Tiết

### 1. Khi Nào Tạo Git Tag?

#### ✅ Nên tạo tag khi:
- **Release mới**: Sau khi hoàn thành feature/fix bug
- **Deploy production**: Trước khi deploy lên production
- **Milestone**: Đạt được milestone quan trọng
- **Hotfix**: Fix bug critical trên production

#### ❌ Không nên tạo tag khi:
- Chỉ commit code development (chưa test)
- Code chưa được review
- Build/test chưa pass

### 2. Loại Version Increment

#### Patch Version (`v1.0.0` → `v1.0.1`)
```bash
make git-tag-patch
```
**Dùng khi:**
- Fix bug
- Minor improvements
- Documentation updates
- Security patches

#### Minor Version (`v1.0.0` → `v1.1.0`)
```bash
make git-tag-minor
```
**Dùng khi:**
- Thêm feature mới (backward compatible)
- API changes (backward compatible)
- New endpoints/services

#### Major Version (`v1.0.0` → `v2.0.0`)
```bash
make git-tag-major
```
**Dùng khi:**
- Breaking changes
- Architecture changes
- API incompatible changes
- Major refactoring

### 3. Quản Lý Base Image Version

#### Base Image Chỉ Rebuild Khi:
- ✅ `requirements.txt` thay đổi
- ✅ Base image chưa tồn tại
- ✅ Force rebuild (`make docker-rebuild`)

#### Base Image Không Rebuild Khi:
- ❌ Chỉ thay đổi service code
- ❌ Chỉ thay đổi config files
- ❌ Chỉ thay đổi documentation

#### Check Base Image:
```bash
# Check xem base image có cần rebuild không
make docker-version-check-base

# Output:
# rebuild - Cần rebuild (requirements.txt thay đổi)
# no-rebuild - Không cần rebuild
```

### 4. Workflow với Git

#### Workflow Khuyến Nghị:

```bash
# 1. Development
git checkout -b feature/new-feature
# ... làm việc với code ...
git add .
git commit -m "Add new feature"

# 2. Test locally
make test
make docker-build
make docker-up

# 3. Merge to main
git checkout main
git merge feature/new-feature

# 4. Create release tag
make git-tag-patch  # hoặc minor/major

# 5. Build và deploy
make docker-build
make docker-up

# 6. Push tag to remote
git push origin v1.0.1
```

### 5. Auto-Tagging từ Commit Message

#### Format:
```
[version: v1.0.1] hoặc [release: v1.0.1]
```

#### Example:
```bash
git commit -m "Fix critical bug [version: v1.0.1]"
./scripts/auto_tag_from_commit.sh
# → Tự động tạo tag v1.0.1 và sync Docker versions
```

#### Git Hook (Tự động):
```bash
# .git/hooks/post-commit
# Tự động tạo tag nếu commit message có [version: vX.Y.Z]
```

### 6. Version Checking

#### Check Project Version:
```bash
make get-version
# Output: v1.0.1 hoặc dev-abc123 hoặc dev-20251229-001234
```

#### Check Docker Versions:
```bash
make docker-versions
# Output:
# Docker Versions:
# ==================================================
# Base Image:
#   Version: v1.0.0
#   Last Updated: 2025-12-29 10:00:00
#   Requirements Hash: 4aa4dbb54b0ccd58...
# 
# Services:
#   gateway      Version: v1.0.1     Depends on base: ✓
#   dcf          Version: v1.0.1     Depends on base: ✓
#   stock        Version: v1.0.1     Depends on base: ✓
#   frontend     Version: v1.0.1     Depends on base: ✗
# 
# Project Version (from git tag):
#   v1.0.1
```

#### Check Base Image:
```bash
make docker-version-check-base
```

## 🔧 Troubleshooting

### Vấn Đề 1: Versions Không Đồng Bộ

**Triệu chứng:**
```bash
make docker-versions
# Service versions khác với git tag
```

**Giải pháp:**
```bash
# Sync lại với git tag
./scripts/docker_version.sh sync-git

# Hoặc tạo lại git tag
make git-tag VERSION=v1.0.1
```

### Vấn Đề 2: Base Image Không Rebuild Khi Cần

**Triệu chứng:**
```bash
make docker-version-check-base
# no-rebuild (nhưng requirements.txt đã đổi)
```

**Giải pháp:**
```bash
# Force rebuild base image
make docker-rebuild

# Hoặc manual update hash
./scripts/docker_version.sh update base
```

### Vấn Đề 3: Project Version Không Đúng

**Triệu chứng:**
```bash
make get-version
# dev-abc123 (không có git tag)
```

**Giải pháp:**
```bash
# Tạo git tag
make git-tag VERSION=v1.0.0

# Check lại
make get-version
# v1.0.0
```

### Vấn Đề 4: Docker Build Dùng Version Cũ

**Triệu chứng:**
```bash
make docker-build
# Build với version cũ mặc dù đã tạo tag mới
```

**Giải pháp:**
```bash
# Check git tag
git describe --tags --abbrev=0

# Nếu tag mới chưa có, tạo tag
make git-tag VERSION=v1.0.1

# Rebuild
make docker-build
```

## 📊 Examples Thực Tế

### Example 1: Feature Development

```bash
# 1. Start feature
git checkout -b feature/add-cache

# 2. Development
# ... code changes ...
git add .
git commit -m "Add Redis cache support"

# 3. Test
make test
make docker-build

# 4. Merge và release
git checkout main
git merge feature/add-cache
make git-tag-minor  # v1.0.0 → v1.1.0 (new feature)

# 5. Deploy
make docker-build
make docker-up
```

### Example 2: Bug Fix

```bash
# 1. Fix bug
git checkout -b hotfix/fix-calculation
# ... fix code ...
git add .
git commit -m "Fix DCF calculation error"

# 2. Test
make test
make docker-build

# 3. Merge và release
git checkout main
git merge hotfix/fix-calculation
make git-tag-patch  # v1.0.0 → v1.0.1 (bug fix)

# 4. Deploy
make docker-build
make docker-up
```

### Example 3: Update Dependencies

```bash
# 1. Update requirements.txt
vim services/common/requirements.txt
# Thêm: fastapi==0.104.1

# 2. Commit
git add services/common/requirements.txt
git commit -m "Update FastAPI to 0.104.1"

# 3. Create tag
make git-tag-patch  # v1.0.0 → v1.0.1

# 4. Build (base image sẽ rebuild)
make docker-build
# → Base image: v1.0.0 → v1.0.1 (requirements.txt đổi)
# → Service images: v1.0.1 (sync với git tag)

# 5. Deploy
make docker-up
```

### Example 4: Major Refactoring

```bash
# 1. Refactor
git checkout -b refactor/microservices
# ... major changes ...
git add .
git commit -m "Refactor to microservices architecture"

# 2. Test thoroughly
make test
make docker-build
make docker-up
# ... test all services ...

# 3. Release major version
git checkout main
git merge refactor/microservices
make git-tag-major  # v1.0.0 → v2.0.0

# 4. Deploy
make docker-build
make docker-up
```

## ✅ Checklist Trước Khi Release

- [ ] Code đã được test
- [ ] All tests pass (`make test`)
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Git tag created (`make git-tag-patch/minor/major`)
- [ ] Docker versions synced (`make docker-versions`)
- [ ] Docker images built (`make docker-build`)
- [ ] Docker containers tested (`make docker-up`)
- [ ] Git tag pushed to remote (`git push origin vX.Y.Z`)

## 🎓 Tips & Tricks

### 1. Quick Version Check
```bash
# Xem tất cả versions một lúc
make get-version && make docker-versions
```

### 2. Auto-Increment trong Script
```bash
# Tự động increment và build
make git-tag-patch && make docker-build
```

### 3. Check Base Image Trước Build
```bash
# Check base image trước khi build để tiết kiệm thời gian
if make docker-version-check-base | grep -q "rebuild"; then
    echo "Base image needs rebuild"
    make docker-build
else
    echo "Base image unchanged, quick build"
    make docker-build-fast
fi
```

### 4. Version trong CI/CD
```yaml
# .github/workflows/deploy.yml
- name: Get version
  run: make get-version > VERSION.txt
  
- name: Build Docker images
  run: make docker-build
  
- name: Tag images
  run: |
    VERSION=$(cat VERSION.txt)
    docker tag dcf-project-gateway:$VERSION dcf-project-gateway:latest
```

## 📚 Tài Liệu Tham Khảo

- [Version Management](./VERSION_MANAGEMENT.md) - Chi tiết về hệ thống version
- [Docker Version Management](./DOCKER_VERSION_MANAGEMENT.md) - Quản lý Docker versions
- [Docker Build Optimization](./DOCKER_BUILD_OPTIMIZATION.md) - Tối ưu Docker builds

---

**Version:** 1.0  
**Last Updated:** 2025-12-29  
**Maintainer:** DCF Project Team

