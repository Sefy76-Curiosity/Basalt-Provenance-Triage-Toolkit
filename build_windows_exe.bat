@echo off
REM ============================================================================
REM Build Script for Basalt Provenance Toolkit v10.1 Windows EXE
REM ============================================================================

echo.
echo ============================================================================
echo Building Basalt Provenance Toolkit v10.1 - Windows Standalone EXE
echo ============================================================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo ERROR: PyInstaller is not installed!
    echo.
    echo Installing PyInstaller...
    python -m pip install pyinstaller
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Failed to install PyInstaller
        echo Please install manually: pip install pyinstaller
        pause
        exit /b 1
    )
)

echo ✓ PyInstaller found
echo.

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo ✓ Cleaned previous builds
echo.

REM Build the EXE
echo Building EXE (this may take 5-10 minutes)...
echo.
pyinstaller --clean Basalt_Provenance_Toolkit.spec

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo BUILD SUCCESSFUL!
echo ============================================================================
echo.
echo The executable has been created:
echo   dist\Basalt_Provenance_Toolkit_v10.1.exe
echo.
echo File size: ~150 MB (includes Python + all dependencies)
echo.
echo This EXE can run on any Windows computer WITHOUT Python installed!
echo ============================================================================
echo.

REM Check file size
for %%A in ("dist\Basalt_Provenance_Toolkit_v10.1.exe") do (
    echo EXE Size: %%~zA bytes
)

echo.
pause
