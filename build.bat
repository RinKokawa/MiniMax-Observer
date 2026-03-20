@echo off
chcp 65001 >nul
echo ========================================
echo   MiniMax Monitor Build Script
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python first.
    pause
    exit /b 1
)

:: Generate icon
echo [1.5/4] Generating icon...
python scripts/generate_icon.py -q
echo      Done

:: Check dependencies
echo [2/4] Installing dependencies...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo      Done

:: Clean old build
echo [3/4] Cleaning old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo      Done

:: Package
echo [4/4] Running PyInstaller...
pyinstaller MiniMaxMonitor.spec --clean
if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build completed!
echo   Output: dist\MiniMaxMonitor\
echo ========================================
echo.
echo Press any key to open output folder...
pause >nul
explorer dist\MiniMaxMonitor
