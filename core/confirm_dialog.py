"""
Hộp xác nhận / thông báo theo theme app — panel trong cửa sổ chính.
"""

from __future__ import annotations

import customtkinter as ctk

from core.ui_theme import C, UI, SPACE, get_font
from core.window_utils import show_overlay_panel


def ask_confirm(
    parent: ctk.Misc,
    title: str,
    message: str,
    *,
    confirm_text: str = "Đồng ý",
    cancel_text: str = "Hủy",
    danger: bool = False,
) -> bool:
    result = {"ok": False}

    def _build(inner: ctk.CTkFrame, close: callable) -> None:
        UI.label(inner, title, variant="heading").pack(anchor="w", pady=(0, SPACE["2"]))
        ctk.CTkLabel(
            inner,
            text=message,
            font=get_font("body"),
            text_color=C["text_secondary"],
            justify="left",
            wraplength=400,
            anchor="w",
        ).pack(anchor="w", fill="x", pady=(0, SPACE["4"]))

        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(fill="x")

        def _cancel() -> None:
            result["ok"] = False
            close()

        def _ok() -> None:
            result["ok"] = True
            close()

        UI.btn(btns, cancel_text, _cancel, variant="ghost", width=100, height=36).pack(
            side="right", padx=(SPACE["2"], 0)
        )
        UI.btn(
            btns,
            confirm_text,
            _ok,
            variant="danger" if danger else "primary",
            width=100,
            height=36,
        ).pack(side="right")

        inner.bind("<Return>", lambda _e: _ok(), add="+")

    show_overlay_panel(parent, _build, max_width=440)
    return bool(result["ok"])


_NOTICE_STYLES = {
    "info": {"btn": "primary"},
    "success": {"btn": "primary"},
    "warning": {"btn": "primary"},
    "error": {"btn": "danger"},
}


def show_notice(
    parent: ctk.Misc,
    title: str,
    message: str,
    *,
    kind: str = "info",
    detail: str = "",
) -> None:
    """Thông báo theo theme app — panel trong cửa sổ chính."""
    style = _NOTICE_STYLES.get(kind, _NOTICE_STYLES["info"])

    def _build(inner: ctk.CTkFrame, close: callable) -> None:
        UI.label(inner, title, variant="heading").pack(anchor="w", pady=(0, SPACE["2"]))
        ctk.CTkLabel(
            inner,
            text=message,
            font=get_font("body"),
            text_color=C["text_secondary"],
            justify="left",
            wraplength=400,
            anchor="w",
        ).pack(anchor="w", fill="x", pady=(0, SPACE["3"]))

        if detail:
            box = UI.textbox(inner, height=min(160, 48 + detail.count("\n") * 18), mono=True)
            box.pack(fill="x", pady=(0, SPACE["4"]))
            box.insert("1.0", detail.strip())
            box.configure(state="disabled")

        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(fill="x")
        UI.btn(btns, "Đóng", close, variant=style["btn"], width=108, height=36).pack(side="right")
        inner.bind("<Return>", lambda _e: close(), add="+")

    show_overlay_panel(parent, _build, max_width=440)
