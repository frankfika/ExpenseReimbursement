#!/bin/bash
# 报销助手 - 自动打包脚本
# 每次 git push 后自动打包最新代码

set -e

echo "===================================="
echo "报销助手 - 自动打包工具"
echo "===================================="
echo ""

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 1. 检查是否有新代码
echo -e "${YELLOW}[1/5] 检查更新...${NC}"
git fetch origin > /dev/null 2>&1
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "代码已是最新"
else
    echo "发现更新，正在拉取..."
    git pull origin main
fi

# 2. 安装/更新依赖
echo ""
echo -e "${YELLOW}[2/5] 检查依赖...${NC}"
pip3 install -r requirements.txt -q --upgrade 2>/dev/null || true

# 3. 清理旧文件
echo ""
echo -e "${YELLOW}[3/5] 清理旧构建文件...${NC}"
rm -rf build
rm -rf dist

# 4. 执行打包
echo ""
echo -e "${YELLOW}[4/5] 开始打包 (这可能需要几分钟)...${NC}"

# 使用 build_mac.sh 的打包方式
python3 -m PyInstaller --clean build_mac.spec

# 5. 创建 DMG
echo ""
echo -e "${YELLOW}[5/5] 创建 DMG 安装包...${NC}"

APP_NAME="报销助手"
DMG_NAME="报销助手-Installer"
TEMP_DIR="dist/dmg_temp"

# 检查 .app 是否存在
if [ ! -d "dist/${APP_NAME}.app" ]; then
    echo "错误: 打包失败，未找到 .app 文件"
    exit 1
fi

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
    "dist/${DMG_NAME}.dmg" > /dev/null 2>&1

# 清理临时目录
rm -rf "$TEMP_DIR"

# 6. 显示结果
echo ""
echo -e "${GREEN}===================================="
echo "打包完成！"
echo "====================================${NC}"
echo ""

if [ -f "dist/${DMG_NAME}.dmg" ]; then
    SIZE=$(du -h "dist/${DMG_NAME}.dmg" | cut -f1)
    echo -e "${GREEN}✓${NC} DMG 文件: dist/${DMG_NAME}.dmg (${SIZE})"
    echo ""
    echo "你可以将此文件分发给其他 Mac 用户"
else
    echo "错误: DMG 创建失败"
    exit 1
fi

echo ""
echo "提示: 运行 './build.sh' 可随时重新打包"
