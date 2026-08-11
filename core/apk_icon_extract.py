"""
Trích icon launcher từ APK: aapt dump badging → PNG trực tiếp hoặc Adaptive Icon (XML merge).
Luồng: pm path → adb pull → aapt → zip/adaptive.
"""

from __future__ import annotations

import logging
import re
import subprocess
import platform
import zipfile
from typing import Callable, Optional

from PIL import Image

from core.icon_extractor import (
    collect_icon_candidates,
    composite_adaptive,
    decode_image_bytes,
    find_aapt_binary,
    normalize_launcher_icon,
)

_RE_APP_ICON = re.compile(
    r"application-icon-(\d+):(?:'([^']+)'|\"([^\"]+)\")",
    re.IGNORECASE,
)
_RE_ADAPTIVE_FG = re.compile(
    r"<foreground[^>]+drawable\s*=\s*\"@?(?:mipmap|drawable)/([^\"]+)\"",
    re.IGNORECASE,
)
_RE_ADAPTIVE_BG = re.compile(
    r"<background[^>]+drawable\s*=\s*\"@?(?:mipmap|drawable)/([^\"]+)\"",
    re.IGNORECASE,
)
_RE_DRAWABLE_REF = re.compile(r"@(?:mipmap|drawable)/([A-Za-z0-9_.]+)")


def aapt_dump_badging(apk_path: str, aapt: Optional[str] = None) -> str:
    tool = aapt or find_aapt_binary()
    if not tool:
        return ""
    try:
        result = subprocess.run(
            [tool, "dump", "badging", apk_path],
            capture_output=True,
            timeout=18,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
        )
        return (result.stdout or b"").decode("utf-8", errors="replace")
    except Exception as exc:
        logging.debug(f"aapt badging {apk_path}: {exc}")
        return ""


def parse_application_icon_paths(badging: str) -> list[tuple[int, str]]:
    """Mọi application-icon-* sắp dpi giảm dần (ưu tiên độ phân giải cao)."""
    found: list[tuple[int, str]] = []
    for m in _RE_APP_ICON.finditer(badging or ""):
        try:
            dpi = int(m.group(1))
        except ValueError:
            dpi = 0
        path = (m.group(2) or m.group(3) or "").strip()
        if path:
            found.append((dpi, path))
    found.sort(key=lambda x: x[0], reverse=True)
    return found


def parse_adaptive_xml_layer_refs(xml_data: bytes) -> tuple[Optional[str], Optional[str]]:
    """Tên resource (không có @mipmap/) của foreground và background."""
    text = xml_data.decode("utf-8", errors="ignore")
    fg_m = _RE_ADAPTIVE_FG.search(text)
    bg_m = _RE_ADAPTIVE_BG.search(text)
    fg = fg_m.group(1) if fg_m else None
    bg = bg_m.group(1) if bg_m else None
    if not fg:
        refs = _RE_DRAWABLE_REF.findall(text)
        if len(refs) >= 2:
            fg, bg = refs[0], refs[1]
        elif len(refs) == 1:
            fg = refs[0]
    return fg, bg


def find_resource_entry(zip_names: list[str], resource_base: str) -> Optional[str]:
    """Tìm res/.../resource_base.png|webp tốt nhất trong APK."""
    if not resource_base:
        return None
    base = resource_base.split("/")[-1]
    if base.endswith((".png", ".webp")):
        base = base.rsplit(".", 1)[0]
    best: Optional[tuple[int, str]] = None
    for name in zip_names:
        lower = name.lower()
        if not lower.endswith((".png", ".webp")):
            continue
        if base not in lower:
            continue
        if "ic_launcher" in lower or base in lower:
            score = 0
            for key, w in (
                ("xxxhdpi", 50),
                ("xxhdpi", 40),
                ("xhdpi", 30),
                ("hdpi", 20),
                ("mdpi", 10),
                ("foreground", 15),
                ("background", 5),
            ):
                if key in lower:
                    score += w
            if "round" in lower and "foreground" not in lower:
                score -= 3
            if best is None or score > best[0]:
                best = (score, name)
    return best[1] if best else None


