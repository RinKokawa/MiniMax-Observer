@echo off
chcp 65001 >nul
echo ========================================
echo   MiniMax Monitor Build Script
echo ========================================
echo.

:: Try multiple ways to find Python
set PYTHON_CMD=

:: 1. Normal PATH
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    goto :found_python
)

:: 2. WindowsApps Python (Microsoft Store)
if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" (
    set PYTHON_CMD=%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe
    goto :found_python
)

:: 3. Try py launcher
py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py
    goto :found_python
)

echo [ERROR] Python not found. Please install Python from:
echo   https://www.python.org/downloads/
echo   or install Python from Microsoft Store.
pause
exit /b 1

:found_python
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is installed but not working properly.
    pause
    exit /b 1
)
echo [OK] Python found.

:: Generate icon
echo [1.5/4] Generating icon...
%PYTHON_CMD% scripts/generate_icon.py -q
echo      Done

:: Check dependencies
echo [2/4] Installing dependencies...
%PYTHON_CMD% -m pip install -r requirements.txt -q
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
%PYTHON_CMD% -m PyInstaller MiniMaxMonitor.spec --clean
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
