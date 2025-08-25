# -*- coding: utf-8 -*-
"""
Build script to convert Flask web app to executable
Creates a standalone .exe file with embedded web server
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def create_pyinstaller_spec():
    """Create PyInstaller spec file for the web app"""
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Data files to include
datas = [
    ('templates', 'templates'),
    ('requirements.txt', '.'),
    ('README.md', '.'),
    ('VERSION_TRACKING.md', '.'),
    ('PROJECT_STATUS_AND_NEXT_STEPS.md', '.'),
]

# Hidden imports for Flask and dependencies
hiddenimports = [
    'flask',
    'requests',
    'beautifulsoup4',
    'selenium',
    'webdriver_manager',
    'openpyxl',
    'sqlite3',
    'threading',
    'webbrowser',
    'datetime',
    'json',
    'urllib3',
    'lxml',
    'pillow',
    'pandas',
    'tkinter',
    'tkinter.filedialog',
    'subprocess',
    'time',
    're'
]

a = Analysis(
    ['smart_app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'IPython',
        'jupyter'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyd = []
for d in a.datas:
    if 'pyconfig' in d[0]:
        pyd.append(d)

a.datas = [x for x in a.datas if x not in pyd]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BID_Smart_App',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico'  # Optional: add icon file
)
'''
    
    with open('smart_app.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ Created PyInstaller spec file: smart_app.spec")

def modify_app_for_executable():
    """Modify smart_app.py for executable compatibility"""
    
    print("🔧 Modifying smart_app.py for executable compatibility...")
    
    # Read the current file
    with open('smart_app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add executable-specific imports and functions at the top
    executable_additions = '''
import sys
import os
import webbrowser
import threading
import time
from pathlib import Path

# Fix encoding issues for Windows executable
if hasattr(sys, 'frozen'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_data_directory():
    """Get directory for user data (database, downloads, etc.)"""
    if getattr(sys, 'frozen', False):
        # Running as executable
        app_data = os.path.join(os.path.expanduser('~'), 'BID_Smart_App')
        os.makedirs(app_data, exist_ok=True)
        return app_data
    else:
        # Running as script
        return os.getcwd()

def select_folder(title="Select Folder"):
    """Open folder selection dialog"""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.attributes('-topmost', True)  # Bring to front

        folder = filedialog.askdirectory(title=title)
        root.destroy()

        return folder if folder else None
    except ImportError:
        # Fallback: use current directory
        return os.getcwd()

def setup_user_directories():
    """Setup user directories with folder selection for executable"""
    if getattr(sys, 'frozen', False):
        settings_file = os.path.join(get_data_directory(), 'user_settings.json')

        # Check if settings already exist
        if os.path.exists(settings_file):
            import json
            with open(settings_file, 'r') as f:
                settings = json.load(f)
            return settings.get('download_directory'), settings.get('reports_directory')

        # First time setup - let user choose directories
        print("First time setup - Please select directories...")

        # Select download directory
        print("Please select folder for downloading artwork files...")
        download_dir = select_folder("Select Download Folder for Artwork Files")
        if not download_dir:
            download_dir = os.path.join(get_data_directory(), 'download_artwork')
            os.makedirs(download_dir, exist_ok=True)

        # Select reports directory
        print("Please select folder for saving reports (QC, Stickers, Packing Lists)...")
        reports_dir = select_folder("Select Reports Folder")
        if not reports_dir:
            reports_dir = os.path.join(get_data_directory(), 'reports')
            os.makedirs(reports_dir, exist_ok=True)

        # Create subdirectories
        os.makedirs(os.path.join(reports_dir, 'qc_report'), exist_ok=True)
        os.makedirs(os.path.join(reports_dir, 'stickers'), exist_ok=True)
        os.makedirs(os.path.join(reports_dir, 'packing_lists'), exist_ok=True)

        # Save user preferences
        settings = {
            'download_directory': download_dir,
            'reports_directory': reports_dir
        }

        import json
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)

        print(f"Download folder: {download_dir}")
        print(f"Reports folder: {reports_dir}")

        return download_dir, reports_dir
    else:
        # Running as script - use current directory
        return 'download_artwork', 'report'

def get_user_directories():
    """Get user-selected directories"""
    if getattr(sys, 'frozen', False):
        settings_file = os.path.join(get_data_directory(), 'user_settings.json')
        if os.path.exists(settings_file):
            import json
            with open(settings_file, 'r') as f:
                settings = json.load(f)
            return settings.get('download_directory'), settings.get('reports_directory')
        else:
            # Settings don't exist - return defaults, setup will be called from main
            default_download = os.path.join(get_data_directory(), 'download_artwork')
            default_reports = os.path.join(get_data_directory(), 'reports')
            return default_download, default_reports
    else:
        return 'download_artwork', 'report'

def open_browser_delayed():
    """Open browser after a short delay to ensure server is ready"""
    time.sleep(2)
    webbrowser.open('http://localhost:5002')
    print("Browser opened to http://localhost:5002")

'''
    
    # Insert after the imports section
    import_end = content.find('app = Flask(__name__)')
    if import_end == -1:
        import_end = content.find('from datetime import datetime') + len('from datetime import datetime\n')
    
    modified_content = content[:import_end] + executable_additions + content[import_end:]
    
    # Modify database path to use user data directory
    modified_content = modified_content.replace(
        "sqlite3.connect('po_database.db')",
        "sqlite3.connect(os.path.join(get_data_directory(), 'po_database.db'))"
    )
    
    # Update directory paths to use user-selected directories
    modified_content = modified_content.replace(
        "sqlite3.connect('po_database.db')",
        "sqlite3.connect(os.path.join(get_data_directory(), 'po_database.db'))"
    )

    # Add global variables for user directories at the top
    directory_setup = '''
# Global variables for user-selected directories
USER_DOWNLOAD_DIR = None
USER_REPORTS_DIR = None

def init_user_directories():
    """Initialize user directory variables"""
    global USER_DOWNLOAD_DIR, USER_REPORTS_DIR
    if getattr(sys, 'frozen', False):
        USER_DOWNLOAD_DIR, USER_REPORTS_DIR = get_user_directories()
    else:
        USER_DOWNLOAD_DIR, USER_REPORTS_DIR = 'download_artwork', 'report'

def get_download_dir():
    """Get download directory"""
    return USER_DOWNLOAD_DIR or 'download_artwork'

def get_reports_dir():
    """Get reports directory"""
    return USER_REPORTS_DIR or 'report'

def open_folder_in_explorer(folder_path):
    """Open folder in Windows Explorer"""
    try:
        import subprocess
        import os
        if os.path.exists(folder_path):
            subprocess.run(['explorer', folder_path], check=True)
            return True
        else:
            print(f"Folder does not exist: {folder_path}")
            return False
    except Exception as e:
        print(f"Error opening folder: {e}")
        return False

'''

    # Insert directory setup after imports
    flask_app_pos = modified_content.find('app = Flask(__name__)')
    modified_content = modified_content[:flask_app_pos] + directory_setup + modified_content[flask_app_pos:]

    # Replace all hardcoded directory references
    replacements = [
        ("'download_artwork'", "get_download_dir()"),
        ('"download_artwork"', "get_download_dir()"),
        ("'report'", "get_reports_dir()"),
        ('"report"', "get_reports_dir()"),
        ("os.path.join('report', 'qc_report')", "os.path.join(get_reports_dir(), 'qc_report')"),
        ('os.path.join("report", "qc_report")', "os.path.join(get_reports_dir(), 'qc_report')"),
        ("f'report/qc_report'", "f'{get_reports_dir()}/qc_report'"),
        ('f"report/qc_report"', "f'{get_reports_dir()}/qc_report'"),
    ]

    for old_path, new_path in replacements:
        modified_content = modified_content.replace(old_path, new_path)

    # Fix specific issues for folder opening

    # 1. Fix "Open Folder" button in download artwork tab
    modified_content = modified_content.replace(
        "subprocess.run(['explorer', download_folder])",
        "subprocess.run(['explorer', get_download_dir()])"
    )

    # 2. Add auto-folder opening after QC report download
    qc_download_pattern = r'return send_file\(file_path, as_attachment=True, download_name=filename\)'
    qc_replacement = '''result = send_file(file_path, as_attachment=True, download_name=filename)
        # Auto-open folder after download
        if getattr(sys, 'frozen', False):
            folder_path = os.path.dirname(file_path)
            threading.Thread(target=lambda: (time.sleep(1), open_folder_in_explorer(folder_path)), daemon=True).start()
        return result'''

    import re
    modified_content = re.sub(qc_download_pattern, qc_replacement, modified_content)

    # 3. Add auto-folder opening after sticker download
    sticker_download_pattern = r'return send_file\(sticker_path, as_attachment=True, download_name=filename\)'
    sticker_replacement = '''result = send_file(sticker_path, as_attachment=True, download_name=filename)
        # Auto-open folder after download
        if getattr(sys, 'frozen', False):
            folder_path = os.path.dirname(sticker_path)
            threading.Thread(target=lambda: (time.sleep(1), open_folder_in_explorer(folder_path)), daemon=True).start()
        return result'''

    modified_content = re.sub(sticker_download_pattern, sticker_replacement, modified_content)
    
    # Add browser auto-launch in main section
    main_section = '''if __name__ == '__main__':
    print(f"Starting artwork downloader v{VERSION}...")
    print(f"Version Date: {VERSION_DATE}")
    print(f"Last Edit: {LAST_EDIT}")

    # Setup user directories for executable (only once)
    if getattr(sys, 'frozen', False):
        setup_user_directories()
        init_user_directories()

    print("Initializing PO database...")
    init_database()

    # Auto-open browser for executable
    if getattr(sys, 'frozen', False):
        print("Starting browser...")
        browser_thread = threading.Thread(target=open_browser_delayed)
        browser_thread.daemon = True
        browser_thread.start()

    print("Server starting on http://localhost:5002")
    print("Press Ctrl+C to stop the server")
    app.run(host='127.0.0.1', port=5002, debug=False)'''
    
    # Replace the existing main section
    old_main_start = modified_content.find("if __name__ == '__main__':")
    if old_main_start != -1:
        modified_content = modified_content[:old_main_start] + main_section
    
    # Remove all emoji and special Unicode characters for Windows compatibility
    import re

    # Comprehensive emoji removal pattern
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"  # dingbats
                               u"\U000024C2-\U0001F251"  # enclosed characters
                               u"\U0001F900-\U0001F9FF"  # supplemental symbols
                               u"\U0001FA00-\U0001FA6F"  # chess symbols
                               u"\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
                               u"\U00002600-\U000026FF"  # miscellaneous symbols
                               u"\U00002700-\U000027BF"  # dingbats
                               "]+", flags=re.UNICODE)

    modified_content = emoji_pattern.sub('', modified_content)

    # Also replace common problematic characters
    replacements = {
        '🚀': 'Starting',
        '📅': 'Date:',
        '📝': 'Edit:',
        '📊': 'Database',
        '🌐': 'Browser',
        '🛑': 'Stop',
        '✅': 'OK',
        '❌': 'ERROR',
        '🧹': 'Cleaning',
        '🔍': 'DEBUG',
        '💡': 'TIP',
        '📁': 'Files',
        '🎉': 'Success',
        '📋': 'Steps',
        '🔧': 'Check'
    }

    for emoji, replacement in replacements.items():
        modified_content = modified_content.replace(emoji, replacement)

    # Write the modified file
    with open('smart_app_executable.py', 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print("✅ Created executable-ready version: smart_app_executable.py")

def build_executable():
    """Build the executable using PyInstaller"""
    
    print("🔨 Building executable with PyInstaller...")
    
    # Update spec file to use the modified Python file
    with open('smart_app.spec', 'r') as f:
        spec_content = f.read()
    
    spec_content = spec_content.replace("['smart_app.py']", "['smart_app_executable.py']")
    
    with open('smart_app.spec', 'w') as f:
        f.write(spec_content)
    
    # Run PyInstaller
    try:
        result = subprocess.run([
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            'smart_app.spec'
        ], check=True, capture_output=True, text=True)
        
        print("✅ Executable built successfully!")
        print(f"📁 Output location: dist/BID_Smart_App.exe")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    
    return True

def create_installer_script():
    """Create NSIS installer script"""
    
    installer_script = '''
; BID Smart App Installer Script
; Generated by build_exe.py

!define APP_NAME "BID Smart App"
!define APP_VERSION "3.3.0"
!define APP_PUBLISHER "BID Solutions"
!define APP_URL "https://github.com/ng0200731/BID"
!define APP_EXE "BID_Smart_App.exe"

; Installer settings
Name "${APP_NAME}"
OutFile "BID_Smart_App_Installer.exe"
InstallDir "$PROGRAMFILES\\${APP_NAME}"
RequestExecutionLevel admin

; Pages
Page directory
Page instfiles

; Installation section
Section "Install"
    SetOutPath "$INSTDIR"
    File "dist\\${APP_EXE}"
    
    ; Create desktop shortcut
    CreateShortCut "$DESKTOP\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXE}"
    
    ; Create start menu shortcut
    CreateDirectory "$SMPROGRAMS\\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXE}"
    CreateShortCut "$SMPROGRAMS\\${APP_NAME}\\Uninstall.lnk" "$INSTDIR\\uninstall.exe"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\\uninstall.exe"
    
    ; Registry entries
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "UninstallString" "$INSTDIR\\uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
SectionEnd

; Uninstaller section
Section "Uninstall"
    Delete "$INSTDIR\\${APP_EXE}"
    Delete "$INSTDIR\\uninstall.exe"
    RMDir "$INSTDIR"
    
    Delete "$DESKTOP\\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\\${APP_NAME}\\Uninstall.lnk"
    RMDir "$SMPROGRAMS\\${APP_NAME}"
    
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}"
SectionEnd
'''
    
    with open('installer.nsi', 'w', encoding='utf-8') as f:
        f.write(installer_script)
    
    print("✅ Created installer script: installer.nsi")
    print("💡 To build installer: Install NSIS and run 'makensis installer.nsi'")

def main():
    """Main build process"""
    print("🚀 BID Smart App - Executable Builder")
    print("=" * 50)
    
    # Step 1: Create PyInstaller spec
    create_pyinstaller_spec()
    
    # Step 2: Modify app for executable
    modify_app_for_executable()
    
    # Step 3: Build executable
    if build_executable():
        # Step 4: Create installer script
        create_installer_script()
        
        print("\n🎉 Build completed successfully!")
        print("📁 Files created:")
        print("   - dist/BID_Smart_App.exe (Main executable)")
        print("   - installer.nsi (Installer script)")
        print("   - smart_app_executable.py (Modified source)")
        print("   - smart_app.spec (PyInstaller config)")
        
        print("\n📋 Next steps:")
        print("1. Test the executable: dist/BID_Smart_App.exe")
        print("2. Optional: Install NSIS and run 'makensis installer.nsi'")
        print("3. Distribute BID_Smart_App.exe or BID_Smart_App_Installer.exe")
        
    else:
        print("❌ Build failed. Check error messages above.")

if __name__ == '__main__':
    main()