def merge_adaptive_layers(
    foreground: Image.Image,
    background: Optional[Image.Image],
) -> Image.Image:
    fg = foreground.convert("RGBA")
    if background is None:
        return fg
    bg = background.convert("RGBA")
    if bg.size != fg.size:
        bg = bg.resize(fg.size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", fg.size, (0, 0, 0, 0))
    canvas.paste(bg, (0, 0))
    canvas.alpha_composite(fg)
    return canvas


def extract_icon_entry(
    entry_path: str,
    read_bytes: Callable[[str], Optional[bytes]],
    zip_names: list[str],
) -> Optional[Image.Image]:
    """
    Trích một entry từ APK (local zip hoặc device unzip -p).
    entry_path: đường dẫn trong APK từ aapt (res/mipmap-xxx/ic_launcher.xml hoặc .png).
    """
    if not entry_path:
        return None

    if entry_path.lower().endswith(".xml"):
        xml_raw = read_bytes(entry_path)
        if not xml_raw:
            return None
        fg_ref, bg_ref = parse_adaptive_xml_layer_refs(xml_raw)
        fg_entry = find_resource_entry(zip_names, fg_ref) if fg_ref else None
        bg_entry = find_resource_entry(zip_names, bg_ref) if bg_ref else None

        fg_img = bg_img = None
        if fg_entry:
            fg_img = decode_image_bytes(read_bytes(fg_entry) or b"")
        if bg_entry:
            bg_img = decode_image_bytes(read_bytes(bg_entry) or b"")

        if fg_img:
            return merge_adaptive_layers(fg_img, bg_img)

        merged = composite_adaptive(zip_names, read_bytes)
        if merged:
            return merged
        return None

    raw = read_bytes(entry_path)
    return decode_image_bytes(raw or b"")


def _fallback_launcher_from_names(
    zip_names: list[str],
    read_bytes: Callable[[str], Optional[bytes]],
) -> Optional[Image.Image]:
    merged = composite_adaptive(zip_names, read_bytes)
    if merged:
        return merged
    candidates = collect_icon_candidates(zip_names)
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    for _, entry in candidates[:12]:
        if entry.lower().endswith(".xml"):
            img = extract_icon_entry(entry, read_bytes, zip_names)
            if img:
                return img
            continue
        img = decode_image_bytes(read_bytes(entry) or b"")
        if img:
            return img
    return None


def extract_best_icon_from_apk(
    apk_path: str,
    aapt: Optional[str] = None,
) -> Optional[Image.Image]:
    """
    Pipeline chính: aapt badging → application-icon (PNG hoặc adaptive XML merge).
  """
    badging = aapt_dump_badging(apk_path, aapt)
    icon_paths = parse_application_icon_paths(badging)

    try:
        with zipfile.ZipFile(apk_path, "r") as zf:
            names = zf.namelist()

            def read_bytes(entry: str) -> Optional[bytes]:
                try:
                    return zf.read(entry)
                except KeyError:
                    return None
                except Exception as exc:
                    logging.debug(f"zip read {entry}: {exc}")
                    return None

            for _dpi, entry in icon_paths:
                img = extract_icon_entry(entry, read_bytes, names)
                if img:
                    return normalize_launcher_icon(img, max(img.size[0], img.size[1], 192))

            img = _fallback_launcher_from_names(names, read_bytes)
            if img:
                return normalize_launcher_icon(img, max(img.size[0], img.size[1], 192))
    except zipfile.BadZipFile as exc:
        logging.debug(f"bad apk zip {apk_path}: {exc}")
    except Exception as exc:
        logging.debug(f"extract_best_icon_from_apk {apk_path}: {exc}")
    return None
