# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/app.py'],
    pathex=[],
    binaries=[('ffmpeg.exe', '.')],  # FFmpeg включается в сборку
    datas=[
        ('resources/icon.ico', 'resources')
    ],
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
