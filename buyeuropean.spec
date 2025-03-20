# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Get the current directory
block_cipher = None
current_dir = os.path.abspath(os.path.dirname('__file__'))

# Define paths to important assets
sounds_dir = os.path.join(current_dir, 'src', 'buyeuropean', 'sounds')
logos_dir = os.path.join(current_dir, 'src', 'buyeuropean', 'ui', 'gtk', 'logos')

# Collect all data files
datas = [
    (sounds_dir, 'src/buyeuropean/sounds'),
    (logos_dir, 'src/buyeuropean/ui/gtk/logos'),
]

a = Analysis(
    ['src/buyeuropean/__main__.py'],
    pathex=[current_dir],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'PyQt6.QtCore',
        'PyQt6.QtMultimedia',
        'gi',
        'gi.repository.Gtk',
        'gi.repository.Gdk',
        'gi.repository.GdkPixbuf',
        'gi.repository.Adw',
        'gi.repository.Gst',
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
    name='buyeuropean',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(logos_dir, 'logo_buyeuropean.png'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='buyeuropean',
) 
