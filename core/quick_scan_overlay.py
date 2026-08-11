"""
Overlay quét nhanh — vòng tiến trình + trạng thái (trong app).
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from core.circular_progress import CircularProgress
from core.ui_theme import C, RADIUS, SPACE, UI, get_font
from core.window_utils import _OVERLAYS


class QuickScanOverlay:
    """Modal quét — cập nhật tiến trình realtime, không che đen toàn màn hình."""

    def __init__(self, parent: ctk.Misc):
        self._parent = parent
        self._root = parent.winfo_toplevel()
        self._closed = False
        self._host: ctk.CTkFrame | None = None
        self._ring: CircularProgress | None = None
        self._status: ctk.CTkLabel | None = None
        self._sub: ctk.CTkLabel | None = None
        self._entry: dict | None = None

    def open(self) -> None:
        if self._host is not None:
            return

        self._host = ctk.CTkFrame(self._root, fg_color="transparent")
        self._host.place(relx=0.5, rely=0.5, anchor="center")

        self._entry = {"layer": self._host, "owner": self._root, "done": tk.BooleanVar(master=self._root)}
        _OVERLAYS.append(self._entry)

        stack = ctk.CTkFrame(self._host, fg_color="transparent")
        stack.pack()

        panel = UI.overlay_panel(stack, padding=SPACE["6"], width=360)
        panel.pack()
        inner = UI.card_inner(panel)

        UI.label(inner, "Quét nhanh", variant="heading").pack(pady=(0, SPACE["1"]))
        UI.muted(inner, "Đang phân tích ứng dụng trên thiết bị…").pack(pady=(0, SPACE["4"]))

        ring_wrap = ctk.CTkFrame(inner, fg_color="transparent")
        ring_wrap.pack(pady=(0, SPACE["4"]))
        self._ring = CircularProgress(ring_wrap, size=140, line_width=8)
        self._ring.pack()
        self._ring.start_animation()

        self._status = ctk.CTkLabel(
            inner,
            text="Chuẩn bị…",
            font=get_font("body"),
            text_color=C["text_primary"],
            wraplength=300,
        )
        self._status.pack(pady=(0, SPACE["1"]))

        self._sub = ctk.CTkLabel(
            inner,
            text="",
            font=get_font("caption"),
            text_color=C["text_tertiary"],
            wraplength=300,
        )
        self._sub.pack()

        try:
            self._host.lift()
            self._host.tkraise()
        except Exception:
            pass
        self._root.update_idletasks()

    def update(self, fraction: float, status: str, *, detail: str = "") -> None:
        if self._closed or self._ring is None:
            return
        self._ring.set_progress(fraction)
        if self._status is not None:
            self._status.configure(text=status)
        if self._sub is not None:
            self._sub.configure(text=detail[:80] if detail else "")

    def flash_complete(self, message: str = "Hoàn tất") -> None:
        if self._ring is not None:
            self._ring.set_complete()
        if self._status is not None:
            self._status.configure(text=message)
        if self._sub is not None:
            self._sub.configure(text="")
        if self._root.winfo_exists():
            self._root.update_idletasks()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._ring is not None:
            self._ring.stop_animation()
        if self._entry is not None:
            try:
                _OVERLAYS.remove(self._entry)
            except ValueError:
                pass
        try:
            if self._host is not None and self._host.winfo_exists():
                self._host.destroy()
        except Exception:
            pass
        self._host = None
