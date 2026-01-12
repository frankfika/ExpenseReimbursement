# Releases

本地构建的安装包存放在此处，按版本号组织。

## 目录结构

```
releases/
├── v1.0.0/
│   ├── 报销助手-1.0.0.dmg    # macOS 安装包
│   └── 报销助手-1.0.0.exe    # Windows 安装包
├── v1.0.1/
│   └── ...
└── README.md
```

## 本地构建

### macOS
```bash
# 自动构建（推荐）
./build/build.sh

# 手动构建
./build/build_mac.sh
```

构建完成后，安装包会自动复制到 `releases/v<VERSION>/` 目录。

### Windows
```bash
# 使用 PyInstaller 手动构建
pyinstaller --clean --onefile --windowed ^
  --name "报销助手" ^
  --add-data "web/templates;web/templates" ^
  --add-data "web/static;web/static" ^
  --hidden-import webview ^
  --hidden-import flask ^
  --hidden-import paddleocr ^
  desktop_app.py

# 手动复制到 releases 目录
copy dist\报销助手.exe releases\v1.0.0\
```

## GitHub 自动发布（推荐）

**更简单的方式：使用 GitHub Actions 自动构建和发布**

```bash
# 1. 更新版本号
echo '1.0.1' > VERSION

# 2. 提交并打 tag
git add VERSION
git commit -m "bump: v1.0.1"
git tag v1.0.1

# 3. 推送 tag（自动触发构建和发布）
git push origin main --tags
```

推送 tag 后，GitHub Actions 会自动：
- 构建 macOS DMG 和 Windows EXE
- 创建 GitHub Release
- 上传安装包到 Release

访问 https://github.com/frankfika/ExpenseReimbursement/releases 下载。

## 版本管理

版本号定义在项目根目录的 `VERSION` 文件中：

```
1.0.0
```

发布新版本时：
1. 更新 `VERSION` 文件
2. 创建并推送 git tag
3. GitHub Actions 自动处理其余工作
