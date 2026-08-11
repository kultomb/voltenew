"""
Danh sách bloatware gỡ nhanh từ Dashboard (Oppo market, Zing MP3, Netflix, Lazada, …).
"""

from __future__ import annotations

# (package, tên hiển thị) — có thể nhiều package cho cùng một app (Oppo / HeyTap / bản VN)
BLOATWARE_TARGETS: list[tuple[str, str]] = [
    # ==================== 1. APPS LIÊN KẾT BÊN THỨ BA (Bị cài sẵn trên nhiều hãng) ====================
    ("com.lazada.android", "Lazada"),
    ("vn.lazada.android", "Lazada (VN)"),
    ("com.netflix.mediaclient", "Netflix"),
    ("vn.com.baomoi", "Báo Mới"),
    ("com.epi.baomoi", "Báo Mới (Epi)"),
    ("com.zing.mp3", "Zing MP3"),
    ("com.zing.zmp3", "Zing MP3 Alt"),
    ("com.facebook.system", "Facebook System App (Chạy ngầm)"),
    ("com.facebook.appmanager", "Facebook App Manager (Tự tải app)"),
    ("com.facebook.services", "Facebook Services"),

    # ==================== 2. OPPO / REALME / ONEPLUS (ColorOS / RealmeUI) ====================
    ("com.heytap.market", "Oppo App Market"),
    ("com.oppo.market", "Oppo App Market (Old)"),
    ("com.oppo.appstore", "Oppo App Store"),
    ("com.heytap.gamecenter", "Oppo Game Center"),
    ("com.oppo.gamecenter", "Oppo Game Center (Old)"),
    ("com.nearme.gamecenter", "Oppo Game Center (NearMe)"),
    ("com.heytap.browser", "Oppo Browser (Đẩy tin rác)"),
    ("com.coloros.browser", "ColorOS Browser"),
    ("com.heytap.yoli", "Oppo Yoli Video"),
    ("com.heytap.quickgame", "Oppo Quick Game"),

    # ==================== 3. XIAOMI / REDMI / POCO (MIUI / HyperOS) ====================
    ("com.xiaomi.mipicks", "Xiaomi GetApps (Market rác)"),
    ("com.miui.analytics", "Xiaomi Analytics (Theo dõi + Đẩy QC)"),
    ("com.miui.msa.global", "Xiaomi MSA (Hệ thống đẩy quảng cáo)"),
    ("com.miui.videoplayer", "Mi Video (Chuyên pop-up bẩn)"),
    ("com.miui.player", "Mi Music"),
    ("com.miui.browser", "Mi Browser"),
    ("com.xiaomi.glance.internet", "Glance (Quảng cáo màn hình khóa)"),
    ("com.mi.android.globalminusscreen", "Mi App Vault (Màn hình phụ rác)"),

    # ==================== 4. SAMSUNG (One UI) ====================
    ("com.sec.android.app.samsungapps", "Galaxy Store"),
    ("com.sec.android.app.gamelauncher", "Samsung Game Launcher"),
    ("com.samsung.android.game.gamehome", "Samsung Game Home"),
    ("com.samsung.android.app.watchmanagerstub", "Galaxy Wearable Stub"),
    ("com.samsung.android.bixby.agent", "Bixby Agent"),
    ("com.samsung.android.app.spage", "Samsung Free (Đọc báo rác)"),

    # ==================== 5. VIVO / iQOO (Funtouch OS / Origin OS) ====================
    ("com.vivo.appstore", "V-Appstore (Vivo Market)"),
    ("com.vivo.gamecube", "Vivo Game Space"),
    ("com.vivo.browser", "Vivo Browser"),
    ("com.vlife.vivo.wallpaper", "Vivo Lockscreen Wallpaper (Rác pin)"),
    ("com.vivo.globalsearch", "Vivo Global Search"),

    # ==================== 6. HUAWEI / HONOR (EMUI / Magic OS) ====================
    ("com.huawei.appmarket", "Huawei AppGallery"),
    ("com.huawei.hwid", "Huawei Mobile Services (HMS rác nếu máy có GMS)"),
    ("com.huawei.browser", "Huawei Browser"),
    ("com.huawei.magazine", "Huawei Magazine Unlock"),
    ("com.hihonor.appmarket", "Honor App Market"),
]


def bloatware_package_set() -> set[str]:
    return {pkg for pkg, _ in BLOATWARE_TARGETS}


def bloatware_label_for(package: str) -> str:
    for pkg, label in BLOATWARE_TARGETS:
        if pkg == package:
            return label
    return package


def find_installed_bloatware(installed: set[str] | list[str]) -> list[str]:
    """Package bloatware có trên máy, giữ thứ tự trong BLOATWARE_TARGETS."""
    on_device = set(installed)
    seen: set[str] = set()
    found: list[str] = []
    for pkg, _ in BLOATWARE_TARGETS:
        if pkg in on_device and pkg not in seen:
            seen.add(pkg)
            found.append(pkg)
    return found
