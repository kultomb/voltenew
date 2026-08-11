"""
Phát hiện / đổi / gỡ Launcher (HOME) qua ADB — xử lý launcher quảng cáo thay màn hình chính.
"""

from __future__ import annotations

import re
from typing import Any, Optional

_PKG_RE = re.compile(r"packageName=([a-zA-Z][a-zA-Z0-9_.]*)")
_COMPONENT_RE = re.compile(
    r"(?:name|ComponentInfo\{)([a-zA-Z][a-zA-Z0-9_.]*)/([a-zA-Z][a-zA-Z0-9_.]*)"
)

# Có intent HOME nhưng không phải launcher — ẩn khỏi danh sách UI, không dùng làm HOME thay thế
_HIDDEN_HOME_PACKAGES = frozenset({
    "com.android.settings",
})

# Launcher gốc theo hãng (package) — thứ tự ưu tiên trong từng nhóm
# Nguồn: launcher mặc định OEM phổ biến; activity lấy qua ADB khi chạy.
OEM_BRAND_LAUNCHERS: list[tuple[tuple[str, ...], tuple[str, ...]]] = [
    (("google", "pixel"), (
        "com.google.android.apps.nexuslauncher",
    )),
    (("samsung",), (
        "com.sec.android.app.launcher",
    )),
    (("xiaomi", "redmi", "poco"), (
        "com.miui.home",
        "com.miui.pocomanager",
        "com.miui.cleanmaster",
    )),
    (("oppo", "oneplus", "realme"), (
        "com.oppo.launcher",
        "com.oneplus.launcher",
        "com.coloros.launcher",
        "com.realme.launcher",
    )),
    (("vivo", "iqoo", "bbk"), (
        "com.vivo.launcher",
        "com.bbk.launcher2",
    )),
    (("sony", "xperia"), (
        "com.sonyericsson.home",
        "com.sonymobile.home",
    )),
    (("asus", "rog"), (
        "com.asus.launcher",
    )),
    (("motorola", "moto"), (
        "com.motorola.launcher3",
    )),
    (("huawei",), (
        "com.huawei.android.launcher",
    )),
    (("honor", "hihonor"), (
        "com.hihonor.android.launcher",
    )),
    (("tecno", "infinix", "itel", "transsion"), (
        "com.transsion.hilauncher",
    )),
    (("meizu",), (
        "com.meizu.flyme.launcher",
    )),
    (("lenovo",), (
        "com.lenovo.launcher",
    )),
    (("zte", "nubia", "redmagic"), (
        "com.zte.launcher",
    )),
    (("nokia", "hmd"), (
        "com.android.launcher3",
    )),
    (("nothing",), (
        "com.nothing.launcher",
    )),
]

# Danh sách phòng thủ toàn cục (khi không khớp hãng hoặc ADB thiếu activity)
ALL_OEM_LAUNCHER_PACKAGES: tuple[str, ...] = tuple(
    dict.fromkeys(
        pkg
        for _keys, pkgs in OEM_BRAND_LAUNCHERS
        for pkg in pkgs
    ).keys()
) + (
    "com.android.launcher3",
    "com.android.launcher",
)


def _device_brand_tokens(device_manager) -> set[str]:
    """Token hãng/model từ getprop để khớp OEM_BRAND_LAUNCHERS."""
    tokens: set[str] = set()
    if not device_manager.serial:
        return tokens
    for prop in (
        "ro.product.manufacturer",
        "ro.product.brand",
        "ro.product.model",
        "ro.product.device",
        "ro.product.name",
    ):
        raw = (device_manager.shell(["getprop", prop], timeout=3) or "").strip().lower()
        if not raw:
            continue
        tokens.add(raw)
        for part in re.split(r"[\s_\-./]+", raw):
            if len(part) >= 2:
                tokens.add(part)
    return tokens


