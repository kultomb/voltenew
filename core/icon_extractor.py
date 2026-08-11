"""
Android app icon extraction — ADB, APK zip, aapt, Pillow cache & UI thumbnails.
"""

from __future__ import annotations

import io
import logging
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import zipfile
import platform
from typing import Callable, Optional

from PIL import Image, ImageDraw

try:
    RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE = Image.LANCZOS

CACHE_TAG = "v2"
UI_PX = 32
MASTER_PX = 96

_ICON_JUNK = (
    "notification", "stat_notify", "widget", "splash",
    "toolbar", "tab_", "abc_", "emoji", "twemoji",
    "branding", "imgly_", "favicon", "sponsor",
)
_ICON_DENSITY = (
    ("xxxhdpi", 6), ("xxhdpi", 5), ("xhdpi", 4),
    ("hdpi", 3), ("mdpi", 2), ("ldpi", 1),
)

# Thử trực tiếp trước unzip -l (APK lớn list rất chậm).
_QUICK_LAUNCHER_PATHS = (
    "res/mipmap-xxxhdpi-v4/ic_launcher.png",
    "res/mipmap-xxxhdpi/ic_launcher.png",
    "res/mipmap-xxhdpi-v4/ic_launcher.png",
    "res/mipmap-xxhdpi/ic_launcher.png",
    "res/mipmap-xhdpi-v4/ic_launcher.png",
    "res/mipmap-xhdpi/ic_launcher.png",
    "res/mipmap-hdpi-v4/ic_launcher.png",
    "res/mipmap-hdpi/ic_launcher.png",
    "res/mipmap-mdpi-v4/ic_launcher.png",
    "res/mipmap-mdpi/ic_launcher.png",
    "res/mipmap-xxxhdpi-v4/ic_launcher.webp",
    "res/mipmap-xxhdpi-v4/ic_launcher.webp",
    "res/mipmap-xxxhdpi-v4/ic_launcher_round.png",
    "res/mipmap-xxhdpi-v4/ic_launcher_round.png",
    "res/mipmap-xxxhdpi-v4/ic_launcher_foreground.png",
    "res/mipmap-xxhdpi-v4/ic_launcher_foreground.png",
    "res/mipmap-xhdpi-v4/ic_launcher_foreground.png",
    "res/mipmap-hdpi-v4/ic_launcher_foreground.png",
    "res/mipmap-xxxhdpi-v4/ic_launcher_background.png",
    "res/mipmap-xxhdpi-v4/ic_launcher_background.png",
    "res/drawable-xxxhdpi/ic_launcher.png",
    "res/drawable-xxhdpi/ic_launcher.png",
    "res/drawable/ic_launcher.png",
)

_ADAPTIVE_XML_PATHS = (
    "res/mipmap-anydpi-v26/ic_launcher.xml",
    "res/mipmap-anydpi/ic_launcher.xml",
    "res/drawable-anydpi-v26/ic_launcher.xml",
)

_LARGE_APK_PACKAGES = frozenset({
    "com.facebook.katana",
    "com.facebook.lite",
    "com.facebook.orca",
    "com.instagram.android",
    "com.whatsapp",
    "com.google.android.youtube",
    "com.ss.android.ugc.trill",
    "com.zhiliaoapp.musically",
    "com.ss.android.ugc.aweme",
    "com.zhiliaoapp.musically.go",
    "com.tiktok.android",
})


def find_aapt_binary() -> Optional[str]:
    for name in ("aapt2", "aapt"):
        found = shutil.which(name)
        if found:
            return found
    for env_key in ("ANDROID_HOME", "ANDROID_SDK_ROOT", "ANDROID_SDK"):
        sdk = os.environ.get(env_key)
        if not sdk or not os.path.isdir(sdk):
            continue
        bt = os.path.join(sdk, "build-tools")
        if not os.path.isdir(bt):
            continue
        versions = sorted(os.listdir(bt), reverse=True)
        for ver in versions:
            for name in ("aapt2.exe", "aapt2", "aapt.exe", "aapt"):
                candidate = os.path.join(bt, ver, name)
                if os.path.isfile(candidate):
                    return candidate
    return None


def _score_icon_entry(lower: str, name: str) -> tuple[int, str]:
    score = 0
    for key, weight in _ICON_DENSITY:
        if key in lower:
            score += weight * 10
    if "round" in lower:
        score -= 3
    if "background" in lower:
        score -= 1
    if "foreground" in lower:
        score -= 1
    if "ic_launcher" in lower or "app_icon" in lower:
        score += 25
    if "mipmap" in lower:
        score += 8
    if "drawable" in lower:
        score += 3
    return score, name


