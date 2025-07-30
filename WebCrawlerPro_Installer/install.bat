@echo off
echo ========================================
echo Web Crawler Pro Installer
echo ========================================
echo.
echo This will install Web Crawler Pro on your computer.
echo.
pause

echo Creating installation directory...
if not exist "C:\Program Files\WebCrawlerPro" mkdir "C:\Program Files\WebCrawlerPro"

echo Copying files...
copy "WebCrawlerPro.exe" "C:\Program Files\WebCrawlerPro\"
copy "README.md" "C:\Program Files\WebCrawlerPro\"
copy "GETTING_STARTED.md" "C:\Program Files\WebCrawlerPro\"

echo Creating desktop shortcut...
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%USERPROFILE%\Desktop\Web Crawler Pro.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "C:\Program Files\WebCrawlerPro\WebCrawlerPro.exe" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript CreateShortcut.vbs
del CreateShortcut.vbs

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo You can now run Web Crawler Pro from:
echo - Desktop shortcut: "Web Crawler Pro"
echo - Or directly: C:\Program Files\WebCrawlerPro\WebCrawlerPro.exe
echo.
pause
