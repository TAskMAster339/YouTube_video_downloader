# -*- mode: python ; coding: utf-8 -*-
from deno import find_deno_bin
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

deno_exe = find_deno_bin()

a = Analysis(
    ['src/app.py'],
    pathex=[],
    binaries=[('ffmpeg.exe', '.'), (str(deno_exe), '.')],
    datas=[
        ('resources/icon.ico', 'resources')
    ] + collect_data_files('yt_dlp_ejs') + copy_metadata('yt-dlp-ejs'),
    hiddenimports=[
        'yt_dlp.compat._legacy',
        'yt_dlp.compat',
        'yt_dlp.downloader',
        'yt_dlp.extractor',
        'yt_dlp.postprocessor',
        'winsound',
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
    name='YouTube_Downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico',
)