def collect_icon_candidates(names: list[str]) -> list[tuple[int, str]]:
    icon_candidates: list[tuple[int, str]] = []
    for name in names:
        lower = name.lower()
        if not lower.endswith((".png", ".webp", ".jpg", ".jpeg", ".xml")):
            continue
        if "res/" not in lower:
            continue
        if any(j in lower for j in _ICON_JUNK):
            continue
        launcherish = (
            "ic_launcher" in lower
            or "app_icon" in lower
            or "launcher_icon" in lower
            or "fb_launcher" in lower
            or ("launcher" in lower and ("foreground" in lower or "background" in lower))
            or ("mipmap" in lower and "icon" in lower)
            or "play_store" in lower
        )
        if not launcherish:
            continue
        icon_candidates.append(_score_icon_entry(lower, name))

    if not icon_candidates:
        for name in names:
            lower = name.lower()
            if not lower.endswith((".png", ".webp")) or "mipmap" not in lower or "res/" not in lower:
                continue
            if "anydpi" in lower or any(j in lower for j in _ICON_JUNK):
                continue
            icon_candidates.append(_score_icon_entry(lower, name))

    if not icon_candidates:
        for name in names:
            lower = name.lower()
            if not lower.endswith((".png", ".webp")) or "drawable" not in lower or "res/" not in lower:
                continue
            if any(j in lower for j in _ICON_JUNK):
                continue
            if not any(x in lower for x in ("ic_launcher", "launcher_icon", "app_icon", "ic_logo", "logo_launcher")):
                continue
            icon_candidates.append(_score_icon_entry(lower, name))
    return icon_candidates


def collect_relaxed_candidates(names: list[str]) -> list[tuple[int, str, int]]:
    """Any launcher-ish PNG/WebP in res/ — sorted by score then size."""
    found: list[tuple[int, str, int]] = []
    for name in names:
        lower = name.lower()
        if not lower.endswith((".png", ".webp", ".jpg", ".jpeg")):
            continue
        if "res/" not in lower or "values" in lower:
            continue
        if any(j in lower for j in _ICON_JUNK):
            continue
        if "mipmap" not in lower and "drawable" not in lower:
            continue
        score = _score_icon_entry(lower, name)[0]
        if "launcher" in lower or "logo" in lower:
            score += 10
        found.append((score, name, 0))
    return found


