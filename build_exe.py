"""
Build script to create executable using PyInstaller
"""

import os
import subprocess
import sys

def build_executable():
    """Build the executable using PyInstaller"""
    
    # PyInstaller command
    cmd = [
        'pyinstaller',
        '--onefile',                    # Create a single executable file
        '--windowed',                   # Hide console window (for GUI apps)
        '--name=WebCrawlerPro',         # Name of the executable
        '--icon=icon.ico',              # Icon file (optional)
        '--add-data=webcrawler.db;.',   # Include database file if it exists
        'main.py'
    ]
    
    # Remove icon parameter if icon file doesn't exist
    if not os.path.exists('icon.ico'):
        cmd.remove('--icon=icon.ico')
    
    # Remove database parameter if it doesn't exist
    if not os.path.exists('webcrawler.db'):
        cmd.remove('--add-data=webcrawler.db;.')
    
    print("Building executable...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build successful!")
        print(f"Executable created in: dist/WebCrawlerPro.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

if __name__ == "__main__":
    success = build_executable()
    if success:
        print("\n" + "="*50)
        print("BUILD COMPLETED SUCCESSFULLY!")
        print("="*50)
        print("Your executable is ready at: dist/WebCrawlerPro.exe")
        print("You can distribute this file to users without Python installed.")
    else:
        print("\n" + "="*50)
        print("BUILD FAILED!")
        print("="*50)
        sys.exit(1)
