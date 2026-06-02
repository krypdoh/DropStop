@echo off
echo DropStop Build Script
echo =====================
echo.

REM Generate the .ico file first
echo Generating icon...
python -m dropstop.icon
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to generate icon. Make sure Pillow is installed.
    exit /b 1
)

echo.
echo Building executable...
pyinstaller --onefile --windowed --icon=dropstop.ico --name=DropStop dropstop\main.py --hidden-import=pystray._win32
if %ERRORLEVEL% neq 0 (
    echo ERROR: PyInstaller build failed.
    exit /b 1
)

echo.
echo Build complete! Executable: dist\DropStop.exe
pause
