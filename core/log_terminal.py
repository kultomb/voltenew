"""Professional log terminal with semantic line coloring."""

from __future__ import annotations

import re
from datetime import datetime

import customtkinter as ctk
import tkinter as tk

from core.ui_theme import C, LOG_TAGS, RADIUS, SPACE, get_font


class LogTerminal(ctk.CTkFrame):
    """Monospace log panel — timestamp, success, pending, error tones."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True)

        self._text = ctk.CTkTextbox(
            inner,
            font=get_font("mono"),
            fg_color=C["terminal_bg"],
            text_color=C["terminal_text"],
            corner_radius=RADIUS["md"],
            border_width=0,
            wrap="word",
            activate_scrollbars=True,
        )
        self._text.pack(fill="both", expand=True)
        self._tk = self._text._textbox
        self._configure_tags()
        self._text.configure(state="disabled")

    def _configure_tags(self) -> None:
        for name, opts in LOG_TAGS.items():
            self._tk.tag_configure(name, **opts)

    @staticmethod
    def classify(message: str) -> str:
        text = (message or "").strip()
        if text.startswith("✕"):
            return "error"
        if text.startswith("⚠"):
            return "warning"
        if text.startswith("✓"):
            return "success"
        if text.startswith("›"):
            return "pending"
        lower = text.lower()
        if re.search(r"\b(lỗi|error|thất bại|không tìm|không có|mất kết nối|failed)\b", lower):
            return "error"
        if re.search(r"\b(đã |thành công|hoàn tất|đặt dns|đã gỡ|đã thêm|đã cập nhật|đã dừng)\b", lower):
            return "success"
        if re.search(r"\b(đang |quét|tải|chờ|kiểm tra|thiết lập|reload)\b", lower):
            return "pending"
        if re.search(r"\b(cảnh báo|warning|bỏ qua)\b", lower):
            return "warning"
        if re.search(r"\b(chưa kết nối|chưa có)\b", lower):
            return "warning"
        return "info"

    def append(self, message: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        kind = self.classify(message)
        self._text.configure(state="normal")
        self._tk.insert("end", f"[{ts}] ", ("timestamp",))
        self._tk.insert("end", f"{message}\n", (kind,))
        self._tk.see("end")
        self._text.configure(state="disabled")

    def clear(self) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", tk.END)
        self._text.configure(state="disabled")

    @property
    def widget(self) -> ctk.CTkTextbox:
        """Backward compatibility for code that references log_area."""
        return self._text
