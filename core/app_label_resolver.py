"""
Android application label resolution — cache-first, aapt/APK pull, dumpsys last resort.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shlex
import subprocess
import platform
import threading
import time
from typing import Callable, Optional

from core.icon_extractor import find_aapt_binary

_RE_AAPT_LABEL = re.compile(
    r"application-label(?:-(?P<locale>[a-zA-Z0-9_-]+))?:(?:'(?P<q1>[^']*)'|\"(?P<q2>[^\"]*)\")"
)
_RE_AAPT_VERSION = re.compile(r"versionCode='(\d+)'")
_RE_DUMPSYS_Q = re.compile(r"application-label(?:-(?P<locale>[\w-]+))?='([^']*)'")
_RE_DUMPSYS_DQ = re.compile(r'application-label(?:-(?P<locale>[\w-]+))?:"([^"]*)"')
_RE_DUMPSYS_BARE = re.compile(r"application-label(?:-(?P<locale>[\w-]+))?=([^\s\n\r]+)")
_RE_NONLOCALIZED = re.compile(r"nonLocalizedLabel=([^\n\r]+)")
_RE_ANDROID_LABEL = re.compile(r'android:label="([^"]+)"')
_RE_APP_LABEL_LINE = re.compile(r"ApplicationLabel:\s*([^\n\r]+)", re.I)

_LOCALE_PRIORITY = ("vi", "en", "default", "en-US", "en-us")

# App phổ biến — package chính xác.
_KNOWN_APP_LABELS: dict[str, str] = {
    "com.ss.android.ugc.trill": "TikTok",
    "com.zhiliaoapp.musically": "TikTok",
    "com.zhiliaoapp.musically.go": "TikTok",
    "com.tiktok.android": "TikTok",
    "com.ss.android.ugc.aweme": "Douyin",
    "com.facebook.katana": "Facebook",
    "com.facebook.lite": "Facebook Lite",
    "com.facebook.orca": "Messenger",
    "com.instagram.android": "Instagram",
    "com.whatsapp": "WhatsApp",
    "com.google.android.youtube": "YouTube",
    "com.android.vending": "Google Play",
    "com.google.android.gm": "Gmail",
    "com.google.android.apps.maps": "Google Maps",
    "com.google.android.apps.youtube.music": "YouTube Music",
    "com.google.android.googlequicksearchbox": "Google",
    "com.google.android.apps.photos": "Google Photos",
    "com.google.android.gms": "Google Play Services",
    "com.shopee.vn": "Shopee",
    "com.android.chrome": "Chrome",
    "com.openai.chatgpt": "ChatGPT",
    "com.openai.chat": "ChatGPT",
    "com.openai.chatgpt.android": "ChatGPT",
    "ai.x.grok": "Grok",
    "com.xai.grok": "Grok",
    "com.google.android.apps.bard": "Gemini",
    "com.google.android.apps.genai": "Gemini",
    "com.anthropic.claude": "Claude",
    "com.deepseek.chat": "DeepSeek",
    "com.microsoft.copilot": "Copilot",
    "com.spotify.music": "Spotify",
    "com.zing.zalo": "Zalo",
    "com.viber.voip": "Viber",
    "com.telegram.messenger": "Telegram",
    "org.telegram.messenger": "Telegram",
    "com.twitter.android": "X",
    "com.discord": "Discord",
    "com.netflix.mediaclient": "Netflix",
    "com.grabtaxi.passenger": "Grab",
    "com.gojek.app": "Gojek",
    "com.mservice.momotransfer": "MoMo",
    "com.viettel.viettelpay": "Viettel Money",
}

# Gợi ý trong package id (app AI / fintech hay đổi id).
_PACKAGE_HINT_LABELS: tuple[tuple[str, str], ...] = (
    ("openai.chatgpt", "ChatGPT"),
    ("openai.chat", "ChatGPT"),
    ("chatgpt", "ChatGPT"),
    ("xai.grok", "Grok"),
    (".grok", "Grok"),
    ("anthropic.claude", "Claude"),
    ("deepseek", "DeepSeek"),
    ("copilot", "Copilot"),
    ("gemini", "Gemini"),
    ("bard", "Gemini"),
    ("musically", "TikTok"),
    ("tiktok", "TikTok"),
    ("instagram", "Instagram"),
    ("whatsapp", "WhatsApp"),
    ("facebook.katana", "Facebook"),
    ("facebook.orca", "Messenger"),
)

# dumpsys package rất nặng — chỉ dùng khi mọi cách nhanh đều thất bại.
_ALLOW_DUMPSYS_FALLBACK = False
_DUMPSYS_TIMEOUT = 8


def _clean_label(raw: str) -> Optional[str]:
    if not raw:
        return None
    val = raw.strip().strip("'\"")
    if not val or val.startswith("0x") or val.startswith("@") or "{" in val or len(val) > 200:
        return None
    if val.lower() in ("null", "none", "undefined"):
        return None
    return val


def _pick_locale_label(candidates: dict[str, str]) -> Optional[str]:
    if not candidates:
        return None
    for key in _LOCALE_PRIORITY:
        if key in candidates and candidates[key]:
            return candidates[key]
    for val in candidates.values():
        if val:
            return val
    return None


def parse_aapt_badging_labels(text: str) -> Optional[str]:
    if not text:
        return None
    found: dict[str, str] = {}
    for m in _RE_AAPT_LABEL.finditer(text):
        loc = (m.group("locale") or "default").lower()
        raw = m.group("q1") if m.group("q1") is not None else m.group("q2")
        label = _clean_label(raw or "")
        if label:
            found[loc] = label
    return _pick_locale_label(found)


def parse_dumpsys_package_labels(text: str) -> Optional[str]:
    if not text:
        return None
    found: dict[str, str] = {}

    for m in _RE_DUMPSYS_Q.finditer(text):
        loc = (m.group("locale") or "default").lower()
        label = _clean_label(m.group(2))
        if label:
            found[loc] = label
    for m in _RE_DUMPSYS_DQ.finditer(text):
        loc = (m.group("locale") or "default").lower()
        label = _clean_label(m.group(2))
        if label:
            found[loc] = label
    for m in _RE_DUMPSYS_BARE.finditer(text):
        loc = (m.group("locale") or "default").lower()
        label = _clean_label(m.group(2))
        if label:
            found[loc] = label

    picked = _pick_locale_label(found)
    if picked:
        return picked

    for pat in (_RE_NONLOCALIZED, _RE_ANDROID_LABEL, _RE_APP_LABEL_LINE):
        m = pat.search(text)
        if m:
            label = _clean_label(m.group(1))
            if label:
                return label
    return None


def package_suffix_label(package: str) -> str:
    """
    Tên tạm từ segment cuối package.
    vn.com.hdsaison.hpo → HPO; com.foo.myapp → Myapp.
    """
    if not package:
        return "?"
    raw = package.split(".")[-1].strip()
    if not raw:
        return package
    token = raw.replace("_", "").replace("-", "")
    if token.isalnum() and len(token) <= 6:
        return token.upper()
    if raw.isalpha() and raw.isupper() and len(raw) <= 8:
        return raw
    return raw.replace("_", " ").replace("-", " ").strip().title()


def lookup_known_label(package: str) -> Optional[str]:
    if not package:
        return None
    exact = _KNOWN_APP_LABELS.get(package)
    if exact:
        return exact
    pl = package.lower()
    for hint, name in _PACKAGE_HINT_LABELS:
        if hint in pl:
            return name
    return None


def is_suffix_fallback(package: str, label: str) -> bool:
    """True nếu label chỉ là phần cuối package kiểu cũ (katana, chat…)."""
    if not package or not label:
        return False
    suffix = package.split(".")[-1].replace("_", " ").replace("-", " ").strip()
    if not suffix:
        return False
    gen = suffix.title()
    norm_label = label.strip()
    if norm_label.lower() == suffix.lower():
        return True
    if norm_label == gen:
        return True
    if norm_label.lower() == package.lower():
        return True
    return False


def is_provisional_label(package: str, label: str) -> bool:
    """Tên tạm (suffix package hoặc fallback cũ) — vẫn nên enrich Play Store."""
    if is_suffix_fallback(package, label):
        return True
    if not label or label in ("…", "...", "—"):
        return True
    return label.strip() == package_suffix_label(package)


class AppLabelResolver:
    """Resolve launcher-style app names; JSON cache + pull APK once for aapt."""

    def __init__(
        self,
        base_dir: str,
        *,
        run_adb: Callable,
        serial_getter: Callable[[], Optional[str]],
        get_apk_path: Callable[[str, Optional[str]], Optional[str]],
    ):
        self.cache_dir = os.path.join(base_dir, "cache", "apps")
        self.pull_dir = os.path.join(base_dir, "cache", "apk_pulls")
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.pull_dir, exist_ok=True)
        self._run = run_adb
        self._serial = serial_getter
        self._get_apk_path = get_apk_path
        self._aapt_local: Optional[str] = None
        self._adb_lock = threading.Lock()
        self._memory: dict[str, str] = {}
        self._warm_memory_from_disk()
        for pkg, lbl in _KNOWN_APP_LABELS.items():
            self._memory.setdefault(pkg, lbl)

    def _cache_file(self, package: str) -> str:
        safe = package.replace("/", "_").replace("\\", "_")
        return os.path.join(self.cache_dir, f"{safe}.json")

    def _pull_apk_path(self, package: str) -> str:
        safe = package.replace("/", "_").replace("\\", "_")
        return os.path.join(self.pull_dir, f"{safe}.apk")

    def _warm_memory_from_disk(self) -> None:
        try:
            for name in os.listdir(self.cache_dir):
                if not name.endswith(".json"):
                    continue
                path = os.path.join(self.cache_dir, name)
                try:
                    with open(path, encoding="utf-8") as f:
                        data = json.load(f)
                    pkg = str(data.get("package") or name[:-5])
                    label = _clean_label(str(data.get("label", "")))
                    if label and not is_suffix_fallback(pkg, label):
                        self._memory[pkg] = label
                except Exception:
                    continue
        except Exception as exc:
            logging.debug(f"warm label cache: {exc}")

    def bulk_apply_to(self, target: dict[str, str]) -> int:
        """Đổ cache RAM/disk vào label_cache của DeviceManager."""
        n = 0
        for pkg, label in self._memory.items():
            target[pkg] = label
            n += 1
        return n

    def load_cached_label(self, package: str) -> Optional[str]:
        if package in self._memory:
            return self._memory[package]
        path = self._cache_file(package)
        if not os.path.isfile(path):
            return None
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            label = _clean_label(str(data.get("label", "")))
            if label and not is_suffix_fallback(package, label):
                self._memory[package] = label
                return label
        except Exception as exc:
            logging.debug(f"load label cache {package}: {exc}")
        return None

    def save_cached_label(self, package: str, label: str, **extra) -> None:
        label = _clean_label(label)
        if not label:
            return
        self._memory[package] = label
        payload = {"package": package, "label": label, "ts": int(time.time()), **extra}
        try:
            with open(self._cache_file(package), "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=0)
        except Exception as exc:
            logging.debug(f"save label cache {package}: {exc}")

    def _local_aapt(self) -> Optional[str]:
        if self._aapt_local is None:
            self._aapt_local = find_aapt_binary() or ""
        return self._aapt_local or None

    def _adb_shell(self, *args: str, timeout: int = 6) -> tuple[str, str, int]:
        serial = self._serial()
        if not serial:
            return "", "no device", -1
        with self._adb_lock:
            return self._run(["-s", serial, "shell", *args], timeout=timeout)

    def _remote_apk_joined(self, package: str, hint: Optional[str]) -> Optional[str]:
        remote = hint or self._get_apk_path(package, hint)
        if remote and remote.startswith("/"):
            return remote
        return None

    def _apk_segments(self, package: str, hint: Optional[str]) -> list[str]:
        remote = self._remote_apk_joined(package, hint)
        if not remote:
            return []
        segs = [s.strip() for s in remote.split(":") if s.strip().startswith("/")]
        segs.sort(key=lambda p: (0 if "base.apk" in p else 1, len(p)))
        return segs

    def _base_apk(self, package: str, hint: Optional[str]) -> Optional[str]:
        for seg in self._apk_segments(package, hint):
            if "base.apk" in seg:
                return seg
        segs = self._apk_segments(package, hint)
        return segs[0] if segs else None

    def _try_device_aapt_segment_label(self, apk_path: str) -> Optional[str]:
        if not apk_path:
            return None
        qapk = shlex.quote(apk_path)
        for aapt in ("/system/bin/aapt2", "/system/bin/aapt", "aapt2", "aapt"):
            out, _, code = self._adb_shell(aapt, "dump", "badging", qapk, timeout=14)
            if code == 0 and out and "application-label" in out:
                label = parse_aapt_badging_labels(out)
                if label:
                    return label
        return None

    def _try_all_segments_label(self, package: str, hint: Optional[str]) -> Optional[str]:
        for seg in self._apk_segments(package, hint):
            label = self._try_device_aapt_segment_label(seg)
            if label and not is_suffix_fallback(package, label):
                return label
        return None

    def _try_dumpsys(self, package: str) -> Optional[str]:
        if not _ALLOW_DUMPSYS_FALLBACK:
            return None
        qpkg = shlex.quote(package)
        out, _, code = self._adb_shell(
            "sh",
            "-c",
            f"dumpsys package {qpkg} 2>/dev/null | grep -E "
            f"'application-label|nonLocalizedLabel|android:label|ApplicationLabel' | head -20",
            timeout=_DUMPSYS_TIMEOUT,
        )
        if code == 0 and out:
            label = parse_dumpsys_package_labels(out)
            if label:
                return label
        return None

    def _try_device_aapt(self, apk_path: str) -> Optional[str]:
        if not apk_path:
            return None
        qapk = shlex.quote(apk_path)
        for aapt in ("/system/bin/aapt2", "/system/bin/aapt", "aapt2", "aapt"):
            out, _, code = self._adb_shell(aapt, "dump", "badging", qapk, timeout=12)
            if code == 0 and out and "application-label" in out:
                label = parse_aapt_badging_labels(out)
                if label:
                    return label
        return None

    def _ensure_local_apk(self, package: str, remote_apk: str) -> Optional[str]:
        local = self._pull_apk_path(package)
        if os.path.isfile(local) and os.path.getsize(local) > 64:
            return local
        serial = self._serial()
        if not serial:
            return None
        with self._adb_lock:
            _, _, code = self._run(
                ["-s", serial, "pull", remote_apk, local],
                timeout=45,
            )
        if code == 0 and os.path.isfile(local) and os.path.getsize(local) > 64:
            return local
        return None

    def _try_local_aapt(self, package: str, remote_apk: str) -> Optional[str]:
        aapt = self._local_aapt()
        if not aapt:
            return None
        segments = self._apk_segments(package, remote_apk)
        if not segments:
            seg = remote_apk if remote_apk and remote_apk.startswith("/") else None
            segments = [seg] if seg else []
        for seg in sorted(segments, key=len)[:4]:
            local = self._ensure_local_apk(package, seg)
            if not local:
                continue
            try:
                result = subprocess.run(
                    [aapt, "dump", "badging", local],
                    capture_output=True,
                    timeout=15,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
                )
                text = (result.stdout or b"").decode("utf-8", errors="replace")
                label = parse_aapt_badging_labels(text)
                if label:
                    return label
            except Exception as exc:
                logging.debug(f"local aapt label {package} {seg}: {exc}")
        return None

    def _try_androguard(self, local_apk: str) -> Optional[str]:
        try:
            from androguard.core.bytecodes.apk import APK  # type: ignore
        except ImportError:
            return None
        try:
            apk = APK(local_apk)
            label = apk.get_app_name()
            return _clean_label(label or "")
        except Exception as exc:
            logging.debug(f"androguard label: {exc}")
        return None

    def resolve(self, package: str, apk_hint: Optional[str] = None) -> Optional[str]:
        """
        Thứ tự nhanh: cache → known/hint → Play Store → segment cuối package (HPO…).
        Không dùng aapt/ADB cho tên.
        """
        cached = self.load_cached_label(package)
        if cached and not is_provisional_label(package, cached):
            return cached

        known = lookup_known_label(package)
        if known:
            self.save_cached_label(package, known, source="known")
            return known

        label = self._try_play_store_label(package)
        if label:
            return label

        fallback = package_suffix_label(package)
        self.save_cached_label(package, fallback, source="package_suffix")
        return fallback

    def _try_play_store_label(self, package: str) -> Optional[str]:
        try:
            from core.play_store_fallback import fetch_play_store_label

            label = fetch_play_store_label(package)
            label = _clean_label(label or "")
            if label and not is_suffix_fallback(package, label):
                self.save_cached_label(package, label, source="play_store")
                return label
        except Exception as exc:
            logging.debug(f"play store label {package}: {exc}")
        return None
