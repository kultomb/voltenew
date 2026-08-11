# -*- mode: python ; coding: utf-8 -*-
import os
import sys

from PyInstaller.utils.hooks import collect_all

_spec_dir = os.path.dirname(os.path.abspath(SPEC))
exe_basename = os.environ.get("HBG_EXE_BASENAME", "HBGAdBlocker")
version_file = os.path.join(_spec_dir, os.environ.get("HBG_VERSION_FILE", "file_version_info.txt"))
_app_icon = os.path.join(_spec_dir, "icons", "app_icon.ico")
_icons_dir = os.path.join(_spec_dir, "icons")

if not os.path.isfile(_app_icon):
    print("LOI: Thieu icons/app_icon.ico — can file .ico truoc khi build.", file=sys.stderr)
    sys.exit(1)

datas = []
binaries = []
hiddenimports = ["PIL._tkinter_finder"]
tmp_ret = collect_all("customtkinter")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Icon runtime (cua so app) + file .exe (tham so icon= ben duoi)
datas.append((_icons_dir, "icons"))

_assets = os.path.join(_spec_dir, "core", "assets")
if os.path.isdir(_assets):
    datas.append((_assets, os.path.join("core", "assets")))

_pt_zip = os.path.join(_spec_dir, "platform-tools.zip")
if os.path.isfile(_pt_zip):
    datas.append((_pt_zip, "."))

_pt_dir = os.path.join(_spec_dir, "platform-tools")
if os.path.isdir(_pt_dir):
    datas.append((_pt_dir, "platform-tools"))

a = Analysis(
    ["HBGAdBlocker.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name=exe_basename,
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
    version=version_file if os.path.isfile(version_file) else None,
    icon=_app_icon,
)
