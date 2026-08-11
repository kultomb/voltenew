"""
Căn giữa cửa sổ, bỏ icon Tk mặc định trên popup, đồng bộ minimize.
"""

from __future__ import annotations

import platform
import tkinter as tk
from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from core.ui_theme import C, RADIUS, SPACE, UI

try:
    from core.app_branding import apply_window_icon as _apply_app_icon
except ImportError:
    _apply_app_icon = None

_MODALS: list[dict] = []
_OVERLAYS: list[dict] = []


def _win_hwnd(win: ctk.Misc) -> int:
    """HWND thật của cửa sổ (CTk/Toplevel)."""
    import ctypes

    wid = win.winfo_id()
    GA_ROOT = 2
    hwnd = ctypes.windll.user32.GetAncestor(wid, GA_ROOT)
    return hwnd or wid


def remove_default_window_icon(win: ctk.Misc) -> None:
    """Xóa hoàn toàn icon mặc định Tk trên thanh title (Windows)."""
    def _clear() -> None:
        if not win.winfo_exists():
            return
        if platform.system() == "Windows":
            try:
                import ctypes

                hwnd = _win_hwnd(win)
                WM_SETICON = 0x0080
                ICON_SMALL, ICON_BIG = 0, 1
                ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, 0)
                ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, 0)

                GWL_EXSTYLE = -20
                WS_EX_DLGMODALFRAME = 0x00000001
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                style |= WS_EX_DLGMODALFRAME
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
                SWP_NOSIZE = 0x0001
                SWP_NOMOVE = 0x0002
                SWP_NOZORDER = 0x0004
                SWP_FRAMECHANGED = 0x0020
                ctypes.windll.user32.SetWindowPos(
                    hwnd, 0, 0, 0, 0, 0,
                    SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_FRAMECHANGED,
                )
            except Exception:
                pass
        try:
            win.iconbitmap("")
        except Exception:
            try:
                win.tk.call("wm", "iconbitmap", win._w, "")
            except Exception:
                pass

    _clear()
    try:
        win.after(1, _clear)
        win.after(50, _clear)
        win.after(200, _clear)
        win.bind("<Map>", lambda _e: _clear(), add="+")
    except Exception:
        pass


