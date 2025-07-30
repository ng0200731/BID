"""
Simple installer creator for Web Crawler Pro
Creates a self-extracting installer using Python
"""

import os
import shutil
import zipfile
from datetime import datetime

def create_installer():
    """Create a simple installer package"""
    
    installer_dir = "WebCrawlerPro_Installer"
    
    # Create installer directory
    if os.path.exists(installer_dir):
        shutil.rmtree(installer_dir)
    os.makedirs(installer_dir)
    
    # Files to include in installer
    files_to_include = [
        "dist/WebCrawlerPro.exe",
        "README.md",
        "GETTING_STARTED.md"
    ]
    
    # Copy files to installer directory
    for file_path in files_to_include:
        if os.path.exists(file_path):
            if "/" in file_path:
                filename = file_path.split("/")[-1]
            else:
                filename = file_path
            shutil.copy2(file_path, os.path.join(installer_dir, filename))
            print(f"Copied: {file_path}")
        else:
            print(f"Warning: {file_path} not found")
    
    # Create installation script
    install_script = """@echo off
echo ========================================
echo Web Crawler Pro Installer
echo ========================================
echo.
echo This will install Web Crawler Pro on your computer.
echo.
pause

echo Creating installation directory...
if not exist "C:\\Program Files\\WebCrawlerPro" mkdir "C:\\Program Files\\WebCrawlerPro"

echo Copying files...
copy "WebCrawlerPro.exe" "C:\\Program Files\\WebCrawlerPro\\"
copy "README.md" "C:\\Program Files\\WebCrawlerPro\\"
copy "GETTING_STARTED.md" "C:\\Program Files\\WebCrawlerPro\\"

echo Creating desktop shortcut...
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%USERPROFILE%\\Desktop\\Web Crawler Pro.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "C:\\Program Files\\WebCrawlerPro\\WebCrawlerPro.exe" >> CreateShortcut.vbs
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
echo - Or directly: C:\\Program Files\\WebCrawlerPro\\WebCrawlerPro.exe
echo.
pause
"""
    
    # Write install script
    with open(os.path.join(installer_dir, "install.bat"), 'w') as f:
        f.write(install_script)
    
    # Create uninstall script
    uninstall_script = """@echo off
echo ========================================
echo Web Crawler Pro Uninstaller
echo ========================================
echo.
echo This will remove Web Crawler Pro from your computer.
echo.
set /p confirm=Are you sure you want to uninstall? (y/N): 
if /i "%confirm%" neq "y" goto :end

echo Removing files...
if exist "C:\\Program Files\\WebCrawlerPro" rmdir /s /q "C:\\Program Files\\WebCrawlerPro"

echo Removing desktop shortcut...
if exist "%USERPROFILE%\\Desktop\\Web Crawler Pro.lnk" del "%USERPROFILE%\\Desktop\\Web Crawler Pro.lnk"

echo.
echo Uninstallation completed.
:end
pause
"""
    
    with open(os.path.join(installer_dir, "uninstall.bat"), 'w') as f:
        f.write(uninstall_script)
    
    # Create README for installer
    installer_readme = f"""# Web Crawler Pro Installer

## Installation Instructions

1. **Run as Administrator**: Right-click on `install.bat` and select "Run as administrator"
2. **Follow prompts**: The installer will guide you through the process
3. **Desktop shortcut**: A shortcut will be created on your desktop

## What gets installed:

- **Program**: C:\\Program Files\\WebCrawlerPro\\WebCrawlerPro.exe
- **Documentation**: README.md and GETTING_STARTED.md
- **Desktop shortcut**: "Web Crawler Pro"

## System Requirements:

- Windows 7 or later
- No additional software required (standalone executable)

## Uninstallation:

Run `uninstall.bat` as administrator to remove the program.

## Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

For support and documentation, see the included README.md file.
"""
    
    with open(os.path.join(installer_dir, "INSTALLER_README.txt"), 'w') as f:
        f.write(installer_readme)
    
    # Create ZIP package
    zip_filename = f"WebCrawlerPro_Installer_{datetime.now().strftime('%Y%m%d')}.zip"
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(installer_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, installer_dir)
                zipf.write(file_path, arcname)
    
    print(f"\n{'='*50}")
    print("INSTALLER CREATED SUCCESSFULLY!")
    print(f"{'='*50}")
    print(f"Installer package: {zip_filename}")
    print(f"Installer folder: {installer_dir}")
    print("\nTo distribute:")
    print(f"1. Send users the {zip_filename} file")
    print("2. Users should extract it and run install.bat as administrator")
    print("\nThe installer includes:")
    print("- WebCrawlerPro.exe (main application)")
    print("- Documentation files")
    print("- Install/uninstall scripts")
    print("- Desktop shortcut creation")

if __name__ == "__main__":
    create_installer()
