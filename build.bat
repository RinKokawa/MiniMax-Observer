@echo off
chcp 65001 >nul
echo ========================================
echo   MiniMax Monitor 构建脚本
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

:: 生成图标
echo [1.5/4] 生成程序图标...
python scripts/generate_icon.py -q
echo      完成

:: 检查依赖
echo [2/4] 检查并安装依赖...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo      完成

:: 清理旧构建
echo [3/4] 清理旧构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo      完成

:: 打包
echo [4/4] 开始打包...
pyinstaller MiniMaxMonitor.spec --clean
if errorlevel 1 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo   构建完成！
echo   可执行文件位于: dist\MiniMaxMonitor\
echo ========================================
echo.
echo 按任意键打开输出目录...
pause >nul
explorer dist\MiniMaxMonitor
