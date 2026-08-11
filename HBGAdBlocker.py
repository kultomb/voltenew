import os
import io
import time
import re
import shlex
import logging
import subprocess
import csv
import tkinter as tk
import webbrowser
import customtkinter as ctk
import json
import tempfile
import zipfile
from datetime import datetime
import platform
from threading import Thread
from PIL import Image, ImageTk
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinter import ttk, filedialog
import sys

from core.app_analyzer import AppAnalyzer
from core.icon_extractor import (
    IconExtractor,
    UI_PX as ICON_UI_PX,
    TABLE_CB_PX,
    TABLE_LEADING_GAP,
    TABLE_LEADING_PAD_LEFT,
    TABLE_LEADING_ICON_PX,
    compose_table_leading,
    draw_table_checkbox,
    table_leading_width,
)
from core.log_terminal import LogTerminal
from core.ui_theme import (
    COLORS, C, UI, FONTS, RADIUS, SPACE, LAYOUT, get_font, init_app_theme, ControlPanelGroup,
)
from core.premium_menu import PremiumMenu
from core.app_label_resolver import (
    AppLabelResolver,
    is_provisional_label,
    is_suffix_fallback,
    lookup_known_label,
    package_suffix_label,
)
from core.notification_control import NotificationControl
from core.activity_log import prepare_log_line
from core.version import APP_VERSION_LABEL, FOOTER_TAGLINE
from core.app_branding import apply_window_icon, load_brand_ctk_image
from core.confirm_dialog import ask_confirm, show_notice
from core.about_dialog import show_about_dialog
from core.risk_detail_dialog import show_risk_detail
from core.window_utils import bind_minimize_cascade, center_on_screen
from core.junk_pick_dialog import ask_junk_removal_pick, prefetch_junk_icons
from core.launcher_helpers import (
    find_oem_home_component,
    get_default_launcher,
    list_installed_launchers,
    set_default_launcher,
    disable_launcher,
)
from core.launcher_pick_dialog import ask_launcher_removal_pick
from core.bloatware_presets import (
    bloatware_label_for,
    find_installed_bloatware,
)
from core.policy import (
    AD_DOMAINS,
    AD_NETWORKS,
    BEHAVIOR_KEYWORDS,
    BLACKLIST,
    JUNK_KEYWORDS,
    TRUSTED_ANALYSIS_PACKAGES,
    check_ad_network_activity,
    init_policy,
    is_ad_related_package,
    is_protected_package,
    persist_blacklist,
    replace_blacklist,
)

RESAMPLE_LANCZOS = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS

# --- Thiết lập logging ---
appdata_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'HBGAdBlocker')
os.makedirs(appdata_dir, exist_ok=True)
logs_dir = os.path.join(appdata_dir, "logs")
os.makedirs(logs_dir, exist_ok=True)
log_file = os.path.join(logs_dir, "app.log")
analysis_cache_file = os.path.join(appdata_dir, "analysis_cache.json")

logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

init_app_theme()

REMOVED_PACKAGES = []

# Biến toàn cục
device_id = None
monitoring = False
current_running_package = None
device_name = "Chưa kết nối"
monitor_process = None
is_running = True
adb_connection_cache = None
last_connection_check = 0
connection_check_interval = 5  # Giảm tần suất kiểm tra

# Hàm tìm đường dẫn adb
def get_adb_path():
    try:
        # Lấy đường dẫn thư mục hiện tại của ứng dụng
        if getattr(sys, 'frozen', False):
            # Nếu đang chạy file đã đóng gói
            base_path = sys._MEIPASS  # Thư mục chứa tài nguyên đã giải nén
            
            # Thử tìm adb trong thư mục platform-tools đã giải nén
            adb_path = os.path.join(base_path, 'platform-tools', 'adb.exe')
            if os.path.exists(adb_path):
                logging.debug(f"ADB found at {adb_path}")
                return adb_path
                
            # Nếu không tìm thấy, thử giải nén từ zip
            temp_dir = os.path.join(os.environ['TEMP'], 'hbg_platform_tools')
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
                import zipfile
                zip_path = os.path.join(base_path, 'platform-tools.zip')
                if os.path.exists(zip_path):
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    adb_path = os.path.join(temp_dir, "platform-tools", "adb.exe")
                    if os.path.exists(adb_path):
                        logging.debug(f"ADB found at {adb_path} (extracted from zip)")
                        return adb_path
        else:
            # Nếu đang chạy file Python trực tiếp
            base_path = os.path.dirname(os.path.abspath(__file__))
            adb_path = os.path.join(base_path, 'platform-tools', 'adb.exe')
            if os.path.exists(adb_path):
                logging.debug(f"ADB found at {adb_path}")
                return adb_path

        logging.warning(f"ADB not found in application directory, trying system PATH")
        adb_path = 'adb'
        try:
            result = subprocess.run(['adb', 'version'], capture_output=True, text=True,
                                   creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0)
            logging.debug(f"ADB found in system PATH: {result.stdout}")
            return adb_path
        except:
            logging.error(f"ADB not found in system PATH")
            raise FileNotFoundError("ADB executable not found")
    except Exception as e:
        logging.error(f"Lỗi tìm ADB: {str(e)}")
        raise

# Hàm kiểm tra kết nối ADB (đã tối ưu)
def is_adb_connected(device_id, force_check=False):
    global adb_connection_cache, last_connection_check
    current_time = time.time()
    if not force_check and adb_connection_cache is not None and (current_time - last_connection_check) < connection_check_interval:
        return adb_connection_cache
    try:
        dm = DeviceManager()
        _, _, code = dm.run(["-s", device_id, "shell", "getprop", "ro.serialno"], timeout=2)
        connected = code == 0
        adb_connection_cache = connected
        last_connection_check = current_time
        return connected
    except:
        adb_connection_cache = False
        last_connection_check = current_time
        return False

# Hàm chạy lệnh adb (đã tối ưu timeout)
def run_adb_command(command, timeout=5):
    try:
        dm = DeviceManager()
        stdout, stderr, _ = dm.run(command, timeout=timeout)
        if stderr:
            logging.error(f"Lỗi ADB: {stderr}")
        return stdout.strip()
    except Exception as e:
        logging.error(f"Lỗi chạy lệnh ADB: {str(e)}")
        return ""

# Hàm lấy danh sách package
def get_installed_packages(device_id):
    output = run_adb_command(["-s", device_id, "shell", "pm", "list", "packages"], timeout=5)
    return [line.split(":")[-1].strip() for line in output.splitlines() if line.strip()]

# Hàm gỡ ứng dụng
def uninstall_package(device_id, package):
    result = run_adb_command(["-s", device_id, "shell", "pm", "uninstall", "-k", "--user", "0", package], timeout=10)
    logging.info(f"Gỡ {package}: {result or 'thành công'}")
    if package not in REMOVED_PACKAGES:
        REMOVED_PACKAGES.append(package)
    return result

# Hàm vô hiệu hóa ứng dụng
def disable_app(device_id, package):
    try:
        result = run_adb_command(["-s", device_id, "shell", "pm", "disable-user", "--user", "0", package], timeout=5)
        if "new state: disabled-user" in result.lower() or not result:
            logging.info(f"Vô hiệu hóa {package}: thành công")
            return ""  # Thành công
        else:
            logging.error(f"Lỗi vô hiệu hóa {package}: {result}")
            return result
    except Exception as e:
        logging.error(f"Lỗi vô hiệu hóa {package}: {str(e)}")
        return str(e)

# Hàm kiểm tra popup
def check_popup(device_id):
    activity = run_adb_command(["-s", device_id, "shell", "dumpsys", "activity", "activities"], timeout=3)
    match = re.search(r"mResumedActivity:.* (\S+)/", activity)
    if match:
        package = match.group(1)
        if not is_protected_package(package):
            return package
    return None

_PACKAGE_ID_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+$")
_PM_PKG_SUFFIX_RE = re.compile(r"=([a-zA-Z][a-zA-Z0-9_.]+)\s*$")


_SEGMENT_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")


def is_valid_package_id(pkg: str) -> bool:
    if not pkg or len(pkg) > 255:
        return False
    if any(c in pkg for c in " /\\\t\r\n"):
        return False
    if pkg.endswith(".apk"):
        return False
    parts = pkg.split(".")
    if len(parts) < 2:
        return False
    return all(_SEGMENT_RE.match(part) for part in parts)


def _package_from_apk_path(path: str) -> str:
    """Suy ra com.example.app từ đường dẫn APK (pm list -f không có hậu tố =package)."""
    path = (path or "").replace("\\", "/")
    for part in reversed(path.split("/")):
        if not part or part in ("base.apk", "base"):
            continue
        name = part[:-4] if part.endswith(".apk") else part
        if "-" in name:
            head = name.rsplit("-", 1)[0]
            if is_valid_package_id(head):
                return head
        if is_valid_package_id(name):
            return name
    m = re.search(r"([a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*){1,})", path)
    return m.group(1) if m else ""


def compact_package_id(raw: str) -> str:
    """Chỉ giữ package id (vd. com.facebook.katana), bỏ đường dẫn APK từ pm list -f."""
    s = (raw or "").strip()
    if not s:
        return ""
    suffix = _PM_PKG_SUFFIX_RE.search(s)
    if suffix:
        return suffix.group(1).strip()
    if s.lower().startswith("package:"):
        s = s.split(":", 1)[1].strip()
    if is_valid_package_id(s):
        return s
    if "/" in s or s.endswith(".apk"):
        from_path = _package_from_apk_path(s)
        if from_path:
            return from_path
    return s


def parse_pm_list_line(raw: str) -> tuple[str, str]:
    """Parse một dòng `pm list packages` → (apk_path, package_id)."""
    raw = (raw or "").strip()
    if not raw or "package:" not in raw.lower():
        return "", ""
    suffix = _PM_PKG_SUFFIX_RE.search(raw)
    if suffix:
        pkg = suffix.group(1).strip()
        apk_path = raw[: suffix.start()].strip()
        if apk_path.lower().startswith("package:"):
            apk_path = apk_path.split(":", 1)[1].strip()
        return apk_path, pkg
    body = raw.split(":", 1)[-1].strip()
    if is_valid_package_id(body):
        return "", body
    pkg = _package_from_apk_path(body)
    return body, pkg


