"""
Icon launcher qua PackageManager trên thiết bị (Phương án B).
Android tự render Adaptive Icon → PNG; Python chỉ push dex, gọi app_process, pull.
"""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
import sys
import tempfile
import shutil
from typing import Callable, Optional

REMOTE_DEX = "/data/local/tmp/hbg_icon_dumper.dex"
REMOTE_ICON_DIR = "/data/local/tmp/hbg_icons"
DEX_NAME = "hbg_icon_dumper.dex"
BATCH_SIZE = 64


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def bundled_dex_path() -> str:
    candidates = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(os.path.join(meipass, "core", "assets", DEX_NAME))
    candidates.append(os.path.join(_project_root(), "core", "assets", DEX_NAME))
    for path in candidates:
        if os.path.isfile(path):
            return path
    return candidates[-1]


def find_android_sdk() -> Optional[str]:
    for key in ("ANDROID_HOME", "ANDROID_SDK_ROOT", "ANDROID_SDK"):
        val = os.environ.get(key)
        if val and os.path.isdir(val):
            return val
    local = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Android", "Sdk")
    if os.path.isdir(local):
        return local
    return None


def try_build_dex() -> Optional[str]:
    """Chỉ dùng khi chạy source — máy khách EXE không build dex."""
    if getattr(sys, "frozen", False):
        return None
    out = bundled_dex_path()
    if os.path.isfile(out) and os.path.getsize(out) > 500:
        return out
    root = _project_root()
    script = os.path.join(root, "scripts", "build_icon_dumper.bat")
    if not os.path.isfile(script):
        return None
    try:
        result = subprocess.run(
            ["cmd", "/c", script],
            cwd=root,
            capture_output=True,
            timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if result.returncode == 0 and os.path.isfile(out):
            return out
        logging.debug(
            "build_icon_dumper: %s",
            (result.stderr or result.stdout or b"").decode("utf-8", errors="replace")[:400],
        )
    except Exception as exc:
        logging.debug(f"build_icon_dumper: {exc}")
    return None


class DeviceIconBridge:
    """Push dex một lần / session; dump icon bằng app_process trên device."""

    def __init__(
        self,
        *,
        run_adb: Callable,
        serial_getter: Callable[[], Optional[str]],
    ):
        self._run = run_adb
        self._serial = serial_getter
        self._dex_ready = False
        self._dex_push_failed = False
        self._warned_missing_dex = False

    def _adb(self, *args: str, timeout: int = 25) -> tuple[str, str, int]:
        serial = self._serial()
        if not serial:
            return "", "", -1
        return self._run(["-s", serial, *args], timeout=timeout)

    def _shell(self, script: str, timeout: int = 30) -> tuple[str, str, int]:
        serial = self._serial()
        if not serial:
            return "", "", -1
        return self._run(["-s", serial, "shell", "sh", "-c", script], timeout=timeout)

    def _resolve_dex(self) -> Optional[str]:
        path = bundled_dex_path()
        if os.path.isfile(path) and os.path.getsize(path) > 500:
            return path
        return try_build_dex()

    def ensure_dex_on_device(self) -> bool:
        if self._dex_push_failed:
            return False
        if self._dex_ready:
            return True
        local = self._resolve_dex()
        if not local:
            if not self._warned_missing_dex:
                self._warned_missing_dex = True
                if getattr(sys, "frozen", False):
                    logging.warning(
                        "File %s chưa được nhúng trong EXE — icon có thể không chuẩn. "
                        "Build lại bằng build_exe.bat.",
                        DEX_NAME,
                    )
                else:
                    logging.info(
                        "Thiếu %s — chạy scripts\\build_icon_dumper.bat (cần Android SDK trên máy dev).",
                        DEX_NAME,
                    )
            return False
        _, _, code = self._adb("push", local, REMOTE_DEX, timeout=40)
        if code != 0:
            self._dex_push_failed = True
            return False
        self._adb("shell", "chmod", "644", REMOTE_DEX, timeout=8)
        self._shell(f"mkdir -p {shlex.quote(REMOTE_ICON_DIR)}", timeout=8)
        self._dex_ready = True
        return True

    def _run_dumper(self, packages: list[str]) -> bool:
        if not packages or not self.ensure_dex_on_device():
            return False
        qdir = shlex.quote(REMOTE_ICON_DIR)
        pkg_args = " ".join(shlex.quote(p) for p in packages)
        classpath = shlex.quote(REMOTE_DEX)
        cmd = (
            f"rm -f {qdir}/*.png 2>/dev/null; "
            f"CLASSPATH={classpath} "
        )
        for proc in ("app_process64", "app_process"):
            full = (
                f"{cmd}{proc} /system/bin IconDumper {qdir} {pkg_args} 2>&1"
            )
            out, err, code = self._shell(
                full, timeout=min(25 + len(packages) // 2, 180)
            )
            combined = (out or "") + (err or "")
            if code == 0 or "DONE ok=" in combined:
                return True
            if "OK " in combined and "fail=0" in combined:
                return True
            if "OK " in combined and any(
                f"OK {p}" in combined for p in packages
            ):
                return True
        return False

    def _remote_png_path(self, package: str) -> str:
        safe = package.replace(".", "_")
        return f"{REMOTE_ICON_DIR}/{safe}.png"

    def fetch_icon_png(self, package: str) -> Optional[bytes]:
        """Pull một icon PNG từ device (PackageManager)."""
        if not self._serial():
            return None
        if not self._run_dumper([package]):
            return None
        remote = self._remote_png_path(package)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            local = tmp.name
        try:
            _, _, code = self._adb("pull", remote, local, timeout=20)
            if code != 0 or not os.path.isfile(local) or os.path.getsize(local) < 32:
                return None
            with open(local, "rb") as f:
                return f.read()
        finally:
            try:
                os.remove(local)
            except OSError:
                pass

    def _pull_icon_dir(self, timeout: int = 60) -> dict[str, bytes]:
        """Một lệnh adb pull cả thư mục icon — nhanh hơn pull từng file."""
        by_safe: dict[str, bytes] = {}
        local_root = tempfile.mkdtemp(prefix="hbg_icons_")
        try:
            dest = os.path.join(local_root, "icons")
            os.makedirs(dest, exist_ok=True)
            remote = REMOTE_ICON_DIR.rstrip("/") + "/"
            _, _, code = self._adb("pull", remote, dest, timeout=timeout)
            if code != 0:
                return by_safe
            for root, _dirs, files in os.walk(dest):
                for name in files:
                    if not name.endswith(".png"):
                        continue
                    path = os.path.join(root, name)
                    try:
                        if os.path.getsize(path) < 32:
                            continue
                        with open(path, "rb") as f:
                            by_safe[name[:-4]] = f.read()
                    except OSError as exc:
                        logging.debug(f"read pulled icon {name}: {exc}")
        finally:
            shutil.rmtree(local_root, ignore_errors=True)
        return by_safe

    def fetch_icons_batch(self, packages: list[str]) -> dict[str, bytes]:
        """Dump nhiều package: 1× app_process + 1× adb pull thư mục / batch."""
        result: dict[str, bytes] = {}
        if not packages or not self._serial():
            return result
        unique = list(dict.fromkeys(packages))
        safe_to_pkg = {p.replace(".", "_"): p for p in unique}
        for start in range(0, len(unique), BATCH_SIZE):
            chunk = unique[start : start + BATCH_SIZE]
            if not self._run_dumper(chunk):
                continue
            pulled = self._pull_icon_dir(timeout=min(45 + len(chunk), 120))
            for safe, raw in pulled.items():
                pkg = safe_to_pkg.get(safe)
                if pkg:
                    result[pkg] = raw
        return result

    def reset_session(self) -> None:
        self._dex_ready = False
        self._dex_push_failed = False