def _brand_matches(tokens: set[str], keywords: tuple[str, ...]) -> bool:
    for kw in keywords:
        if kw in tokens:
            return True
        for t in tokens:
            if kw in t or t in kw:
                return True
    return False


def _looks_like_launcher_package(package: str) -> bool:
    low = package.lower()
    return any(k in low for k in ("launcher", ".home", "nexuslauncher", "hilauncher"))


def is_known_oem_launcher_package(package: str) -> bool:
    return package in ALL_OEM_LAUNCHER_PACKAGES


def _parse_home_activities(raw: str) -> dict[str, str]:
    """package -> activity chính (HOME) từ pm query-activities."""
    by_pkg: dict[str, str] = {}
    if not raw:
        return by_pkg
    for pkg, act in _COMPONENT_RE.findall(raw):
        if "launcher" in act.lower() or "home" in act.lower() or pkg not in by_pkg:
            by_pkg[pkg] = act
    return by_pkg


def list_installed_launchers(device_manager) -> list[dict[str, Any]]:
    """Liệt kê mọi app có thể làm màn hình chính."""
    if not device_manager.serial:
        return []
    out = device_manager.shell(
        [
            "pm", "query-activities",
            "-c", "android.intent.category.HOME",
            "-a", "android.intent.action.MAIN",
        ],
        timeout=12,
    )
    activities = _parse_home_activities(out)
    packages: list[str] = []
    for m in _PKG_RE.finditer(out):
        pkg = m.group(1)
        if pkg not in packages:
            packages.append(pkg)
    for pkg in activities:
        if pkg not in packages:
            packages.append(pkg)

    user_out = device_manager.shell(["pm", "list", "packages", "-3"], timeout=8)
    user_pkgs = {
        line.split(":", 1)[-1].strip()
        for line in (user_out or "").splitlines()
        if line.strip().startswith("package:")
    }

    default_pkg, _ = get_default_launcher(device_manager)
    rows = []
    for pkg in sorted(packages, key=str.lower):
        if pkg in _HIDDEN_HOME_PACKAGES:
            continue
        activity = activities.get(pkg) or resolve_home_activity(device_manager, pkg)
        is_user = pkg in user_pkgs
        rows.append({
            "package": pkg,
            "activity": activity or "",
            "is_default": pkg == default_pkg,
            "is_user": is_user,
            "is_system": not is_user,
            "is_oem_stock": not is_user and is_known_oem_launcher_package(pkg),
        })
    return rows


def get_default_launcher(device_manager) -> tuple[Optional[str], Optional[str]]:
    """Launcher HOME đang được hệ thống chọn."""
    if not device_manager.serial:
        return None, None
    out = device_manager.shell(
        [
            "cmd", "package", "resolve-activity",
            "-a", "android.intent.action.MAIN",
            "-c", "android.intent.category.HOME",
        ],
        timeout=8,
    )
    if not out:
        out = device_manager.shell(["cmd", "shortcut", "get-default-launcher"], timeout=6)
    pkg_m = _PKG_RE.search(out or "")
    comp = _COMPONENT_RE.search(out or "")
    if comp:
        return comp.group(1), comp.group(2)
    if pkg_m:
        pkg = pkg_m.group(1)
        return pkg, resolve_home_activity(device_manager, pkg)
    return None, None


def resolve_home_activity(device_manager, package: str) -> Optional[str]:
    """Activity MAIN/HOME của package (từ query hoặc dumpsys)."""
    if not device_manager.serial or not package:
        return None
    out = device_manager.shell(
        [
            "pm", "query-activities",
            "-c", "android.intent.category.HOME",
            "-a", "android.intent.action.MAIN",
        ],
        timeout=10,
    )
    for pkg, act in _COMPONENT_RE.findall(out or ""):
        if pkg == package:
            return act
    dump = device_manager.shell(["dumpsys", "package", package], timeout=8)
    if not dump:
        return None
    block = re.search(
        r"android\.intent\.category\.HOME.*?(?=android\.intent\.|$)",
        dump,
        re.DOTALL | re.IGNORECASE,
    )
    if block:
        m = _COMPONENT_RE.search(block.group(0))
        if m and m.group(1) == package:
            return m.group(2)
    m = _COMPONENT_RE.search(dump)
    if m and m.group(1) == package:
        return m.group(2)
    return None