# Giao diện chính - Premium Design
class DeviceManager:
    """Singleton quản lý duy nhất kết nối ADB và cache thiết bị."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.adb_path = None
            cls._instance.serial = None
            cls._instance.device_connected = False
            cls._instance.device_model = "Chưa kết nối"
            cls._instance.android_version = "Unknown"
            cls._instance.icon_cache = {}
            cls._instance.label_cache = {}
            cls._instance._label_enrich_tried = set()
            cls._instance.size_cache = {}
            cls._instance.icons_dir = os.path.join(appdata_dir, "icons_cache")
            os.makedirs(cls._instance.icons_dir, exist_ok=True)
            inst = cls._instance
            inst._icon_extractor = IconExtractor(
                inst.icons_dir,
                run_adb=lambda cmd, timeout=8: inst.run(cmd, timeout=timeout),
                exec_out_shell=lambda script, timeout=18: inst.exec_out_shell_raw(script, timeout),
                serial_getter=lambda: inst.serial,
            )
            inst._label_resolver = AppLabelResolver(
                appdata_dir,
                run_adb=lambda cmd, timeout=8: inst.run(cmd, timeout=timeout),
                serial_getter=lambda: inst.serial,
                get_apk_path=lambda pkg, hint=None: inst._icon_extractor.get_package_apk_path(pkg, hint),
            )
            inst._notification = NotificationControl(
                shell=lambda cmd, timeout=8: inst.shell(cmd) if inst.serial else "",
                serial_getter=lambda: inst.serial,
                run_adb=inst.run,
            )
        return cls._instance

    def _base_cmd(self):
        if not self.adb_path:
            self.adb_path = get_adb_path()
        return [self.adb_path]

    def run(self, cmd, timeout=8):
        try:
            result = subprocess.run(
                self._base_cmd() + cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            if result.stderr:
                logging.debug(f"ADB stderr ({' '.join(cmd)}): {result.stderr.strip()}")
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except subprocess.TimeoutExpired:
            return "", f"Timeout: {' '.join(cmd)}", -1
        except Exception as exc:
            logging.exception("ADB run failed")
            return "", str(exc), -1

    def shell(self, cmd, timeout=8):
        if not self.serial:
            return ""
        out, _, _ = self.run(["-s", self.serial, "shell"] + cmd, timeout=timeout)
        return out

    def refresh(self):
        out, err, code = self.run(["devices"], timeout=5)
        if code != 0:
            self.device_connected = False
            self.serial = None
            return False, err or "ADB lỗi, vui lòng kiểm tra cài đặt."

        lines = [x.strip() for x in out.splitlines()[1:] if x.strip()]
        device_lines = [x for x in lines if x.endswith("\tdevice")]
        if not device_lines:
            self.device_connected = False
            self.serial = None
            self.device_model = "Chưa kết nối"
            self.android_version = "Unknown"
            return False, "Chưa kết nối hoặc chưa bật USB Debug."

        self.serial = device_lines[0].split("\t")[0]
        model = self.shell(["getprop", "ro.product.model"], timeout=4) or "Không xác định"
        android = self.shell(["getprop", "ro.build.version.release"], timeout=4) or "Unknown"
        self.device_model = model
        self.android_version = android
        self.device_connected = True
        return True, "OK"

    def connect(self):
        return self.refresh()

    def install(self, apk_path):
        if not self.serial:
            return "", "No device", -1
        return self.run(["-s", self.serial, "install", "-r", apk_path], timeout=40)

    def uninstall(self, package):
        if not self.serial:
            return "", "No device", -1
        return self.run(["-s", self.serial, "shell", "pm", "uninstall", "-k", "--user", "0", package], timeout=15)

    @staticmethod
    def _is_system_apk_path(apk_path):
        """Đường dẫn base.apk nằm partition hệ thống / vendor / apex."""
        if not apk_path:
            return False
        p = apk_path.strip()
        prefixes = (
            "/system", "/product", "/vendor", "/odm", "/apex",
            "/system_ext", "/oem", "/op1", "/op2",
        )
        return any(p.startswith(pref) for pref in prefixes)

    @staticmethod
    def _packages_from_pm_list_output(out: str) -> set[str]:
        found: set[str] = set()
        for line in (out or "").splitlines():
            line = line.strip()
            if not line.startswith("package:"):
                continue
            pkg = compact_package_id(line.split(":", 1)[-1].strip())
            if is_valid_package_id(pkg):
                found.add(pkg)
        return found

    def get_disabled_packages(self) -> set[str]:
        """Package đang bị pm disable (toàn máy + user 0)."""
        if not self.serial:
            return set()
        disabled: set[str] = set()
        for args in (["pm", "list", "packages", "-d"], ["pm", "list", "packages", "-d", "-u"]):
            out, _, code = self.run(["-s", self.serial, "shell"] + args, timeout=10)
            if code == 0:
                disabled |= self._packages_from_pm_list_output(out)
        return disabled

    def _package_apk_path(self, package: str) -> str:
        """Đường dẫn base APK (pm path), kể cả app partition hệ thống."""
        if not self.serial or not package:
            return ""
        out, _, code = self.run(
            ["-s", self.serial, "shell", "pm", "path", package],
            timeout=8,
        )
        if code != 0 or not out:
            return ""
        for line in out.splitlines():
            line = line.strip()
            if not line.lower().startswith("package:"):
                continue
            path = line.split(":", 1)[-1].strip()
            if path.endswith(".apk"):
                return path
        return ""

    def list_packages(self):
        """App cài thêm (third-party)."""
        if not self.serial:
            return []
        disabled_pkgs = self.get_disabled_packages()
        out, _, code = self.run(
            ["-s", self.serial, "shell", "pm", "list", "packages", "-3", "-f"],
            timeout=12,
        )
        if code != 0 or not (out or "").strip():
            out, _, code = self.run(
                ["-s", self.serial, "shell", "pm", "list", "packages", "-3"],
                timeout=12,
            )
        if code != 0:
            return []
        rows: list[dict] = []
        seen: set[str] = set()
        for raw in out.splitlines():
            apk_path, pkg = parse_pm_list_line(raw)
            if not pkg:
                continue
            pkg = compact_package_id(pkg)
            if not is_valid_package_id(pkg) or pkg in seen:
                continue
            if self._is_system_apk_path(apk_path):
                continue
            seen.add(pkg)
            system_kind = "User"
            if apk_path:
                self._icon_extractor.cache_apk_path(pkg, apk_path)
            rows.append({
                "checked": False,
                "icon": self.get_icon_token(pkg, system_kind),
                "name": self.get_app_label(pkg, apk_path or None),
                "package": pkg,
                "apk_path": apk_path or "",
                "size": self.size_cache.get(pkg, "..."),
                "kind": system_kind,
                "enabled": pkg not in disabled_pkgs,
            })
        rows.sort(key=lambda r: (r.get("name") or r["package"]).lower())
        if not rows and (out or "").strip():
            logging.warning(
                "list_packages: 0 app sau khi parse, %s dòng ADB. Mẫu: %s",
                len(out.splitlines()),
                (out.splitlines()[0][:120] if out.splitlines() else ""),
            )
        return rows

    def get_icon_token(self, package, kind):
        if package in self.icon_cache:
            return self.icon_cache[package]
        pkg = package.lower()
        if any(k in pkg for k in ("ad", "ads", "cleaner", "boost", "junk")):
            icon = "🧹"
        elif kind == "System":
            icon = "⚙"
        elif kind == "Google":
            icon = "G"
        else:
            icon = "📱"
        self.icon_cache[package] = icon
        return icon

    def get_package_apk_path(self, package, hint=None):
        return self._icon_extractor.get_package_apk_path(package, hint)

    def get_cached_icon_path(self, package):
        return self._icon_extractor.get_cached_ui_path(package)

    def has_real_icon_cached(self, package):
        return self._icon_extractor.has_real_icon_cached(package)

    def get_instant_ui_icon_path(self, package, label=None):
        return self._icon_extractor.get_instant_ui_path(package, label or "")

    def extract_icon_to_cache(self, package, apk_path_hint=None, label=None):
        return self._icon_extractor.extract_icon_to_cache(package, apk_path_hint, label or "")

    def ensure_ui_icon(self, package, apk_path_hint=None, label=None):
        return self._icon_extractor.ensure_ui_icon(package, apk_path_hint, label or "")

    def get_package_insights(self, package):
        """Thu thập metadata package ở mức vừa đủ để phân tích rủi ro."""
        if not self.serial:
            return {"permissions": [], "services": [], "receivers": [], "apk_strings": []}
        out, _, _ = self.run(["-s", self.serial, "shell", "dumpsys", "package", package], timeout=6)
        perms = []
        services = []
        receivers = []
        for line in out.splitlines():
            s = line.strip()
            if "android.permission." in s:
                token = s.split()[-1]
                perms.append(token.replace("android.permission.", "").strip())
            if "Service{" in s:
                services.append(s)
            if "Receiver{" in s or "BOOT_COMPLETED" in s:
                receivers.append(s)
        # Chuỗi nhẹ để bắt domain/ad sdk mà không parse dex nặng.
        quick_strings = [out.lower()[:20000]]
        return {
            "permissions": sorted(set(perms)),
            "services": services[:30],
            "receivers": receivers[:30],
            "apk_strings": quick_strings,
        }

    def exec_out_shell_raw(self, shell_script, timeout=18):
        """adb exec-out — giữ nguyên byte (unzip -p)."""
        if not self.serial:
            return b"", -1
        try:
            result = subprocess.run(
                self._base_cmd()
                + ["-s", self.serial, "exec-out", "shell", "sh", "-c", shell_script],
                capture_output=True,
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
            )
            return result.stdout or b"", result.returncode
        except subprocess.TimeoutExpired:
            return b"", -1
        except Exception as exc:
            logging.debug(f"exec_out_shell_raw: {exc}")
            return b"", -1

    def disable_notifications(self, package: str) -> tuple[bool, str]:
        if hasattr(self, "_notification"):
            return self._notification.disable_notifications(package)
        return False, "NotificationControl chưa khởi tạo"

    def enable_notifications(self, package: str) -> tuple[bool, str]:
        if hasattr(self, "_notification"):
            return self._notification.enable_notifications(package)
        return False, "NotificationControl chưa khởi tạo"

    def get_notification_mode(self, package: str) -> str:
        if hasattr(self, "_notification"):
            return self._notification.get_post_notification_mode(package)
        return "unknown"

    def are_notifications_blocked(self, package: str) -> bool:
        if hasattr(self, "_notification"):
            return self._notification.are_notifications_blocked(package)
        return False

    def block_network(self, package):
        if not self.serial:
            return "", "No device", -1
        # Best-effort: revoke network permissions (không phải app nào cũng hỗ trợ).
        cmds = [
            ["-s", self.serial, "shell", "pm", "revoke", package, "android.permission.INTERNET"],
            ["-s", self.serial, "shell", "pm", "revoke", package, "android.permission.ACCESS_NETWORK_STATE"],
        ]
        last = ("", "", 0)
        for cmd in cmds:
            last = self.run(cmd, timeout=6)
        return last

    def backup_apk(self, package, target_folder):
        if not self.serial:
            return None
        apk_path = self.get_package_apk_path(package)
        if not apk_path:
            return None
        os.makedirs(target_folder, exist_ok=True)
        local_apk = os.path.join(target_folder, f"{package}.apk")
        _, _, code = self.run(["-s", self.serial, "pull", apk_path, local_apk], timeout=30)
        return local_apk if code == 0 and os.path.exists(local_apk) else None

    def clear_label_enrich_tried(self):
        """Gọi khi làm mới danh sách app — cho phép đọc lại tên từ máy."""
        self._label_enrich_tried.clear()
        stale = [p for p, n in self.label_cache.items() if is_provisional_label(p, n)]
        for p in stale:
            self.label_cache.pop(p, None)
        if hasattr(self, "_icon_extractor"):
            self._icon_extractor.clear_apk_path_cache()
            self._icon_extractor.purge_ui_without_master()

    def invalidate_package_icon(self, package: str) -> None:
        if hasattr(self, "_icon_extractor"):
            self._icon_extractor.invalidate_package(package)

    def enrich_app_label_from_device(self, package, apk_hint=None):
        """Lấy tên app như launcher (dumpsys / aapt); cache RAM + disk."""
        if not self.serial:
            return None
        row_hint = apk_hint
        if hasattr(self, "_label_resolver"):
            name = self._label_resolver.resolve(package, row_hint)
            if name:
                self.label_cache[package] = name
                return name
        return None

    def get_app_label(self, package, apk_hint=None):
        if package in self.label_cache:
            cached = self.label_cache[package]
            if not is_provisional_label(package, cached):
                return cached
        if hasattr(self, "_label_resolver"):
            disk = self._label_resolver.load_cached_label(package)
            if disk and not is_provisional_label(package, disk):
                self.label_cache[package] = disk
                return disk
        known = lookup_known_label(package)
        if known:
            return known
        return package_suffix_label(package)

    def get_package_size(self, package):
        if package in self.size_cache:
            return self.size_cache[package]
        size_text = "-"
        size_out = self.shell(["du", "-sk", f"/data/data/{package}"], timeout=3)
        if size_out:
            try:
                kb = int(size_out.split()[0])
                size_text = f"{round(kb/1024, 1)} MB"
            except Exception:
                size_text = "-"
        if size_text == "-":
            apk_path = self.get_package_apk_path(package)
            if apk_path:
                total_kb = 0
                for segment in apk_path.split(":"):
                    segment = segment.strip()
                    if not segment.startswith("/"):
                        continue
                    du_apk = self.shell(["du", "-sk", segment], timeout=4)
                    if du_apk:
                        try:
                            total_kb += int(du_apk.split()[0])
                        except Exception:
                            pass
                if total_kb > 0:
                    size_text = f"{round(total_kb/1024, 1)} MB"
        self.size_cache[package] = size_text
        return size_text


class AppManagerTab(ctk.CTkFrame):
    """Tab quản lý app chạy trong cùng cửa sổ chính."""
    def __init__(self, master, device_manager, log_callback):
        super().__init__(master, fg_color="transparent")
        self.device_manager = device_manager
        self.log = log_callback
        self.executor = ThreadPoolExecutor(max_workers=6)
        self._icon_executor = ThreadPoolExecutor(max_workers=8)
        self._icon_fetch_gen = 0
        self._icon_bg_pending = False
        self.search_after_id = None
        self.all_rows = []
        self.filtered_rows = []
        self._size_refresh_in_progress = False
        self._render_scheduled = None
        self.package_to_iid = {}
        self.tk_icon_cache = {}
        self._icon_failed = set()
        self._label_refresh_in_progress = False
        self._placeholder_img = None
        self._icon_rgba_cache: dict[str, Image.Image] = {}
        self._row_leading_photos: dict[str, ImageTk.PhotoImage] = {}
        self._leading_hit_w = table_leading_width()
        self._tree_leading_w = self._leading_hit_w
        self._hover_iid: str | None = None
        self.package_to_row = {}
        self.is_connected = False
        self._loading_packages = False
        self._load_error = None
        self._risk_filter = None
        self._pending_refresh = False
        self.analyzer = AppAnalyzer(
            BLACKLIST,
            AD_NETWORKS,
            AD_DOMAINS,
            BEHAVIOR_KEYWORDS,
            JUNK_KEYWORDS,
            trusted_packages=TRUSTED_ANALYSIS_PACKAGES,
        )
        self.analysis_cache = self._load_analysis_cache()
        self._refresh_trusted_analysis_cache()
        self.on_scan_finished = None
        self._build_ui()

    @staticmethod
    def _app_state_label(row: dict) -> str:
        return "Bật" if row.get("enabled", True) else "Tắt"

    @staticmethod
    def _package_from_values(values: tuple) -> str | None:
        """values = (package, status, size)."""
        if not values:
            return None
        return compact_package_id(values[0])

    @staticmethod
    def _set_badge_text(badge_frame, text: str):
        for child in badge_frame.winfo_children():
            if isinstance(child, ctk.CTkLabel):
                child.configure(text=text)
                break

    def _build_ui(self):
        self._layout_root = ctk.CTkFrame(self, fg_color="transparent")
        self._layout_root.pack(fill="both", expand=True)
        root = self._layout_root
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(2, weight=1)
        tb_h = LAYOUT["toolbar_h"]
        block_pad = SPACE["3"]

        summary_card = UI.card(root, padding=block_pad, tight=True)
        summary_card.grid(row=0, column=0, sticky="ew", pady=(0, block_pad))
        sum_inner = UI.card_inner(summary_card)
        strip_row = UI.metric_strip_row(sum_inner)
        self._sum_device = UI.metric_cell(strip_row, "📱", "Thiết bị", "—", "Chưa kết nối")
        self._sum_android = UI.metric_cell(strip_row, "🤖", "Android", "—", "Phiên bản OS")
        self._sum_serial = UI.metric_cell(strip_row, "🔑", "Serial", "—", "Serial")
        self._sum_count = UI.metric_cell(strip_row, "▦", "Tổng ứng dụng", "0", "package")
        UI.metric_strip_layout(
            strip_row, [self._sum_device, self._sum_android, self._sum_serial, self._sum_count]
        )
        self.device_info = self._sum_device._sub

        tool_card, cmd_inner = UI.command_bar(root, padding=block_pad)
        tool_card.grid(row=1, column=0, sticky="ew", pady=(0, block_pad))

        bar = ctk.CTkFrame(cmd_inner, fg_color="transparent")
        bar.pack(fill="x")
        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.pack(side="left")
        self.refresh_btn = UI.btn(
            left, "Làm mới", self.load_packages_async, variant="secondary", width=84, height=tb_h
        )
        self.refresh_btn.pack(side="left", padx=(0, SPACE["2"]))
        self.scan_btn = UI.btn(
            left, "Phân tích", self.scan_all_async, variant="primary", width=88, height=tb_h
        )
        self.scan_btn.pack(side="left", padx=(0, SPACE["2"]))
        self.uninstall_btn = UI.btn(
            left, "Gỡ chọn", self.uninstall_selected_async, variant="danger", width=76, height=tb_h
        )
        self.uninstall_btn.pack(side="left", padx=(0, SPACE["2"]))
        self.more_btn = UI.btn(
            left, "Thêm ▾", self._open_more_menu, variant="ghost", width=92, height=tb_h,
            font=get_font("body"),
        )
        self.more_btn.pack(side="left")
        search_wrap = UI.search_field(bar, placeholder="Tìm app hoặc package…", width=360)
        search_wrap.pack(side="right")
        self.search_entry = search_wrap._entry
        self.search_entry.bind("<KeyRelease>", self._on_search_change)

        meta = ctk.CTkFrame(cmd_inner, fg_color="transparent")
        meta.pack(fill="x", pady=(SPACE["3"], 0))
        meta_left = ctk.CTkFrame(meta, fg_color="transparent")
        meta_left.pack(side="left")
        self.selected_count_label = UI.muted(meta_left, "Đã chọn: 0", anchor="w")
        self.selected_count_label.pack(side="left", padx=(0, SPACE["3"]))
        self.badge_high = UI.badge(meta_left, "Nguy cơ cao: 0", tone="danger")
        self.badge_high.pack(side="left", padx=(0, SPACE["2"]))
        self._bind_risk_filter_badge(self.badge_high, "dangerous")
        self.badge_safe = UI.badge(meta_left, "An toàn: 0", tone="success")
        self.badge_safe.pack(side="left", padx=(0, SPACE["2"]))
        self._bind_risk_filter_badge(self.badge_safe, "safe")
        self.badge_warn = UI.badge(meta_left, "Cảnh báo: 0", tone="warning")
        self.badge_warn.pack(side="left")
        self._bind_risk_filter_badge(self.badge_warn, "warning")
        self.scan_ready = UI.status_ready(meta)
        self.scan_ready.pack(side="right")

        self._progress_holder = ctk.CTkFrame(cmd_inner, fg_color="transparent")
        self.scan_progress = UI.progress(self._progress_holder)
        self.scan_progress.pack(fill="x", pady=(SPACE["1"], 0))
        self._progress_holder.pack(fill="x")
        self._progress_holder.pack_forget()

        self.table_outer = UI.card(root, padding=block_pad, inset=True)
        self.table_outer.grid(row=2, column=0, sticky="nsew")
        table_outer = UI.card_inner(self.table_outer)
        table_outer.grid_columnconfigure(0, weight=1)
        table_outer.grid_rowconfigure(1, weight=1)

        head = ctk.CTkFrame(table_outer, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", pady=(0, SPACE["2"]))
        self.table_section_title = UI.label(head, "Danh sách ứng dụng (0 package)", variant="heading")
        self.table_section_title.pack(side="left")

        table_card = ctk.CTkFrame(table_outer, fg_color=C["bg_inset"], corner_radius=RADIUS["md"])
        table_card.grid(row=1, column=0, sticky="nsew")
        self._col_leading_w = 260
        self._col_package_w = 280
        self._col_state_w = 96
        self._col_size_w = 72
        self._sort_desc: dict[str, bool] = {}

        table_host = ctk.CTkFrame(table_card, fg_color=C["bg_inset"], corner_radius=0)
        table_host.pack(fill="both", expand=True)
        table_host.grid_columnconfigure(0, weight=1)
        table_host.grid_rowconfigure(1, weight=1)
        self._table_host = table_host
        self._sync_header_after_id = None

        self._build_table_header(table_host)

        columns = ("package", "state", "size")
        self._tree_style = ttk.Style()
        tree_style, _ = UI.configure_treeview(self._tree_style, "HBG")
        self.table = ttk.Treeview(
            table_host, columns=columns, show="tree", selectmode="extended", style=tree_style
        )
        self.table.grid(row=1, column=0, sticky="nsew")
        self._table_scrollbar = ttk.Scrollbar(table_host, orient="vertical", command=self.table.yview)
        self._table_scrollbar.grid(row=1, column=1, sticky="ns")
        self.table.configure(yscrollcommand=self._table_scrollbar.set)
        self.table.column("#0", width=self._col_leading_w, minwidth=180, stretch=True, anchor="w")
        self.table.column("package", width=self._col_package_w, minwidth=140, stretch=True, anchor="w")
        self.table.column("state", width=self._col_state_w, minwidth=88, stretch=False, anchor="center")
        self.table.column("size", width=self._col_size_w, minwidth=56, stretch=False, anchor="e")
        self.table.bind("<Configure>", self._schedule_sync_table_columns)
        table_host.bind("<Configure>", self._schedule_sync_table_columns)
        self.after_idle(self._sync_table_columns)
        self.table.bind("<Button-1>", self._on_table_click, add="+")
        self.table.bind("<ButtonRelease-1>", self._on_table_release, add="+")
        self.table.bind("<Double-1>", self._on_table_double_click)
        self.table.bind("<Button-3>", self._open_context_menu)
        self.table.bind("<space>", self._on_space_toggle)
        self.table.bind("<Motion>", self._on_table_motion)
        self.table.bind("<Leave>", self._on_table_leave)
        self.table.bind("<<TreeviewSelect>>", self._on_row_select)

        self.table.tag_configure("row_odd", background=C["bg_inset"])
        self.table.tag_configure("row_even", background=C["row_alt"])
        self.table.tag_configure("row_hover", background=C["bg_card_hover"])
        self.table.tag_configure("checked_row", background=C["row_hover"])
        self.table.tag_configure("risk_safe", foreground="#86efac")
        self.table.tag_configure("risk_warning", foreground="#fcd34d")
        self.table.tag_configure("risk_danger", foreground="#fda4af")
        self.table.tag_configure("app_disabled", foreground=C["text_tertiary"])

        self.scan_status_label = getattr(self.scan_ready, "_status", self.scan_ready)

        self.empty_state = UI.empty_state(
            root,
            icon="◇",
            title="Chưa kết nối thiết bị",
            description="Cắm cáp USB và bật USB Debugging để tải danh sách ứng dụng.",
            action_text="Kết nối lại",
            action_cmd=self._reconnect_device,
        )
        self.empty_state.grid(row=2, column=0, sticky="nsew")
        self.empty_state.grid_remove()
        self.empty_icon = None
        self.empty_text = None
        self.empty_desc = None
        self.reconnect_btn = None
        self.set_connected(False)

    def refresh_summary_card(self):
        if not hasattr(self, "_sum_device"):
            return
        dm = self.device_manager
        online = dm.device_connected
        if online:
            self._sum_device.set_metric(dm.device_model or "—", "Đã kết nối", sub_tone="success")
            self._sum_android.set_metric(f"Android {dm.android_version}", "Phiên bản OS")
            self._sum_serial.set_metric(dm.serial or "—", "Serial")
        else:
            self._sum_device.set_metric("—", "Chưa kết nối", sub_tone="muted")
            self._sum_android.set_metric("—", "Phiên bản OS")
            self._sum_serial.set_metric("—", "Serial")
        n = len(self.all_rows)
        self._sum_count.set_metric(str(n), f"{n} package")

    def update_device_info(self):
        dm = self.device_manager
        if dm.device_connected:
            self.is_connected = True
        self.refresh_summary_card()

    def set_connected(self, connected):
        self.is_connected = bool(connected)
        state = "normal" if connected else "disabled"
        for btn in [self.refresh_btn, self.scan_btn, self.uninstall_btn, self.more_btn]:
            btn.configure(state=state)
        self.search_entry.configure(state=state)
        self._update_selection_ui()
        self.update_device_info()
        self._update_empty_state()

    def _open_more_menu(self):
        connected = self.is_connected
        selected = bool(self._selected_packages())
        PremiumMenu.show_below_widget(
            self,
            self.more_btn,
            [
                {"label": "Chọn tất cả", "icon": "✓", "command": self.toggle_select_all, "enabled": connected},
                {"type": "separator"},
                {"label": "Tắt ứng dụng", "icon": "⛔", "command": lambda: self._bulk_pm_async("disable-user"), "enabled": connected and selected},
                {"label": "Bật ứng dụng", "icon": "▶", "command": lambda: self._bulk_pm_async("enable"), "enabled": connected and selected},
                {"type": "separator"},
                {"label": "Tắt thông báo", "icon": "🔕", "command": self.mute_notifications_selected, "enabled": connected and selected},
                {"label": "Bật thông báo", "icon": "🔔", "command": self.unmute_notifications_selected, "enabled": connected and selected},
                {"type": "separator"},
                {"label": "Xuất danh sách", "icon": "⬇", "command": self.export_list, "enabled": connected},
            ],
            min_width=260,
        )

    def _context_menu_items(self) -> list:
        connected = self.is_connected
        selected = bool(self._selected_packages())
        on = connected and selected
        return [
            {"label": "Mở app", "icon": "⏵", "command": self.open_selected_app, "enabled": on},
            {"label": "Copy package", "icon": "⎘", "command": self.copy_selected_package, "enabled": selected},
            {
                "label": "Tìm kiếm APK",
                "icon": "🔍",
                "enabled": selected,
                "submenu": [
                    {"label": "Tìm trên Play Store", "icon": "▣", "command": self.search_apk_playstore, "enabled": selected},
                    {"label": "Tìm trên Google", "icon": "G", "command": self.search_apk_google, "enabled": selected},
                ],
            },
            {"type": "separator"},
            {"label": "Gỡ cài đặt", "icon": "🗑", "command": self.uninstall_selected_async, "enabled": on},
            {"label": "Tắt ứng dụng", "icon": "⊘", "command": lambda: self._bulk_pm_async("disable-user"), "enabled": on},
            {"label": "Bật lại ứng dụng", "icon": "◉", "command": self.enable_app_selected, "enabled": on},
            {"label": "Force stop", "icon": "⊗", "command": self.force_stop_selected, "enabled": on},
            {"label": "Chặn mạng app", "icon": "⛨", "command": self.block_network_selected, "enabled": on},
            {"type": "separator"},
            {
                "label": "Quản lý thông báo",
                "icon": "🔔",
                "trail": "⚙",
                "enabled": on,
                "submenu": [
                    {"label": "Tắt thông báo", "icon": "🔕", "command": self.mute_notifications_selected, "enabled": on},
                    {"label": "Bật thông báo", "icon": "🔔", "command": self.unmute_notifications_selected, "enabled": on},
                ],
            },
            {"label": "Xóa dữ liệu", "icon": "⌧", "command": self.clear_app_data_selected, "enabled": on},
            {"label": "Xóa bộ nhớ đệm", "icon": "↺", "command": self.clear_app_cache_selected, "enabled": on},
        ]

    def load_packages_async(self):
        ok, msg = self.device_manager.refresh()
        if not ok:
            self.log(f"Chưa có thiết bị ADB — {msg}")
            self.set_connected(False)
            self._update_empty_state()
            return
        self.set_connected(True)
        self.update_device_info()

        if self._loading_packages:
            self._pending_refresh = True
            self.log("Đang quét — sẽ làm mới lại khi xong.")
            return

        self._loading_packages = True
        self._load_error = None
        self._risk_filter = None
        self._update_risk_badge_highlight()
        self._icon_fetch_gen += 1
        self.tk_icon_cache.clear()
        self._icon_rgba_cache.clear()
        self._row_leading_photos.clear()
        self.log("Đang làm mới danh sách ứng dụng...")
        self.refresh_btn.configure(state="disabled", text="Đang tải...")
        if hasattr(self, "table_section_title"):
            self.table_section_title.configure(text="Đang quét ứng dụng…")
        for iid in self.table.get_children():
            self.table.delete(iid)
        self._update_empty_state()
        self.executor.submit(self._load_packages_thread)

    def _load_packages_thread(self):
        try:
            rows = self.device_manager.list_packages()
            self.after(0, lambda r=rows: self._apply_rows(r))
        except Exception as exc:
            logging.exception("load_packages failed")
            self.after(0, lambda e=str(exc): self._apply_rows_failed(e))

    def _apply_rows_failed(self, message: str):
        self._loading_packages = False
        self._load_error = message
        self.refresh_btn.configure(state="normal", text="Làm mới")
        self.log(f"Lỗi tải danh sách: {message}")
        self._update_empty_state()

    def _apply_rows(self, rows):
        self._loading_packages = False
        self._load_error = None
        seen = set()
        normalized = []
        for row in rows:
            pkg = compact_package_id(row["package"])
            row["package"] = pkg
            if not pkg or pkg in seen:
                continue
            seen.add(pkg)
            quick = self.analysis_cache.get(pkg)
            if not quick:
                quick = self.analyzer.analyze(pkg, row.get("name", ""))
                self.analysis_cache[pkg] = quick
            row["analysis"] = quick
            row["risk_text"] = self._format_risk(quick)
            row["tags_text"] = ",".join(quick.get("tags", [])[:5])
            normalized.append(row)
        self._save_analysis_cache()
        self.all_rows = normalized
        self.package_to_row = {r["package"]: r for r in normalized}
        if hasattr(self.device_manager, "_label_resolver"):
            n_cache = self.device_manager._label_resolver.bulk_apply_to(
                self.device_manager.label_cache,
            )
            if n_cache:
                for row in normalized:
                    lbl = self.device_manager.label_cache.get(row["package"])
                    if lbl:
                        row["name"] = lbl
        self._icon_failed.clear()
        self._icon_bg_pending = True
        self.device_manager.clear_label_enrich_tried()
        self._apply_filter()
        self.after(400, self._start_background_icon_warmup)
        self.refresh_btn.configure(state="normal", text="Làm mới")
        if normalized:
            self.log(f"✓ Danh sách · {len(normalized)} ứng dụng")
        else:
            self.log("Không tìm thấy ứng dụng — thử bấm Làm mới.")
        self._update_empty_state()
        self._start_lazy_size_refresh()
        self._start_lazy_label_refresh()

        if self._pending_refresh:
            self._pending_refresh = False
            self.after(300, self.load_packages_async)

    def _on_search_change(self, _):
        if self.search_after_id:
            self.after_cancel(self.search_after_id)
        self.search_after_id = self.after(250, self._apply_filter)

    @staticmethod
    def _row_risk_level(row) -> str:
        return (row.get("analysis") or {}).get("level", "safe")

    def _row_matches_risk_filter(self, row) -> bool:
        if not self._risk_filter:
            return True
        level = self._row_risk_level(row)
        if self._risk_filter == "dangerous":
            return level == "dangerous"
        if self._risk_filter == "warning":
            return level in ("warning", "high_risk")
        if self._risk_filter == "safe":
            return level in ("safe", "low_risk")
        return True

    def _bind_risk_filter_badge(self, badge_frame, filter_key: str):
        badge_frame._risk_filter_key = filter_key

        def on_click(_event=None):
            self._toggle_risk_filter(filter_key)

        for widget in (badge_frame, *badge_frame.winfo_children()):
            widget.bind("<Button-1>", on_click)
            try:
                widget.configure(cursor="hand2")
            except tk.TclError:
                pass

    def _toggle_risk_filter(self, filter_key: str):
        self._risk_filter = None if self._risk_filter == filter_key else filter_key
        self._update_risk_badge_highlight()
        self._apply_filter()

    def _update_risk_badge_highlight(self):
        tone_border = {
            "dangerous": C["danger"],
            "safe": C["success"],
            "warning": C["warning"],
        }
        for badge, key in (
            (getattr(self, "badge_high", None), "dangerous"),
            (getattr(self, "badge_safe", None), "safe"),
            (getattr(self, "badge_warn", None), "warning"),
        ):
            if badge is None:
                continue
            active = self._risk_filter == key
            border = tone_border.get(key, C["border_default"])
            badge.configure(
                border_width=2 if active else 1,
                border_color=border,
                fg_color=C["bg_card_hover"] if active else "transparent",
            )

    def _apply_filter(self):
        q = self.search_entry.get().strip().lower()
        rows = list(self.all_rows)
        if q:
            rows = [r for r in rows if q in r["package"].lower() or q in r["name"].lower()]
        if self._risk_filter:
            rows = [r for r in rows if self._row_matches_risk_filter(r)]
        self.filtered_rows = rows
        self._render_table()

    def _render_table(self):
        self.package_to_iid = {}
        for iid in self.table.get_children():
            self.table.delete(iid)
        for idx, r in enumerate(self.filtered_rows):
            display_name = r["name"]
            pkg = r["package"]
            enabled = r.get("enabled", True)
            state_lbl = self._app_state_label(r)
            if enabled:
                level = (r.get("analysis") or {}).get("level", "safe")
                risk_tag = "risk_safe"
                if level in ("warning", "high_risk"):
                    risk_tag = "risk_warning"
                elif level == "dangerous":
                    risk_tag = "risk_danger"
                tags = [risk_tag, "row_even" if idx % 2 == 0 else "row_odd"]
            else:
                tags = ["app_disabled", "row_even" if idx % 2 == 0 else "row_odd"]
            if r["checked"]:
                tags.append("checked_row")
            sz = r.get("size", "...")
            if sz in ("-", "", None):
                sz = "N/A"
            iid = self.table.insert(
                "",
                "end",
                text=self._table_display_name(display_name),
                image=self._leading_photo(pkg, r["checked"]),
                values=(compact_package_id(pkg), state_lbl, sz),
                tags=tuple(tags),
            )
            self.package_to_iid[pkg] = iid
            disk = self.device_manager.get_cached_icon_path(pkg)
            if disk:
                self._apply_icon_to_row(pkg, disk)
        self._update_selection_ui()
        self._update_empty_state()
        self._schedule_sync_table_columns()
        if self.is_connected and self.filtered_rows:
            self._start_lazy_icon_refresh()

    def _schedule_render(self, delay_ms=120):
        if self._render_scheduled:
            self.after_cancel(self._render_scheduled)
        self._render_scheduled = self.after(delay_ms, self._render_table)

    def _start_lazy_size_refresh(self):
        if self._size_refresh_in_progress:
            return
        self._size_refresh_in_progress = True
        packages = [r["package"] for r in self.all_rows if r.get("size") in ("...", "-", "", None)]
        if not packages:
            self._size_refresh_in_progress = False
            return
        self.executor.submit(self._lazy_size_worker, packages)

    def _lazy_size_worker(self, packages):
        updated = 0
        for pkg in packages:
            size = self.device_manager.get_package_size(pkg)
            for row in self.all_rows:
                if row["package"] == pkg:
                    row["size"] = size
                    break
            updated += 1
            # Cập nhật theo batch để UI không giật khi data lớn.
            if updated % 25 == 0:
                self.after(0, self._schedule_render)
        self.after(0, self._finish_lazy_size_refresh)

    def _finish_lazy_size_refresh(self):
        self._size_refresh_in_progress = False
        self._apply_filter()

    def _packages_label_order(self) -> list[str]:
        """Thứ tự trên bảng (trên → dưới), rồi phần còn lại — lazy load đúng UX."""
        order: list[str] = []
        seen: set[str] = set()
        for iid in self.table.get_children():
            vals = self.table.item(iid, "values")
            pkg = self._package_from_values(vals)
            if pkg and pkg not in seen:
                seen.add(pkg)
                order.append(pkg)
        for row in self.all_rows:
            pkg = row["package"]
            if pkg not in seen:
                seen.add(pkg)
                order.append(pkg)
        return order

    def _start_lazy_label_refresh(self):
        if self._label_refresh_in_progress or not self.all_rows:
            return
        self._label_refresh_in_progress = True
        packages = self._packages_label_order()
        self.executor.submit(self._lazy_label_worker, packages)

    def _lazy_label_worker(self, packages):
        """Luồng nền: tên app từ cache → aapt (không dumpsys hàng loạt)."""
        for pkg in packages:
            try:
                row = self.package_to_row.get(pkg) or {}
                current = row.get("name", "")
                if current and not is_provisional_label(pkg, current):
                    continue
                hint = row.get("apk_path") or None
                label = self.device_manager.enrich_app_label_from_device(pkg, hint)
                if label:
                    self.after(0, lambda p=pkg, n=label: self._apply_label_to_row(p, n))
            except Exception as exc:
                logging.debug(f"label {pkg}: {exc}")
        self.after(0, self._finish_lazy_label_refresh)

    def _finish_lazy_label_refresh(self):
        self._label_refresh_in_progress = False

    def _apply_label_to_row(self, package, new_name):
        row = self.package_to_row.get(package)
        if not row:
            return
        row["name"] = new_name
        iid = self.package_to_iid.get(package)
        if iid and self.table.exists(iid):
            self.table.item(iid, text=self._table_display_name(new_name))

    @staticmethod
    def _table_display_name(name: str, max_len: int = 42) -> str:
        text = (name or "").strip()
        if not text or text in ("…", "...", "—"):
            return "—"
        if len(text) <= max_len:
            return text
        return text[: max_len - 1] + "…"

    def _placeholder_icon_rgba(self) -> Image.Image:
        return Image.new("RGBA", (TABLE_LEADING_ICON_PX, TABLE_LEADING_ICON_PX), (38, 42, 52, 255))

    def _icon_rgba_for(self, package: str) -> Image.Image:
        cached = self._icon_rgba_cache.get(package)
        if cached is not None:
            return cached
        path = self.device_manager.get_cached_icon_path(package)
        if path:
            try:
                cached = Image.open(path).convert("RGBA")
            except Exception:
                cached = self._placeholder_icon_rgba()
        else:
            cached = self._placeholder_icon_rgba()
        self._icon_rgba_cache[package] = cached
        return cached

    def _leading_photo(self, package: str, checked: bool) -> ImageTk.PhotoImage:
        composite = compose_table_leading(
            self._icon_rgba_for(package),
            checked=checked,
            icon_px=TABLE_LEADING_ICON_PX,
        )
        photo = ImageTk.PhotoImage(composite)
        self._row_leading_photos[package] = photo
        return photo

    def _refresh_row_leading(self, package: str) -> None:
        row = self.package_to_row.get(package)
        iid = self.package_to_iid.get(package)
        if not row or not iid or not self.table.exists(iid):
            return
        self.table.item(
            iid,
            image=self._leading_photo(package, bool(row.get("checked"))),
            text=self._table_display_name(row.get("name", "")),
        )

    def _start_lazy_icon_refresh(self):
        if not self.is_connected:
            return
        targets = [
            r["package"]
            for r in self.filtered_rows
            if not self.device_manager.has_real_icon_cached(r["package"])
        ]
        if not targets:
            return
        self._icon_fetch_gen += 1
        gen = self._icon_fetch_gen
        self._icon_executor.submit(self._lazy_icon_worker, targets, gen)

    def _start_background_icon_warmup(self):
        if not self._icon_bg_pending or not self.is_connected:
            return
        self._icon_bg_pending = False
        rest = [
            r["package"]
            for r in self.all_rows
            if not self.device_manager.has_real_icon_cached(r["package"])
        ][:120]
        if rest:
            self._icon_executor.submit(self._lazy_icon_worker, rest, -1)

    def _apply_icon_batch(self, pairs, gen=None):
        if gen is not None and gen != self._icon_fetch_gen and gen != -1:
            return
        for pkg, path in pairs:
            self._apply_icon_to_row(pkg, path)

    def _lazy_icon_worker(self, packages, gen):
        def work(pkg):
            try:
                if self.device_manager.has_real_icon_cached(pkg):
                    return pkg, self.device_manager.get_cached_icon_path(pkg)
                row = self.package_to_row.get(pkg) or {}
                hint = row.get("apk_path") or None
                path = self.device_manager.extract_icon_to_cache(pkg, hint)
                return pkg, path
            except Exception as exc:
                logging.debug(f"Lấy icon {pkg}: {exc}")
                return pkg, None

        batch_size = 16 if gen == -1 else 8
        for start in range(0, len(packages), batch_size):
            if gen != -1 and gen != self._icon_fetch_gen:
                return
            chunk = packages[start : start + batch_size]
            updates = []
            futures = [self._icon_executor.submit(work, pkg) for pkg in chunk]
            for fu in as_completed(futures):
                try:
                    pkg, path = fu.result()
                except Exception as exc:
                    logging.debug(f"icon future: {exc}")
                    continue
                if path:
                    updates.append((pkg, path))
            if updates:
                batch = list(updates)
                self.after(0, lambda b=batch, g=gen: self._apply_icon_batch(b, g))

    def _mark_icon_failed(self, packages):
        for p in packages:
            self._icon_failed.add(p)

    def _apply_icon_to_row(self, package, icon_path):
        iid = self.package_to_iid.get(package)
        if not iid or not self.table.exists(iid):
            return
        try:
            self._icon_rgba_cache[package] = Image.open(icon_path).convert("RGBA")
            self._icon_failed.discard(package)
            self._refresh_row_leading(package)
        except Exception as exc:
            logging.debug(f"Không thể apply icon {package}: {exc}")

    def _toggle_package_checked(self, package):
        row = self.package_to_row.get(package)
        if not row:
            return
        row["checked"] = not row["checked"]
        iid = self.package_to_iid.get(package)
        if iid and self.table.exists(iid):
            self._refresh_row_leading(package)
            current_tags = [t for t in self.table.item(iid, "tags") if t != "checked_row"]
            if row["checked"]:
                current_tags.append("checked_row")
            self.table.item(iid, tags=tuple(current_tags))
        self._update_selection_ui()

    def _package_from_iid(self, iid: str) -> str | None:
        return self._package_from_values(self.table.item(iid, "values"))

    def _on_table_motion(self, event):
        row_id = self.table.identify_row(event.y)
        if row_id == self._hover_iid:
            return
        if self._hover_iid and self.table.exists(self._hover_iid):
            tags = [t for t in self.table.item(self._hover_iid, "tags") if t != "row_hover"]
            self.table.item(self._hover_iid, tags=tuple(tags))
        self._hover_iid = row_id or None
        if row_id and self.table.exists(row_id):
            tags = list(self.table.item(row_id, "tags"))
            if "row_hover" not in tags:
                tags.append("row_hover")
                self.table.item(row_id, tags=tuple(tags))

    def _on_table_leave(self, _event):
        if self._hover_iid and self.table.exists(self._hover_iid):
            tags = [t for t in self.table.item(self._hover_iid, "tags") if t != "row_hover"]
            self.table.item(self._hover_iid, tags=tuple(tags))
        self._hover_iid = None

    def _build_table_header(self, parent):
        """Header tùy chỉnh (tk) — checkbox/icon/Package căn khớp cột Treeview."""
        hdr_h = 40
        hdr_font = ("Segoe UI", 11, "bold")
        hdr_fg = C["text_secondary"]
        hdr_bg = C["bg_card"]
        icon_x = TABLE_LEADING_PAD_LEFT + TABLE_CB_PX + TABLE_LEADING_GAP

        self._table_hdr = tk.Frame(parent, bg=hdr_bg, height=hdr_h, highlightthickness=0, bd=0)
        self._table_hdr.grid(row=0, column=0, sticky="ew")
        self._table_hdr.grid_propagate(False)
        self._table_hdr.grid_columnconfigure(0, minsize=self._col_leading_w, weight=1)
        self._table_hdr.grid_columnconfigure(1, minsize=self._col_package_w, weight=1)
        self._table_hdr.grid_columnconfigure(2, minsize=self._col_state_w, weight=0)
        self._table_hdr.grid_columnconfigure(3, minsize=self._col_size_w, weight=0)
        self._table_hdr.grid_rowconfigure(0, weight=1)

        self._hdr_scroll_spacer = tk.Frame(parent, bg=hdr_bg, width=17, highlightthickness=0, bd=0)
        self._hdr_scroll_spacer.grid(row=0, column=1, sticky="ns")

        leading = tk.Frame(self._table_hdr, bg=hdr_bg, highlightthickness=0, bd=0)
        leading.grid(row=0, column=0, sticky="nsew")

        self._hdr_cb_photo = ImageTk.PhotoImage(draw_table_checkbox(checked=False))
        self._hdr_cb = tk.Label(
            leading, image=self._hdr_cb_photo, bg=hdr_bg, bd=0, highlightthickness=0, cursor="hand2",
        )
        self._hdr_cb.place(x=TABLE_LEADING_PAD_LEFT, rely=0.5, anchor="w")
        self._hdr_cb.bind("<Button-1>", lambda _e: self.toggle_select_all())

        self._hdr_name = tk.Label(
            leading, text="Tên ứng dụng", font=hdr_font, fg=hdr_fg, bg=hdr_bg, anchor="w",
        )
        self._hdr_name.place(x=icon_x, rely=0.5, anchor="w")

        self._hdr_package = tk.Label(
            self._table_hdr, text="Package", font=hdr_font, fg=hdr_fg, bg=hdr_bg, anchor="w", cursor="hand2",
        )
        self._hdr_package.grid(row=0, column=1, sticky="w")
        self._hdr_package.bind(
            "<Button-1>", lambda _e: self._sort_by("package", not self._sort_desc.get("package", True))
        )

        self._hdr_state = tk.Label(
            self._table_hdr, text="Status", font=hdr_font, fg=hdr_fg, bg=hdr_bg, anchor="center", cursor="hand2",
        )
        self._hdr_state.grid(row=0, column=2, sticky="ew")
        self._hdr_state.bind(
            "<Button-1>", lambda _e: self._sort_by("state", not self._sort_desc.get("state", True))
        )

        self._hdr_size = tk.Label(
            self._table_hdr, text="Size", font=hdr_font, fg=hdr_fg, bg=hdr_bg, anchor="e", cursor="hand2",
        )
        self._hdr_size.grid(row=0, column=3, sticky="ew", padx=(0, 8))
        self._hdr_size.bind(
            "<Button-1>", lambda _e: self._sort_by("size", not self._sort_desc.get("size", True))
        )

        tk.Frame(self._table_hdr, bg=C["border_subtle"], height=1).place(
            relx=0, rely=1, relwidth=1, anchor="sw"
        )

    def _schedule_sync_table_columns(self, _event=None):
        if self._sync_header_after_id is not None:
            self.after_cancel(self._sync_header_after_id)
        self._sync_header_after_id = self.after(40, self._sync_table_columns)

    def _sync_table_columns(self):
        self._sync_header_after_id = None
        if not hasattr(self, "table") or not hasattr(self, "_table_hdr"):
            return
        try:
            if not self.table.winfo_exists():
                return
        except tk.TclError:
            return

        w0 = int(self.table.column("#0", "width"))
        wp = int(self.table.column("package", "width"))
        ws = int(self.table.column("state", "width"))
        wz = int(self.table.column("size", "width"))

        self._table_hdr.grid_columnconfigure(0, minsize=w0, weight=1)
        self._table_hdr.grid_columnconfigure(1, minsize=wp, weight=1)
        self._table_hdr.grid_columnconfigure(2, minsize=ws, weight=0)
        self._table_hdr.grid_columnconfigure(3, minsize=wz, weight=0)

        pkg_pad = 0
        children = self.table.get_children("")
        if children:
            bbox = self.table.bbox(children[0], column="package")
            if bbox:
                pkg_pad = max(0, bbox[0] - w0)

        self._hdr_package.grid_configure(padx=(pkg_pad, 0))

        if hasattr(self, "_hdr_scroll_spacer") and hasattr(self, "_table_scrollbar"):
            try:
                sw = max(self._table_scrollbar.winfo_width(), self._table_scrollbar.winfo_reqwidth(), 16)
            except tk.TclError:
                sw = 17
            self._hdr_scroll_spacer.configure(width=sw)

    def _header_checkbox_flags(self) -> tuple[bool, bool]:
        visible_count = len(self.filtered_rows)
        if visible_count == 0:
            return False, False
        checked_visible = sum(1 for r in self.filtered_rows if r.get("checked"))
        if checked_visible == 0:
            return False, False
        if checked_visible == visible_count:
            return True, False
        return False, True

    def _refresh_table_header(self):
        if not hasattr(self, "_hdr_cb"):
            return
        checked, indeterminate = self._header_checkbox_flags()
        self._hdr_cb_photo = ImageTk.PhotoImage(
            draw_table_checkbox(checked=checked, indeterminate=indeterminate)
        )
        self._hdr_cb.configure(image=self._hdr_cb_photo)

    def _click_in_leading_zone(self, event, row_id: str) -> bool:
        """Vùng checkbox + icon (không gồm text tên app)."""
        if self.table.identify_column(event.x) != "#0":
            return False
        bbox = self.table.bbox(row_id, column="#0")
        if bbox:
            return (event.x - bbox[0]) <= self._leading_hit_w
        return event.x <= self._leading_hit_w + 16

    def _on_table_click(self, event):
        """Focus bảng ngay — tránh click đầu chỉ “arm” hàng."""
        self.table.focus_set()

    def _on_table_release(self, event):
        region = self.table.identify_region(event.x, event.y)
        if region not in ("cell", "tree"):
            return
        row_id = self.table.identify_row(event.y)
        if not row_id:
            return
        if not self._click_in_leading_zone(event, row_id):
            return
        package = self._package_from_iid(row_id)
        if package:
            self._toggle_package_checked(package)
        return "break"

    def _on_table_double_click(self, event):
        row_id = self.table.identify_row(event.y)
        if not row_id:
            return
        col_id = self.table.identify_column(event.x)
        if col_id == "#0" and self._click_in_leading_zone(event, row_id):
            return "break"
        if col_id == "#1":
            self.table.selection_set(row_id)
            self.show_selected_details()
            return "break"
        return None

    def _on_space_toggle(self, _event):
        focused = self.table.focus()
        if not focused:
            return "break"
        pkg = self._package_from_iid(focused)
        if pkg:
            self._toggle_package_checked(pkg)
        return "break"

    def toggle_select_all(self):
        all_selected = all(r["checked"] for r in self.filtered_rows) if self.filtered_rows else False
        for row in self.filtered_rows:
            row["checked"] = not all_selected
            iid = self.package_to_iid.get(row["package"])
            if iid and self.table.exists(iid):
                self._refresh_row_leading(row["package"])
                current_tags = [t for t in self.table.item(iid, "tags") if t != "checked_row"]
                if row["checked"]:
                    current_tags.append("checked_row")
                self.table.item(iid, tags=tuple(current_tags))
        self._update_selection_ui()

    def _update_selection_ui(self):
        selected_count = sum(1 for r in self.all_rows if r.get("checked"))
        self.selected_count_label.configure(text=f"Đã chọn: {selected_count}")
        high = warn = safe = 0
        for row in self.all_rows:
            level = (row.get("analysis") or {}).get("level", "safe")
            if level == "dangerous":
                high += 1
            elif level in ("warning", "high_risk"):
                warn += 1
            else:
                safe += 1
        if hasattr(self, "badge_high"):
            self._set_badge_text(self.badge_high, f"Nguy cơ cao: {high}")
            self._set_badge_text(self.badge_safe, f"An toàn: {safe}")
            self._set_badge_text(self.badge_warn, f"Cảnh báo: {warn}")
            self._update_risk_badge_highlight()
        self.refresh_summary_card()
        self._refresh_table_header()
        action_state = "normal" if self.is_connected and selected_count > 0 else "disabled"
        self.uninstall_btn.configure(state=action_state)
        if hasattr(self, "table_section_title"):
            n = len(self.filtered_rows)
            total = len(self.all_rows)
            if self._risk_filter and n != total:
                self.table_section_title.configure(text=f"Danh sách ứng dụng ({n}/{total} package)")
            else:
                self.table_section_title.configure(text=f"Danh sách ứng dụng ({n} package)")

    def _format_risk(self, analysis):
        score = analysis.get("score", 0)
        level = analysis.get("level", "safe")
        if level == "dangerous":
            return f"{score} 🔴 Dangerous"
        if level in ("warning", "high_risk"):
            return f"{score} 🟡 Warning"
        if level == "low_risk":
            return f"{score} 🟠 Low"
        return f"{score} 🟢 Safe"

    def _load_analysis_cache(self):
        try:
            if os.path.exists(analysis_cache_file):
                with open(analysis_cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
        except Exception as exc:
            logging.debug(f"Không load được analysis cache: {exc}")
        return {}

    def _refresh_trusted_analysis_cache(self):
        """Xóa cache risk sai (vd. TikTok từng nằm nhầm BLACKLIST)."""
        changed = False
        for pkg in list(self.analysis_cache):
            if pkg not in TRUSTED_ANALYSIS_PACKAGES:
                continue
            entry = self.analysis_cache.get(pkg) or {}
            if entry.get("level") in ("dangerous", "high_risk") or "blacklist" in entry.get("tags", []):
                del self.analysis_cache[pkg]
                changed = True
        if changed:
            self._save_analysis_cache()

    def _save_analysis_cache(self):
        try:
            with open(analysis_cache_file, "w", encoding="utf-8") as f:
                json.dump(self.analysis_cache, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logging.debug(f"Không lưu được analysis cache: {exc}")

    def collect_removable_junk_packages(self) -> list[str]:
        """App nên gỡ sau phân tích — nguy hiểm / blacklist / rác QC."""
        return [item["package"] for item in self.collect_removable_junk_items()]

    def collect_removable_junk_items(self) -> list[dict]:
        found: list[dict] = []
        for row in self.all_rows:
            pkg = row["package"]
            if is_protected_package(pkg):
                continue
            analysis = row.get("analysis") or {}
            level = analysis.get("level", "safe")
            tags = set(analysis.get("tags") or [])
            # Chỉ gợi ý gỡ khi tín hiệu mạnh — tránh app chấm công / sideload chỉ vì quyền/dumpsys
            match = (
                "blacklist" in tags
                or "remove_recommended" in tags
                or level == "dangerous"
                or (
                    level == "high_risk"
                    and (
                        "cleaner" in tags
                        or "ads" in tags
                        or "popup" in tags
                        or is_ad_related_package(pkg)
                    )
                )
            )
            if match:
                found.append({
                    "package": pkg,
                    "name": row.get("name", pkg),
                    "analysis": analysis,
                    "level": level,
                    "score": int(analysis.get("score", 0)),
                })
        found.sort(key=lambda x: (-x["score"], x["name"].lower()))
        return found

    def scan_all_async(
        self,
        *,
        quiet: bool = False,
        on_progress=None,
        on_finished=None,
    ):
        self._scan_quiet = quiet
        self._scan_on_progress = on_progress
        self._scan_finished_cb = on_finished
        if not self.all_rows:
            cb = on_finished or getattr(self, "on_scan_finished", None)
            if cb:
                self.after(0, lambda: cb([]))
            self._scan_quiet = False
            self._scan_on_progress = None
            self._scan_finished_cb = None
            return
        if not quiet:
            self.scan_btn.configure(state="disabled", text="Đang quét...")
            self.scan_progress.set(0)
            self._progress_holder.pack(fill="x", pady=(SPACE["2"], 0))
            self.scan_status_label.configure(text=f"Đang phân tích {len(self.all_rows)} ứng dụng...")
        self.executor.submit(self._scan_all_worker)

    def _scan_all_worker(self):
        total = len(self.all_rows)
        for idx, row in enumerate(self.all_rows):
            pkg = row["package"]
            try:
                insights = self.device_manager.get_package_insights(pkg)
                analysis = self.analyzer.analyze(
                    pkg,
                    row.get("name", ""),
                    permissions=insights.get("permissions"),
                    services=insights.get("services"),
                    receivers=insights.get("receivers"),
                    apk_strings=insights.get("apk_strings"),
                )
            except Exception as exc:
                logging.debug(f"Analyze fail {pkg}: {exc}")
                analysis = self.analysis_cache.get(pkg, self.analyzer.analyze(pkg, row.get("name", "")))
            row["analysis"] = analysis
            row["risk_text"] = self._format_risk(analysis)
            row["tags_text"] = ",".join(analysis.get("tags", [])[:5])
            self.analysis_cache[pkg] = analysis
            prog = getattr(self, "_scan_on_progress", None)
            if prog:
                self.after(
                    0,
                    lambda i=idx + 1, t=total, p=pkg, n=row.get("name", ""): prog(i, t, p, n),
                )
                if not self.device_manager.has_real_icon_cached(pkg):
                    hint = row.get("apk_path")
                    label = row.get("name", "") or pkg
                    self._icon_executor.submit(
                        self.device_manager.extract_icon_to_cache,
                        pkg,
                        hint,
                        label,
                    )
            elif idx % 5 == 0:
                self.after(0, lambda p=(idx + 1) / total: self.scan_progress.set(p))
                self.after(0, lambda i=idx + 1, t=total: self.scan_status_label.configure(text=f"Đang phân tích {i}/{t} ứng dụng..."))
            if idx % 5 == 0 or prog:
                self.after(0, lambda package=pkg: self._update_row_view(package))
        self._save_analysis_cache()
        self.after(0, self._finish_scan_all)

    def _update_row_view(self, package):
        row = self.package_to_row.get(package)
        iid = self.package_to_iid.get(package)
        if not row or not iid or not self.table.exists(iid):
            return
        values = list(self.table.item(iid, "values"))
        if len(values) >= 3:
            values[1] = self._app_state_label(row)
            level = (row.get("analysis") or {}).get("level", "safe")
            values[2] = row.get("size", values[2])
            base = [t for t in self.table.item(iid, "tags") if t not in ("risk_safe", "risk_warning", "risk_danger", "app_disabled")]
            if row.get("enabled", True):
                if level == "dangerous":
                    base.append("risk_danger")
                elif level in ("warning", "high_risk"):
                    base.append("risk_warning")
                else:
                    base.append("risk_safe")
            else:
                base.append("app_disabled")
            self.table.item(iid, values=values, tags=tuple(base))

    def _finish_scan_all(self):
        quiet = getattr(self, "_scan_quiet", False)
        if not quiet:
            self.scan_progress.set(1.0)
            self._progress_holder.pack_forget()
            self.scan_status_label.configure(text="Sẵn sàng quét")
            self.scan_btn.configure(state="normal", text="Phân tích")
            self._update_selection_ui()
            self.log("Quét AI hoàn tất.")
        junk = self.collect_removable_junk_packages()
        cb = getattr(self, "_scan_finished_cb", None) or (
            None if quiet else getattr(self, "on_scan_finished", None)
        )
        if cb:
            self.after(0, lambda j=junk: cb(j))
        self._scan_quiet = False
        self._scan_on_progress = None
        self._scan_finished_cb = None

    def _on_row_select(self, _event):
        pass

    def show_selected_details(self):
        pkgs = self._selected_packages()
        if not pkgs:
            return
        pkg = pkgs[0]
        row = self.package_to_row.get(pkg)
        if not row:
            return
        analysis = row.get("analysis") or {}
        show_risk_detail(
            self,
            app_name=self._display_app_name(row, pkg),
            package=pkg,
            analysis=analysis,
        )

    def _selected_packages(self):
        selected = {r["package"] for r in self.all_rows if r["checked"]}
        for iid in self.table.selection():
            vals = self.table.item(iid, "values")
            pkg = self._package_from_values(vals)
            if pkg:
                selected.add(pkg)
        return sorted(selected)

    @staticmethod
    def _display_app_name(row: dict | None, package: str) -> str:
        """Tên hiển thị — không dùng placeholder «…» trong dialog."""
        if not row:
            return package
        name = (row.get("name") or "").strip()
        if not name or name in ("…", "...", "—"):
            return package
        return name

    def uninstall_selected_async(self):
        packages = self._selected_packages()
        if not packages:
            show_notice(self, "Thông báo", "Chưa chọn ứng dụng nào.", kind="info")
            return
        extra = f"\nVà {len(packages) - 1} app khác." if len(packages) > 1 else ""
        if not ask_confirm(
            self,
            "Xác nhận gỡ cài đặt",
            f"Gỡ {len(packages)} ứng dụng đã chọn?{extra}",
            confirm_text="Gỡ",
            cancel_text="Hủy",
            danger=True,
        ):
            return
        self.executor.submit(self._bulk_uninstall_thread, packages)

    def _labels_for_packages(self, packages: list[str]) -> list[str]:
        return [
            self._display_app_name(self.package_to_row.get(pkg) or {}, pkg)
            for pkg in packages
        ]

    def _action_success_message(self, action_name: str, succeeded_packages: list[str]) -> str:
        labels = self._labels_for_packages(succeeded_packages)
        n = len(labels)
        if n == 0:
            return f"Thao tác {action_name} đã thực hiện thành công."

        action = (action_name or "").strip().lower()
        if "gỡ" in action:
            if n == 1:
                return f'Gỡ "{labels[0]}" thành công.'
            shown = ", ".join(labels[:3])
            extra = f" và {n - 3} app khác" if n > 3 else ""
            return f"Đã gỡ {n} ứng dụng ({shown}{extra}) thành công."

        if n == 1:
            return f'"{labels[0]}": {action_name} thành công.'
        shown = ", ".join(labels[:3])
        extra = f" và {n - 3} app khác" if n > 3 else ""
        return f"{action_name} thành công cho {n} app ({shown}{extra})."

    def _bulk_uninstall_thread(self, packages):
        failed = []
        succeeded = []
        for pkg in packages:
            _, err, code = self.device_manager.uninstall(pkg)
            if code != 0:
                failed.append((pkg, err or "Lỗi không xác định"))
            else:
                succeeded.append(pkg)
                self.log(f"Đã gỡ: {pkg}")
        self.after(0, lambda f=failed, s=succeeded: self._after_bulk_action(f, "gỡ cài đặt", s))

    def _bulk_pm_async(self, action):
        packages = self._selected_packages()
        if not packages:
            show_notice(self, "Thông báo", "Chưa chọn ứng dụng nào.", kind="info")
            return
        self.executor.submit(self._bulk_pm_thread, action, packages)

    def _bulk_pm_thread(self, action, packages):
        failed = []
        succeeded = []
        for pkg in packages:
            _, err, code = self.device_manager.run(
                ["-s", self.device_manager.serial, "shell", "pm", action, "--user", "0", pkg],
                timeout=8,
            )
            if code != 0:
                failed.append((pkg, err or "Lỗi không xác định"))
            else:
                succeeded.append(pkg)
                enabled = action == "enable"
                for row in self.all_rows:
                    if row["package"] == pkg:
                        row["enabled"] = enabled
                        break
        label = {"disable-user": "tắt ứng dụng", "enable": "bật lại ứng dụng"}.get(action, action)
        self.after(0, lambda f=failed, s=succeeded, a=label: self._after_bulk_action(f, a, s))

    def _after_bulk_action(self, failed, action_name, succeeded=None):
        succeeded = list(succeeded or [])
        reload_list = False
        if failed and succeeded:
            detail = "\n".join(
                f"{self._display_app_name(self.package_to_row.get(pkg) or {}, pkg)} ({pkg}): {err}"
                for pkg, err in failed[:15]
            )
            show_notice(
                self,
                "Hoàn tất một phần",
                self._action_success_message(action_name, succeeded),
                kind="warning",
                detail=f"Không thực hiện được:\n{detail}",
            )
            for pkg, err in failed:
                logging.error(f"{action_name} fail {pkg}: {err}")
            reload_list = True
        elif failed:
            detail = "\n".join(
                f"{self._display_app_name(self.package_to_row.get(pkg) or {}, pkg)} ({pkg}): {err}"
                for pkg, err in failed[:15]
            )
            show_notice(
                self,
                "Hoàn tất có lỗi",
                f"Một số thao tác {action_name} không thành công.",
                kind="warning",
                detail=detail,
            )
            for pkg, err in failed:
                logging.error(f"{action_name} fail {pkg}: {err}")
            reload_list = True
        else:
            show_notice(
                self,
                "Hoàn tất",
                self._action_success_message(action_name, succeeded),
                kind="success",
            )
            self.log(f"✓ {self._action_success_message(action_name, succeeded)}")
            if "gỡ" in (action_name or "").lower():
                reload_list = True
            else:
                self._schedule_render()
        if reload_list:
            self.load_packages_async()

    def force_stop_selected(self):
        packages = self._selected_packages()
        if not packages:
            return
        for pkg in packages:
            self.device_manager.run(["-s", self.device_manager.serial, "shell", "am", "force-stop", pkg], timeout=6)
        self.log(f"Đã force stop {len(packages)} ứng dụng.")

    def enable_app_selected(self):
        packages = self._selected_packages()
        if not packages or not self.is_connected:
            return
        self.executor.submit(self._enable_apps_thread, list(packages))

    def _enable_apps_thread(self, packages: list[str]):
        failed = []
        succeeded = []
        serial = self.device_manager.serial
        for pkg in packages:
            self.device_manager.run(
                ["-s", serial, "shell", "am", "force-stop", pkg], timeout=5
            )
            _, err, code = self.device_manager.run(
                ["-s", serial, "shell", "pm", "enable", pkg], timeout=8
            )
            if code != 0:
                failed.append((pkg, err or "pm enable"))
                continue
            succeeded.append(pkg)
            for row in self.all_rows:
                if row["package"] == pkg:
                    row["enabled"] = True
                    break
            self.device_manager.run(
                ["-s", serial, "shell", "pm", "unhide", pkg], timeout=6
            )
        self.after(0, lambda f=failed, s=succeeded: self._after_bulk_action(f, "bật lại ứng dụng", s))

    def clear_app_data_selected(self):
        packages = self._selected_packages()
        if not packages or not self.is_connected:
            return
        pkg0 = packages[0]
        name = self._display_app_name(self.package_to_row.get(pkg0), pkg0)
        extra = f"\nVà {len(packages) - 1} app khác." if len(packages) > 1 else ""
        if not ask_confirm(
            self,
            "Xóa dữ liệu",
            f'Xóa toàn bộ dữ liệu "{name}"?{extra}\n\nKhông thể hoàn tác.',
            confirm_text="Xóa",
            cancel_text="Hủy",
        ):
            return
        self.executor.submit(self._clear_app_data_thread, list(packages))

    def _clear_app_data_thread(self, packages: list[str]):
        failed = []
        succeeded = []
        serial = self.device_manager.serial
        for pkg in packages:
            self.device_manager.run(
                ["-s", serial, "shell", "am", "force-stop", pkg], timeout=5
            )
            out, err, code = self.device_manager.run(
                ["-s", serial, "shell", "pm", "clear", "--user", "0", pkg],
                timeout=12,
            )
            ok = code == 0 and (not out or "Success" in out)
            if not ok:
                failed.append((pkg, err or out or "pm clear"))
                continue
            succeeded.append(pkg)
            label = self._display_app_name(self.package_to_row.get(pkg), pkg)
            self.after(0, lambda m=f"✓ {label}: đã xóa dữ liệu": self.log(m))
        self.after(0, lambda f=failed, s=succeeded: self._after_bulk_action(f, "xóa dữ liệu", s))

    def clear_app_cache_selected(self):
        packages = self._selected_packages()
        if not packages or not self.is_connected:
            return
        pkg0 = packages[0]
        name = self._display_app_name(self.package_to_row.get(pkg0), pkg0)
        extra = f"\nVà {len(packages) - 1} app khác." if len(packages) > 1 else ""
        if not ask_confirm(
            self,
            "Xóa bộ nhớ đệm",
            f'Xóa cache "{name}"?{extra}',
            confirm_text="Xóa",
            cancel_text="Hủy",
        ):
            return
        self.executor.submit(self._clear_app_cache_thread, list(packages))

    def _clear_app_cache_thread(self, packages: list[str]):
        failed = []
        succeeded = []
        serial = self.device_manager.serial
        for pkg in packages:
            self.device_manager.run(
                ["-s", serial, "shell", "am", "force-stop", pkg], timeout=5
            )
            out, err, code = self.device_manager.run(
                ["-s", serial, "shell", "pm", "clear", "--user", "0", pkg],
                timeout=12,
            )
            ok = code == 0 and (not out or "Success" in out)
            if not ok:
                failed.append((pkg, err or out or "pm clear"))
                continue
            succeeded.append(pkg)
            label = self._display_app_name(self.package_to_row.get(pkg), pkg)
            self.after(0, lambda m=f"✓ {label}: đã xóa bộ nhớ đệm": self.log(m))
        self.after(0, lambda f=failed, s=succeeded: self._after_bulk_action(f, "xóa bộ nhớ đệm", s))

    def search_apk_playstore(self):
        packages = self._selected_packages()
        if not packages:
            return
        webbrowser.open(
            f"https://play.google.com/store/apps/details?id={packages[0]}"
        )

    def search_apk_google(self):
        packages = self._selected_packages()
        if not packages:
            return
        pkg = packages[0]
        row = self.package_to_row.get(pkg) or {}
        name = self._display_app_name(row, pkg)
        query = f"{name} {pkg}".strip().replace(" ", "+")
        webbrowser.open(f"https://www.google.com/search?q={query}")

    def open_selected_app(self):
        """Mở app trên thiết bị qua ADB — không mở cửa sổ / trình duyệt trên PC."""
        packages = self._selected_packages()
        if not packages or not self.is_connected:
            return
        pkg = packages[0]
        serial = self.device_manager.serial

        def _launch():
            out, err, code = self.device_manager.run(
                [
                    "-s", serial, "shell", "am", "start",
                    "-a", "android.intent.action.MAIN",
                    "-c", "android.intent.category.LAUNCHER",
                    "-p", pkg,
                ],
                timeout=8,
            )
            if code == 0:
                msg = f"Đã mở app trên thiết bị: {pkg}"
            else:
                # Fallback một số máy không resolve intent launcher
                out2, err2, code2 = self.device_manager.run(
                    [
                        "-s", serial, "shell", "monkey", "-p", pkg,
                        "-c", "android.intent.category.LAUNCHER", "1",
                    ],
                    timeout=8,
                )
                if code2 == 0:
                    msg = f"Đã mở app trên thiết bị: {pkg}"
                else:
                    msg = f"Không mở được {pkg}: {(err2 or out2 or err or out or 'lỗi ADB')[:120]}"
            self.after(0, lambda m=msg: self.log(m))

        self.executor.submit(_launch)

    def copy_selected_package(self):
        packages = self._selected_packages()
        if not packages:
            return
        self.clipboard_clear()
        self.clipboard_append(packages[0])
        self.log(f"Đã copy package: {packages[0]}")

    def mute_notifications_selected(self):
        packages = self._selected_packages()
        if not packages or not self.is_connected:
            return
        pkg0 = packages[0]
        name = self._display_app_name(self.package_to_row.get(pkg0), pkg0)
        extra = f"\nVà {len(packages) - 1} app khác." if len(packages) > 1 else ""
        if not ask_confirm(
            self,
            "Tắt thông báo",
            f'Tắt thông báo cho "{name}"?{extra}',
            confirm_text="Tắt",
            cancel_text="Hủy",
        ):
            return
        self.log(f"› Đang tắt thông báo ({len(packages)} app)…")
        self.executor.submit(self._mute_notifications_worker, list(packages))

    def _mute_notifications_worker(self, packages: list[str]):
        succeeded: list[str] = []
        failed: list[str] = []
        for pkg in packages:
            ok, _ = self.device_manager.disable_notifications(pkg)
            row = self.package_to_row.get(pkg)
            if row is not None:
                row["notify_blocked"] = self.device_manager.are_notifications_blocked(pkg)
            if ok:
                succeeded.append(pkg)
            else:
                failed.append(pkg)
        self.after(0, lambda s=succeeded, f=failed: self._after_notification_bulk(s, f, "tắt"))

    def unmute_notifications_selected(self):
        packages = self._selected_packages()
        if not packages or not self.is_connected:
            return
        pkg0 = packages[0]
        name = self._display_app_name(self.package_to_row.get(pkg0), pkg0)
        extra = f"\nVà {len(packages) - 1} app khác." if len(packages) > 1 else ""
        if not ask_confirm(
            self,
            "Bật thông báo",
            f'Bật lại thông báo cho "{name}"?{extra}',
            confirm_text="Bật",
            cancel_text="Hủy",
        ):
            return
        self.log(f"› Đang bật thông báo ({len(packages)} app)…")
        self.executor.submit(self._unmute_notifications_worker, list(packages))

    def _unmute_notifications_worker(self, packages: list[str]):
        succeeded: list[str] = []
        failed: list[str] = []
        for pkg in packages:
            ok, _ = self.device_manager.enable_notifications(pkg)
            row = self.package_to_row.get(pkg)
            if row is not None:
                row["notify_blocked"] = self.device_manager.are_notifications_blocked(pkg)
            if ok:
                succeeded.append(pkg)
            else:
                failed.append(pkg)
        self.after(0, lambda s=succeeded, f=failed: self._after_notification_bulk(s, f, "bật"))

    def _after_notification_bulk(
        self,
        succeeded: list[str],
        failed: list[str],
        action_label: str,
    ) -> None:
        if succeeded:
            show_notice(
                self,
                "Thông báo",
                f"Đã {action_label} thông báo cho {len(succeeded)} ứng dụng.",
                kind="success",
            )
        if failed:
            self.log(f"! Không {action_label} được {len(failed)} app (một số app hệ thống/OEM không hỗ trợ qua ADB).")

    def block_network_selected(self):
        packages = self._selected_packages()
        if not packages:
            return
        for pkg in packages:
            self.device_manager.block_network(pkg)
        self.log(f"Đã chặn mạng (best-effort) cho {len(packages)} app.")

    def backup_selected_apk(self):
        packages = self._selected_packages()
        if not packages:
            return
        folder = filedialog.askdirectory(title="Chọn thư mục lưu APK")
        if not folder:
            return
        ok = 0
        for pkg in packages:
            if self.device_manager.backup_apk(pkg, folder):
                ok += 1
        self.log(f"Đã sao lưu {ok}/{len(packages)} APK.")

    def export_list(self):
        if not self.all_rows:
            return
        path = filedialog.asksaveasfilename(
            title="Xuất danh sách ứng dụng",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Text", "*.txt")]
        )
        if not path:
            return
        try:
            if path.lower().endswith(".txt"):
                with open(path, "w", encoding="utf-8") as f:
                    for row in self.filtered_rows:
                        f.write(
                            f"{row['name']} | {row['package']} | {self._app_state_label(row)}"
                            f" | {row.get('risk_text', '')} | {row.get('tags_text', '')} | {row['kind']}\n"
                        )
            else:
                with open(path, "w", encoding="utf-8-sig", newline="") as f:
                    w = csv.writer(f)
                    w.writerow(["Tên app", "Package", "Status", "Risk", "Tags", "User/System"])
                    for row in self.filtered_rows:
                        w.writerow([
                            row["name"],
                            row["package"],
                            self._app_state_label(row),
                            row.get("risk_text", ""),
                            row.get("tags_text", ""),
                            row["kind"],
                        ])
            self.log(f"Đã xuất danh sách: {path}")
        except Exception as exc:
            logging.exception("Export fail")
            show_notice(self, "Không xuất được file", str(exc), kind="error")

    def _open_context_menu(self, event):
        row_id = self.table.identify_row(event.y)
        if row_id:
            self.table.selection_set(row_id)
        PremiumMenu.popup(self, event.x_root, event.y_root, self._context_menu_items(), min_width=272)

    def _update_empty_state(self):
        has_rows = bool(self.filtered_rows)
        connected = self.is_connected or self.device_manager.device_connected
        if connected and not self.is_connected:
            self.is_connected = True

        if has_rows:
            self.empty_state.grid_remove()
            self.table_outer.grid(row=2, column=0, sticky="nsew")
            return

        self.table_outer.grid_remove()
        self.empty_state.grid(row=2, column=0, sticky="nsew")

        title_lbl = getattr(self.empty_state, "empty_title", None)
        desc_lbl = getattr(self.empty_state, "empty_desc", None)
        action_btn = getattr(self.empty_state, "empty_action", None)

        if self._loading_packages:
            title, desc = "Đang tải ứng dụng…", "Đang đọc danh sách từ thiết bị qua ADB."
        elif not connected:
            title, desc = (
                "Chưa kết nối thiết bị",
                "Cắm cáp USB và bật USB Debugging để tải danh sách ứng dụng.",
            )
        elif self._load_error:
            title, desc = (
                "Không tải được danh sách",
                f"{self._load_error}\nThử rút cắm USB hoặc bấm Làm mới.",
            )
        else:
            title, desc = (
                "Không có ứng dụng để hiển thị",
                "Không tìm thấy app cài thêm (bên thứ ba). Bấm Làm mới để quét lại.",
            )

        if title_lbl:
            title_lbl.configure(text=title)
        if desc_lbl:
            desc_lbl.configure(text=desc)
        if action_btn:
            action_btn.configure(
                text="Làm mới" if connected else "Kết nối lại",
                command=self.load_packages_async if connected else self._reconnect_device,
            )

    def _reconnect_device(self):
        ok, reason = self.device_manager.refresh()
        if ok:
            self.set_connected(True)
            self.load_packages_async()
        else:
            show_notice(self, "Kết nối thiết bị", reason, kind="warning")

    def _sort_by(self, col, descending):
        data = [(self.table.set(child, col), child) for child in self.table.get_children("")]
        data.sort(reverse=descending, key=lambda x: x[0])
        for index, (_, child) in enumerate(data):
            self.table.move(child, "", index)
        self._sort_desc[col] = descending


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("HBG AdBlocker")
        self._win_w, self._win_h = 1320, 840
        self.geometry(f"{self._win_w}x{self._win_h}")
        self.minsize(1100, 700)
        self._connected_at = None
        self._last_scan_at = None
        self.configure(fg_color=C["bg_app"])
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        apply_window_icon(self)
        self._brand_logo = load_brand_ctk_image(36)

        self.app_executor = ThreadPoolExecutor(max_workers=4)
        self.device_manager = DeviceManager()
        self.app_manager_tab = None
        self._nav_buttons = {}
        self._active_nav = "dashboard"

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_shell()
        self._ensure_app_manager_tab()
        self._show_view("dashboard")
        bind_minimize_cascade(self)
        self.after(20, lambda: center_on_screen(self, self._win_w, self._win_h))
        self.start_device_check()

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=LAYOUT["sidebar_width"],
            corner_radius=0,
            fg_color=C["bg_sidebar"],
            border_width=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_propagate(False)

        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=SPACE["4"], pady=(SPACE["6"], SPACE["5"]))
        mark = ctk.CTkFrame(brand, width=40, height=40, corner_radius=20, fg_color=C["accent"])
        mark.pack(side="left")
        mark.pack_propagate(False)
        if getattr(self, "_brand_logo", None) is not None:
            ctk.CTkLabel(mark, text="", image=self._brand_logo).place(
                relx=0.5, rely=0.5, anchor="center"
            )
        else:
            ctk.CTkLabel(mark, text="🛡", font=("Segoe UI", 18), text_color=C["text_primary"]).place(
                relx=0.5, rely=0.5, anchor="center"
            )
        titles = ctk.CTkFrame(brand, fg_color="transparent")
        titles.pack(side="left", padx=(SPACE["3"], 0))
        UI.label(titles, "HBG AdBlocker", variant="title").pack(anchor="w")
        UI.muted(titles, "Xóa quảng cáo · Dọn rác").pack(anchor="w", pady=(SPACE["1"], 0))

        UI.section_label(self.sidebar, "Menu", anchor="w").pack(
            fill="x", padx=SPACE["4"], pady=(SPACE["2"], SPACE["2"])
        )
        nav = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav.pack(fill="x", padx=SPACE["3"])
        self._nav_buttons["dashboard"] = UI.nav_item(
            nav, "Dashboard", "⌂", lambda: self._show_view("dashboard"), active=True
        )
        self._nav_buttons["dashboard"].pack(fill="x", pady=(0, SPACE["2"]))
        self._nav_buttons["apps"] = UI.nav_item(
            nav, "Ứng dụng", "☰", lambda: self._show_view("apps"), active=False
        )
        self._nav_buttons["apps"].pack(fill="x", pady=(0, SPACE["2"]))

        UI.muted(self.sidebar, APP_VERSION_LABEL, anchor="w").pack(
            side="bottom", fill="x", padx=SPACE["4"], pady=(SPACE["4"], SPACE["2"]),
        )

    def _set_active_nav(self, key: str):
        self._active_nav = key
        for nav_key, btn in self._nav_buttons.items():
            active = nav_key == key
            btn.configure(
                fg_color=C["accent"] if active else "transparent",
                hover_color=C["accent_hover"] if active else C["bg_card_hover"],
                text_color=C["text_primary"] if active else C["text_secondary"],
            )

    def _show_view(self, view: str):
        self._set_active_nav(view)
        self.dashboard_view.pack_forget()
        self.apps_view.pack_forget()
        if view == "dashboard":
            self.page_title.configure(text="Dashboard")
            self.page_breadcrumb.configure(text="Tổng quan bảo vệ thiết bị")
            self.dashboard_view.pack(fill="both", expand=True)
        else:
            self.page_title.configure(text="Ứng dụng")
            self.page_breadcrumb.configure(text="Quản lý & phân tích package")
            self._ensure_app_manager_tab()
            self.apps_view.pack(fill="both", expand=True)

    def _build_main_shell(self):
        shell = ctk.CTkFrame(self, fg_color="transparent")
        shell.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(LAYOUT["content_pad_x"], LAYOUT["content_pad_right"]),
            pady=(LAYOUT["content_pad_y"], SPACE["4"]),
        )
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(1, weight=1)

        topbar = ctk.CTkFrame(shell, fg_color="transparent")
        topbar.grid(row=0, column=0, sticky="ew", pady=(0, SPACE["3"]))
        topbar.grid_columnconfigure(0, weight=1)

        header_block = ctk.CTkFrame(topbar, fg_color="transparent")
        header_block.grid(row=0, column=0, sticky="w")
        self.page_title = UI.label(header_block, "Dashboard", variant="page")
        self.page_title.pack(anchor="w")
        self.page_breadcrumb = UI.subtitle(header_block, "Tổng quan bảo vệ thiết bị", anchor="w")
        self.page_breadcrumb.pack(anchor="w", pady=(SPACE["1"], 0))

        actions = ctk.CTkFrame(topbar, fg_color="transparent")
        actions.grid(row=0, column=1, sticky="e", padx=(SPACE["3"], 0))

        self.scan_button = UI.btn(
            actions, "⚡ Quét nhanh", self.quick_scan, variant="success", width=118, height=LAYOUT["toolbar_h"]
        )
        self.scan_button.pack(side="left", padx=(0, SPACE["2"]))
        self.refresh_button = UI.toolbar_reload_btn(
            actions, self.reload_adb, width=40, height=LAYOUT["toolbar_h"],
        )
        self.refresh_button.pack(side="left", padx=(0, SPACE["1"]))
        UI.toolbar_youtube_btn(
            actions,
            lambda: webbrowser.open("https://www.youtube.com/@habg68"),
            width=40,
            height=LAYOUT["toolbar_h"],
        ).pack(side="left", padx=(0, SPACE["1"]))
        UI.btn(
            actions, "ℹ", self.open_about, variant="ghost", width=40, height=LAYOUT["toolbar_h"],
        ).pack(side="left")

        self.content_stack = ctk.CTkFrame(shell, fg_color="transparent")
        self.content_stack.grid(row=1, column=0, sticky="nsew")

        self.dashboard_view = ctk.CTkFrame(self.content_stack, fg_color="transparent")
        self.apps_view = ctk.CTkFrame(self.content_stack, fg_color="transparent")
        self.app_manager_tab_container = self.apps_view
        self._build_dashboard(self.dashboard_view)

    def _build_dashboard(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)
        block_pad = SPACE["4"]

        stats_card = UI.card(parent, padding=block_pad)
        stats_card.grid(row=0, column=0, sticky="ew", pady=(0, block_pad))
        stats_inner = UI.card_inner(stats_card)
        stats_row = ctk.CTkFrame(stats_inner, fg_color="transparent")
        stats_row.pack(fill="x")
        for col in range(5):
            stats_row.grid_columnconfigure(col, weight=1)
        self._stat_device = UI.metric_cell(stats_row, "📱", "Thiết bị", "—", "Chưa kết nối")
        self._stat_device.grid(row=0, column=0, sticky="w", padx=(0, SPACE["2"]))
        self._stat_adb = UI.metric_cell(stats_row, "✓", "ADB", "—", "")
        self._stat_adb.grid(row=0, column=1, sticky="w", padx=(0, SPACE["2"]))
        self._stat_android = UI.metric_cell(stats_row, "🤖", "Phiên bản OS", "—", "")
        self._stat_android.grid(row=0, column=2, sticky="w", padx=(0, SPACE["2"]))
        self._stat_uptime = UI.metric_cell(stats_row, "⏱", "Uptime", "—", "")
        self._stat_uptime.grid(row=0, column=3, sticky="w", padx=(0, SPACE["2"]))
        self._stat_scan = UI.metric_cell(stats_row, "🔍", "Lần quét cuối", "—", "")
        self._stat_scan.grid(row=0, column=4, sticky="w")

        mid = ctk.CTkFrame(parent, fg_color="transparent")
        mid.grid(row=1, column=0, sticky="nsew")
        mid.grid_columnconfigure(0, weight=0, minsize=LAYOUT["control_col"])
        mid.grid_columnconfigure(1, weight=1)
        mid.grid_rowconfigure(0, weight=1)

        ctrl_card = UI.card(mid, padding=block_pad)
        ctrl_card.grid(row=0, column=0, sticky="nsew", padx=(0, SPACE["3"]))
        ctrl = UI.card_inner(ctrl_card)
        UI.label(ctrl, "Điều khiển", variant="heading").pack(anchor="w", pady=(0, SPACE["3"]))
        self._control_panel = ControlPanelGroup(ctrl)
        specs = [
            ("Bật giám sát", self.toggle_monitor, "🛡", 0),
            ("Cài AdGuard DNS", self.set_adguard_dns, "🌐", 1),
            ("Xóa ứng dụng rác", self.remove_junk_apps, "🗑", 2),
            ("Tìm QC đang chạy", self.find_running_junk, "🔎", 3),
            ("Xóa QC đang chạy", self.add_current_to_blacklist, "🗑", 4),
            ("Xóa Launcher", self.remove_launcher, "🏠", 5),
            ("Xóa Bloatware", self.remove_bloatware, "📦", 6),
            ("Cài APK", self.install_apk_pick, "📲", 7),
            ("Ép Bật VoLTE (VN)", self.enable_volte_direct, "⚡", 8),
        ]
        for text, cmd, icon, idx in specs:
            btn = self._control_panel.add(text, cmd, icon=icon)
            setattr(self, f"button_{idx}", btn)
        self._control_panel.set_enabled(False)

        log_card = UI.card(mid, padding=block_pad)
        log_card.grid(row=0, column=1, sticky="nsew")
        log_inner = UI.card_inner(log_card)
        log_header = ctk.CTkFrame(log_inner, fg_color="transparent")
        log_header.pack(fill="x", pady=(0, SPACE["3"]))
        log_titles = ctk.CTkFrame(log_header, fg_color="transparent")
        log_titles.pack(side="left")
        UI.label(log_titles, "Nhật ký chi tiết", variant="heading").pack(anchor="w")
        UI.muted(
            log_titles,
            "Tiến trình từng thao tác hiển thị tại nút bên trái",
        ).pack(anchor="w")
        self.clear_log_button = UI.btn(
            log_header, "🗑 Xóa", self.clear_log, variant="ghost", width=80, height=36
        )
        self.clear_log_button.pack(side="right")
        self.log_terminal = LogTerminal(log_inner)
        self.log_terminal.pack(fill="both", expand=True)
        self.log_area = self.log_terminal.widget

        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", pady=(SPACE["4"], 0))
        UI.subtitle(
            footer,
            FOOTER_TAGLINE,
            anchor="center",
            justify="center",
        ).pack()

    def start_device_check(self):
        Thread(target=self._device_check_thread, daemon=True).start()
        self._refresh_status_ui()
        self.after(1500, self._refresh_status_ui_loop)

    def _device_check_thread(self):
        global device_id, device_name
        last_device_id = None
        
        while is_running:
            try:
                connected, reason = self.device_manager.refresh()
                if connected:
                    if last_device_id != self.device_manager.serial:
                        device_id = self.device_manager.serial
                        device_name = self.device_manager.device_model
                        last_device_id = device_id
                        self.after(0, lambda: self.update_ui_on_connect(device_name))
                else:
                    if last_device_id:
                        self.after(0, self.update_ui_on_disconnect)
                        self.after(0, lambda: self.log_message(reason))
                        last_device_id = None
                        device_id = None
                        device_name = "Chưa kết nối"
                time.sleep(1.2 if connected else 3.0)
                
            except Exception as e:
                logging.error(f"Lỗi kiểm tra thiết bị: {str(e)}")
                time.sleep(3)

    def update_ui_on_connect(self, device_name):
        self._connected_at = time.time()
        self.log_message(f"Đã kết nối: {device_name}")
        self.update_device_name(device_name)
        self.toggle_buttons(True)
        self._refresh_status_ui()
        self._app_manager_refresh_on_connect()

    def _app_manager_refresh_on_connect(self):
        """Đồng bộ tab Quản lý ứng dụng khi ADB đã có serial (kết nối sau khi mở app hoặc đổi máy)."""
        if not self.app_manager_tab:
            return
        ok = self.device_manager.device_connected
        self.app_manager_tab.set_connected(ok)
        self.app_manager_tab.update_device_info()
        if ok:
            self.app_manager_tab.load_packages_async()

    def update_ui_on_disconnect(self):
        self.log_message("Đã ngắt kết nối thiết bị")
        self._connected_at = None
        self.update_device_name("Chưa kết nối")
        self.toggle_buttons(False)
        if monitoring:
            self.stop_monitor()
        self._refresh_status_ui()
        if self.app_manager_tab:
            self.app_manager_tab.set_connected(False)
            self.app_manager_tab.update_device_info()

    def _format_uptime(self) -> str:
        if not self._connected_at:
            return "—"
        sec = int(time.time() - self._connected_at)
        h, rem = divmod(sec, 3600)
        m, s = divmod(rem, 60)
        if h:
            return f"{h}h {m}m {s}s"
        if m:
            return f"{m}m {s}s"
        return f"{s}s"

    def _refresh_status_ui(self, force_check: bool = False) -> None:
        dm = self.device_manager
        online = bool(device_id and is_adb_connected(device_id, force_check=force_check)) or dm.device_connected
        model = dm.device_model if online else "—"
        android = dm.android_version if online else "—"

        if hasattr(self, "_stat_device"):
            if online:
                self._stat_device.set_metric(model or device_name or "Thiết bị", "Đã kết nối", sub_tone="success")
                self._stat_adb.set_metric("Hoạt động", "Trạng thái ADB", sub_tone="success")
                self._stat_android.set_metric(f"Android {android}", "Phiên bản OS")
            else:
                self._stat_device.set_metric("—", "Thiết bị", sub_tone="muted")
                self._stat_adb.set_metric("Chờ", "Trạng thái ADB", sub_tone="muted")
                self._stat_android.set_metric("—", "Phiên bản OS")
            self._stat_uptime.set_metric(self._format_uptime(), "Uptime")
            scan_txt = self._last_scan_at.strftime("%H:%M:%S") if self._last_scan_at else "—"
            self._stat_scan.set_metric(scan_txt, "Lần quét cuối")

        if self.app_manager_tab and hasattr(self.app_manager_tab, "refresh_summary_card"):
            self.app_manager_tab.refresh_summary_card()

    def _refresh_status_ui_loop(self) -> None:
        if not is_running:
            return
        self._refresh_status_ui()
        self.after(1500, self._refresh_status_ui_loop)

    def _disable_markets_thread(self):
        try:
            installed_packages = get_installed_packages(device_id)
            for package, friendly_name in APP_MARKETS.items():
                if package in installed_packages:
                    result = disable_app(device_id, package)
                    if not result:  # Thành công
                        self.log_message(f"Đã vô hiệu hóa {friendly_name}")
        finally:
            self.after(0, lambda: (
                self.button_5.configure(text="  ▦  Tắt CH Play & App Market", state="normal"),
                self._control_panel.refresh_style(self.button_5),
            ))

    def log_message(self, message):
        """Hiển thị thông báo trong log terminal."""
        line = prepare_log_line(message)
        if line is None:
            return
        if hasattr(self, "log_terminal"):
            self.log_terminal.append(line)
        else:
            logging.info(line)

    def _action_task(
        self,
        btn: ctk.CTkButton,
        phase: str,
        *,
        progress: float | None = None,
        detail: str = "",
        autoclear: bool = True,
    ) -> None:
        if hasattr(self, "_control_panel"):
            self._control_panel.set_task(
                btn, phase, progress=progress, detail=detail, autoclear=autoclear,
            )

    def _action_running(self, btn: ctk.CTkButton, detail: str = "", progress: float | None = None) -> None:
        self._action_task(btn, "running", detail=detail, progress=progress, autoclear=False)

    def _action_done(self, btn: ctk.CTkButton, ok: bool, detail: str = "") -> None:
        self._action_task(btn, "success" if ok else "error", detail=detail, autoclear=True)

    def toggle_buttons(self, enabled):
        self._control_panel.set_enabled(enabled)

    def set_adguard_dns(self):
        if not device_id or not is_adb_connected(device_id):
            self.log_message("Chưa kết nối thiết bị!")
            self._action_done(self.button_1, False, "Chưa kết nối thiết bị")
            return
        self._action_running(self.button_1, "Đang đặt AdGuard DNS…")
        self.log_message("Đang thiết lập AdGuard DNS...")
        try:
            run_adb_command(["-s", device_id, "shell", "settings", "put", "global", "private_dns_mode", "hostname"], timeout=5)
            run_adb_command(["-s", device_id, "shell", "settings", "put", "global", "private_dns_specifier", "dns.adguard.com"], timeout=5)
            self.log_message("Đã đặt DNS: dns.adguard.com")
            self._action_done(self.button_1, True, "DNS: dns.adguard.com")
        except Exception as exc:
            self.log_message(f"Lỗi DNS: {exc}")
            self._action_done(self.button_1, False, "Không đặt được DNS")

    def enable_volte_direct(self):
        if not device_id or not is_adb_connected(device_id):
            self.log_message("Chưa kết nối thiết bị!")
            self._action_done(self.button_8, False, "Chưa kết nối thiết bị")
            return
        self._action_running(self.button_8, "Đang ép bật VoLTE…", progress=0.1)
        self.log_message("⚡ Đang thực hiện ép bật VoLTE (Viettel/Vina/Mobi) qua ADB...")
        self.app_executor.submit(self._enable_volte_thread)

    def _enable_volte_thread(self):
        try:
            self.after(0, lambda: self.log_message("› [1/4] Ép cờ System Properties (Qualcomm/MTK)..."))
            props = [
                ("persist.dbg.volte_avail_ovr", "1"),
                ("persist.dbg.vt_avail_ovr", "1"),
                ("persist.dbg.wfc_avail_ovr", "1"),
                ("persist.vendor.radio.volte_mismatch_op", "0"),
                ("persist.radio.volte_enabled_by_default", "1"),
                ("persist.sys.cust.lte_config", "true"),
            ]
            for prop, val in props:
                run_adb_command(["-s", device_id, "shell", "setprop", prop, val], timeout=3)

            self.after(0, lambda: self.log_message("› [2/4] Đưa cấu hình vào Settings Global (VoLTE/VoWiFi)..."))
            settings = [
                ("volte_vt_enabled", "1"),
                ("voice_over_lte_enabled", "1"),
                ("vt_ims_enabled", "1"),
                ("wfc_ims_enabled", "1"),
            ]
            for name, val in settings:
                run_adb_command(["-s", device_id, "shell", "settings", "put", "global", name, val], timeout=3)

            self.after(0, lambda: self.log_message("› [3/4] Override CarrierConfig (Android 11+)..."))
            configs = [
                ("carrier_volte_available_bool", "true"),
                ("carrier_volte_provisioned_bool", "true"),
                ("hide_enhanced_4g_lte_bool", "false"),
                ("editable_enhanced_4g_lte_bool", "true"),
                ("carrier_supports_ss_over_ut_bool", "true"),
                ("show_4g_for_lte_data_icon_bool", "true"),
            ]
            for k, v in configs:
                run_adb_command(["-s", device_id, "shell", "cmd", "phone", "carrier_config", "set", k, v], timeout=3)

            self.after(0, lambda: self.log_message("› [4/4] Khởi động lại dịch vụ mạng (Refresh SIM)..."))
            run_adb_command(["-s", device_id, "shell", "settings", "put", "global", "airplane_mode_on", "1"], timeout=3)
            run_adb_command(["-s", device_id, "shell", "am", "broadcast", "-a", "android.intent.action.AIRPLANE_MODE", "--ez", "state", "true"], timeout=3)
            time.sleep(1.5)
            run_adb_command(["-s", device_id, "shell", "settings", "put", "global", "airplane_mode_on", "0"], timeout=3)
            run_adb_command(["-s", device_id, "shell", "am", "broadcast", "-a", "android.intent.action.AIRPLANE_MODE", "--ez", "state", "false"], timeout=3)

            self.after(0, lambda: self._after_enable_volte_ui(True, "Thành công"))
        except Exception as exc:
            self.after(0, lambda e=str(exc): self._after_enable_volte_ui(False, e))

    def _after_enable_volte_ui(self, ok: bool, msg: str):
        if ok:
            self.log_message("✓ Đã gửi toàn bộ chuỗi lệnh kích hoạt VoLTE thành công!")
            self.log_message("› Vui lòng kiểm tra thanh trạng thái xem biểu tượng VoLTE/HD đã xuất hiện chưa.")
            self._action_done(self.button_8, True, "Bật VoLTE thành công")
        else:
            self.log_message(f"✗ Lỗi khi kích hoạt VoLTE: {msg}")
            self._action_done(self.button_8, False, "Lỗi bật VoLTE")

    def install_apk_pick(self):
        if not device_id or not is_adb_connected(device_id):
            self.log_message("Chưa kết nối thiết bị!")
            self._action_done(self.button_7, False, "Chưa kết nối thiết bị")
            return
        apk_path = filedialog.askopenfilename(
            parent=self,
            title="Chọn file APK để cài lên thiết bị",
            filetypes=[
                ("Android APK", "*.apk"),
                ("Tất cả các file", "*.*"),
            ],
        )
        if not apk_path:
            self._action_done(self.button_7, True, "Đã hủy")
            return
        if not apk_path.lower().endswith(".apk"):
            self.log_message("File không phải .apk — vẫn thử cài qua ADB.")
        apk_name = os.path.basename(apk_path)
        self.log_message(f"› Đang cài {apk_name}…")
        self._action_running(self.button_7, f"Đang cài {apk_name}…", progress=0.15)
        self.app_executor.submit(self._install_apk_thread, apk_path)

    def _install_apk_thread(self, apk_path: str) -> None:
        apk_name = os.path.basename(apk_path)
        try:
            out, err, code = self.device_manager.install(apk_path)
            blob = f"{out}\n{err}".strip()
            ok = code == 0 and "failure" not in blob.lower() and (
                "success" in blob.lower() or not blob
            )
            detail = (blob or err or out or "Không có phản hồi từ ADB")[:200]
        except Exception as exc:
            ok = False
            detail = str(exc)
        self.after(0, lambda o=ok, n=apk_name, d=detail: self._after_install_apk_ui(o, n, d))

    def _after_install_apk_ui(self, ok: bool, apk_name: str, detail: str) -> None:
        if ok:
            self.log_message(f"✓ Đã cài {apk_name}")
            self._action_done(self.button_7, True, f"Đã cài {apk_name}")
            show_notice(
                self,
                "Cài APK",
                f"Đã cài thành công:\n{apk_name}",
                kind="success",
            )
            if self.app_manager_tab and self.app_manager_tab.is_connected:
                self.app_manager_tab.load_packages_async()
        else:
            self.log_message(f"✕ Không cài được {apk_name}: {detail}")
            self._action_done(self.button_7, False, "Cài thất bại")
            show_notice(
                self,
                "Cài APK",
                f"Không cài được {apk_name}.",
                kind="warning",
                detail=detail,
            )

    def remove_junk_apps(self):
        if not device_id or not is_adb_connected(device_id):
            self.log_message("Chưa kết nối thiết bị!")
            self._action_done(self.button_2, False, "Chưa kết nối thiết bị")
            return

        self._action_running(self.button_2, "Đang quét ứng dụng rác…")
        self.log_message("Đang quét ứng dụng rác...")
        self.app_executor.submit(self._scan_then_confirm_remove)

    def _scan_then_confirm_remove(self):
        """Quét trước, hiển thị danh sách và xác nhận trước khi xóa (tránh xóa nhầm)"""
        try:
            packages = get_installed_packages(device_id)
            junk_packages = [
                pkg for pkg in packages
                if is_ad_related_package(pkg)
                and not is_protected_package(pkg)  # Bỏ qua: system, chat, ngân hàng, app phổ biến (TikTok, Shopee...)
            ]
            # Chuyển sang main thread để hiển thị dialog (Tkinter yêu cầu)
            self.after(0, lambda j=junk_packages: self._confirm_and_remove_junk(j))
        except Exception as e:
            self.after(0, lambda err=str(e): self._on_junk_scan_failed(err))

    def _on_junk_scan_failed(self, err: str) -> None:
        self.log_message(f"Lỗi quét: {err}")
        self._action_done(self.button_2, False, "Lỗi khi quét")

    def _junk_display_label(self, package: str) -> str:
        if self.app_manager_tab:
            row = self.app_manager_tab.package_to_row.get(package)
            if row:
                name = AppManagerTab._display_app_name(row, package)
                if name and name != package:
                    return name
        return self.device_manager.get_app_label(package)

    def _confirm_and_remove_junk(self, junk_packages):
        """Hiển thị danh sách chọn app và thực hiện gỡ (main thread)."""
        if not junk_packages:
            self.log_message("Không tìm thấy ứng dụng rác.")
            self._action_done(self.button_2, True, "Không có app rác")
            return
        self._action_task(self.button_2, "idle")
        selected = ask_junk_removal_pick(
            self,
            junk_packages,
            device_manager=self.device_manager,
            label_for=self._junk_display_label,
            hint_for=self._apk_hint_for,
        )
        if selected is None:
            self._action_done(self.button_2, True, "Đã hủy")
            return
        if not selected:
            self.log_message("Không có app nào được chọn để gỡ.")
            self._action_done(self.button_2, True, "Không chọn app nào")
            return
        self._action_running(self.button_2, f"Đang gỡ {len(selected)} app…", progress=0.05)
        self.log_message(f"Đang gỡ {len(selected)} ứng dụng đã chọn...")
        self.app_executor.submit(self._remove_junk_apps_thread, selected)

    def _junk_removal_success_message(self, packages: list[str]) -> str:
        labels = [self._junk_display_label(p) for p in packages]
        n = len(labels)
        if n == 0:
            return "Không có ứng dụng nào được gỡ."
        if n == 1:
            return f'Đã gỡ thành công "{labels[0]}".'
        shown = ", ".join(labels[:3])
        extra = f" và {n - 3} app khác" if n > 3 else ""
        return f"Đã gỡ thành công {n} ứng dụng ({shown}{extra})."

    def _remove_junk_apps_thread(self, junk_packages):
        succeeded: list[str] = []
        total = max(len(junk_packages), 1)
        try:
            new_packages = []
            for idx, pkg in enumerate(junk_packages):
                frac = (idx + 1) / total
                self.after(
                    0,
                    lambda f=frac, i=idx + 1, t=total: self._action_running(
                        self.button_2, f"Đang gỡ {i}/{t}…", progress=f * 0.95,
                    ),
                )
                try:
                    if is_protected_package(pkg):
                        self.log_message(f"Bỏ qua app được bảo vệ: {pkg}")
                        continue
                    result = uninstall_package(device_id, pkg)
                    if result is not None:
                        succeeded.append(pkg)
                        self.log_message(f"Đã gỡ: {pkg}")
                        if pkg not in BLACKLIST:
                            BLACKLIST.append(pkg)
                            new_packages.append(pkg)
                            self.log_message(f"Đã thêm {pkg} vào blacklist")
                except Exception as e:
                    self.log_message(f"Lỗi gỡ {pkg}: {str(e)}")

            if new_packages:
                replace_blacklist(BLACKLIST)
                self.update_config()
                self.log_message(f"Đã cập nhật blacklist với {len(new_packages)} package mới")

            if succeeded:
                self.log_message(f"Đã gỡ {len(succeeded)} ứng dụng rác")
            else:
                self.log_message("Không có ứng dụng nào được gỡ")
        finally:
            ok = list(succeeded)
            self.after(0, lambda s=ok: self._after_junk_removal_ui(s))

    def _after_junk_removal_ui(self, succeeded_packages: list[str] | None = None):
        pkgs = succeeded_packages or []
        if pkgs:
            short = self._junk_removal_success_message(pkgs)
            if len(short) > 56:
                short = f"Đã gỡ {len(pkgs)} app thành công"
            self._action_done(self.button_2, True, short)
            show_notice(
                self,
                "Gỡ thành công",
                self._junk_removal_success_message(pkgs),
                kind="success",
            )
        elif succeeded_packages is not None and len(succeeded_packages) == 0:
            self._action_done(self.button_2, False, "Không gỡ được app nào")
            show_notice(
                self,
                "Gỡ ứng dụng",
                "Không gỡ được ứng dụng nào. Xem nhật ký để biết chi tiết.",
                kind="warning",
            )
        else:
            self._action_task(self.button_2, "idle")

    def remove_bloatware(self):
        if not device_id or not is_adb_connected(device_id):
            self.log_message("Chưa kết nối thiết bị!")
            self._action_done(self.button_6, False, "Chưa kết nối thiết bị")
            return
        self._action_running(self.button_6, "Đang quét bloatware…")
        self.log_message("Đang quét app bloatware…")
        self.app_executor.submit(self._scan_bloatware_thread)

    def _scan_bloatware_thread(self):
        try:
            installed = get_installed_packages(device_id)
            found = find_installed_bloatware(installed)
            # Lọc bỏ package hệ thống được bảo vệ (vd: com.miui.*, com.xiaomi.*)
            found = [p for p in found if not is_protected_package(p)]
            self.after(0, lambda f=found: self._confirm_and_remove_bloatware(f))
        except Exception as e:
            self.after(0, lambda err=str(e): self._on_bloatware_scan_failed(err))

    def _on_bloatware_scan_failed(self, err: str) -> None:
        self.log_message(f"Lỗi quét bloatware: {err}")
        self._action_done(self.button_6, False, "Lỗi khi quét")

    def _bloatware_display_label(self, package: str) -> str:
        preset = bloatware_label_for(package)
        if self.app_manager_tab:
            row = self.app_manager_tab.package_to_row.get(package)
            if row:
                name = AppManagerTab._display_app_name(row, package)
                if name and name != package:
                    return name
        friendly = self.device_manager.get_app_label(package)
        if friendly and friendly != package:
            return friendly
        return preset

    def _confirm_and_remove_bloatware(self, packages: list[str]) -> None:
        if not packages:
            self.log_message("Không có app bloatware (Oppo Market, Zing MP3, Netflix, Lazada…) trên máy.")
            self._action_done(self.button_6, True, "Không có bloatware")
            return
        self._action_task(self.button_6, "idle")
        lines = "\n".join(f"• {self._bloatware_display_label(pkg)}" for pkg in packages)
        if not ask_confirm(
            self,
            "Xóa Bloatware",
            f"Gỡ {len(packages)} ứng dụng sau?\n\n{lines}",
            confirm_text="Gỡ",
            cancel_text="Hủy",
            danger=True,
        ):
            self._action_done(self.button_6, True, "Đã hủy")
            return
        self._action_running(self.button_6, f"Đang gỡ {len(packages)} app…", progress=0.05)
        self.log_message(f"Đang gỡ {len(packages)} app bloatware…")
        self.app_executor.submit(self._remove_bloatware_thread, packages)

    def _remove_bloatware_thread(self, packages: list[str]) -> None:
        succeeded: list[str] = []
        total = max(len(packages), 1)
        try:
            for idx, pkg in enumerate(packages):
                frac = (idx + 1) / total
                self.after(
                    0,
                    lambda f=frac, i=idx + 1, t=total: self._action_running(
                        self.button_6, f"Đang gỡ {i}/{t}…", progress=f * 0.95,
                    ),
                )
                try:
                    if is_protected_package(pkg):
                        self.log_message(f"Bỏ qua app hệ thống được bảo vệ: {self._bloatware_display_label(pkg)}")
                        continue
                    result = uninstall_package(device_id, pkg)
                    if result is not None:
                        succeeded.append(pkg)
                        self.log_message(f"Đã gỡ bloatware: {self._bloatware_display_label(pkg)}")
                    else:
                        self.log_message(f"Không gỡ được: {self._bloatware_display_label(pkg)}")
                except Exception as e:
                    self.log_message(f"Lỗi gỡ {pkg}: {e}")
        finally:
            self.after(0, lambda s=list(succeeded): self._after_bloatware_removal_ui(s))

    def _after_bloatware_removal_ui(self, succeeded_packages: list[str]) -> None:
        if succeeded_packages:
            labels = [self._bloatware_display_label(p) for p in succeeded_packages]
            short = f"Đã gỡ {len(labels)} app"
            self._action_done(self.button_6, True, short)
            body = "\n".join(f"• {name}" for name in labels)
            show_notice(
                self,
                "Xóa Bloatware",
                f"Đã gỡ {len(labels)} ứng dụng:\n{body}",
                kind="success",
            )
            if self.app_manager_tab and self.app_manager_tab.is_connected:
                self.app_manager_tab.load_packages_async()
        else:
            self._action_done(self.button_6, False, "Không gỡ được app nào")
            show_notice(
                self,
                "Xóa Bloatware",
                "Không gỡ được ứng dụng nào. Xem nhật ký để biết chi tiết.",
                kind="warning",
            )

    def _on_app_scan_finished(self, junk_packages: list[str]) -> None:
        self.scan_button.configure(state="normal", text="⚡ Quét nhanh")
        if junk_packages:
            self.log_message(f"Quét xong: phát hiện {len(junk_packages)} app nên gỡ — dùng nút Gỡ app rác.")
        else:
            self.log_message("Quét xong — không phát hiện app rác cần gỡ.")

    def find_running_junk(self):
        global current_running_package
        if not device_id or not is_adb_connected(device_id):
            self.log_message("Chưa kết nối thiết bị!")
            self._action_done(self.button_3, False, "Chưa kết nối thiết bị")
            return

        self._action_running(self.button_3, "Đang kiểm tra app foreground…")
        self.log_message("Kiểm tra ứng dụng rác đang chạy...")
        try:
            result = run_adb_command(["-s", device_id, "shell", "dumpsys", "window"], timeout=5)
            match = re.search(r"mCurrentFocus=.* (\S+)/", result)

            if match:
                package = match.group(1)
                current_running_package = package
                self.log_message(f"Ứng dụng đang chạy: {package}")

                if is_protected_package(package):
                    self.log_message(f"Bỏ qua app được bảo vệ (hệ thống/whitelist/ngân hàng/phổ biến): {package}")
                    self._action_done(self.button_3, True, "App được bảo vệ")
                    return

                if is_ad_related_package(package) and package in get_installed_packages(device_id):
                    self.log_message(f"Phát hiện rác đang chạy: {package}")
                    self._action_done(self.button_3, True, "Phát hiện app rác")
                    self.handle_junk_package(package)
                else:
                    self.log_message(f"Không phải rác: {package}")
                    self._action_done(self.button_3, True, "Không phải app rác")
            else:
                self.log_message("Không tìm thấy ứng dụng đang chạy!")
                current_running_package = None
                self._action_done(self.button_3, True, "Không có app foreground")
        except Exception as exc:
            self.log_message(f"Lỗi kiểm tra: {exc}")
            self._action_done(self.button_3, False, "Lỗi kiểm tra")

    def toggle_monitor(self):
        global monitoring
        if monitoring:
            self.stop_monitor()
        else:
            self.start_monitor()

    def start_monitor(self):
        global monitoring, monitor_process
        if monitoring:
            self.log_message("Giám sát đã bật!")
            return
            
        if not device_id or not is_adb_connected(device_id):
            self.log_message("Chưa kết nối thiết bị!")
            return
            
        self.button_0.configure(text="  🛡  Dừng giám sát")
        self._control_panel.set_selected(self.button_0)
        self._action_running(self.button_0, "Giám sát realtime — đang lắng nghe")
        monitoring = True
        monitor_process = None
        self.log_message("Bật giám sát thời gian thực...")
        
        # Kiểm tra popup ngay khi bắt đầu giám sát
        popup_package = check_popup(device_id)
        if popup_package and popup_package in get_installed_packages(device_id):
            self.log_message(f"Popup từ: {popup_package}")
            self.handle_junk_package(popup_package)
        
        self.app_executor.submit(self._monitor)

    def _monitor(self):
        global monitoring, monitor_process
        try:
            adb_path = get_adb_path()
            run_adb_command(["-s", device_id, "shell", "logcat", "-c"], timeout=3)
            monitor_process = subprocess.Popen(
                [adb_path, "-s", device_id, "shell", "logcat", "ActivityManager:I", "*:S"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
        except Exception as e:
            self.log_message(f"Lỗi khởi động giám sát: {str(e)}")
            monitoring = False
            self.after(0, lambda: self._action_done(self.button_0, False, "Lỗi giám sát"))
            return

        while monitoring:
            try:
                line = monitor_process.stdout.readline().strip()
                if not line:
                    if monitoring:  # Only show message if monitoring is still active
                        self.log_message("Mất kết nối ADB, dừng giám sát...")
                    break
                    
                if check_ad_network_activity(line):
                    match = re.search(r"([a-zA-Z0-9._-]+)\s*[\(\[]", line)
                    if match:
                        package = match.group(1)
                        if package in get_installed_packages(device_id) and not is_protected_package(package):
                            self.log_message(f"Phát hiện quảng cáo từ: {package}")
                            self.handle_junk_package(package)
                            break
                
                # Kiểm tra popup mỗi 3 giây thay vì liên tục
                if int(time.time()) % 3 == 0:
                    popup_package = check_popup(device_id)
                    if popup_package and popup_package in get_installed_packages(device_id):
                        self.log_message(f"Popup từ: {popup_package}")
                        self.handle_junk_package(popup_package)
                
                time.sleep(0.5)
            except Exception as e:
                self.log_message(f"Lỗi giám sát: {str(e)}")
                time.sleep(1)

        if monitor_process:
            try:
                monitor_process.terminate()
                monitor_process.wait(timeout=2)
                if monitoring:  # Only show message if monitoring is still active
                    self.log_message("Đã dừng giám sát")
            except Exception as e:
                self.log_message(f"Lỗi dừng giám sát: {str(e)}")
            finally:
                monitor_process = None
        monitoring = False
        def _reset_monitor_btn():
            self.button_0.configure(text="  🛡  Bật giám sát")
            self._control_panel.clear_selection()

        self.after(0, _reset_monitor_btn)

    def stop_monitor(self):
        global monitoring, monitor_process
        if not monitoring:
            self.log_message("Giám sát chưa được bật!")
            return
        monitoring = False
        if monitor_process:
            try:
                monitor_process.terminate()
                monitor_process.wait(timeout=2)
                self.log_message("Đã dừng giám sát!")
            except Exception as e:
                self.log_message(f"Lỗi dừng giám sát: {str(e)}")
            finally:
                monitor_process = None
        self.button_0.configure(text="  🛡  Bật giám sát")
        self._control_panel.clear_selection()
        self._action_done(self.button_0, True, "Đã dừng giám sát")

    def handle_junk_package(self, package, control_btn=None):
        if is_protected_package(package):
            self.log_message(f"Không thao tác - app được bảo vệ: {package}")
            if control_btn is not None:
                self._action_done(control_btn, False, "App được bảo vệ")
            return
        if package not in BLACKLIST:
            replace_blacklist(list(BLACKLIST) + [package])
            try:
                self.update_config()
                self.log_message(f"Đã thêm {package} vào blacklist")
            except Exception as e:
                self.log_message(f"Lỗi cập nhật blacklist: {str(e)}")
        self.app_executor.submit(self._uninstall_package_thread, package, control_btn)

    def _uninstall_package_thread(self, package, control_btn=None):
        ok = True
        try:
            result = uninstall_package(device_id, package)
            self.log_message(f"Đã gỡ {package}: {result or 'thành công'}")
        except Exception as exc:
            ok = False
            self.log_message(f"Lỗi gỡ {package}: {exc}")
        if control_btn is not None:
            self.after(
                0,
                lambda b=control_btn, o=ok: self._action_done(
                    b, o, "Hoàn tất" if o else "Lỗi",
                ),
            )

    def update_config(self):
        try:
            persist_blacklist(appdata_dir)
            self.log_message(f"Đã cập nhật: {len(BLACKLIST)} gói trong blacklist")
        except Exception as e:
            self.log_message(f"Lỗi cập nhật cấu hình: {str(e)}")

    def add_current_to_blacklist(self):
        global current_running_package
        btn = self.button_4
        if not device_id or not is_adb_connected(device_id):
            self.log_message("Chưa kết nối thiết bị!")
            self._action_done(btn, False, "Chưa kết nối")
            return
        if not current_running_package:
            self.log_message("Không có ứng dụng để thêm!")
            self._action_done(btn, False, "Chưa có app QC")
            return
        if is_protected_package(current_running_package):
            self.log_message(
                f"Không thêm {current_running_package}: app được bảo vệ (TikTok, ngân hàng, v.v.)!",
            )
            self._action_done(btn, False, "App được bảo vệ")
            return
        if current_running_package not in get_installed_packages(device_id):
            self.log_message(f"{current_running_package} không tồn tại!")
            self._action_done(btn, False, "Không tồn tại")
            return
        self._action_running(btn, "Đang xóa QC…")
        self.handle_junk_package(current_running_package, btn)

    def _ensure_app_manager_tab(self):
        if self.app_manager_tab is None:
            self.app_manager_tab = AppManagerTab(
                self.app_manager_tab_container,
                self.device_manager,
                self.log_message
            )
            self.app_manager_tab.pack(fill="both", expand=True)
        if self.app_manager_tab:
            self.app_manager_tab.on_scan_finished = self._on_app_scan_finished
        self.app_manager_tab.set_connected(self.device_manager.device_connected)
        self.app_manager_tab.update_device_info()
        if self.device_manager.device_connected:
            self.app_manager_tab.load_packages_async()

    def remove_launcher(self):
        """Liệt kê launcher HOME, cho phép chọn và gỡ (chuyển về launcher hệ thống nếu cần)."""
        if not device_id or not is_adb_connected(device_id):
            self.log_message("Chưa kết nối thiết bị!")
            self._action_done(self.button_5, False, "Chưa kết nối")
            return
        self._action_running(self.button_5, "Đang quét launcher…")
        self.log_message("Đang liệt kê launcher (màn hình chính)…")
        self.app_executor.submit(self._remove_launcher_thread)

    def _remove_launcher_thread(self):
        try:
            launchers = list_installed_launchers(self.device_manager)
            current_pkg, _ = get_default_launcher(self.device_manager)
            self.after(
                0,
                lambda ls=launchers, cur=current_pkg: self._confirm_remove_launchers(ls, cur),
            )
        except Exception as exc:
            self.after(0, lambda e=str(exc): self._on_launcher_scan_failed(e))

    def _on_launcher_scan_failed(self, err: str) -> None:
        self.log_message(f"Lỗi quét launcher: {err}")
        self._action_done(self.button_5, False, "Lỗi quét launcher")

    def _confirm_remove_launchers(self, launchers: list, current_pkg: str | None) -> None:
        if not launchers:
            self.log_message("Không tìm thấy launcher nào trên thiết bị.")
            self._action_done(self.button_5, True, "Không có launcher")
            return
        self._action_task(self.button_5, "idle")
        selected = ask_launcher_removal_pick(
            self,
            launchers,
            device_manager=self.device_manager,
            label_for=self._junk_display_label,
            current_package=current_pkg,
        )
        if selected is None:
            self._action_done(self.button_5, True, "Đã hủy")
            return
        if not selected:
            self._action_done(self.button_5, True, "Không chọn")
            return
        if not ask_confirm(
            self,
            "Xóa Launcher",
            f"Gỡ {len(selected)} launcher đã chọn?\n\n"
            "Nếu đang là màn hình chính, app sẽ chuyển về launcher hệ thống trước khi gỡ.",
            confirm_text="Gỡ",
            danger=True,
        ):
            self._action_done(self.button_5, True, "Đã hủy")
            return
        self._action_running(self.button_5, f"Đang xử lý {len(selected)} launcher…", progress=0.05)
        self.log_message(f"Đang gỡ {len(selected)} launcher…")
        self.app_executor.submit(self._remove_launchers_worker, selected, current_pkg)

    def _remove_launchers_worker(self, packages: list[str], current_pkg: str | None) -> None:
        succeeded: list[str] = []
        total = max(len(packages), 1)
        try:
            need_home_switch = current_pkg and current_pkg in packages
            if need_home_switch:
                oem = find_oem_home_component(
                    self.device_manager, exclude=set(packages),
                )
                if oem:
                    ok, msg = set_default_launcher(self.device_manager, oem[0], oem[1])
                    self.log_message(msg if ok else f"Không đổi launcher hệ thống: {msg}")
                else:
                    self.log_message(
                        "Cảnh báo: không tìm thấy launcher OEM — có thể cần chọn màn hình chính thủ công trên máy.",
                    )

            for idx, pkg in enumerate(packages):
                frac = (idx + 1) / total
                self.after(
                    0,
                    lambda f=frac, i=idx + 1, t=total: self._action_running(
                        self.button_5, f"Đang gỡ launcher {i}/{t}…", progress=f * 0.95,
                    ),
                )
                if is_protected_package(pkg):
                    self.log_message(f"Bỏ qua launcher được bảo vệ: {pkg}")
                    continue
                try:
                    out, err, code = self.device_manager.uninstall(pkg)
                    detail = (out or err or "").strip()
                    if code == 0 or "success" in detail.lower():
                        succeeded.append(pkg)
                        self.log_message(f"Đã gỡ launcher: {pkg}")
                        continue
                    ok, dmsg = disable_launcher(self.device_manager, pkg)
                    if ok:
                        succeeded.append(pkg)
                        self.log_message(f"Đã vô hiệu hóa launcher: {pkg}")
                    else:
                        self.log_message(f"Không gỡ được {pkg}: {detail or dmsg}")
                except Exception as exc:
                    self.log_message(f"Lỗi gỡ launcher {pkg}: {exc}")

            n = len(succeeded)
            if n:
                self.after(0, lambda: self._action_done(
                    self.button_5, True, f"Đã xử lý {n} launcher",
                ))
                self.log_message(f"Hoàn tất: đã xử lý {n} launcher.")
            else:
                self.after(0, lambda: self._action_done(self.button_5, False, "Không gỡ được"))
        except Exception as exc:
            self.after(0, lambda e=str(exc): (
                self.log_message(f"Lỗi xóa launcher: {e}"),
                self._action_done(self.button_5, False, "Lỗi"),
            ))

    def on_closing(self):
        global is_running
        is_running = False
        if hasattr(self, 'app_executor'):
            self.app_executor.shutdown(wait=False)
        if device_id:
            try:
                subprocess.run(
                    [get_adb_path(), "kill-server"],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                )
            except:
                pass
        self.destroy()

    def update_device_name(self, name):
        global device_name
        device_name = name

    def quick_scan(self):
        if not self.device_manager.device_connected:
            self.log_message("Chưa kết nối thiết bị!")
            return
        self._last_scan_at = datetime.now()
        self._refresh_status_ui()
        self.scan_button.configure(state="disabled", text="Đang quét…")
        self._ensure_app_manager_tab()
        tab = self.app_manager_tab
        if not tab:
            self.scan_button.configure(state="normal", text="⚡ Quét nhanh")
            return
        if not tab.all_rows:
            self.scan_button.configure(state="normal", text="⚡ Quét nhanh")
            show_notice(
                self,
                "Quét nhanh",
                "Đang tải danh sách ứng dụng. Vui lòng đợi vài giây rồi thử lại.",
                kind="info",
            )
            return

        from core.quick_scan_overlay import QuickScanOverlay

        overlay = QuickScanOverlay(self)
        overlay.open()
        self.log_message("Bắt đầu quét nhanh AI…")

        def on_progress(index: int, total: int, _pkg: str, name: str) -> None:
            overlay.update(
                index / max(total, 1),
                f"Đang phân tích {index}/{total}",
                detail=name or _pkg,
            )

        def on_finished(junk: list) -> None:
            self.scan_button.configure(state="normal", text="⚡ Quét nhanh")
            if not junk:
                overlay.flash_complete("Không có app rác")
                self.after(480, lambda: (overlay.close(), show_notice(
                    self,
                    "Quét nhanh",
                    "Không phát hiện ứng dụng rác cần gỡ.",
                    kind="success",
                )))
                return

            overlay.update(1.0, "Đang tải icon…", detail=f"{len(junk)} ứng dụng")
            overlay.flash_complete("Đang tải icon…")

            def _open_on_main() -> None:
                overlay.close()
                self._show_quick_scan_results(junk)

            def _prefetch_in_background() -> None:
                try:
                    self._prefetch_junk_icons_worker(junk)
                except Exception as exc:
                    logging.debug("prefetch junk icons: %s", exc)
                self.after(0, _open_on_main)

            self.app_executor.submit(_prefetch_in_background)

        tab.scan_all_async(quiet=True, on_progress=on_progress, on_finished=on_finished)

    def _apk_hint_for(self, package: str) -> str | None:
        if not self.app_manager_tab:
            return None
        row = self.app_manager_tab.package_to_row.get(package, {})
        return row.get("apk_path") or None

    def _prefetch_junk_icons_worker(self, packages: list[str]) -> None:
        prefetch_junk_icons(
            self.device_manager,
            packages,
            label_for=self._junk_display_label,
            hint_for=self._apk_hint_for,
        )

    def _show_quick_scan_results(self, junk_packages: list[str]) -> None:
        def meta_for(pkg: str) -> dict:
            if not self.app_manager_tab:
                return {}
            row = self.app_manager_tab.package_to_row.get(pkg, {})
            return row.get("analysis") or {}

        selected = ask_junk_removal_pick(
            self,
            junk_packages,
            device_manager=self.device_manager,
            label_for=self._junk_display_label,
            meta_for=meta_for,
            hint_for=self._apk_hint_for,
            premium=True,
        )
        if selected is None:
            return
        if not selected:
            self.log_message("Không chọn app nào để gỡ.")
            return
        self.log_message(f"Đang gỡ {len(selected)} ứng dụng đã chọn…")
        self.app_executor.submit(self._remove_junk_apps_thread, selected)

    def open_about(self):
        show_about_dialog(self)

    def reload_adb(self):
        """Reload ADB connection"""
        if not is_running:
            return
            
        # Disable button and show loading state
        self.refresh_button.configure(state="disabled", text="…")
        self.log_message("Đang reload kết nối ADB...")
        
        # Run reload in separate thread
        Thread(target=self._reload_adb_thread, daemon=True).start()

    def _reload_adb_thread(self):
        """Thread function for reloading ADB"""
        global device_id, device_name
        try:
            # Kill ADB server
            self.after(0, lambda: self.log_message("Reloading ADB..."))
            subprocess.run(
                [get_adb_path(), "kill-server"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            time.sleep(0.5)
            
            # Start ADB server
            subprocess.run(
                [get_adb_path(), "start-server"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            time.sleep(0.5)
            
            # Get device info
            devices = subprocess.run(
                [get_adb_path(), "devices"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            ).stdout.strip().split("\n")[1:]
            
            devices = [d.split()[0] for d in devices if "device" in d]
            if devices and devices[0]:
                device_id = devices[0]
                device_name = run_adb_command(
                    ["-s", device_id, "shell", "getprop", "ro.product.model"],
                    timeout=3
                ) or "Không xác định"
                
                if device_name != "Không xác định":
                    self.after(0, lambda: self.update_device_name(device_name))
                    self.after(0, lambda: self.log_message(f"Đã kết nối: {device_name}"))
                    self.device_manager.serial = device_id
                    self.device_manager.device_model = device_name
                    self.device_manager.device_connected = True
                    self.after(0, lambda: self.toggle_buttons(True))
                    self.after(0, lambda: self._app_manager_refresh_on_connect())
            
            # Force check connection
            self.after(0, lambda: self._refresh_status_ui(force_check=True))
        except Exception as e:
            self.after(0, lambda: self.log_message(f"Lỗi reload ADB: {str(e)}"))
        finally:
            # Re-enable button and restore original text
            self.after(0, lambda: self.refresh_button.configure(state="normal", text="↻"))

    def clear_log(self):
        if hasattr(self, "log_terminal"):
            self.log_terminal.clear()

if __name__ == "__main__":
    init_policy(appdata_dir)
    app = MainApp()
    app.mainloop()