"""
Tăng patch version, sinh file_version_info.txt + core/_build_version.py + build_env.bat.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_JSON = ROOT / "version.json"
VERSION_INFO = ROOT / "file_version_info.txt"
BUILD_VERSION_PY = ROOT / "core" / "_build_version.py"
BUILD_ENV_BAT = ROOT / "build_env.bat"
INSTALLER_DEFINES = ROOT / "installer" / "build_defines.iss"


def _load_version() -> tuple[int, int, int]:
    if VERSION_JSON.exists():
        data = json.loads(VERSION_JSON.read_text(encoding="utf-8"))
        return int(data["major"]), int(data["minor"]), int(data["patch"])
    return 1, 0, 0


def _save_version(major: int, minor: int, patch: int) -> None:
    VERSION_JSON.write_text(
        json.dumps({"major": major, "minor": minor, "patch": patch}, indent=2) + "\n",
        encoding="utf-8",
    )


def _bump_patch(major: int, minor: int, patch: int) -> tuple[int, int, int]:
    return major, minor, patch + 1


def _version_string(major: int, minor: int, patch: int) -> str:
    return f"{major}.{minor}.{patch}"


def _exe_basename(ver: str) -> str:
    return f"HBGAdBlocker{ver}"


def _write_build_version_py(ver: str, major: int, minor: int, patch: int) -> None:
    display = f"v{ver}"
    content = f'''# Sinh tự động bởi scripts/prepare_build.py — không sửa tay.
VERSION = "{ver}"
VERSION_TUPLE = ({major}, {minor}, {patch})
VERSION_DISPLAY = "{display}"
FOOTER_TAGLINE = (
    "HBG AdBlocker {display}\\n"
    "Xóa quảng cáo · Dọn app rác · Tối ưu thiết bị"
)
'''
    BUILD_VERSION_PY.write_text(content, encoding="utf-8")


def _write_file_version_info(ver: str, major: int, minor: int, patch: int, exe_base: str) -> None:
    """PyInstaller đọc file Python VSVersionInfo (tên .txt theo yêu cầu)."""
    content = f'''# UTF-8 — Windows EXE metadata (PyInstaller --version-file)
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({major}, {minor}, {patch}, 0),
    prodvers=({major}, {minor}, {patch}, 0),
    mask=0x3F,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0),
  ),
  kids=[
    StringFileInfo([
      StringTable(
        "040904B0",
        [
          StringStruct("CompanyName", "Hà BG"),
          StringStruct("FileDescription", "HBG Ad Blocker"),
          StringStruct("FileVersion", "{ver}"),
          StringStruct("InternalName", "HBGAdBlocker"),
          StringStruct("LegalCopyright", "Copyright (c) 2026 by Hà BG"),
          StringStruct("OriginalFilename", "{exe_base}.exe"),
          StringStruct("ProductName", "HBG Ad Blocker"),
          StringStruct("ProductVersion", "{ver}"),
        ],
      ),
    ]),
    VarFileInfo([VarStruct("Translation", [1033, 1200])]),
  ],
)
'''
    VERSION_INFO.write_text(content, encoding="utf-8")


def _write_build_env_bat(exe_base: str, ver: str) -> None:
    BUILD_ENV_BAT.write_text(
        "@echo off\r\n"
        f"set HBG_EXE_BASENAME={exe_base}\r\n"
        f"set HBG_VERSION={ver}\r\n"
        "set HBG_VERSION_FILE=file_version_info.txt\r\n",
        encoding="utf-8",
    )


def _write_installer_defines(ver: str, exe_base: str) -> None:
    INSTALLER_DEFINES.parent.mkdir(parents=True, exist_ok=True)
    INSTALLER_DEFINES.write_text(
        f'; Sinh tu dong — scripts/prepare_build.py\n'
        f'#define HBGAppVersion "{ver}"\n'
        f'#define HBGExeBaseName "{exe_base}"\n'
        f'#define HBGAppPublisher "Hà BG"\n'
        f'#define HBGAppName "HBG AdBlocker"\n',
        encoding="utf-8",
    )


def main() -> int:
    major, minor, patch = _load_version()
    major, minor, patch = _bump_patch(major, minor, patch)
    _save_version(major, minor, patch)
    ver = _version_string(major, minor, patch)
    exe_base = _exe_basename(ver)

    _write_build_version_py(ver, major, minor, patch)
    _write_file_version_info(ver, major, minor, patch, exe_base)
    _write_build_env_bat(exe_base, ver)
    _write_installer_defines(ver, exe_base)

    print(ver)
    print(exe_base)
    return 0


if __name__ == "__main__":
    sys.exit(main())
