"""
Phiên bản ứng dụng — đọc từ file sinh khi build (core/_build_version.py).
"""

from __future__ import annotations

try:
    from core._build_version import (  # type: ignore
        VERSION,
        VERSION_DISPLAY,
        FOOTER_TAGLINE,
    )
except ImportError:
    VERSION = "1.0.0"
    VERSION_DISPLAY = f"v{VERSION}"
    FOOTER_TAGLINE = (
        f"HBG AdBlocker {VERSION_DISPLAY}\n"
        "Xóa quảng cáo · Dọn app rác · Tối ưu thiết bị"
    )

APP_VERSION = VERSION
APP_VERSION_LABEL = VERSION_DISPLAY
