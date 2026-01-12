@echo off
REM 报销助手 - Windows 打包脚本
REM 使用 PyInstaller 将应用打包成单个 exe 文件

echo ====================================
echo 报销助手 - Windows 打包工具
echo ====================================
echo.

REM 检查 Python 是否已安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.9+
    pause
    exit /b 1
)

echo [1/4] 安装依赖...
pip install -r requirements.txt -q

echo.
echo [2/4] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo [3/4] 开始打包...
python -m PyInstaller --clean build_win.spec

echo.
if exist dist\报销助手.exe (
    echo [4/4] 打包成功！
    echo.
    echo 输出文件: dist\报销助手.exe
    echo.
    echo 您可以将 exe 文件分发给其他用户使用
) else (
    echo [错误] 打包失败，请检查错误信息
)

echo.
pause
