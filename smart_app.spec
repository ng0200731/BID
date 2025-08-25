# -*- mode: python ; coding: utf-8 -*-

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
    ['smart_app_executable.py'],
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
