"""
Google Play Store — nguồn chính cho icon; tên app khi không có trong danh sách known.
"""

from __future__ import annotations

import io
import logging
import re
import threading
import time
from dataclasses import dataclass
from typing import Optional

try:
    import requests
    from bs4 import BeautifulSoup

    _HAS_DEPS = True
except ImportError:
    _HAS_DEPS = False

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}
_TIMEOUT = 12
_MAX_RETRIES = 2
_CACHE_TTL = 7 * 86400

_lock = threading.Lock()
_cache: dict[str, tuple[float, "PlayStoreInfo"]] = {}


@dataclass
class PlayStoreInfo:
    name: Optional[str] = None
    icon_bytes: Optional[bytes] = None


def play_store_available() -> bool:
    return _HAS_DEPS


def _package_key(package: str) -> str:
    return (package or "").strip().lower()


def _clean_name(raw: str) -> Optional[str]:
    if not raw:
        return None
    name = raw.strip()
    if not name or len(name) > 200:
        return None
    for sep in (" - ", " – ", " — "):
        if sep in name:
            name = name.split(sep)[0].strip()
    if name.lower() in ("google play", "apps on google play"):
        return None
    return name


def _upgrade_icon_url(url: str) -> str:
    if not url:
        return url
    for old in ("=w48-h48", "=w72-h72", "=w96-h96"):
        url = url.replace(old, "=w128-h128")
    return url


def _parse_html(package: str, html: str) -> PlayStoreInfo:
    soup = BeautifulSoup(html, "html.parser")
    name: Optional[str] = None

    title_tag = soup.find("title")
    if title_tag and title_tag.text:
        name = _clean_name(title_tag.text)
    if not name:
        h1 = soup.find("h1", class_=re.compile(r"Fd93Bb", re.I)) or soup.find("h1")
        if h1 and h1.text:
            name = _clean_name(h1.text.strip())

    icon_url: Optional[str] = None
    candidates = [
        soup.find("img", alt=re.compile(r"icon", re.I)),
        soup.find("img", class_=re.compile(r"T75of", re.I)),
        soup.find("meta", property="og:image"),
    ]
    for node in candidates:
        if not node:
            continue
        if node.name == "meta":
            icon_url = node.get("content")
        else:
            icon_url = node.get("src")
        if icon_url:
            break

    icon_bytes: Optional[bytes] = None
    if icon_url:
        icon_url = _upgrade_icon_url(icon_url)
        try:
            resp = requests.get(icon_url, headers=_HEADERS, timeout=_TIMEOUT)
            if resp.status_code == 200 and len(resp.content) > 64:
                icon_bytes = resp.content
        except Exception as exc:
            logging.debug(f"play store icon download {package}: {exc}")

    return PlayStoreInfo(name=name, icon_bytes=icon_bytes)


def fetch_play_store_info(package: str) -> Optional[PlayStoreInfo]:
    """Một request HTML (+ tải icon). Trả None nếu không có requests/bs4 hoặc lỗi mạng."""
    if not _HAS_DEPS or not package:
        return None

    key = _package_key(package)
    now = time.time()
    with _lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < _CACHE_TTL:
            return hit[1]

    url = f"https://play.google.com/store/apps/details?id={package}"
    html = ""
    for attempt in range(_MAX_RETRIES):
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
            if resp.status_code == 200:
                html = resp.text
                break
            if resp.status_code == 404:
                return None
        except Exception as exc:
            logging.debug(f"play store html {package} attempt {attempt}: {exc}")
            if attempt + 1 < _MAX_RETRIES:
                time.sleep(0.8)

    if not html or "not found" in html.lower()[:2000]:
        return None

    info = _parse_html(package, html)
    if not info.name and not info.icon_bytes:
        return None

    with _lock:
        _cache[key] = (now, info)
    return info


def fetch_play_store_label(package: str) -> Optional[str]:
    info = fetch_play_store_info(package)
    return info.name if info else None


def fetch_play_store_icon_image(package: str):
    """PIL RGBA hoặc None."""
    from PIL import Image

    info = fetch_play_store_info(package)
    if not info or not info.icon_bytes:
        return None
    try:
        return Image.open(io.BytesIO(info.icon_bytes)).convert("RGBA")
    except Exception as exc:
        logging.debug(f"play store icon decode {package}: {exc}")
        return None
