"""
Logo / icon ứng dụng — cửa sổ chính, taskbar, file .exe (PyInstaller).
Đặt file: icons/app_icon.ico (khuyến nghị 256×256, nhiều kích thước trong .ico).
"""

from __future__ import annotations

import os
import platform
import sys
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import customtkinter as ctk

_ICON_NAME = "app_icon.ico"
_ICON_DIR = "icons"


def _project_root() -> str:
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_app_icon_path() -> Optional[str]:
    """Đường dẫn tuyệt đối tới icons/app_icon.ico nếu có."""
    for base in (_project_root(), os.path.dirname(os.path.abspath(__file__))):
        path = os.path.normpath(os.path.join(base, _ICON_DIR, _ICON_NAME))
        if os.path.isfile(path):
            return path
    return None


def apply_window_icon(win: "ctk.CTk | ctk.CTkToplevel") -> bool:
    """Gán icon app (thay logo Tk/CTk mặc định) — title bar + taskbar Windows."""
    path = resolve_app_icon_path()
    if not path:
        return False

    ok = False
    try:
        win.iconbitmap(path)
        ok = True
    except Exception:
        pass

    if platform.system() == "Windows":
        try:
            import ctypes

            from core.window_utils import _win_hwnd

            hwnd = _win_hwnd(win)
            WM_SETICON = 0x0080
            ICON_SMALL, ICON_BIG = 0, 1
            LR_LOADFROMFILE = 0x0010
            IMAGE_ICON = 1
            for size in (16, 32, 48, 256):
                hicon = ctypes.windll.user32.LoadImageW(
                    0, path, IMAGE_ICON, size, size, LR_LOADFROMFILE
                )
                if hicon:
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
                    ok = True
                    break
        except Exception:
            pass

    try:
        from PIL import Image, ImageTk

        img = Image.open(path)
        if img.mode not in ("RGBA", "RGB"):
            img = img.convert("RGBA")
        photo = ImageTk.PhotoImage(img)
        win._hbg_app_icon_photo = photo  # giữ reference
        win.iconphoto(True, photo)
        ok = True
    except Exception:
        pass

    return ok


def load_brand_ctk_image(size: int = 36):
    """Ảnh logo cho sidebar (CTkImage) — None nếu chưa có app_icon.ico."""
    path = resolve_app_icon_path()
    if not path:
        return None
    try:
        import customtkinter as ctk
        from PIL import Image

        img = Image.open(path).convert("RGBA")
        resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
        img = img.resize((size, size), resample)
        return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
    except Exception:
        return None
