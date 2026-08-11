"""
Premium floating menu — fluent dark dropdown (đặt trực tiếp trên cửa sổ chính, không lớp phủ fullscreen).
"""

from __future__ import annotations

import customtkinter as ctk
from typing import Any, Callable, Optional

from core.ui_theme import C, get_font

MenuItem = dict[str, Any]

_MENU_BG = "#141820"
_MENU_BORDER = "#2d3548"
_MENU_HOVER = "#252b3a"
_ROW_H = 40
_SUB_DELAY_MS = 140


class PremiumMenu:
    """Menu nổi trong app — không dùng lớp phủ fullscreen (tránh màn hình đen trên Windows)."""

    _active_shell: Optional[ctk.CTkFrame] = None
    _submenu_shell: Optional[ctk.CTkFrame] = None
    _outside_bind: Optional[str] = None
    _escape_bind: Optional[str] = None
    _parent_ref: Optional[ctk.Misc] = None
    _host_ref: Optional[ctk.Misc] = None
    _hover_job: Optional[str] = None
    _submenu_spec: Optional[list[MenuItem]] = None

    @classmethod
    def dismiss(cls) -> None:
        cls._cancel_hover_job()
        cls._destroy_submenu()
        host = cls._host_ref
        if host is not None:
            if cls._outside_bind:
                try:
                    host.unbind_all("<Button-1>")
                except Exception:
                    pass
            if cls._escape_bind:
                try:
                    host.unbind("<Escape>", cls._escape_bind)
                except Exception:
                    pass
        cls._outside_bind = None
        cls._escape_bind = None
        cls._parent_ref = None
        cls._host_ref = None
        if cls._active_shell is not None:
            try:
                cls._active_shell.destroy()
            except Exception:
                pass
            cls._active_shell = None

    @classmethod
    def popup(cls, parent: ctk.Misc, x: int, y: int, items: list[MenuItem], *, min_width: int = 268) -> None:
        cls.show(parent, x, y, items, min_width=min_width)

    @classmethod
    def show(
        cls,
        parent: ctk.Misc,
        x: int,
        y: int,
        items: list[MenuItem],
        *,
        min_width: int = 268,
    ) -> None:
        cls.dismiss()

        host = parent.winfo_toplevel()
        cls._host_ref = host
        cls._parent_ref = parent

        shell = ctk.CTkFrame(
            host,
            fg_color=_MENU_BG,
            corner_radius=10,
            border_width=1,
            border_color=_MENU_BORDER,
        )
        cls._active_shell = shell

        inner = ctk.CTkFrame(shell, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=5, pady=5)

        for spec in items:
            if spec.get("type") == "separator":
                sep_wrap = ctk.CTkFrame(inner, fg_color="transparent")
                sep_wrap.pack(fill="x", pady=(5, 5))
                ctk.CTkFrame(sep_wrap, height=1, fg_color=_MENU_BORDER, corner_radius=0).pack(
                    fill="x", padx=8
                )
                continue
            cls._add_item(inner, shell, host, spec, min_width)

        cls._place_shell(shell, host, x, y, min_width)
        try:
            shell.tkraise()
        except Exception:
            shell.lift()
        cls._bind_dismiss(host, shell)

    @classmethod
    def show_below_widget(
        cls,
        parent: ctk.Misc,
        widget: ctk.Misc,
        items: list[MenuItem],
        *,
        min_width: int = 268,
        offset_y: int = 6,
    ) -> None:
        widget.update_idletasks()
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height() + offset_y
        cls.show(parent, x, y, items, min_width=min_width)

    @classmethod
    def _place_shell(cls, shell: ctk.CTkFrame, host: ctk.Misc, root_x: int, root_y: int, min_width: int) -> None:
        shell.update_idletasks()
        w = max(min_width, shell.winfo_reqwidth())
        h = shell.winfo_reqheight()
        hx = root_x - host.winfo_rootx()
        hy = root_y - host.winfo_rooty()
        max_x = max(0, host.winfo_width() - w - 4)
        max_y = max(0, host.winfo_height() - h - 4)
        hx = max(4, min(hx, max_x))
        hy = max(4, min(hy, max_y))
        shell.place(x=hx, y=hy)

    @classmethod
    def _point_in_panel(cls, panel: ctk.CTkFrame, event) -> bool:
        try:
            px = panel.winfo_rootx()
            py = panel.winfo_rooty()
            pw = panel.winfo_width()
            ph = panel.winfo_height()
            return px <= event.x_root <= px + pw and py <= event.y_root <= py + ph
        except Exception:
            return False

    @classmethod
    def _bind_dismiss(cls, host: ctk.Misc, shell: ctk.CTkFrame) -> None:
        def _outside_click(event):
            if cls._active_shell is None:
                return
            for panel in (cls._active_shell, cls._submenu_shell):
                if panel is not None and cls._point_in_panel(panel, event):
                    return
            cls.dismiss()

        def _escape(_e=None):
            cls.dismiss()

        def _arm_outside():
            if cls._active_shell is not None:
                cls._outside_bind = host.bind_all("<Button-1>", _outside_click, add="+")

        host.after(80, _arm_outside)
        cls._escape_bind = host.bind("<Escape>", _escape, add="+")

    @classmethod
    def _cancel_hover_job(cls) -> None:
        host = cls._host_ref
        if cls._hover_job and host is not None:
            try:
                host.after_cancel(cls._hover_job)
            except Exception:
                pass
        cls._hover_job = None

    @classmethod
    def _destroy_submenu(cls) -> None:
        if cls._submenu_shell is not None:
            try:
                cls._submenu_shell.destroy()
            except Exception:
                pass
        cls._submenu_shell = None
        cls._submenu_spec = None

    @classmethod
    def _show_submenu(cls, anchor_row: ctk.CTkFrame, items: list[MenuItem], min_width: int) -> None:
        host = cls._host_ref
        if not items or host is None:
            return
        if cls._submenu_spec is items and cls._submenu_shell is not None:
            return
        cls._destroy_submenu()
        cls._submenu_spec = items

        sub = ctk.CTkFrame(
            host,
            fg_color=_MENU_BG,
            corner_radius=10,
            border_width=1,
            border_color=_MENU_BORDER,
        )
        cls._submenu_shell = sub
        inner = ctk.CTkFrame(sub, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=5, pady=5)

        for spec in items:
            if spec.get("type") == "separator":
                continue
            cls._add_item(inner, sub, host, spec, min_width, is_submenu=True)

        anchor_row.update_idletasks()
        sub.update_idletasks()
        ax = anchor_row.winfo_rootx() - host.winfo_rootx() + anchor_row.winfo_width() - 4
        ay = anchor_row.winfo_rooty() - host.winfo_rooty() - 4
        w = max(200, sub.winfo_reqwidth())
        h = sub.winfo_reqheight()
        if ax + w > host.winfo_width() - 4:
            ax = anchor_row.winfo_rootx() - host.winfo_rootx() - w + 8
        ay = max(4, min(ay, host.winfo_height() - h - 4))
        sub.place(x=ax, y=ay)
        try:
            sub.tkraise()
        except Exception:
            sub.lift()

        def _sub_enter(_e=None):
            cls._cancel_hover_job()

        def _sub_leave(_e=None):
            if host is not None:
                host.after(200, cls._maybe_destroy_submenu)

        for w in (sub, inner):
            w.bind("<Enter>", _sub_enter)
            w.bind("<Leave>", _sub_leave)

    @classmethod
    def _maybe_destroy_submenu(cls) -> None:
        host = cls._host_ref
        if cls._submenu_shell is None or host is None:
            return
        try:
            px = host.winfo_pointerx()
            py = host.winfo_pointery()
            for panel in (cls._active_shell, cls._submenu_shell):
                if panel is None:
                    continue
                wx = panel.winfo_rootx()
                wy = panel.winfo_rooty()
                ww = panel.winfo_width()
                wh = panel.winfo_height()
                if wx <= px <= wx + ww and wy <= py <= wy + wh:
                    return
        except Exception:
            pass
        cls._destroy_submenu()

    @classmethod
    def _add_item(
        cls,
        parent: ctk.CTkFrame,
        shell: ctk.CTkFrame,
        scheduler: ctk.Misc,
        spec: MenuItem,
        min_width: int,
        *,
        is_submenu: bool = False,
    ) -> None:
        label = spec.get("label", "")
        icon = spec.get("icon", "")
        trail = spec.get("trail", "")
        enabled = spec.get("enabled", True)
        command: Optional[Callable[[], None]] = spec.get("command")
        submenu: Optional[list[MenuItem]] = spec.get("submenu")

        fg_idle = "transparent"
        fg_hover = _MENU_HOVER
        text_color = C["text_primary"] if enabled else C["text_tertiary"]
        icon_color = "#c8d0dc" if enabled else C["text_tertiary"]

        row = ctk.CTkFrame(
            parent,
            fg_color=fg_idle,
            corner_radius=8,
            height=_ROW_H,
        )
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        row.grid_columnconfigure(1, weight=1)

        icon_lbl = ctk.CTkLabel(
            row,
            text=icon,
            width=34,
            font=("Segoe UI Symbol", 15),
            text_color=icon_color,
        )
        icon_lbl.grid(row=0, column=0, padx=(8, 0), sticky="w")

        text_lbl = ctk.CTkLabel(
            row,
            text=label,
            font=get_font("body"),
            text_color=text_color,
            anchor="w",
        )
        text_lbl.grid(row=0, column=1, padx=(2, 4), sticky="ew")

        col_trail = 2
        chevron = None
        if submenu and not trail:
            chevron = ctk.CTkLabel(
                row,
                text="›",
                width=22,
                font=("Segoe UI", 16),
                text_color=C["text_tertiary"],
            )
            chevron.grid(row=0, column=col_trail, padx=(0, 10), sticky="e")
        if trail:
            trail_lbl = ctk.CTkLabel(
                row,
                text=trail,
                width=22,
                font=("Segoe UI Symbol", 13),
                text_color=C["text_tertiary"],
            )
            trail_lbl.grid(row=0, column=col_trail, padx=(0, 10), sticky="e")
            if chevron is None:
                chevron = trail_lbl

        def on_enter(_e=None):
            if not enabled:
                return
            row.configure(fg_color=fg_hover)
            if submenu and not is_submenu:
                cls._cancel_hover_job()

                def _open():
                    cls._show_submenu(row, submenu, min_width)

                cls._hover_job = scheduler.after(_SUB_DELAY_MS, _open)

        def on_leave(_e=None):
            row.configure(fg_color=fg_idle)
            if submenu and not is_submenu:
                cls._cancel_hover_job()
                scheduler.after(280, cls._maybe_destroy_submenu)

        def on_click(_e=None):
            if not enabled:
                return "break"
            if submenu and not is_submenu:
                cls._show_submenu(row, submenu, min_width)
                return "break"
            if not command:
                return "break"
            cmd = command
            cls.dismiss()
            host = cls._parent_ref
            if host is not None:
                host.after(10, cmd)
            else:
                try:
                    cmd()
                except Exception:
                    pass
            return "break"

        widgets = [row, icon_lbl, text_lbl]
        if chevron is not None:
            widgets.append(chevron)

        for w in widgets:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            if enabled:
                w.bind("<Button-1>", on_click)
                try:
                    w.configure(cursor="hand2")
                except Exception:
                    pass
