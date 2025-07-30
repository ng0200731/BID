"""
Build script for E-BrandID File Downloader executable
"""

import os
import subprocess
import sys

def build_ebrandid_executable():
    """Build the E-BrandID downloader executable using PyInstaller"""
    
    # PyInstaller command for GUI version
    cmd = [
        'pyinstaller',
        '--onefile',                    # Create a single executable file
        '--windowed',                   # Hide console window (for GUI apps)
        '--name=EBrandID_Downloader',   # Name of the executable
        '--add-data=ebrandid_downloader.py;.',  # Include the downloader module
        'ebrandid_gui.py'               # Main GUI file
    ]
    
    print("Building E-BrandID File Downloader executable...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build successful!")
        print(f"Executable created in: dist/EBrandID_Downloader.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def build_console_version():
    """Build console version for testing"""
    cmd = [
        'pyinstaller',
        '--onefile',                    # Create a single executable file
        '--console',                    # Show console window
        '--name=EBrandID_Downloader_Console',
        'test_ebrandid_simple.py'       # Console test file
    ]
    
    print("Building console version...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Console build successful!")
        print(f"Console executable created in: dist/EBrandID_Downloader_Console.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Console build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

if __name__ == "__main__":
    print("E-BrandID File Downloader - Build Script")
    print("=" * 50)
    
    # Build GUI version
    gui_success = build_ebrandid_executable()
    
    print()
    
    # Build console version for testing
    console_success = build_console_version()
    
    print()
    print("=" * 50)
    if gui_success and console_success:
        print("BUILD COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print("Files created:")
        print("- dist/EBrandID_Downloader.exe (GUI version)")
        print("- dist/EBrandID_Downloader_Console.exe (Console test version)")
        print()
        print("The GUI version is ready for distribution!")
    else:
        print("BUILD FAILED!")
        print("=" * 50)
        if not gui_success:
            print("- GUI version build failed")
        if not console_success:
            print("- Console version build failed")
        sys.exit(1)
