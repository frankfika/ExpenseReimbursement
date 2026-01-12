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

## 构建流程

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

## 发布到 GitHub

本地构建完成后，使用 GitHub CLI 发布：

```bash
# 创建 Release 并上传文件
gh release create v1.0.0 \
  --title "报销助手 v1.0.0" \
  --notes "发布说明..." \
  releases/v1.0.0/*
```

## 版本管理

版本号定义在项目根目录的 `VERSION` 文件中：

```
1.0.0
```

发布新版本时：
1. 更新 `VERSION` 文件
2. 运行构建脚本
3. 发布到 GitHub Releases
4. 打 git tag: `git tag v1.0.0 && git push --tags`