def center_on_screen(win: ctk.Misc, width: int, height: int) -> None:
    """Đặt cửa sổ chính giữa màn hình."""
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = max(0, (sw - width) // 2)
    y = max(0, (sh - height) // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


def center_on_owner(win: ctk.Misc, parent: ctk.Misc) -> None:
    """Căn giữa popup theo cửa sổ app chính."""
    if not win.winfo_exists():
        return
    root = parent.winfo_toplevel()
    try:
        root.update_idletasks()
        win.update_idletasks()
    except Exception:
        return

    w = max(win.winfo_reqwidth(), win.winfo_width(), 320)
    h = max(win.winfo_reqheight(), win.winfo_height(), 120)

    rx = root.winfo_rootx()
    ry = root.winfo_rooty()
    rw = max(root.winfo_width(), 400)
    rh = max(root.winfo_height(), 300)

    x = rx + max(0, (rw - w) // 2)
    y = ry + max(0, (rh - h) // 2)

    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = min(max(0, x), max(0, sw - w))
    y = min(max(0, y), max(0, sh - h))

    win.geometry(f"{w}x{h}+{x}+{y}")


def _set_dialog_icon(win: ctk.CTkToplevel) -> None:
    if _apply_app_icon and _apply_app_icon(win):
        return
    remove_default_window_icon(win)


def register_modal(win: ctk.CTkToplevel, owner: ctk.Misc) -> None:
    """Theo dõi dialog — ẩn khi minimize app; dùng icon app hoặc bỏ icon Tk mặc định."""
    owner_root = owner.winfo_toplevel()
    entry = {"win": win, "owner": owner_root, "hidden": False}

    def _untrack(_event=None):
        try:
            _MODALS.remove(entry)
        except ValueError:
            pass

    _MODALS.append(entry)
    _set_dialog_icon(win)
    win.bind("<Destroy>", _untrack, add="+")


def present_modal(win: ctk.CTkToplevel, parent: ctk.Misc, *, grab: bool = True) -> None:
    """
    Hoàn tất popup: transient, không icon Tk, căn giữa app, (tuỳ chọn) grab.
    Gọi sau khi đã pack xong toàn bộ UI.
    """
    root = parent.winfo_toplevel()
    win.transient(root)
    register_modal(win, parent)

    def _finish() -> None:
        if not win.winfo_exists():
            return
        center_on_owner(win, parent)
        _set_dialog_icon(win)
        if grab:
            try:
                win.grab_set()
            except Exception:
                pass

    center_on_owner(win, parent)
    _finish()
    win.after(10, _finish)
    win.after(120, _finish)


def _widget_is_descendant(widget: tk.Misc, ancestor: tk.Misc) -> bool:
    w: tk.Misc | None = widget
    while w is not None:
        if w == ancestor:
            return True
        try:
            w = w.master
        except Exception:
            break
    return False


def show_overlay_panel(
    parent: ctk.Misc,
    builder: Callable[[ctk.CTkFrame, Callable[[], None]], Any],
    *,
    max_width: int = 480,
) -> None:
    """
    Panel modal trong cửa sổ chính — thẻ nổi, app phía sau vẫn hiện (không lớp đen che).
    """
    root = parent.winfo_toplevel()
    done = tk.BooleanVar(master=root, value=False)
    closed = {"ok": False}

    host = ctk.CTkFrame(root, fg_color="transparent")
    host.place(relx=0.5, rely=0.5, anchor="center")

    entry = {"layer": host, "owner": root, "done": done}
    _OVERLAYS.append(entry)
    esc_bind: list[str | None] = [None]
    click_bind: list[str | None] = [None]

    def close() -> None:
        if closed["ok"]:
            return
        closed["ok"] = True
        if esc_bind[0]:
            try:
                root.unbind("<Escape>", esc_bind[0])
            except Exception:
                pass
            esc_bind[0] = None
        if click_bind[0]:
            try:
                root.unbind_all(click_bind[0])
            except Exception:
                pass
            click_bind[0] = None
        try:
            _OVERLAYS.remove(entry)
        except ValueError:
            pass
        try:
            if host.winfo_exists():
                host.destroy()
        except Exception:
            pass
        done.set(True)

    def _on_outside_click(event: tk.Event) -> None:
        if closed["ok"] or not host.winfo_exists():
            return
        if _widget_is_descendant(event.widget, host):
            return
        close()

    stack = ctk.CTkFrame(host, fg_color="transparent")
    stack.pack()
    stack.bind("<Button-1>", lambda _e: "break")

    shell = UI.overlay_panel(stack, padding=SPACE["4"], width=max_width)
    shell.pack()
    inner = UI.card_inner(shell)
    builder(inner, close)

    for w in (host, stack, shell, inner):
        w.bind("<Button-1>", lambda _e: "break", add="+")

    esc_bind[0] = root.bind("<Escape>", lambda _e: close(), add="+")
    click_bind[0] = root.bind_all("<Button-1>", _on_outside_click, add="+")

    host.update_idletasks()
    try:
        host.lift()
        host.tkraise()
    except Exception:
        pass
    root.wait_variable(done)


def withdraw_modals_for(owner: ctk.Misc) -> None:
    owner_root = owner.winfo_toplevel()
    for entry in list(_OVERLAYS):
        if entry["owner"] is not owner_root:
            continue
        layer = entry.get("layer")
        try:
            if layer is not None and layer.winfo_exists():
                layer.destroy()
        except Exception:
            pass
        try:
            entry["done"].set(True)
        except Exception:
            pass
        try:
            _OVERLAYS.remove(entry)
        except ValueError:
            pass
    for entry in _MODALS:
        if entry["owner"] is not owner_root:
            continue
        win = entry["win"]
        if not win.winfo_exists():
            continue
        try:
            st = win.state()
            if st not in ("withdrawn", "iconic"):
                win.withdraw()
                entry["hidden"] = True
        except Exception:
            pass


def restore_modals_for(owner: ctk.Misc) -> None:
    owner_root = owner.winfo_toplevel()
    for entry in _MODALS:
        if entry["owner"] is not owner_root or not entry.get("hidden"):
            continue
        win = entry["win"]
        if not win.winfo_exists():
            continue
        try:
            win.deiconify()
            win.lift()
            try:
                win.grab_set()
            except Exception:
                pass
            entry["hidden"] = False
        except Exception:
            pass


def bind_minimize_cascade(main_window: ctk.Misc) -> None:
    """Khi minimize cửa sổ chính — ẩn mọi dialog con."""

    def _on_unmap(event):
        if event.widget != main_window:
            return
        try:
            if str(main_window.state()) == "iconic":
                withdraw_modals_for(main_window)
        except Exception:
            pass

    def _on_map(event):
        if event.widget != main_window:
            return
        try:
            if str(main_window.state()) in ("normal", "zoomed"):
                restore_modals_for(main_window)
        except Exception:
            pass

    main_window.bind("<Unmap>", _on_unmap, add="+")
    main_window.bind("<Map>", _on_map, add="+")
