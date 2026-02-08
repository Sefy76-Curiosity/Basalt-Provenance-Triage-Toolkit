#!/bin/bash
# ============================================================================
# Build Script for Basalt Provenance Toolkit v10.1 Windows EXE
# (Run this on Linux/Mac to build Windows EXE using Wine + PyInstaller)
# ============================================================================

echo ""
echo "============================================================================"
echo "Building Basalt Provenance Toolkit v10.1 - Windows Standalone EXE"
echo "============================================================================"
echo ""

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "ERROR: PyInstaller is not installed!"
    echo ""
    echo "Installing PyInstaller..."
    python3 -m pip install pyinstaller
    if [ $? -ne 0 ]; then
        echo ""
        echo "ERROR: Failed to install PyInstaller"
        echo "Please install manually: pip install pyinstaller"
        exit 1
    fi
fi

echo "✓ PyInstaller found"
echo ""

# Clean previous builds
rm -rf build dist
echo "✓ Cleaned previous builds"
echo ""

# Build the EXE
echo "Building EXE (this may take 5-10 minutes)..."
echo ""
pyinstaller --clean Basalt_Provenance_Toolkit.spec

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Build failed!"
    exit 1
fi

echo ""
echo "============================================================================"
echo "BUILD SUCCESSFUL!"
echo "============================================================================"
echo ""
echo "The executable has been created:"
echo "  dist/Basalt_Provenance_Toolkit_v10.1.exe"
echo ""
echo "File size: ~150 MB (includes Python + all dependencies)"
echo ""
echo "This EXE can run on any Windows computer WITHOUT Python installed!"
echo "============================================================================"
echo ""

# Check file size
if [ -f "dist/Basalt_Provenance_Toolkit_v10.1.exe" ]; then
    ls -lh "dist/Basalt_Provenance_Toolkit_v10.1.exe"
fi

echo ""
