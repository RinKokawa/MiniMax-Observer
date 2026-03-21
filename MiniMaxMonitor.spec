# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(SPEC))
src_path = os.path.join(PROJECT_ROOT, "src")

a = Analysis(
    [os.path.join(src_path, "main.py")],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=[
        (os.path.join(src_path, "observer-logo.svg"), "src"),
        (os.path.join(PROJECT_ROOT, "MiniMaxMonitor.ico"), "."),
    ],
    hiddenimports=[
        "pystray",
        "PIL",
        "PIL.Image",
        "PIL.ImageDraw",
        "matplotlib",
        "matplotlib.backends",
        "matplotlib.backends.backend_tkagg",
        "tkinter",
        "tkinter.ttk",
        "tkinter.font",
        "cairosvg",
        "requests",
        "certifi",
        "charset_normalizer",
        "idna",
        "urllib3",
        "sqlite3",
        "json",
        "threading",
        "subprocess",
        "_cffi_backend",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MiniMaxMonitor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,        # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(PROJECT_ROOT, "MiniMaxMonitor.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MiniMaxMonitor",
)
