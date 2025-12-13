@echo off
REM SyncoPaid Build Script
REM Compiles the Python application into SyncoPaid.exe

echo ================================================
echo SyncoPaid Build Script
echo ================================================
echo.

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo ERROR: Virtual environment not activated!
    echo Please run: venv\Scripts\activate
    echo.
    pause
    exit /b 1
)

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
)

REM Clean previous build artifacts
echo Cleaning previous build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist SyncoPaid.spec.bak del SyncoPaid.spec.bak

REM Generate version information
echo.
echo Generating version information...
python generate_version.py
if errorlevel 1 (
    echo.
    echo ERROR: Failed to generate version information
    pause
    exit /b 1
)

REM Build the executable
echo.
echo Building SyncoPaid.exe...
echo.
pyinstaller SyncoPaid.spec

if errorlevel 1 (
    echo.
    echo ================================================
    echo BUILD FAILED!
    echo ================================================
    pause
    exit /b 1
)

echo.
echo ================================================
echo BUILD SUCCESSFUL!
echo ================================================
echo.
echo Executable location: dist\SyncoPaid.exe
echo.
echo To test the executable:
echo   1. Navigate to dist\ folder
echo   2. Run SyncoPaid.exe
echo   3. Check system tray for the icon
echo.
pause
