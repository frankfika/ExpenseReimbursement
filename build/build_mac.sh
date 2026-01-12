#!/bin/bash
# 报销助手 - macOS 打包脚本
# 使用 PyInstaller 将应用打包成 .app 文件

set -e

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

echo "===================================="
echo "报销助手 - macOS 打包工具"
echo "===================================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3，请先安装 Python 3.9+"
    exit 1
fi

echo "[1/4] 安装依赖..."
python3 -m pip install -r requirements.txt -q --user

echo ""
echo "[2/4] 清理旧的构建文件..."
rm -rf build dist

echo ""
echo "[3/4] 开始打包..."

python3 -m PyInstaller --clean build/build_mac.spec

echo ""
if [ -d "dist/报销助手.app" ]; then
    echo "[4/4] 打包成功！"
    echo ""
    echo "输出文件: dist/报销助手.app"
    echo ""
    echo "创建 DMG 镜像..."

    # 创建 DMG
    APP_NAME="报销助手"
    DMG_NAME="报销助手-Installer"
    TEMP_DIR="dist/dmg_temp"

    # 清理并创建临时目录
    rm -rf "$TEMP_DIR"
    mkdir -p "$TEMP_DIR"

    # 复制 .app 到临时目录
    cp -R "dist/${APP_NAME}.app" "$TEMP_DIR/"

    # 创建 Applications 链接
    ln -s /Applications "$TEMP_DIR/Applications"

    # 创建 DMG
    hdiutil create -volname "$APP_NAME" \
        -srcfolder "$TEMP_DIR" \
        -ov \
        -format UDZO \
        "dist/${DMG_NAME}.dmg"

    # 清理临时目录
    rm -rf "$TEMP_DIR"

    echo ""
    echo "DMG 文件: dist/${DMG_NAME}.dmg"
    echo ""
    echo "您可以将 DMG 文件分发给其他 Mac 用户使用"
else
    echo "[错误] 打包失败，请检查错误信息"
fi

echo ""