def parse_unzip_list_filenames(listing_text: str) -> list[tuple[str, int]]:
    """(entry_name, uncompressed_size) from unzip -l."""
    names: list[tuple[str, int]] = []
    for line in (listing_text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("Archive:") or line.startswith("--------"):
            continue
        if "Length" in line and "Name" in line:
            continue
        parts = line.split(None, 3)
        if len(parts) < 4 or not parts[0].isdigit():
            continue
        try:
            size = int(parts[0])
        except ValueError:
            size = 0
        names.append((parts[3], size))
    return names


def normalize_launcher_icon(img: Image.Image, size: int) -> Image.Image:
    """Crop vuông giữa + resize cố định — mọi icon cùng kích thước."""
    img = img.convert("RGBA")
    w, h = img.size
    if w < 1 or h < 1:
        return Image.new("RGBA", (size, size), (0, 0, 0, 0))
    if w != h:
        side = max(w, h)
        canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        canvas.paste(img, ((side - w) // 2, (side - h) // 2))
        img = canvas
    if img.size != (size, size):
        img = img.resize((size, size), RESAMPLE)
    return img


def parse_aapt_icon_resource(text: str) -> Optional[str]:
    """Đường dẫn res trong APK từ aapt dump badging (dpi cao nhất)."""
    if not text:
        return None
    best: Optional[str] = None
    best_dpi = -1
    for m in re.finditer(
        r"application-icon-(\d+):(?:'([^']+)'|\"([^\"]+)\")",
        text,
    ):
        dpi = int(m.group(1))
        path = m.group(2) or m.group(3)
        if path and dpi >= best_dpi:
            best_dpi = dpi
            best = path
    return best


def make_squircle_thumbnail(img: Image.Image, size: int = UI_PX) -> Image.Image:
    """Rounded icon like Play Store / mockup."""
    img = normalize_launcher_icon(img, size)
    radius = max(6, int(size * 0.22))
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size, size), radius=radius, fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


TABLE_CB_PX = 20
TABLE_LEADING_ICON_PX = 24
TABLE_LEADING_GAP = 10
TABLE_LEADING_PAD_LEFT = 16
TABLE_LEADING_PAD_RIGHT = 14


def draw_table_checkbox(*, checked: bool, indeterminate: bool = False, size: int = TABLE_CB_PX) -> Image.Image:
    """Checkbox vuông bo góc cho cột leading của bảng app."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = 2
    box = (pad, pad, size - pad - 1, size - pad - 1)
    radius = max(4, size // 5)
    if checked:
        draw.rounded_rectangle(box, radius=radius, fill="#4f46e5", outline="#6366f1", width=1)
        draw.line(
            [(size * 0.26, size * 0.54), (size * 0.44, size * 0.70), (size * 0.76, size * 0.32)],
            fill="#ffffff",
            width=max(2, size // 10),
            joint="curve",
        )
    elif indeterminate:
        draw.rounded_rectangle(box, radius=radius, fill="#4f46e5", outline="#6366f1", width=1)
        iy0, iy1 = int(size * 0.44), int(size * 0.56)
        draw.rounded_rectangle((int(size * 0.28), iy0, int(size * 0.72), iy1), radius=2, fill="#ffffff")
    else:
        draw.rounded_rectangle(box, radius=radius, fill="#1a1f28", outline="#4b5563", width=2)
    return img


def compose_table_leading(
    app_icon: Image.Image,
    *,
    checked: bool = False,
    indeterminate: bool = False,
    cb_px: int = TABLE_CB_PX,
    icon_px: int = TABLE_LEADING_ICON_PX,
    gap: int = TABLE_LEADING_GAP,
    pad_left: int = TABLE_LEADING_PAD_LEFT,
    pad_right: int = TABLE_LEADING_PAD_RIGHT,
) -> Image.Image:
    """Checkbox + icon + khoảng trống phải (trước text tên app trong Treeview #0)."""
    cb = draw_table_checkbox(checked=checked, indeterminate=indeterminate, size=cb_px)
    thumb = make_squircle_thumbnail(app_icon, icon_px)
    inner_w = cb_px + gap + icon_px
    width = pad_left + inner_w + pad_right
    height = max(cb_px, icon_px, 28)
    out = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    y_cb = (height - cb_px) // 2
    y_icon = (height - icon_px) // 2
    out.paste(cb, (pad_left, y_cb), cb)
    out.paste(thumb, (pad_left + cb_px + gap, y_icon), thumb)
    return out


def table_leading_width(
    cb_px: int = TABLE_CB_PX,
    icon_px: int = TABLE_LEADING_ICON_PX,
    gap: int = TABLE_LEADING_GAP,
    pad_left: int = TABLE_LEADING_PAD_LEFT,
    pad_right: int = TABLE_LEADING_PAD_RIGHT,
) -> int:
    return pad_left + cb_px + gap + icon_px + pad_right


def decode_image_bytes(raw: bytes) -> Optional[Image.Image]:
    if not raw or len(raw) < 32:
        return None
    if raw.startswith(b"\r\n"):
        raw = raw.lstrip(b"\r\n")
    if raw.startswith(b"\n"):
        raw = raw.lstrip(b"\n")
    try:
        return Image.open(io.BytesIO(raw)).convert("RGBA")
    except Exception:
        return None


def composite_adaptive(names: list[str], read_entry: Callable[[str], Optional[bytes]]) -> Optional[Image.Image]:
    """Merge adaptive icon foreground + background from APK entries."""
    fg_entry = bg_entry = None
    for name in names:
        lower = name.lower()
        if not lower.endswith((".png", ".webp")):
            continue
        if "ic_launcher_foreground" in lower:
            fg_entry = name
        elif "ic_launcher_background" in lower:
            bg_entry = name
    if not fg_entry:
        return None
    fg_raw = read_entry(fg_entry)
    if not fg_raw:
        return None
    fg = decode_image_bytes(fg_raw)
    if not fg:
        return None
    if bg_entry:
        bg_raw = read_entry(bg_entry)
        if bg_raw:
            bg = decode_image_bytes(bg_raw)
            if bg:
                bg = bg.resize(fg.size, RESAMPLE)
                base = Image.new("RGBA", fg.size, (0, 0, 0, 0))
                base.paste(bg, (0, 0))
                base.alpha_composite(fg)
                return base
    return fg


class IconExtractor:
    """Production icon pipeline: device unzip → local APK → aapt; disk cache + UI thumbs."""

    def __init__(
        self,
        icons_dir: str,
        *,
        run_adb: Callable,
        exec_out_shell: Callable,
        serial_getter: Callable[[], Optional[str]],
    ):
        self.icons_dir = icons_dir
        os.makedirs(self.icons_dir, exist_ok=True)
        self._run = run_adb
        self._exec_out = exec_out_shell
        self._serial = serial_getter
        self._apk_path_cache: dict[str, str] = {}
        self._aapt: Optional[str] = None
        self._pull_skip: set[str] = set()

    def _path_ui(self, package: str) -> str:
        return os.path.join(self.icons_dir, f"{package}.{CACHE_TAG}_{UI_PX}.png")

    def _path_master(self, package: str) -> str:
        return os.path.join(self.icons_dir, f"{package}.{CACHE_TAG}_{MASTER_PX}.png")

    def _path_legacy(self, package: str) -> str:
        return os.path.join(self.icons_dir, f"{package}.png")

    def clear_apk_path_cache(self):
        self._apk_path_cache.clear()
        self._pull_skip.clear()

    def purge_ui_without_master(self) -> int:
        """Xóa thumbnail UI cũ (avatar chữ) không có master/legacy APK."""
        removed = 0
        suffix = f".{CACHE_TAG}_{UI_PX}.png"
        try:
            for name in os.listdir(self.icons_dir):
                if not name.endswith(suffix):
                    continue
                pkg = name[: -len(suffix)]
                if not pkg or self.has_real_icon_cached(pkg):
                    continue
                try:
                    os.remove(os.path.join(self.icons_dir, name))
                    removed += 1
                except OSError as exc:
                    logging.debug(f"purge ui icon {pkg}: {exc}")
        except OSError as exc:
            logging.debug(f"purge ui icons: {exc}")
        return removed

    def invalidate_package(self, package: str) -> None:
        """Xóa cache icon để lần sau trích lại (Làm mới / app nặng)."""
        for path in (self._path_ui(package), self._path_master(package), self._path_legacy(package)):
            try:
                if os.path.isfile(path):
                    os.remove(path)
            except OSError as exc:
                logging.debug(f"invalidate icon {package}: {exc}")
        self._pull_skip.discard(package)
        self._apk_path_cache.pop(package, None)

    def has_real_icon_cached(self, package: str) -> bool:
        master = self._path_master(package)
        if os.path.isfile(master) and os.path.getsize(master) > 64:
            return True
        legacy = self._path_legacy(package)
        return os.path.isfile(legacy) and os.path.getsize(legacy) > 64

    def get_instant_ui_path(self, package: str, label: str = "") -> Optional[str]:
        """Chỉ icon APK đã cache — không tạo avatar chữ cái."""
        return self.get_cached_ui_path(package)

    def get_cached_ui_path(self, package: str) -> Optional[str]:
        """Icon thật từ APK (master/legacy); bỏ qua file UI cũ kiểu avatar chữ."""
        ui = self._path_ui(package)
        legacy = self._path_legacy(package)
        master = self._path_master(package)
        if os.path.isfile(master) and os.path.getsize(master) > 64:
            try:
                self._write_ui_from_master(master, ui, package=package)
                return ui
            except Exception:
                pass
        if os.path.isfile(legacy) and os.path.getsize(legacy) > 64:
            try:
                self._write_ui_from_master(legacy, ui, package=package)
                return ui
            except Exception:
                return legacy
        return None

    def get_cached_icon_path(self, package: str) -> Optional[str]:
        return self.get_cached_ui_path(package)

    def _write_ui_from_master(self, master_path: str, ui_path: Optional[str] = None, package: str = "") -> str:
        if not ui_path and package:
            ui_path = self._path_ui(package)
        elif not ui_path:
            ui_path = self._path_ui(os.path.basename(master_path).split(".")[0])
        img = Image.open(master_path).convert("RGBA")
        thumb = make_squircle_thumbnail(img, UI_PX)
        thumb.save(ui_path, format="PNG", optimize=True)
        return ui_path

    def _save_master(self, img: Image.Image, package: str) -> str:
        master_path = self._path_master(package)
        m = normalize_launcher_icon(img, MASTER_PX)
        m.save(master_path, format="PNG", optimize=True)
        ui_path = self._path_ui(package)
        make_squircle_thumbnail(m, UI_PX).save(ui_path, format="PNG", optimize=True)
        return ui_path

    def cache_apk_path(self, package: str, apk_path: str):
        if package and apk_path:
            self._apk_path_cache[package] = apk_path

    def _query_pm_path_joined(self, package: str) -> Optional[str]:
        """Tất cả segment split APK (Facebook/Meta thường icon ở split, không chỉ base)."""
        serial = self._serial()
        if not serial:
            return None
        out, _, code = self._run(["-s", serial, "shell", "pm", "path", package], timeout=8)
        if code != 0 or not out:
            return None
        paths: list[str] = []
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("package:"):
                path = line.replace("package:", "", 1).strip()
                if path.startswith("/"):
                    paths.append(path)
        if not paths:
            return None
        joined = ":".join(paths)
        self._apk_path_cache[package] = joined
        return joined

    def get_package_apk_path(self, package: str, hint: Optional[str] = None) -> Optional[str]:
        if hint and hint.startswith("/") and ":" in hint:
            self._apk_path_cache[package] = hint
            return hint
        if package in self._apk_path_cache and ":" in self._apk_path_cache[package]:
            return self._apk_path_cache[package]
        joined = self._query_pm_path_joined(package)
        if joined:
            return joined
        if hint and hint.startswith("/"):
            self._apk_path_cache[package] = hint
            return hint
        if package in self._apk_path_cache:
            return self._apk_path_cache[package]
        return None

    def _resolve_apk_paths_for_icon(self, package: str, hint: Optional[str] = None) -> Optional[str]:
        joined = self._query_pm_path_joined(package)
        if joined:
            return joined
        if hint and hint.startswith("/"):
            return hint
        return self._apk_path_cache.get(package)

    def _aapt_binary(self) -> Optional[str]:
        if self._aapt is None:
            self._aapt = find_aapt_binary() or ""
        return self._aapt or None

    def _aapt_icon_entry(self, local_apk: str) -> Optional[str]:
        aapt = self._aapt_binary()
        if not aapt:
            return None
        try:
            result = subprocess.run(
                [aapt, "dump", "badging", local_apk],
                capture_output=True,
                timeout=12,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
            )
            text = (result.stdout or b"").decode("utf-8", errors="replace")
            return parse_aapt_icon_resource(text)
        except Exception as exc:
            logging.debug(f"aapt badging: {exc}")
            return None

    def _device_aapt_badging(self, remote_apk: str) -> Optional[str]:
        qapk = shlex.quote(remote_apk)
        for aapt in ("/system/bin/aapt2", "/system/bin/aapt", "aapt2", "aapt"):
            out, _, code = self._run(
                ["-s", self._serial(), "shell", aapt, "dump", "badging", qapk],
                timeout=14,
            )
            if code == 0 and out:
                return out
        return None

    def _device_apk_read_context(self, seg: str) -> tuple[Callable[[str], Optional[bytes]], list[str]]:
        """Đọc byte từ APK trên thiết bị + danh sách entry res/ (grep nhanh)."""
        qapk = shlex.quote(seg)
        names = list(self._grep_launcher_entries_on_device(seg, timeout=16))
        for xml_path in _ADAPTIVE_XML_PATHS:
            if xml_path not in names:
                names.append(xml_path)

        def read_bytes(entry: str) -> Optional[bytes]:
            raw, _ = self._exec_out(
                f"unzip -p {qapk} {shlex.quote(entry)} 2>/dev/null",
                timeout=12,
            )
            return raw if raw else None

        return read_bytes, names

    def _extract_entry_on_device(self, package: str, seg: str, entry: str) -> Optional[str]:
        """PNG trực tiếp hoặc Adaptive Icon (parse XML + merge fg/bg)."""
        from core.apk_icon_extract import extract_icon_entry

        read_bytes, names = self._device_apk_read_context(seg)
        img = extract_icon_entry(entry, read_bytes, names)
        if img:
            return self._save_master(img, package)
        return None

    def _unzip_entry_from_segment(self, package: str, seg: str, entry: str) -> Optional[str]:
        return self._extract_entry_on_device(package, seg, entry)

    def _try_device_aapt_icon(self, package: str, remote_apk: str) -> Optional[str]:
        """aapt trên từng split APK — hỗ trợ application-icon XML (adaptive)."""
        from core.apk_icon_extract import parse_application_icon_paths

        if not self._serial():
            return None
        for seg in self._apk_segments_ordered(remote_apk):
            text = self._device_aapt_badging(seg)
            if not text:
                continue
            for _dpi, entry in parse_application_icon_paths(text):
                got = self._extract_entry_on_device(package, seg, entry)
                if got:
                    return got
        return None

    def _try_local_aapt_icon(self, package: str, remote_apk: str) -> Optional[str]:
        """pm path → adb pull → aapt badging → PNG hoặc merge adaptive (PC aapt)."""
        from core.apk_icon_extract import extract_best_icon_from_apk

        aapt = self._aapt_binary()
        if not aapt:
            return None
        serial = self._serial()
        if not serial:
            return None
        timeout = 45 if package in _LARGE_APK_PACKAGES else 22
        for seg in self._apk_segments_by_size(remote_apk)[:5]:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".apk") as tmp:
                tmp_path = tmp.name
            try:
                _, _, code = self._run(
                    ["-s", serial, "pull", seg, tmp_path],
                    timeout=timeout,
                )
                if code != 0 or not os.path.isfile(tmp_path) or os.path.getsize(tmp_path) < 64:
                    continue
                img = extract_best_icon_from_apk(tmp_path, aapt)
                if img:
                    return self._save_master(img, package)
            finally:
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
        return None

    def _extract_from_zip_file(self, zf: zipfile.ZipFile, package: str, *, relaxed: bool = False) -> Optional[str]:
        names = zf.namelist()
        adaptive = composite_adaptive(names, lambda e: zf.read(e))
        if adaptive:
            return self._save_master(adaptive, package)
        candidates = collect_icon_candidates(names)
        if not candidates and relaxed:
            relaxed_list = collect_relaxed_candidates(names)
            candidates = [(s, n) for s, n, _ in relaxed_list]
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0], reverse=True)
        try_list = candidates[:12] if relaxed else candidates[:8]
        from core.apk_icon_extract import extract_icon_entry

        def read_bytes(e: str) -> Optional[bytes]:
            try:
                return zf.read(e)
            except KeyError:
                return None

        for _, entry in try_list:
            if entry.lower().endswith(".xml"):
                img = extract_icon_entry(entry, read_bytes, names)
                if img:
                    return self._save_master(img, package)
                continue
            try:
                with zf.open(entry) as icon_file:
                    img = Image.open(icon_file).convert("RGBA")
                    return self._save_master(img, package)
            except Exception:
                continue
        return None

    @staticmethod
    def _apk_segments_ordered(remote_apk: str) -> list[str]:
        segments = [s.strip() for s in remote_apk.split(":") if s.strip().startswith("/")]
        if not segments:
            return []

        def sort_key(p: str) -> tuple:
            if "base.apk" in p:
                tier = 0
            elif "split_config" in p and any(d in p for d in ("xxhdpi", "xxxhdpi", "xhdpi", "density")):
                tier = 1
            elif "split_config" in p and ("resource" in p or "res" in p):
                tier = 2
            elif "split_config" in p:
                tier = 3
            else:
                tier = 4
            return (tier, len(p))

        return sorted(segments, key=sort_key)

    def _apk_segments_by_size(self, remote_apk: str) -> list[str]:
        """Split nhỏ (density) thường chứa icon — thử trước base.apk 100MB+."""
        segments = self._apk_segments_ordered(remote_apk)
        if not segments:
            return []
        serial = self._serial()
        if not serial:
            return segments
        sized: list[tuple[int, str]] = []
        for seg in segments:
            q = shlex.quote(seg)
            out, _, code = self._run(
                ["-s", serial, "shell", "stat", "-c", "%s", q],
                timeout=6,
            )
            try:
                sz = int(out.strip()) if code == 0 and out.strip().isdigit() else 2**31 - 1
            except ValueError:
                sz = 2**31 - 1
            sized.append((sz, seg))
        sized.sort(key=lambda x: x[0])
        return [seg for _, seg in sized]

    def _try_quick_unzip_paths(self, package: str, seg: str) -> Optional[str]:
        """Vài lệnh unzip -p nhỏ — tránh unzip -l trên APK game."""
        qapk = shlex.quote(seg)
        fg = bg = None
        for rel in _QUICK_LAUNCHER_PATHS:
            raw, _ = self._exec_out(f"unzip -p {qapk} {shlex.quote(rel)} 2>/dev/null", timeout=5)
            img = decode_image_bytes(raw or b"")
            if not img:
                continue
            lower = rel.lower()
            if "foreground" in lower:
                fg = img
            elif "background" in lower:
                bg = img
            else:
                return self._save_master(img, package)
        if fg:
            if bg:
                bg = bg.resize(fg.size, RESAMPLE)
                base = Image.new("RGBA", fg.size, (0, 0, 0, 0))
                base.paste(bg, (0, 0))
                base.alpha_composite(fg)
                return self._save_master(base, package)
            return self._save_master(fg, package)
        return None

    def _grep_launcher_entries_on_device(self, seg: str, *, timeout: int = 14) -> list[str]:
        """grep trên thiết bị — nhanh hơn parse full unzip -l cho APK lớn."""
        serial = self._serial()
        if not serial:
            return []
        qapk = shlex.quote(seg)
        script = (
            f"unzip -l {qapk} 2>/dev/null | "
            r"grep -iE 'ic_launcher|launcher_icon|app_icon|fb_.*icon|meta_.*icon|tiktok|musically|logo' | "
            r"grep -E '\.(png|webp)$' | awk '{print $NF}' | head -25"
        )
        out, _, code = self._run(["-s", serial, "shell", "sh", "-c", script], timeout=timeout)
        if code != 0 or not out:
            return []
        entries = []
        for line in out.splitlines():
            name = line.strip()
            if name.startswith("res/") and name.lower().endswith((".png", ".webp")):
                entries.append(name)
        return entries

    def _try_adaptive_xml_on_device(self, package: str, seg: str) -> Optional[str]:
        qapk = shlex.quote(seg)
        for xml_path in _ADAPTIVE_XML_PATHS:
            raw, _ = self._exec_out(f"unzip -p {qapk} {shlex.quote(xml_path)} 2>/dev/null", timeout=5)
            if not raw or b"adaptive-icon" not in raw.lower():
                continue
            text = raw.decode("utf-8", errors="ignore")
            refs = re.findall(r"@(?:mipmap|drawable)/([A-Za-z0-9_]+)", text)
            if not refs:
                continue
            names = self._grep_launcher_entries_on_device(seg, timeout=12)
            if not names:
                names = []
            for ref in refs:
                for name in names:
                    if f"/{ref}." in name or name.endswith(f"/{ref}.png"):
                        raw_img, _ = self._exec_out(
                            f"unzip -p {qapk} {shlex.quote(name)} 2>/dev/null", timeout=8
                        )
                        img = decode_image_bytes(raw_img or b"")
                        if img:
                            return self._save_master(img, package)
                for density in ("xxxhdpi-v4", "xxxhdpi", "xxhdpi-v4", "xxhdpi", "xhdpi", "hdpi"):
                    for ext in (".png", ".webp"):
                        guess = f"res/mipmap-{density}/{ref}{ext}"
                        raw_img, _ = self._exec_out(
                            f"unzip -p {qapk} {shlex.quote(guess)} 2>/dev/null", timeout=5
                        )
                        img = decode_image_bytes(raw_img or b"")
                        if img:
                            return self._save_master(img, package)
        return None

    def _extract_from_grep_entries(
        self, package: str, seg: str, entries: list[str]
    ) -> Optional[str]:
        if not entries:
            return None
        scored: list[tuple[int, str]] = []
        for name in entries:
            score, _ = _score_icon_entry(name.lower(), name)
            scored.append((score, name))
        scored.sort(key=lambda x: x[0], reverse=True)
        qapk = shlex.quote(seg)
        names_only = [n for _, n in scored]
        adaptive = composite_adaptive(names_only, lambda e: self._exec_out(
            f"unzip -p {qapk} {shlex.quote(e)} 2>/dev/null", timeout=8
        )[0])
        if adaptive:
            return self._save_master(adaptive, package)
        for _, entry in scored[:6]:
            raw, _ = self._exec_out(f"unzip -p {qapk} {shlex.quote(entry)} 2>/dev/null", timeout=8)
            img = decode_image_bytes(raw or b"")
            if img:
                return self._save_master(img, package)
        return None

    def ensure_ui_icon(
        self, package: str, apk_path_hint: Optional[str] = None, label: str = ""
    ) -> Optional[str]:
        """Trích icon APK; None nếu thất bại (UI giữ placeholder)."""
        return self.extract_icon_to_cache(package, apk_path_hint, label=label)

    def _try_device_unzip(self, package: str, remote_apk: str) -> Optional[str]:
        serial = self._serial()
        if not serial:
            return None
        segments = self._apk_segments_by_size(remote_apk)
        if not segments:
            return None
        list_timeout = 22 if package in _LARGE_APK_PACKAGES else 10

        for seg in segments[:8]:
            quick = self._try_quick_unzip_paths(package, seg)
            if quick:
                return quick
            adaptive_xml = self._try_adaptive_xml_on_device(package, seg)
            if adaptive_xml:
                return adaptive_xml
            grep_entries = self._grep_launcher_entries_on_device(seg, timeout=list_timeout)
            if grep_entries:
                got = self._extract_from_grep_entries(package, seg, grep_entries)
                if got:
                    return got

        for seg in segments[:3]:
            listing = ""
            code = -1
            for unzip_bin in ("unzip", "/system/bin/unzip"):
                listing, _, code = self._run(
                    ["-s", serial, "shell", unzip_bin, "-l", seg],
                    timeout=list_timeout,
                )
                if code == 0 and listing and "res/" in listing:
                    break
            if code != 0 or not listing:
                continue
            entries = parse_unzip_list_filenames(listing)
            names = [n for n, _ in entries]

            def read_entry(entry: str) -> Optional[bytes]:
                qseg = shlex.quote(seg)
                qent = shlex.quote(entry)
                raw, _ = self._exec_out(f"unzip -p {qseg} {qent} 2>/dev/null", timeout=12)
                return raw if raw else None

            adaptive = composite_adaptive(names, read_entry)
            if adaptive:
                return self._save_master(adaptive, package)

            candidates = collect_icon_candidates(names)
            if not candidates:
                size_map = {n: s for n, s in entries}
                relaxed = collect_relaxed_candidates(names)
                if relaxed:
                    for score, name, _ in relaxed:
                        score += min(size_map.get(name, 0) // 512, 40)
                        candidates.append((score, name))
            if not candidates and entries:
                big = sorted(entries, key=lambda x: -x[1])[:5]
                for name, _ in big:
                    if name.lower().endswith((".png", ".webp")) and "res/" in name.lower():
                        candidates.append((0, name))
            if not candidates:
                continue
            candidates.sort(key=lambda x: x[0], reverse=True)
            qseg = shlex.quote(seg)
            for _, entry in candidates[:4]:
                if entry.lower().endswith(".xml"):
                    continue
                qent = shlex.quote(entry)
                raw, _ = self._exec_out(f"unzip -p {qseg} {qent} 2>/dev/null", timeout=8)
                img = decode_image_bytes(raw or b"")
                if img:
                    return self._save_master(img, package)
        return None

    def _try_pm_clear_and_repath(self, package: str) -> Optional[str]:
        """Xóa cache path cũ và hỏi lại pm path (split APK đổi đường dẫn)."""
        self._apk_path_cache.pop(package, None)
        return self.get_package_apk_path(package)

    def _shared_pulled_apk(self, package: str) -> Optional[str]:
        """APK đã pull cho nhãn app (cache/apk_pulls) — tránh pull trùng."""
        safe = package.replace("/", "_").replace("\\", "_")
        root = os.path.dirname(self.icons_dir)
        path = os.path.join(root, "cache", "apk_pulls", f"{safe}.apk")
        if os.path.isfile(path) and os.path.getsize(path) > 64:
            return path
        return None

    def _try_icon_from_local_apk(self, package: str, local_apk: str) -> Optional[str]:
        entry = self._aapt_icon_entry(local_apk)
        if entry:
            try:
                with zipfile.ZipFile(local_apk, "r") as zf:
                    with zf.open(entry) as icon_file:
                        img = Image.open(icon_file).convert("RGBA")
                        return self._save_master(img, package)
            except Exception:
                pass
        try:
            with zipfile.ZipFile(local_apk, "r") as zf:
                return self._extract_from_zip_file(zf, package)
        except Exception:
            return None

    def _try_pull_apk(self, package: str, remote_apk: str) -> Optional[str]:
        if package in self._pull_skip:
            return None
        shared = self._shared_pulled_apk(package)
        if shared:
            got = self._try_icon_from_local_apk(package, shared)
            if got:
                return got
        serial = self._serial()
        if not serial:
            return None
        segments = self._apk_segments_by_size(remote_apk)
        if not segments:
            return None
        pull_timeout = 45 if package in _LARGE_APK_PACKAGES else 24
        with tempfile.TemporaryDirectory(prefix="hbg_icon_") as temp_dir:
            for idx, seg in enumerate(segments[:5]):
                local_apk = os.path.join(temp_dir, f"{package}_{idx}.apk")
                _, _, code = self._run(
                    ["-s", serial, "pull", seg, local_apk],
                    timeout=pull_timeout,
                )
                if code != 0 or not os.path.isfile(local_apk) or os.path.getsize(local_apk) < 64:
                    continue
                got = self._try_icon_from_local_apk(package, local_apk)
                if got:
                    return got
                try:
                    with zipfile.ZipFile(local_apk, "r") as zf:
                        got = self._extract_from_zip_file(zf, package)
                        if got:
                            return got
                        got = self._extract_from_zip_file(zf, package, relaxed=True)
                        if got:
                            return got
                except Exception:
                    continue
            self._pull_skip.add(package)
        return None

    def _try_dumpsys_icon_path(self, package: str) -> Optional[str]:
        """Một số ROM ghi đường dẫn APK trong dumpsys — dùng làm gợi ý pull."""
        serial = self._serial()
        if not serial:
            return None
        qpkg = shlex.quote(package)
        out, _, code = self._run(
            ["-s", serial, "shell", "sh", "-c", f"dumpsys package {qpkg} 2>/dev/null | head -c 48000"],
            timeout=10,
        )
        if code != 0 or not out:
            return None
        for m in re.finditer(r"(/data/app/[^\s:]+\.apk)", out):
            path = m.group(1)
            if package.replace(".", "_") in path or package.split(".")[-1] in path:
                self._apk_path_cache[package] = path
                return path
        return None

    def extract_icon_to_cache(
        self, package: str, apk_path_hint: Optional[str] = None, label: str = ""
    ) -> Optional[str]:
        """Chỉ Play Store (nhanh) — không pull APK / aapt qua ADB."""
        if self.has_real_icon_cached(package):
            return self.get_cached_ui_path(package)
        return self._try_play_store_icon(package)

    def _try_play_store_icon(self, package: str) -> Optional[str]:
        try:
            from core.play_store_fallback import fetch_play_store_icon_image

            img = fetch_play_store_icon_image(package)
            if img:
                return self._save_master(img, package)
        except Exception as exc:
            logging.debug(f"play store icon {package}: {exc}")
        return None
