@echo off
echo ========================================
echo Web Crawler Pro Uninstaller
echo ========================================
echo.
echo This will remove Web Crawler Pro from your computer.
echo.
set /p confirm=Are you sure you want to uninstall? (y/N): 
if /i "%confirm%" neq "y" goto :end

echo Removing files...
if exist "C:\Program Files\WebCrawlerPro" rmdir /s /q "C:\Program Files\WebCrawlerPro"

echo Removing desktop shortcut...
if exist "%USERPROFILE%\Desktop\Web Crawler Pro.lnk" del "%USERPROFILE%\Desktop\Web Crawler Pro.lnk"

echo.
echo Uninstallation completed.
:end
pause
