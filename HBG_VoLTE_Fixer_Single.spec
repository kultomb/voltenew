# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['volte_fixer_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('adb', 'adb'), ('assets', 'assets'), ('scrcpy', 'scrcpy'), ('Shizuku_13.6.0.r1091.b844bc49_APKPure.apk', '.'), ('pixel-ims-1-3-2.apk', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='HBG_VoLTE_Fixer_Single',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
