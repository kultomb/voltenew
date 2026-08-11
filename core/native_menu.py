"""
Menu ngữ cảnh gắn cửa sổ chính (tk.Menu) — không tạo CTkToplevel riêng.
"""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, Optional

from core.ui_theme import UI

MenuItem = dict[str, Any]


class NativeMenu:
    """Popup menu hệ thống — cùng format item với PremiumMenu."""

    @staticmethod
    def popup(parent: tk.Misc, x: int, y: int, items: list[MenuItem]) -> None:
        root = parent.winfo_toplevel()
        menu = tk.Menu(root, tearoff=0)
        UI.style_context_menu(menu)
        NativeMenu._fill(menu, items)
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    @staticmethod
    def _fill(menu: tk.Menu, items: list[MenuItem]) -> None:
        for spec in items:
            if spec.get("type") == "separator":
                menu.add_separator()
                continue
            icon = spec.get("icon", "")
            label = spec.get("label", "")
            text = f"{icon}  {label}".strip() if icon else label
            enabled = spec.get("enabled", True)
            state = tk.NORMAL if enabled else tk.DISABLED
            submenu = spec.get("submenu")
            if submenu:
                child = tk.Menu(menu, tearoff=0)
                UI.style_context_menu(child)
                NativeMenu._fill(child, submenu)
                menu.add_cascade(label=text, menu=child, state=state)
                continue
            command: Optional[Callable[[], None]] = spec.get("command")
            menu.add_command(
                label=text,
                command=command if enabled and command else None,
                state=state,
            )
