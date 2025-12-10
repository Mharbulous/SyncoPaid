#!/bin/bash
# TimeLawg Build Script (Git Bash / Linux)
# Compiles the Python application into TimeLawg.exe

echo "================================================"
echo "TimeLawg Build Script"
echo "================================================"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "ERROR: Virtual environment not activated!"
    echo "Please run: source venv/Scripts/activate"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if PyInstaller is installed
if ! python -c "import PyInstaller" 2>/dev/null; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install PyInstaller"
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

# Clean previous build artifacts
echo "Cleaning previous build artifacts..."
rm -rf build dist TimeLawg.spec.bak

# Generate version information
echo ""
echo "Generating version information..."
python generate_version.py
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to generate version information"
    read -p "Press Enter to exit..."
    exit 1
fi

# Build the executable
echo ""
echo "Building TimeLawg.exe..."
echo ""
pyinstaller TimeLawg.spec

if [ $? -ne 0 ]; then
    echo ""
    echo "================================================"
    echo "BUILD FAILED!"
    echo "================================================"
    read -p "Press Enter to exit..."
    exit 1
fi

echo ""
echo "================================================"
echo "BUILD SUCCESSFUL!"
echo "================================================"
echo ""
echo "Executable location: dist/TimeLawg.exe"
echo ""
echo "To test the executable:"
echo "  1. Navigate to dist/ folder"
echo "  2. Run TimeLawg.exe"
echo "  3. Check system tray for the icon"
echo ""
read -p "Press Enter to exit..."
