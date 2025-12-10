# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for TimeLogger

a = Analysis(
    ['lawtime\\__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('LawTime.ico', '.'),  # Include icon in root of bundle
    ],
    hiddenimports=[
        'win32timezone',  # pywin32 hidden dependency
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='TimeLogger',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (system tray app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    coerce_macros=True,
    entitlements_file=None,
    icon='LawTime.ico',
    version='version_info.txt',
)
