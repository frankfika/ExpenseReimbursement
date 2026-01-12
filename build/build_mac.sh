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

# 读取版本号
VERSION=$(cat VERSION)
VERSION_TAG="v${VERSION}"

echo "版本: ${VERSION_TAG}"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3，请先安装 Python 3.9+"
    exit 1
fi

echo "[1/5] 安装依赖..."
python3 -m pip install -r requirements.txt -q --user

echo ""
echo "[2/5] 清理旧的构建文件..."
rm -rf build/build
rm -rf dist

echo ""
echo "[3/5] 开始打包..."

python3 -m PyInstaller --clean build/build_mac.spec

echo ""
if [ -d "dist/ExpenseHelper.app" ]; then
    echo "[4/5] 打包成功！"
    echo ""
    echo "输出文件: dist/ExpenseHelper.app"
    echo ""
    echo "创建 DMG 镜像..."

    # 创建 DMG
    APP_NAME="ExpenseHelper"
    DMG_NAME="报销助手-${VERSION}"
    TEMP_DIR="dist/dmg_temp"
    DMG_TEMP_DIR="dist/dmg_mount"
    RELEASE_DIR="releases/${VERSION_TAG}"

    # 清理并创建临时目录
    rm -rf "$TEMP_DIR" "$DMG_TEMP_DIR"
    mkdir -p "$TEMP_DIR"

    # 复制 .app 到临时目录
    cp -R "dist/${APP_NAME}.app" "$TEMP_DIR/"

    # 创建 Applications 链接
    ln -s /Applications "$TEMP_DIR/Applications"

    # 先创建一个可读写的临时 DMG
    hdiutil create -volname "报销助手" \
        -srcfolder "$TEMP_DIR" \
        -ov -format UDRW \
        "dist/${DMG_NAME}_temp.dmg"

    # 挂载临时 DMG 并设置视图
    mkdir -p "$DMG_TEMP_DIR"
    hdiutil attach "dist/${DMG_NAME}_temp.dmg" -mountpoint "$DMG_TEMP_DIR" -nobrowse -quiet

    # 使用 AppleScript 设置 Finder 视图
    osascript <<EOF
tell application "Finder"
  tell disk "报销助手"
    open
    set current view of container window to icon view
    set toolbar visible of container window to false
    set statusbar visible of container window to false
    set the bounds of container window to {400, 100, 900, 450}
    set viewOptions to the icon view options of container window
    set arrangement of viewOptions to not arranged
    set icon size of viewOptions to 72
    set position of item "ExpenseHelper.app" of container window to {125, 175}
    set position of item "Applications" of container window to {375, 175}
    close
    update without registering applications
    delay 2
  end tell
end tell
EOF

    # 同步并卸载
    sync
    hdiutil detach "$DMG_TEMP_DIR" -quiet 2>/dev/null || true

    # 压缩成最终 DMG
    hdiutil convert "dist/${DMG_NAME}_temp.dmg" \
        -format UDZO \
        -imagekey zlib-level=9 \
        -o "dist/${DMG_NAME}.dmg"

    # 清理临时文件
    rm -f "dist/${DMG_NAME}_temp.dmg"
    rm -rf "$TEMP_DIR" "$DMG_TEMP_DIR"

    # 创建 releases 目录并复制
    echo ""
    echo "[5/5] 复制到 releases 目录..."
    mkdir -p "$RELEASE_DIR"
    cp "dist/${DMG_NAME}.dmg" "${RELEASE_DIR}/"
    SIZE=$(du -h "${RELEASE_DIR}/${DMG_NAME}.dmg" | cut -f1)

    echo ""
    echo "===================================="
    echo "完成！"
    echo "===================================="
    echo ""
    echo "版本: ${VERSION_TAG}"
    echo "DMG:  ${RELEASE_DIR}/${DMG_NAME}.dmg (${SIZE})"
    echo ""
    echo "如需发布到 GitHub，运行:"
    echo "  gh release create ${VERSION_TAG} ${RELEASE_DIR}/*.dmg"
else
    echo "[错误] 打包失败，请检查错误信息"
fi

echo ""
