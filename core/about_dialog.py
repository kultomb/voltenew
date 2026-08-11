"""
Hộp thoại thông tin tác giả, phiên bản và ủng hộ.
"""

from __future__ import annotations

import webbrowser

import customtkinter as ctk

from core.ui_theme import C, RADIUS, UI, SPACE, get_font
from core.version import APP_VERSION, VERSION_DISPLAY
from core.window_utils import show_overlay_panel

# Chỉnh link ủng hộ tại đây (YouTube, Momo, PayPal, …)
AUTHOR_NAME = "Hà BG"
AUTHOR_TAGLINE = "HBG AdBlocker · Xóa quảng cáo · Dọn rác"
DONATE_URL = "https://www.youtube.com/@habg68"
DONATE_BUTTON_TEXT = "Ủng hộ tác giả"
COPYRIGHT = "Copyright © 2026 by Hà BG"


def show_about_dialog(parent: ctk.Misc) -> None:
    def _build(inner: ctk.CTkFrame, close: callable) -> None:
        UI.label(inner, "Thông tin", variant="heading").pack(anchor="w", pady=(0, SPACE["3"]))

        hero = ctk.CTkFrame(inner, fg_color=C["bg_inset"], corner_radius=RADIUS["md"])
        hero.pack(fill="x", pady=(0, SPACE["3"]))
        hero_inner = ctk.CTkFrame(hero, fg_color="transparent")
        hero_inner.pack(fill="x", padx=SPACE["4"], pady=SPACE["4"])
        UI.label(hero_inner, "HBG AdBlocker", variant="title").pack(anchor="w")
        UI.muted(hero_inner, AUTHOR_TAGLINE).pack(anchor="w", pady=(SPACE["1"], 0))
        ctk.CTkLabel(
            hero_inner,
            text=VERSION_DISPLAY,
            font=get_font("stat_sm"),
            text_color=C["accent_muted"],
            anchor="w",
        ).pack(anchor="w", pady=(SPACE["2"], 0))

        info_lines = (
            f"Tác giả: {AUTHOR_NAME}\n"
            f"Phiên bản: {APP_VERSION}\n"
            f"{COPYRIGHT}\n\n"
            "Ứng dụng quản lý Android qua ADB: xóa quảng cáo, gỡ app rác, "
            "tối ưu launcher và quản lý ứng dụng."
        )
        ctk.CTkLabel(
            inner,
            text=info_lines,
            font=get_font("body"),
            text_color=C["text_secondary"],
            justify="left",
            wraplength=420,
            anchor="w",
        ).pack(anchor="w", fill="x", pady=(0, SPACE["4"]))

        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(fill="x")
        UI.btn(btns, "Đóng", close, variant="ghost", width=100, height=38).pack(side="right")
        UI.btn(
            btns,
            f"♥ {DONATE_BUTTON_TEXT}",
            lambda: webbrowser.open(DONATE_URL),
            variant="primary",
            width=168,
            height=38,
        ).pack(side="right", padx=(0, SPACE["2"]))

        inner.bind("<Return>", lambda _e: close(), add="+")
        inner.bind("<Escape>", lambda _e: close(), add="+")

    show_overlay_panel(parent, _build, max_width=480)