def _resolve_oem_package(
    device_manager,
    package: str,
    *,
    exclude: set[str],
    installed: set[str],
    rows_by_pkg: dict[str, dict[str, Any]],
) -> Optional[tuple[str, str]]:
    if package in exclude or package in _HIDDEN_HOME_PACKAGES:
        return None
    if package not in installed:
        return None
    row = rows_by_pkg.get(package)
    if row and row.get("is_user"):
        return None
    act = (row or {}).get("activity") or resolve_home_activity(device_manager, package)
    if act:
        return package, act
    return None


def find_oem_home_component(
    device_manager,
    *,
    exclude: set[str] | None = None,
) -> Optional[tuple[str, str]]:
    """
    Launcher hệ thống an toàn để chuyển về trước khi gỡ launcher lạ.
    Ưu tiên: khớp hãng máy → danh sách OEM phòng thủ → quét ADB.
    """
    exclude = exclude or set()
    launchers = list_installed_launchers(device_manager)
    installed = {r["package"] for r in launchers}
    rows_by_pkg = {r["package"]: r for r in launchers}
    tokens = _device_brand_tokens(device_manager)

    def try_pkg(pkg: str) -> Optional[tuple[str, str]]:
        return _resolve_oem_package(
            device_manager, pkg,
            exclude=exclude, installed=installed, rows_by_pkg=rows_by_pkg,
        )

    # 1) Launcher gốc đúng hãng (getprop)
    for keywords, packages in OEM_BRAND_LAUNCHERS:
        if _brand_matches(tokens, keywords):
            for pkg in packages:
                hit = try_pkg(pkg)
                if hit:
                    return hit

    # 2) Phòng thủ: duyệt toàn bộ bảng OEM đã cài
    for pkg in ALL_OEM_LAUNCHER_PACKAGES:
        hit = try_pkg(pkg)
        if hit:
            return hit

    # 3) Fallback ADB: launcher hệ thống có intent HOME
    candidates: list[tuple[str, str]] = []
    for row in launchers:
        pkg = row["package"]
        if pkg in exclude or row.get("is_user") or pkg in _HIDDEN_HOME_PACKAGES:
            continue
        act = row.get("activity") or resolve_home_activity(device_manager, pkg)
        if act:
            candidates.append((pkg, act))
    for pkg, act in candidates:
        if _looks_like_launcher_package(pkg):
            return pkg, act
    return candidates[0] if candidates else None


def set_default_launcher(device_manager, package: str, activity: str) -> tuple[bool, str]:
    if not device_manager.serial:
        return False, "Chưa kết nối thiết bị"
    if not package or not activity:
        return False, "Thiếu package/activity"
    component = f"{package}/{activity}"
    out = device_manager.shell(["cmd", "package", "set-home-activity", component], timeout=10)
    err = (out or "").lower()
    if "error" in err or "exception" in err or "unknown" in err:
        return False, (out or "Không đặt được launcher mặc định")[:200]
    now_pkg, _ = get_default_launcher(device_manager)
    if now_pkg == package:
        return True, f"Đã đặt màn hình chính: {package}"
    if not out or "success" in err:
        return True, f"Đã gửi lệnh đặt HOME: {component}"
    return True, (out or component)[:200]


def disable_launcher(device_manager, package: str) -> tuple[bool, str]:
    if not device_manager.serial:
        return False, "Chưa kết nối"
    out = device_manager.shell(["pm", "disable-user", "--user", "0", package], timeout=8)
    low = (out or "").lower()
    if "disabled" in low or not out.strip():
        return True, out or "disabled"
    return False, out or "Không vô hiệu hóa được"
