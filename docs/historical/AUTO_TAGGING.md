# Auto Tagging System

Hệ thống tự động tạo git tag và tag Docker images.

## Tổng quan

Có 3 cách để tự động tạo tag:

1. **Auto-increment version** - Tự động tăng version (patch/minor/major)
2. **Auto-tag from commit message** - Tạo tag từ commit message
3. **Auto-tag on build** - Tự động tạo tag khi build Docker images

## 1. Auto-Increment Version

Tự động tăng version theo semantic versioning.

### Commands

```bash
# Tăng patch version (v1.0.0 -> v1.0.1)
make git-tag-patch
# hoặc
make git-tag-auto

# Tăng minor version (v1.0.0 -> v1.1.0)
make git-tag-minor

# Tăng major version (v1.0.0 -> v2.0.0)
make git-tag-major
```

### Ví dụ

```bash
# Hiện tại: v1.0.0
make git-tag-patch
# Kết quả: v1.0.1

make git-tag-minor
# Kết quả: v1.1.0

make git-tag-major
# Kết quả: v2.0.0
```

## 2. Auto-Tag from Commit Message

Tự động tạo tag từ commit message nếu có pattern version.

### Commit Message Format

```bash
# Pattern 1: [version: v1.0.0]
git commit -m "Fix bug [version: v1.0.1]"

# Pattern 2: [release: v1.0.0]
git commit -m "New feature [release: v1.1.0]"
```

### Command

```bash
# Tạo tag từ commit message
make git-tag-from-commit
```

### Git Hook (Tự động)

Git hook tự động chạy sau mỗi commit:

```bash
# Hook được cài đặt tại: .git/hooks/post-commit
# Tự động tạo tag nếu commit message có version pattern
```

## 3. Auto-Tag on Build

Tự động tạo tag khi build Docker images nếu chưa có tag.

### Commands

```bash
# Build với auto-tagging
make docker-build-auto

# Rebuild với auto-tagging
make docker-rebuild-auto
```

### Behavior

- Nếu chưa có git tag → Tự động tạo tag v1.0.0
- Nếu có uncommitted changes → Tự động tăng patch version và tạo tag
- Nếu đã có tag và code clean → Sử dụng tag hiện tại

## Workflow Examples

### Workflow 1: Auto-increment và Build

```bash
# 1. Tăng patch version
make git-tag-patch
# Output: Created tag: v1.0.1

# 2. Build với version mới
make docker-rebuild
# Images được tag với v1.0.1
```

### Workflow 2: Commit với version và Build

```bash
# 1. Commit với version trong message
git commit -m "Fix critical bug [version: v1.0.2]"

# 2. Tag được tạo tự động (nếu có git hook)
# Hoặc tạo thủ công:
make git-tag-from-commit

# 3. Build
make docker-rebuild
```

### Workflow 3: Auto-build (Fully Automatic)

```bash
# 1. Commit changes
git add .
git commit -m "New feature"

# 2. Build với auto-tagging
make docker-rebuild-auto
# Tự động tạo tag nếu cần và build images
```

### Workflow 4: Semantic Versioning

```bash
# Bug fix → Patch version
make git-tag-patch
make docker-rebuild

# New feature → Minor version
make git-tag-minor
make docker-rebuild

# Breaking change → Major version
make git-tag-major
make docker-rebuild
```

## Scripts

### `scripts/auto_version.sh`

Tự động tăng version:

```bash
# Patch (default)
./scripts/auto_version.sh patch

# Minor
./scripts/auto_version.sh minor

# Major
./scripts/auto_version.sh major
```

### `scripts/auto_tag_from_commit.sh`

Tạo tag từ commit message:

```bash
./scripts/auto_tag_from_commit.sh
```

## Git Hooks

### Post-Commit Hook

Tự động chạy sau mỗi commit để tạo tag nếu commit message có version pattern.

Location: `.git/hooks/post-commit`

**Enable:**
```bash
chmod +x .git/hooks/post-commit
```

**Disable:**
```bash
chmod -x .git/hooks/post-commit
```

## Best Practices

### 1. Use Semantic Versioning

- **Patch** (v1.0.0 → v1.0.1): Bug fixes
- **Minor** (v1.0.0 → v1.1.0): New features (backward compatible)
- **Major** (v1.0.0 → v2.0.0): Breaking changes

### 2. Tag Before Build

Luôn tạo tag trước khi build production:

```bash
make git-tag-patch
make docker-rebuild
```

### 3. Use Commit Messages

Ghi version trong commit message để dễ trace:

```bash
git commit -m "Fix bug [version: v1.0.1]"
```

### 4. Push Tags

Sau khi tạo tag, push lên remote:

```bash
git push origin v1.0.1
```

## Troubleshooting

### Tag không được tạo tự động

Kiểm tra git hook:
```bash
ls -la .git/hooks/post-commit
chmod +x .git/hooks/post-commit
```

### Version không tăng đúng

Kiểm tra tag hiện tại:
```bash
git tag
git describe --tags --abbrev=0
```

### Auto-tag không hoạt động

Kiểm tra uncommitted changes:
```bash
git status
```

---

**Version:** 1.0  
**Last Updated:** 2025-12-29

