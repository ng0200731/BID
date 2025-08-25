@echo off
echo ========================================
echo BID Smart App - Executable Builder
echo ========================================
echo.

echo 1. Installing build requirements...
pip install -r requirements_exe.txt

echo.
echo 2. Building executable...
python build_exe.py

echo.
echo 3. Build process completed!
echo Check the dist/ folder for BID_Smart_App.exe

pause
