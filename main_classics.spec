# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['main_classics.py'],
    pathex=[],
    binaries=[],
    datas=[('DeskPageV2/Resources/.', 'Resources/.'), ('DeskPageV2/Resources/ppocronnx/.', 'ppocronnx/.'), ('README.md', '.')],
    hiddenimports=[],
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
    name='JiuDancing_classics',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='JiuDancing',
    icon='.\DeskPageV2\Resources\logo\app_logo.ico',
)
