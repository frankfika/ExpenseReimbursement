# 报销助手 - 桌面应用打包说明

## 概述

本项目可以将报销助手打包成独立的桌面应用，支持 Windows (exe) 和 macOS (dmg) 两种格式。打包后的应用无需用户安装 Python 环境，双击即可运行。

## 打包方式

### macOS 打包

在 macOS 上运行打包脚本：

```bash
./build_mac.sh
```

打包完成后会生成：
- `dist/报销助手.app` - macOS 应用程序
- `dist/报销助手-Installer.dmg` - DMG 安装镜像

**分发方式**：将 `报销助手-Installer.dmg` 文件发送给其他 Mac 用户，用户打开后拖拽到 Applications 文件夹即可安装。

### Windows 打包

在 Windows 上运行打包脚本：

```bash
build_win.bat
```

打包完成后会生成：
- `dist/报销助手.exe` - Windows 可执行文件

**分发方式**：将 `报销助手.exe` 文件发送给 Windows 用户，用户双击即可运行（首次运行可能需要防火墙授权）。

## 注意事项

### 首次运行

用户首次运行应用时，需要进行以下配置：

1. **DeepSeek API Key**：应用会提示用户输入 DeepSeek API Key（用于发票识别分析）
2. **防火墙授权**（Windows）：可能需要允许防火墙访问
3. **安全警告**（macOS）：如果是未签名应用，需要右键点击 -> 打开 -> 信任

### 文件体积

由于打包了 PaddleOCR 等深度学习库，应用体积较大（约 300-400MB），这是正常的。

### 系统要求

- **macOS**: macOS 10.13 或更高版本
- **Windows**: Windows 10 或更高版本
- **内存**: 建议 4GB 以上
- **磁盘空间**: 至少 1GB 可用空间

## 开发者信息

如需修改打包配置，可以编辑以下文件：
- `build_mac.sh` - macOS 打包脚本
- `build_win.bat` - Windows 打包脚本
- `build_win.spec` / `build_mac.spec` - PyInstaller 配置文件
