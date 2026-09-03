"""
HBG VoLTE Fixer GUI — Standalone Modern & Professional Tool
Dedicated, lightweight, and modern UI specialized for VoLTE fixing on Android.
Includes 60 FPS Real-Time Hardware-Accelerated Interactive Android Screen Control.
"""

from __future__ import annotations

import os
import sys
import re
import time
import datetime
import subprocess
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

# Win32 API imports for Windows window embedding & viewport synchronization
if os.name == "nt":
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    GWL_STYLE = -16
    WS_CHILD = 0x40000000
    WS_VISIBLE = 0x10000000
    WS_CAPTION = 0x00C00000
    WS_THICKFRAME = 0x00040000
    RDW_INVALIDATE = 0x0001
    RDW_UPDATENOW = 0x0100
    RDW_ALLCHILDREN = 0x0080
    WM_SIZE = 0x0005
    SIZE_RESTORED = 0
else:
    user32 = None

# Ensure engine module can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from volte_engine import VoLTEEngine

# ---------------------------------------------------------------------------
# Font System & Color Palette (Enterprise Dark Design System)
# ---------------------------------------------------------------------------
FONT_FAMILY = ("Roboto", "Segoe UI", "Arial", "sans-serif")
FONT_TITLE = (FONT_FAMILY[0], 19, "bold")
FONT_SUBTITLE = (FONT_FAMILY[0], 11)
FONT_CARD_TITLE = (FONT_FAMILY[0], 12, "bold")
FONT_LABEL = (FONT_FAMILY[0], 11)
FONT_LABEL_BOLD = (FONT_FAMILY[0], 11, "bold")
FONT_BTN_MAIN = (FONT_FAMILY[0], 13, "bold")
FONT_BTN_GRID = (FONT_FAMILY[0], 11, "bold")
FONT_MONO = ("Roboto Mono", 12, "bold")

THEME = {
    "bg_app": "#0d1117",
    "bg_card": "#161b22",
    "bg_card_hover": "#21262d",
    "bg_inset": "#0b0e14",
    "border": "#30363d",
    "border_highlight": "#38bdf8",
    "text_primary": "#ffffff",
    "text_secondary": "#cbd5e1",
    "text_muted": "#94a3b8",
    "accent_blue": "#38bdf8",
    "accent_indigo": "#6366f1",
    "accent_cyan": "#38bdf8",
    "success": "#10b981",
    "success_hover": "#059669",
    "warning": "#d97706",
    "danger": "#f43f5e",
}


class VoLTEFixerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Configuration & Symmetrical Dual-Window Centering
        self.title("HBG VoLTE & IMS Fixer ⚡ v3.6.6")
        w, h = 1080, 680
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        # Calculate position to center the enlarged combined pair (Main App 1080px + 12px Gap + ~440px Live Screen = 1532px total)
        combined_w = 1532
        if screen_w >= 1540:
            cx = (screen_w - combined_w) // 2
        else:
            cx = (screen_w - w) // 2
        cy = (screen_h - h) // 2

        self.geometry(f"{w}x{h}+{max(0, cx)}+{max(0, cy)}")
        self.resizable(False, False)

        # CustomTkinter Appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.configure(fg_color=THEME["bg_app"])

        # Engine & Multi-threading
        self.engine = VoLTEEngine()
        self.executor = ThreadPoolExecutor(max_workers=6)

        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, "assets", "app_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self.dex_path = os.path.join(base_dir, "assets", "hbg_volte_fixer.dex")
        if not os.path.exists(self.dex_path):
            self.dex_path = os.path.join(os.path.dirname(base_dir), "core", "assets", "hbg_volte_fixer.dex")

        # Locate scrcpy executable
        self.scrcpy_bin = os.path.join(base_dir, "scrcpy", "scrcpy-win64-v2.7", "scrcpy.exe")

        # State Variables
        self.devices: list[dict] = []
        self.selected_device_id: str | None = None
        self.is_working = False
        self.is_running = True
        self.scrcpy_proc: subprocess.Popen | None = None

        # Protocol
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Build Main UI
        self._build_ui()

        # Clean Startup: Log remains clean & quiet until user takes action
        # Start ADB Auto Detection Loop
        self.start_device_auto_check()

    # ---------------------------------------------------------------------------
    # UI Layout Construction
    # ---------------------------------------------------------------------------
    def _build_ui(self):
        """Build main clean fixed-size layout for VoLTE Fixer tool."""
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=16, pady=14)

        # 1. Top Header Bar
        self._build_header()

        # 2. Device Info Card
        self._build_device_card(self.main_container)

        # 3. Split 2-Column Container (Left: Actions Panel, Right: Log Console)
        split_body = ctk.CTkFrame(self.main_container, fg_color="transparent")
        split_body.pack(fill="both", expand=True, pady=(0, 6))

        left_col = ctk.CTkFrame(split_body, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 4))

        right_col = ctk.CTkFrame(split_body, fg_color="transparent")
        right_col.pack(side="right", fill="both", expand=True, padx=(4, 0))

        # Actions Panel (Left Side)
        self._build_actions_panel(left_col)

        # Log Console (Right Side)
        self._build_log_console(right_col)

        # 4. Progress Status Bar (Bottom)
        self._build_progress_bar(self.main_container)

    def _build_header(self):
        header = ctk.CTkFrame(
            self.main_container,
            fg_color=THEME["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=THEME["border"]
        )
        header.pack(fill="x")

        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=10)

        title_frame = ctk.CTkFrame(inner, fg_color="transparent")
        title_frame.pack(side="left")

        title_row = ctk.CTkFrame(title_frame, fg_color="transparent")
        title_row.pack(anchor="w")

        title_lbl = ctk.CTkLabel(
            title_row,
            text="⚡ HBG VoLTE & IMS Fixer",
            font=FONT_TITLE,
            text_color=THEME["text_primary"]
        )
        title_lbl.pack(side="left")

        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(side="right")

        self.status_badge = ctk.CTkLabel(
            btn_frame,
            text="● Chưa kết nối ADB",
            font=FONT_LABEL_BOLD,
            text_color=THEME["danger"],
            fg_color=THEME["bg_inset"],
            corner_radius=16,
            padx=12,
            pady=4
        )
        self.status_badge.pack(side="left", padx=(0, 6))

        self.btn_refresh = ctk.CTkButton(
            btn_frame,
            text="↻",
            font=(FONT_FAMILY[0], 15, "bold"),
            fg_color=THEME["bg_card_hover"],
            hover_color=THEME["border"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["accent_cyan"],
            width=34,
            height=32,
            corner_radius=8,
            command=self.refresh_devices_manual
        )
        self.btn_refresh.pack(side="left", padx=(0, 8))

        self.btn_live_screen = ctk.CTkButton(
            btn_frame,
            text="📱 Live Screen 60 FPS",
            font=FONT_LABEL_BOLD,
            fg_color=THEME["bg_card_hover"],
            hover_color=THEME["border"],
            border_width=1,
            border_color=THEME["accent_cyan"],
            text_color=THEME["accent_cyan"],
            height=32,
            corner_radius=8,
            command=self.toggle_standalone_mirror
        )
        self.btn_live_screen.pack(side="left", padx=(0, 6))

        self.btn_donate = ctk.CTkButton(
            btn_frame,
            text="❤️ DONATE 🍼",
            font=FONT_LABEL_BOLD,
            fg_color="#f43f5e",
            hover_color="#e11d48",
            text_color="#ffffff",
            height=32,
            corner_radius=8,
            command=self.open_donate_dialog
        )
        self.btn_donate.pack(side="left", padx=(0, 6))

        def open_hangho_web():
            import webbrowser
            webbrowser.open("https://hangho.com/")

        self.btn_hangho = ctk.CTkButton(
            btn_frame,
            text="🛒 HangHo.com (PM Bán Hàng)",
            font=FONT_LABEL_BOLD,
            fg_color="#10b981",
            hover_color="#059669",
            text_color="#ffffff",
            height=32,
            corner_radius=8,
            command=open_hangho_web
        )
        self.btn_hangho.pack(side="left")

    def _build_device_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        card.pack(fill="x", pady=(0, 6))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=6)

        # Header Row: Title on Left, Device Selector Dropdown on Right
        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            top_row,
            text="📱 THIẾT BỊ KẾT NỐI",
            font=FONT_CARD_TITLE,
            text_color=THEME["accent_cyan"]
        ).pack(side="left")

        self.device_option = ctk.CTkOptionMenu(
            top_row,
            values=["Đang quét ADB tự động..."],
            command=self.on_device_selected,
            font=FONT_LABEL,
            dropdown_font=FONT_LABEL,
            fg_color=THEME["bg_inset"],
            button_color=THEME["bg_card_hover"],
            button_hover_color=THEME["border"],
            dropdown_fg_color=THEME["bg_card"],
            dropdown_hover_color=THEME["bg_card_hover"],
            dropdown_text_color=THEME["text_primary"],
            text_color=THEME["text_primary"],
            height=28,
            corner_radius=6
        )
        self.device_option.pack(side="right", fill="x", expand=True, padx=(12, 0))

        # Compact Info Bar (3 Columns x 2 Rows)
        self.info_frame = ctk.CTkFrame(inner, fg_color=THEME["bg_inset"], corner_radius=8, border_width=1, border_color=THEME["border"])
        self.info_frame.pack(fill="x")

        info_grid = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        info_grid.pack(fill="x", padx=8, pady=3)
        info_grid.columnconfigure(0, weight=1)
        info_grid.columnconfigure(1, weight=1)
        info_grid.columnconfigure(2, weight=1)

        self.lbl_model = self._create_info_cell(info_grid, 0, 0, "Model:", "Chưa kết nối")
        self.lbl_brand = self._create_info_cell(info_grid, 0, 1, "Hãng:", "---")
        self.lbl_android = self._create_info_cell(info_grid, 0, 2, "Android:", "---")

        self.lbl_sim = self._create_info_cell(info_grid, 1, 0, "Nhà mạng:", "---")
        self.lbl_ims = self._create_info_cell(info_grid, 1, 1, "Trạng thái VoLTE:", "---", col_span=2)

    def _create_info_cell(self, parent, row: int, col: int, title: str, default_val: str, col_span: int = 1) -> ctk.CTkLabel:
        cell = ctk.CTkFrame(parent, fg_color="transparent")
        cell.grid(row=row, column=col, columnspan=col_span, sticky="ew", padx=4, pady=2)

        ctk.CTkLabel(cell, text=title, font=FONT_LABEL, text_color=THEME["text_muted"], width=110, anchor="w").pack(side="left")
        val_lbl = ctk.CTkLabel(cell, text=default_val, font=FONT_LABEL_BOLD, text_color=THEME["text_primary"], anchor="w")
        val_lbl.pack(side="left", fill="x", expand=True)
        return val_lbl

    def _build_actions_panel(self, parent):
        card = ctk.CTkFrame(parent, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        card.pack(fill="both", expand=True)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=12)

        ctk.CTkLabel(
            inner,
            text="⚙ CÔNG CỤ KÍCH HOẠT",
            font=FONT_CARD_TITLE,
            text_color=THEME["accent_cyan"]
        ).pack(anchor="w", pady=(0, 8))

        # Button 1: 1-Click Auto Fix Button
        self.btn_all_in_one = ctk.CTkButton(
            inner,
            text="KÍCH HOẠT VOLTE TỰ ĐỘNG (1-CLICK FIX)",
            font=FONT_BTN_MAIN,
            fg_color=THEME["success"],
            hover_color=THEME["success_hover"],
            height=42,
            corner_radius=10,
            command=self.action_fix_all_in_one
        )
        self.btn_all_in_one.pack(fill="x", pady=(0, 8))

        # Button BROM 1-Click: MediaTek BROM Auto Dump -> Patch -> Flash Engine (Dynamic Toggle Button)
        self.btn_brom_1click = ctk.CTkButton(
            inner,
            text="⚡ BROM 1-CLICK: TỰ ĐỘNG RÚT ➔ VÁ ➔ NẠP VENDOR (MTK BROM)",
            font=FONT_BTN_MAIN,
            fg_color="#d97706",
            hover_color="#b45309",
            text_color="#ffffff",
            height=44,
            corner_radius=10,
            command=self.action_brom_1click_all_in_one
        )
        self.btn_brom_1click.pack(fill="x", pady=(0, 8))

        # Button 2: Vivo VoLTE Switch Opener (All Android Versions)
        self.btn_vivo_fix = ctk.CTkButton(
            inner,
            text="📱 BẬT VOLTE & CÔNG TẮC VIVO",
            font=FONT_BTN_GRID,
            fg_color="#0284c7",
            hover_color="#0369a1",
            text_color="#ffffff",
            height=40,
            corner_radius=8,
            command=self.action_fix_vivo_volte
        )
        self.btn_vivo_fix.pack(fill="x", pady=(0, 8))

        # Button 3: Universal Vendor VoLTE Patcher (Direct In-App File Picker)
        self.btn_vendor_oppo = ctk.CTkButton(
            inner,
            text="TẠO TỆP VÁ VENDOR VOLTE (DUMP/PATCH)",
            font=FONT_BTN_GRID,
            fg_color=THEME["accent_indigo"],
            hover_color=THEME["bg_card_hover"],
            text_color="#ffffff",
            height=40,
            corner_radius=8,
            command=self.action_nap_vendor_oppo_series
        )
        self.btn_vendor_oppo.pack(fill="x", pady=(0, 8))

        # Button 3: Secret Dial Codes Button
        self.btn_secret_codes = ctk.CTkButton(
            inner,
            text="BẢNG MÃ BÍ MẬT DIAL CODES CÁC HÃNG",
            font=FONT_BTN_GRID,
            fg_color=THEME["bg_card_hover"],
            hover_color=THEME["border"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["accent_cyan"],
            height=40,
            corner_radius=8,
            command=self.open_secret_codes_dialog
        )
        self.btn_secret_codes.pack(fill="x")

    def _build_progress_bar(self, parent):
        prog_card = ctk.CTkFrame(parent, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        prog_card.pack(fill="x", pady=(0, 8))

        inner = ctk.CTkFrame(prog_card, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=8)

        status_bar = ctk.CTkFrame(inner, fg_color="transparent")
        status_bar.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            status_bar,
            text="⚡ TIẾN TRÌNH",
            font=FONT_CARD_TITLE,
            text_color=THEME["accent_cyan"]
        ).pack(side="left")

        self.lbl_status = ctk.CTkLabel(
            status_bar,
            text="Đang tự động nhận diện thiết bị ADB...",
            font=FONT_LABEL,
            text_color=THEME["text_secondary"]
        )
        self.lbl_status.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(
            inner,
            height=6,
            corner_radius=3,
            fg_color=THEME["bg_inset"],
            progress_color=THEME["accent_cyan"]
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

    def _build_log_console(self, parent):
        log_card = ctk.CTkFrame(parent, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        log_card.pack(fill="both", expand=True)

        inner = ctk.CTkFrame(log_card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=10)

        title_row = ctk.CTkFrame(inner, fg_color="transparent")
        title_row.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            title_row,
            text="📋 NHẬT KÝ THỰC THI",
            font=FONT_CARD_TITLE,
            text_color=THEME["accent_cyan"]
        ).pack(side="left")

        self.txt_log = ctk.CTkTextbox(
            inner,
            font=FONT_MONO,
            fg_color=THEME["bg_inset"],
            text_color=THEME["text_primary"],
            corner_radius=8,
            border_width=1,
            border_color=THEME["border"]
        )
        self.txt_log.pack(fill="both", expand=True)
        self.txt_log.configure(state="disabled")

    def get_outer_window_bounds(self):
        """Get exact visible screen bounds (left, top, width, height) of main window on Windows 10/11."""
        self.update_idletasks()
        try:
            import ctypes
            from ctypes import wintypes
            hwnd = int(self.wm_frame(), 16)
            rect = wintypes.RECT()
            # DWMWA_EXTENDED_FRAME_BOUNDS (9) gets the exact visible window bounds on Windows 10/11
            ctypes.windll.dwmapi.DwmGetWindowAttribute(
                wintypes.HWND(hwnd),
                wintypes.DWORD(9),
                ctypes.byref(rect),
                ctypes.sizeof(rect)
            )
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            if w > 100 and h > 100:
                return rect.left, rect.top, w, h
        except Exception:
            pass

        # Fallback to standard Tkinter geometry
        return self.winfo_x(), self.winfo_y(), self.winfo_width(), self.winfo_height()

    # ---------------------------------------------------------------------------
    # Scrcpy Native Hardware Streaming Engine (Standalone Native Window Mode)
    # ---------------------------------------------------------------------------
    def start_scrcpy_stream(self, device_id: str):
        """Launch Scrcpy ultra-fast 60 FPS stream in a standalone native window."""
        if not os.path.exists(self.scrcpy_bin):
            self.log("⚠ Không tìm thấy Engine Scrcpy v2.7 để truyền luồng 60 FPS.", "warning")
            return

        self.stop_scrcpy_stream()

        # Dynamically calculate window position & height to open Scrcpy perfectly aligned with main tool window
        left, top, width, height = self.get_outer_window_bounds()
        target_x = left + width + 10
        target_y = top
        scrcpy_height = max(350, height - 38)

        cmd = [
            self.scrcpy_bin,
            "-s", device_id,
            "--no-audio",
            "--max-size=1280",
            "--window-title", f"Màn Hình Android Live — [{device_id}]",
            f"--window-x={target_x}",
            f"--window-y={target_y}",
            f"--window-height={scrcpy_height}"
        ]

        env = os.environ.copy()
        if hasattr(self.engine, "adb_path") and self.engine.adb_path:
            env["ADB"] = self.engine.adb_path

        try:
            self.scrcpy_proc = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.log(f"🚀 Đã tự động mở màn hình Android Live (60 FPS) cân đối bên phải cho {device_id}!", "success")
        except Exception as e:
            self.log(f"⚠ Khởi động Scrcpy thất bại: {e}", "warning")

    def stop_scrcpy_stream(self):
        if self.scrcpy_proc:
            try:
                self.scrcpy_proc.terminate()
                self.scrcpy_proc.wait(timeout=1)
            except Exception:
                pass
            self.scrcpy_proc = None

    def toggle_standalone_mirror(self):
        if self.scrcpy_proc and self.scrcpy_proc.poll() is None:
            self.stop_scrcpy_stream()
            self.log("Đã đóng cửa sổ màn hình Live.", "info")
        else:
            if self.selected_device_id:
                self.start_scrcpy_stream(self.selected_device_id)
            else:
                messagebox.showwarning("Cảnh báo", "Vui lòng kết nối thiết bị Android trước!")

    # ---------------------------------------------------------------------------
    # ADB Device Monitor Thread (Parity with HBGAdBlocker DeviceManager)
    # ---------------------------------------------------------------------------
    def start_device_auto_check(self):
        Thread(target=self._adb_monitor_thread, daemon=True).start()

    def _adb_monitor_thread(self):
        last_device_id = None

        while self.is_running:
            try:
                if not self.is_working:
                    connected, reason = self.engine.refresh()
                    if connected and self.engine.dm and self.engine.dm.serial:
                        cur_id = self.engine.dm.serial
                        cur_model = self.engine.dm.device_model or cur_id
                        if last_device_id != cur_id:
                            last_device_id = cur_id
                            self.selected_device_id = cur_id
                            options = [f"{cur_model} ({cur_id})"]
                            self.devices = [{"id": cur_id, "model": cur_model}]
                            self.after(0, lambda m=cur_model, opts=options, cid=cur_id: self._on_device_connected(m, opts, cid))
                    else:
                        devs = self.engine.get_devices()
                        if devs:
                            cur_id = devs[0]["id"]
                            cur_model = devs[0]["model"]
                            if last_device_id != cur_id:
                                last_device_id = cur_id
                                self.selected_device_id = cur_id
                                options = [f"{cur_model} ({cur_id})"]
                                self.devices = devs
                                self.after(0, lambda m=cur_model, opts=options, cid=cur_id: self._on_device_connected(m, opts, cid))
                        elif last_device_id is not None:
                            last_device_id = None
                            self.devices = []
                            self.selected_device_id = None
                            self.after(0, self._on_adb_disconnected)

                time.sleep(1.2 if last_device_id else 2.5)
            except Exception:
                time.sleep(2.5)

    def _on_device_connected(self, model_name: str, options: list[str], dev_id: str):
        self.status_badge.configure(text="● Đã kết nối ADB", text_color=THEME["success"])
        self.device_option.configure(values=options)
        self.device_option.set(options[0])
        self.lbl_model.configure(text=model_name)
        self.set_status("Sẵn sàng kích hoạt VoLTE.", 1.0)
        self.log(f"✓ Đã kết nối ADB thiết bị: {model_name} [{dev_id}]", "success")

        # Fetch deep info in background without blocking ADB loop
        self.executor.submit(self._fetch_device_details_async, dev_id)

        # Start 60 FPS hardware accelerated stream
        self.start_scrcpy_stream(dev_id)

    def _fetch_device_details_async(self, device_id: str):
        try:
            info = self.engine.get_device_info(device_id)
            if self.selected_device_id == device_id:
                self.after(0, lambda: self._apply_device_specs(info))
        except Exception:
            pass

    def _on_adb_disconnected(self):
        self.stop_scrcpy_stream()
        self.status_badge.configure(text="● Bị ngắt kết nối", text_color=THEME["danger"])
        self.device_option.configure(values=["Không tìm thấy thiết bị"])
        self.device_option.set("Không tìm thấy thiết bị")
        self.lbl_model.configure(text="Chưa kết nối")
        self.lbl_brand.configure(text="---")
        self.lbl_android.configure(text="---")
        self.lbl_sim.configure(text="---")
        self.lbl_ims.configure(text="---")
        self.set_status("Chưa kết nối thiết bị ADB nào.", 0.0)
        self.log("⚠ Đã ngắt kết nối thiết bị ADB.", "warning")

    def refresh_devices_manual(self):
        if self.is_working:
            return
        self.log("🔍 Đang tải lại danh sách ADB...", "info")
        self.set_status("Đang tải lại ADB...", 0.3)
        self.executor.submit(self._refresh_manual_thread)

    def _refresh_manual_thread(self):
        ok, reason = self.engine.refresh()
        if ok and self.engine.dm and self.engine.dm.serial:
            cur_id = self.engine.dm.serial
            cur_model = self.engine.dm.device_model or cur_id
            self.selected_device_id = cur_id
            options = [f"{cur_model} ({cur_id})"]
            self.devices = [{"id": cur_id, "model": cur_model}]
            self.after(0, lambda: self._on_device_connected(cur_model, options, cur_id))
        else:
            devs = self.engine.get_devices()
            if devs:
                cur_id = devs[0]["id"]
                cur_model = devs[0]["model"]
                self.selected_device_id = cur_id
                options = [f"{cur_model} ({cur_id})"]
                self.devices = devs
                self.after(0, lambda: self._on_device_connected(cur_model, options, cur_id))
            else:
                self.selected_device_id = None
                self.after(0, self._on_adb_disconnected)

    def on_device_selected(self, choice: str):
        for d in self.devices:
            if d["id"] in choice or d["model"] in choice:
                self.selected_device_id = d["id"]
                self.executor.submit(self._fetch_device_details_async, d["id"])
                self.start_scrcpy_stream(d["id"])
                break

    def _apply_device_specs(self, info: dict):
        marketname = info.get("marketname", "")
        model = info.get("model", "Unknown")
        brand = info.get("brand", "Unknown")

        if marketname and marketname != "Không xác định":
            display_name = marketname
        elif model and model != "Unknown":
            if brand and brand != "Unknown" and not model.lower().startswith(brand.lower()):
                display_name = f"{brand} {model}"
            else:
                display_name = model
        else:
            display_name = "Thiết bị Android"

        self.lbl_model.configure(text=model)
        self.lbl_brand.configure(text=brand)
        self.lbl_android.configure(text=f"{info.get('android_ver', '')} ({info.get('sdk', '')})")
        self.lbl_sim.configure(text=info.get("operator", "Chưa rõ"))
        self.lbl_ims.configure(text=info.get("ims_status", "---"))

        if self.selected_device_id:
            option_str = f"{display_name} ({self.selected_device_id})"
            self.device_option.configure(values=[option_str])
            self.device_option.set(option_str)
            for d in self.devices:
                if d["id"] == self.selected_device_id:
                    d["model"] = display_name

    # ---------------------------------------------------------------------------
    # Logging & Status Helpers
    # ---------------------------------------------------------------------------
    def log(self, message: str, level: str = "info"):
        now = datetime.datetime.now().strftime("[%H:%M:%S]")
        line = f"{now} [{level.upper()}] {message}\n"
        self.after(0, lambda: self._append_log_to_txt(line, level))

    def _append_log_to_txt(self, line: str, level: str = "info"):
        if hasattr(self, "txt_log") and self.txt_log:
            self.txt_log.configure(state="normal")
            
            # Anti-glare eye-soothing color tags
            if "tag_info" not in self.txt_log.tag_names():
                self.txt_log.tag_config("tag_info", foreground="#38bdf8")     # Soft Sky Blue
                self.txt_log.tag_config("tag_success", foreground="#34d399")  # Soft Emerald Green
                self.txt_log.tag_config("tag_warning", foreground="#fbbf24")  # Warm Amber Gold
                self.txt_log.tag_config("tag_error", foreground="#f87171")    # Gentle Coral Red

            tag_name = f"tag_{level.lower()}" if f"tag_{level.lower()}" in self.txt_log.tag_names() else "tag_info"
            self.txt_log.insert("end", line, tag_name)
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")

    def set_status(self, text: str, progress: float = 0.0):
        self.after(0, lambda: self._update_status(text, progress))

    def _update_status(self, text: str, progress: float):
        self.lbl_status.configure(text=text)
        self.progress_bar.set(progress)

    def set_controls_enabled(self, enabled: bool):
        self.after(0, lambda: self._apply_controls_state(enabled))

    def _apply_controls_state(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        buttons = [
            getattr(self, "btn_all_in_one", None),
            getattr(self, "btn_brom_1click", None),
            getattr(self, "btn_vivo_fix", None),
            getattr(self, "btn_vendor_oppo", None),
            getattr(self, "btn_vendor_rom_advanced", None),
            getattr(self, "btn_deep_diagnostics", None),
            getattr(self, "btn_giai_ma_overlay", None),
            getattr(self, "btn_repack_apk", None),
            getattr(self, "btn_export_unlocktool", None),
            getattr(self, "btn_secret_codes", None),
            getattr(self, "btn_refresh", None),
            getattr(self, "btn_live_screen", None),
        ]
        for btn in buttons:
            if btn is not None:
                if btn == getattr(self, "btn_brom_1click", None) and getattr(self, "brom_running", False):
                    btn.configure(state="normal")
                else:
                    btn.configure(state=state)

    def on_closing(self):
        self.is_running = False
        try:
            from tools.mtk_brom_auto_engine import cancel_brom_process
            cancel_brom_process()
        except Exception:
            pass
        self.stop_scrcpy_stream()
        self.destroy()

    # ---------------------------------------------------------------------------
    # Action Handlers
    # ---------------------------------------------------------------------------
    def action_stop_brom_process(self):
        """Cancels any running BROM process immediately and unlocks controls."""
        print("\n[DEBUG CLICK] 🛑 Bấm nút: DỪNG TIẾN TRÌNH BROM")
        try:
            from tools.mtk_brom_auto_engine import cancel_brom_process
            cancel_brom_process()
        except Exception as e:
            print("Error cancelling brom:", e)
            
        self.brom_running = False
        if hasattr(self, "btn_brom_1click"):
            self.btn_brom_1click.configure(
                text="⚡ BROM 1-CLICK: TỰ ĐỘNG RÚT ➔ VÁ ➔ NẠP VENDOR (MTK BROM)",
                fg_color="#d97706",
                hover_color="#b45309",
                state="normal"
            )
        self.is_working = False
        self.set_controls_enabled(True)
        self.set_status("Đã dừng tiến trình BROM. Sẵn sàng thao tác!", 0.0)
        self.log("🛑 Đã dừng tiến trình BROM và mở lại giao diện!", "warning")

    def action_brom_1click_all_in_one(self):
        """Action for single 1-Click BROM Auto Engine with Dynamic Toggle Button."""
        if getattr(self, "brom_running", False):
            # User clicked while running -> STOP BROM!
            self.action_stop_brom_process()
            return

        print("\n[DEBUG CLICK] ⚡ Bấm nút: BROM 1-CLICK ALL-IN-ONE (RÚT -> VÁ -> NẠP VENDOR)")
        
        self.brom_running = True
        self.is_working = True
        
        # Transform button into RED STOP BUTTON
        if hasattr(self, "btn_brom_1click"):
            self.btn_brom_1click.configure(
                text="🛑 DỪNG TIẾN TRÌNH BROM (STOP)",
                fg_color="#dc2626",
                hover_color="#991b1b",
                state="normal"
            )
            
        self.set_controls_enabled(False)
        self.set_status("Đang đứng chờ kết nối MediaTek BROM Mode...", 0.2)
        
        self.log("⚡ BROM 1-CLICK: Tắt nguồn máy ➔ Giữ phím TĂNG + GIẢM ÂM LƯỢNG ➔ Cắm cáp USB", "warning")
        self.log("⌛ Đang đứng chờ cắm cáp kết nối MediaTek BROM Mode...", "info")

        def _thread():
            try:
                from tools.mtk_brom_auto_engine import run_brom_1click_all_in_one
                from vendor_patcher.vendor_engine import patch_vendor_image
                
                work_dir = os.path.abspath("scratch/brom_work")
                success = run_brom_1click_all_in_one(work_dir, patch_vendor_image, log_cb=self.log)
                self.after(0, lambda: self._on_brom_completed(success))
            except Exception as e:
                self.log(f"⚠ Lỗi BROM 1-Click: {e}", "error")
                self.after(0, lambda: self._on_brom_completed(False))

        self.executor.submit(_thread)

    def _on_brom_completed(self, success: bool):
        self.brom_running = False
        if hasattr(self, "btn_brom_1click"):
            self.btn_brom_1click.configure(
                text="⚡ BROM 1-CLICK: TỰ ĐỘNG RÚT ➔ VÁ ➔ NẠP VENDOR (MTK BROM)",
                fg_color="#d97706",
                hover_color="#b45309",
                state="normal"
            )
        self._on_action_completed(success, "BROM 1-Click VoLTE Auto Engine")

    def _check_selected_device(self) -> bool:
        if not self.selected_device_id:
            devs = self.engine.get_devices()
            if devs:
                self.selected_device_id = devs[0]["id"]
                return True
            messagebox.showwarning("Cảnh báo", "Vui lòng cắm cáp USB và bật Gỡ Lỗi USB (USB Debugging) trên điện thoại!")
            return False
        return True

    def action_fix_all_in_one(self):
        """Single Smart Auto-Fix Button action for ALL brands."""
        print("\n[DEBUG CLICK] ⚡ Bấm nút: KÍCH HOẠT VoLTE TỰ ĐỘNG (1-CLICK FIX)")
        if not self._check_selected_device():
            print("[DEBUG WARNING] Chưa phát hiện thiết bị nào kết nối ADB!")
            return
        print(f"[DEBUG DEVICE] ID thiết bị đang chọn: {self.selected_device_id}")
        self.is_working = True
        self.set_controls_enabled(False)
        self.set_status("Đang thực hiện kích hoạt VoLTE tự động 1-Click...", 0.2)
        self.executor.submit(self._run_all_in_one_thread)

    def action_fix_vivo_volte(self):
        """Action for Vivo VoLTE activation button."""
        print("\n[DEBUG CLICK] 📱 Bấm nút: BẬT VOLTE & CÔNG TẮC VIVO")
        if not self._check_selected_device():
            return
        self.is_working = True
        self.set_controls_enabled(False)
        self.set_status("Đang nạp cấu hình ép hiện công tắc VoLTE Vivo...", 0.3)

        def _thread():
            try:
                res = self.engine.fix_vivo_volte(self.selected_device_id, self.log)
                self.after(0, lambda: self._on_action_completed(res, "Kích Hoạt VoLTE Vivo HD"))
            except Exception as e:
                self.log(f"⚠ Lỗi Vivo Fix: {e}", "error")
                self.after(0, lambda: self._on_action_completed(False, "Kích Hoạt VoLTE Vivo HD"))

        self.executor.submit(_thread)

    def _on_action_completed(self, success: bool, action_name: str):
        self.is_working = False
        self.set_controls_enabled(True)
        if success:
            self.set_status(f"✓ Đã hoàn tất: {action_name}", 1.0)
        else:
            self.set_status(f"⚠ Hoàn tất với cảnh báo: {action_name}", 1.0)

    def _run_all_in_one_thread(self):
        dev_id = self.selected_device_id
        try:
            res = self.engine.smart_fix_all(dev_id, self.dex_path, self.log)
            print(f"[DEBUG RESULT] Kết quả Fix 1-Click: {res}")
            self.after(0, lambda: self._on_action_completed(res, "Kích Hoạt VoLTE Tự Động"))
        except Exception as e:
            import traceback
            print(f"[DEBUG ERROR] Lỗi khi chạy Fix 1-Click:\n{traceback.format_exc()}")
            self.log(f"⚠ Lỗi hệ thống: {e}", "error")
            self.after(0, lambda: self._on_action_completed(False, "Kích Hoạt VoLTE Tự Động"))

    def action_mtk_brom_workflow(self):
        """Run MTK BROM Automated Read, Patch & Flash workflow."""
        self.is_working = True
        self.set_controls_enabled(False)
        
        def _thread():
            try:
                from vendor_patcher.mtk_brom_engine import MTKBromEngine
                engine = MTKBromEngine()
                ok = engine.run_full_brom_workflow(self.log, self.set_status)
                self.after(0, lambda: self._on_action_completed(ok, "Kích hoạt Vendor MTK BROM"))
            except Exception as ex:
                self.log(f"❌ Lỗi tiến trình MTK BROM: {ex}", "error")
                self.after(0, lambda: self._on_action_completed(False, "Kích hoạt Vendor MTK BROM"))

        self.executor.submit(_thread)

    def action_nap_vendor_oppo_series(self):
        """Run Universal Vendor VoLTE Patcher directly inside main app console."""
        from tkinter import filedialog
        fpath = filedialog.askopenfilename(
            title="Chọn Tệp Vendor (vendor.bin / vendor.img)",
            filetypes=[("Vendor Partition Image", "*.bin *.img"), ("All Files", "*.*")]
        )
        if not fpath or not os.path.exists(fpath):
            return

        self.log(f"\n⚡ Đang tiến hành tạo tệp vá VoLTE cho [{os.path.basename(fpath)}]...", "info")
        
        def _thread():
            try:
                from vendor_patcher.vendor_engine import patch_vendor_image
                out_file = patch_vendor_image(fpath)
                if out_file:
                    self.log("🎉 TẠO TỆP VÁ VENDOR THÀNH CÔNG! Tệp bản vá đã lưu tại:", "success")
                    self.log(f"👉 {out_file}", "success")
                    self.log("👉 HƯỚNG DẪN NẠP UNLOCKTOOL: Chọn Tab MTK -> Boot Device -> Chuột phải vào phân vùng Vendor -> Chọn Write -> Trỏ đến tệp PATCHED_vendor", "info")
                    self.after(0, lambda: messagebox.showinfo("Thành công", f"Đã tạo tệp vá Vendor VoLTE thành công!\n\nTệp đầu ra:\n{out_file}"))
            except Exception as ex:
                self.log(f"❌ Lỗi tạo tệp vá Vendor: {ex}", "error")

        self.executor.submit(_thread)

    def action_restore_defaults(self):
        """Run Automated Restore directly inside main app console."""
        self.log("\n🛡️ Bắt đầu khôi phục VoLTE về cài đặt mặc định...", "info")
        def _thread():
            try:
                from vendor_patcher.restore_engine import main as run_restore
                run_restore()
                self.log("🎉 Đã hoàn tất khôi phục cài đặt VoLTE về mặc định nhà sản xuất!", "success")
                self.after(0, lambda: messagebox.showinfo("Khôi Phục", "Đã hoàn tất khôi phục cài đặt VoLTE về mặc định!"))
            except Exception as ex:
                self.log(f"⚠ Lỗi khôi phục: {ex}", "error")

        self.executor.submit(_thread)

    def action_nap_vendor_rom_advanced(self):
        """Run Advanced Vendor ROM Flashing & Partition Injection."""
        print("\n[DEBUG CLICK] 🔥 Bấm nút: NẠP VENDOR NÂNG CAO THẲNG VÀO ROM")
        self.is_working = True
        self.set_controls_enabled(False)
        self.set_status("Đang thực hiện nạp Vendor Nâng Cao vào ROM...", 0.3)
        self.log("🔥 Khởi chạy kịch bản Nạp Vendor Nâng Cao vào ROM (Partition Flashing)...", "info")

        def _thread():
            try:
                import napkich_vendor_rom_advanced
                napkich_vendor_rom_advanced.main()
                self.after(0, lambda: self._on_action_completed(True, "Nạp Vendor Nâng Cao Vào ROM"))
            except Exception as ex:
                import traceback
                print(f"[DEBUG ERROR] Lỗi khi nạp Vendor ROM:\n{traceback.format_exc()}")
                self.log(f"⚠ Lỗi nạp Vendor ROM: {ex}", "error")
                self.after(0, lambda: self._on_action_completed(False, "Nạp Vendor Nâng Cao Vào ROM"))

        self.executor.submit(_thread)

    def action_run_deep_diagnostics(self):
        """Run 5-layer deep scientific diagnostics scan on connected Android device."""
        cur_model = self.lbl_model.cget("text")
        dev_title = f"{cur_model}" if cur_model and cur_model != "Chưa kết nối" else "thiết bị"
        print(f"\n[DEBUG CLICK] 🔬 Bấm nút: CHẨN ĐOÁN KHOA HỌC CHUYÊN SÂU {dev_title}")
        self.is_working = True
        self.set_controls_enabled(False)
        self.set_status("Đang thực hiện chẩn đoán khoa học 5 tầng...", 0.3)
        self.log(f"🔬 Bắt đầu chẩn đoán khoa học chuyên sâu {dev_title} (5 Tầng System)...", "info")

        def _thread():
            try:
                import oppo_a31_deep_diagnostics
                oppo_a31_deep_diagnostics.main()
                self.after(0, lambda: self._on_action_completed(True, "Chẩn Đoán Khoa Học Chuyên Sâu"))
            except Exception as ex:
                import traceback
                print(f"[DEBUG ERROR] Lỗi khi chẩn đoán:\n{traceback.format_exc()}")
                self.log(f"⚠ Lỗi chẩn đoán: {ex}", "error")
                self.after(0, lambda: self._on_action_completed(False, "Chẩn Đoán Khoa Học Chuyên Sâu"))

        self.executor.submit(_thread)

    def action_giai_ma_overlay(self):
        """Run root cause discovery and patch extraction."""
        print("\n[DEBUG CLICK] 🔓 Bấm nút: GIẢI MÃ GỐC RỄ KHÓA VOLTE")
        self.is_working = True
        self.set_controls_enabled(False)
        self.set_status("Đang thực hiện giải mã gốc rễ tệp XML cấu hình OPPO...", 0.3)
        self.log("🔓 Bắt đầu truy tìm & bóc tách bản vá XML mở khóa VoLTE...", "info")

        def _thread():
            try:
                import oppo_a31_overlay_patcher
                oppo_a31_overlay_patcher.main()
                self.after(0, lambda: self._on_action_completed(True, "Giải Mã Gốc Rễ Khóa VoLTE"))
            except Exception as ex:
                import traceback
                print(f"[DEBUG ERROR] Lỗi khi giải mã:\n{traceback.format_exc()}")
                self.log(f"⚠ Lỗi giải mã: {ex}", "error")
                self.after(0, lambda: self._on_action_completed(False, "Giải Mã Gốc Rễ Khóa VoLTE"))

        self.executor.submit(_thread)

    def action_repack_and_flash_apk(self):
        """Run OppoSimSettings APK repacker and prompt for system flashing."""
        print("\n[DEBUG CLICK] 📦 Bấm nút: ĐÓNG GÓI & NẠP OPPOSIMSETTINGS PATCHED")
        self.is_working = True
        self.set_controls_enabled(False)
        self.set_status("Đang thực hiện đóng gói OppoSimSettings_Patched.apk...", 0.3)
        self.log("📦 Đang thay thế tệp XML volte_status=\"1\" và đóng gói APK...", "info")

        def _thread():
            try:
                import repack_opposimsettings_apk
                repack_opposimsettings_apk.main()
                self.after(0, lambda: self._on_action_completed(True, "Đóng Gói & Nạp OppoSimSettings Patched"))
            except Exception as ex:
                import traceback
                print(f"[DEBUG ERROR] Lỗi khi đóng gói APK:\n{traceback.format_exc()}")
                self.log(f"⚠ Lỗi đóng gói APK: {ex}", "error")
                self.after(0, lambda: self._on_action_completed(False, "Đóng Gói & Nạp OppoSimSettings Patched"))

        self.executor.submit(_thread)

    def action_export_unlocktool(self):
        """Run export package generator for UnlockTool / SP Flash Tool."""
        print("\n[DEBUG CLICK] 🎁 Bấm nút: TẠO GÓI NẠP CHUYÊN NGHỆP UNLOCKTOOL")
        self.is_working = True
        self.set_controls_enabled(False)
        self.set_status("Đang gom gói nạp chuyên nghiệp cho UnlockTool...", 0.3)
        self.log("🎁 Đang tạo thư mục GOI_NAP_UNLOCKTOOL_OPPO...", "info")

        def _thread():
            try:
                import tao_goi_nap_oppo_unlocktool
                tao_goi_nap_oppo_unlocktool.main()
                self.after(0, lambda: self._on_action_completed(True, "Tạo Gói Nạp UnlockTool"))
            except Exception as ex:
                import traceback
                print(f"[DEBUG ERROR] Lỗi khi tạo gói nạp:\n{traceback.format_exc()}")
                self.log(f"⚠ Lỗi tạo gói nạp: {ex}", "error")
                self.after(0, lambda: self._on_action_completed(False, "Tạo Gói Nạp UnlockTool"))

        self.executor.submit(_thread)

    def open_secret_codes_dialog(self):
        """Open interactive popup listing secret dial codes for all brands (OPPO, Xiaomi, MTK, Vivo, Samsung, Qualcomm)."""
        print("\n[DEBUG CLICK] 🔑 Bấm nút: BẢNG MÃ BÍ MẬT DIAL CODES TẤT CẢ CÁC HÃNG")
        dlg = ctk.CTkToplevel(self)
        dlg.title("🔑 BẢNG MÃ BÍ MẬT DIAL CODES CÁC HÃNG (MBN / VOLTE / TESTING)")
        w, h = 640, 600
        dlg.update_idletasks()
        self.update_idletasks()
        screen_w = dlg.winfo_screenwidth()
        screen_h = dlg.winfo_screenheight()

        parent_x = self.winfo_x()
        parent_y = self.winfo_y()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()

        cx = parent_x + (parent_w - w) // 2
        cy = parent_y + (parent_h - h) // 2

        if cx < 0 or cy < 0 or cx > screen_w - 50 or cy > screen_h - 50:
            cx = (screen_w - w) // 2
            cy = (screen_h - h) // 2

    def open_secret_codes_dialog(self):
        """Open popup modal dialog for Secret Codes organized into 3 tabs with zero scrolling."""
        dlg = ctk.CTkToplevel(self)
        dlg.title("🔑 BẢNG MÃ BÍ MẬT DIAL CODES TẤT CẢ CÁC HÃNG")
        
        w, h = 740, 520
        dlg.update_idletasks()
        self.update_idletasks()
        screen_w = dlg.winfo_screenwidth()
        screen_h = dlg.winfo_screenheight()

        parent_x = self.winfo_x()
        parent_y = self.winfo_y()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()

        cx = parent_x + (parent_w - w) // 2
        cy = parent_y + (parent_h - h) // 2

        if cx < 0 or cy < 0 or cx > screen_w - 50 or cy > screen_h - 50:
            cx = (screen_w - w) // 2
            cy = (screen_h - h) // 2

        dlg.geometry(f"{w}x{h}+{max(0, cx)}+{max(0, cy)}")
        dlg.resizable(False, False)
        dlg.configure(fg_color=THEME["bg_app"])
        dlg.lift()
        dlg.focus_force()
        dlg.attributes("-topmost", True)
        dlg.after(200, lambda: dlg.attributes("-topmost", False))
        dlg.grab_set()

        # Title
        banner = ctk.CTkFrame(dlg, fg_color=THEME["bg_card"], corner_radius=10, border_width=1, border_color=THEME["border"])
        banner.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(
            banner,
            text="🔑 BẢNG MÃ BÍ MẬT DIAL CODES TẤT CẢ CÁC HÃNG",
            font=FONT_CARD_TITLE,
            text_color=THEME["accent_cyan"]
        ).pack(pady=(8, 2))

        ctk.CTkLabel(
            banner,
            text="Bấm nút '🚀 Mở' bên cạnh mã để kích hoạt trực tiếp lên điện thoại đang kết nối.",
            font=FONT_SUBTITLE,
            text_color=THEME["text_muted"]
        ).pack(pady=(0, 6))

        # Tabview Container (Zero Scrollbar Needed)
        tabview = ctk.CTkTabview(
            dlg,
            fg_color=THEME["bg_card"],
            segmented_button_fg_color=THEME["bg_inset"],
            segmented_button_selected_color=THEME["accent_indigo"],
            segmented_button_selected_hover_color=THEME["accent_blue"],
            corner_radius=10
        )
        tabview.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        tab_ims = tabview.add("🌐 IMS & CARRIER OVERRIDE")
        tab_modem = tabview.add("🛠️ MODEM & ENGINEERING")
        tab_oem = tabview.add("🔬 OEM DIAGNOSTIC")

        # Categorized Secret Codes Mapping according to User Specification
        categories_data = {
            "tab_ims": [
                ("IMS_STATUS", [
                    ("*#*#4636#*#*", "Menu Trạng Thái IMS & Radio Info")
                ]),
                ("VOLTE_CARRIER_OVERRIDE", [
                    ("*#*#86583#*#*", "Mở Khóa VoLTE Xiaomi Carrier Check"),
                    ("*#*#86436#*#*", "Mở Công Tắc VoLTE Vivo HD (Funtouch OS)")
                ]),
                ("VOWIFI_CARRIER_OVERRIDE", [
                    ("*#*#869434#*#*", "Mở Khóa VoWiFi Xiaomi Carrier Check")
                ])
            ],
            "tab_modem": [
                ("MODEM_ENGINEERING", [
                    ("*#*#3646633#*#*", "MediaTek EngineerMode (Telephony -> IMS)"),
                    ("*#0011#", "Samsung ServiceMode (LTE Band / QCI)"),
                    ("*#9090#", "Samsung Diagnostic Config")
                ]),
                ("MODEM_INTERFACE", [
                    ("*#0808#", "Samsung USB / Serial Port Settings (RMNET+DM)")
                ])
            ],
            "tab_oem": [
                ("OEM_DIAGNOSTIC", [
                    ("*#800#", "OPPO Logcat & Feedback Log (IMS Log)"),
                    ("*#801#", "OPPO Engineering Switch / Port"),
                    ("*#808#", "OPPO Device Testing (RF / Hardware)"),
                    ("*#899#", "OPPO EngineerMode / AfterSales"),
                    ("*#*#558#*#*", "Vivo Factory Test & Engineering"),
                    ("*#*#2846579#*#*", "Huawei Project Menu"),
                    ("*#*#7378423#*#*", "Sony Xperia Service Menu")
                ])
            ]
        }

        tab_objs = {
            "tab_ims": tab_ims,
            "tab_modem": tab_modem,
            "tab_oem": tab_oem
        }

        for tab_key, cat_list in categories_data.items():
            parent_tab = tab_objs[tab_key]
            
            for cat_title, code_tuples in cat_list:
                cat_frame = ctk.CTkFrame(parent_tab, fg_color=THEME["bg_inset"], corner_radius=8, border_width=1, border_color=THEME["border"])
                cat_frame.pack(fill="x", padx=6, pady=4)

                ctk.CTkLabel(
                    cat_frame,
                    text=f"❖ {cat_title}",
                    font=FONT_LABEL_BOLD,
                    text_color=THEME["accent_cyan"]
                ).pack(anchor="w", padx=10, pady=(6, 2))

                for code_str, desc in code_tuples:
                    item = ctk.CTkFrame(cat_frame, fg_color="transparent")
                    item.pack(fill="x", padx=8, pady=2)
                    item.columnconfigure(1, weight=1)

                    lbl_code = ctk.CTkLabel(item, text=code_str, font=FONT_LABEL_BOLD, text_color=THEME["success"], width=145, anchor="w")
                    lbl_code.grid(row=0, column=0, sticky="w", padx=(4, 4), pady=2)

                    lbl_desc = ctk.CTkLabel(item, text=desc, font=FONT_LABEL, text_color=THEME["text_primary"], anchor="w", justify="left")
                    lbl_desc.grid(row=0, column=1, sticky="w", padx=4, pady=2)

                    def make_launch_cmd(target_code=code_str):
                        print(f"\n[DEBUG CLICK SECRET CODE] 🚀 Bấm nút mở mã bí mật: {target_code}")
                        if not self._check_selected_device():
                            messagebox.showwarning("Cảnh báo", "Vui lòng kết nối điện thoại ADB để mở mã bí mật!", parent=dlg)
                            return
                        self.log(f"⚡ Đang gửi lệnh kích hoạt mã [{target_code}] tới điện thoại qua ADB...", "info")
                        def _thread():
                            try:
                                self.engine.launch_secret_code(self.selected_device_id, target_code, self.log)
                            except Exception as ex:
                                import traceback
                                print(f"[DEBUG ERROR] Lỗi khi gửi mã bí mật {target_code}:\n{traceback.format_exc()}")
                        self.executor.submit(_thread)

                    btn_launch = ctk.CTkButton(
                        item,
                        text="🚀 Mở",
                        font=FONT_LABEL_BOLD,
                        width=65,
                        height=26,
                        fg_color=THEME["accent_indigo"],
                        hover_color=THEME["bg_card_hover"],
                        command=make_launch_cmd
                    )
                    btn_launch.grid(row=0, column=2, sticky="e", padx=(4, 6), pady=2)

    def action_install_both_apks(self):
        """Install both Shizuku and Pixel IMS APKs manually onto target Android device in correct order."""
        if not self._check_selected_device():
            return
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        shizuku_path = os.path.join(base_dir, "Shizuku_13.6.0.r1091.b844bc49_APKPure.apk")
        pixel_ims_path = os.path.join(base_dir, "pixel-ims-1-3-2.apk")

        apks_to_install = [p for p in [shizuku_path, pixel_ims_path] if os.path.exists(p)]
        if not apks_to_install:
            messagebox.showerror("Lỗi", "Không tìm thấy các tệp APK Shizuku & Pixel IMS!")
            return

        self.is_working = True
        self.set_controls_enabled(False)
        self.set_status("Đang cài đặt bộ ứng dụng Shizuku & Pixel IMS lên điện thoại...", 0.3)
        self.executor.submit(self._run_install_both_apks_thread, apks_to_install)

    def _run_install_both_apks_thread(self, apk_paths: list[str]):
        dev_id = self.selected_device_id
        ok = self.engine.install_apks(dev_id, apk_paths, self.log)
        if ok:
            self.log("⚡ Đang tự động kích hoạt Shizuku Server & nạp cờ CarrierConfig...", "info")
            self.engine.start_shizuku_daemon(dev_id, self.log)
            self.engine.apply_pixel_ims_overrides(dev_id, self.log)
        self.after(0, lambda: self._on_action_completed(ok, "Cài đặt & Kích hoạt Shizuku & Pixel IMS"))

    def action_diagnostics(self):
        if not self._check_selected_device():
            return
        self.executor.submit(self._run_diagnostics_thread)

    def _run_diagnostics_thread(self):
        self.engine.open_radio_info_menu(self.selected_device_id, self.log)
        self.engine.check_ims_diagnostics(self.selected_device_id, self.log)

    def open_donate_dialog(self):
        """Open popup modal dialog displaying VietQR code and daughter milk call-to-action centered on screen."""
        from PIL import Image

        dlg = ctk.CTkToplevel(self)
        dlg.title("❤️ Ủng Hộ Tác Giả — Hộp Sữa Cho Con Gái 🍼")
        
        w, h = 480, 590
        dlg.update_idletasks()
        self.update_idletasks()
        screen_w = dlg.winfo_screenwidth()
        screen_h = dlg.winfo_screenheight()

        parent_x = self.winfo_x()
        parent_y = self.winfo_y()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()

        cx = parent_x + (parent_w - w) // 2
        cy = parent_y + (parent_h - h) // 2

        if cx < 0 or cy < 0 or cx > screen_w - 50 or cy > screen_h - 50:
            cx = (screen_w - w) // 2
            cy = (screen_h - h) // 2

        dlg.geometry(f"{w}x{h}+{max(0, cx)}+{max(0, cy)}")
        dlg.resizable(False, False)
        dlg.configure(fg_color=THEME["bg_app"])
        dlg.lift()
        dlg.focus_force()
        dlg.attributes("-topmost", True)
        dlg.after(200, lambda: dlg.attributes("-topmost", False))
        dlg.grab_set()

        # Title Banner
        banner = ctk.CTkFrame(dlg, fg_color=THEME["bg_card"], corner_radius=10, border_width=1, border_color=THEME["border"])
        banner.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(
            banner,
            text="❤️ HỘP SỮA CHO CON GÁI TÁC GIẢ 🍼",
            font=FONT_CARD_TITLE,
            text_color="#f43f5e"
        ).pack(pady=(10, 2))

        ctk.CTkLabel(
            banner,
            text="Nếu công cụ đã giúp bạn sửa lỗi VoLTE thành công và gọi thoại mượt mà,\ntiếc gì một hộp sữa nho nhỏ cho con gái của tác giả đúng không ạ? 🥰\nMọi ủng hộ của bạn là động lực rất lớn để tác giả tiếp tục nâng cấp tool!",
            font=FONT_SUBTITLE,
            text_color=THEME["text_secondary"],
            justify="center"
        ).pack(padx=12, pady=(0, 10))

        # QR Image Frame
        qr_frame = ctk.CTkFrame(dlg, fg_color=THEME["bg_inset"], corner_radius=12, border_width=1, border_color=THEME["border"])
        qr_frame.pack(padx=16, pady=4, fill="both", expand=True)

        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        qr_path = os.path.join(base_dir, "assets", "donate_qr.jpg")
        if os.path.exists(qr_path):
            try:
                pil_img = Image.open(qr_path)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(320, 350))
                lbl_qr = ctk.CTkLabel(qr_frame, image=ctk_img, text="")
                lbl_qr.pack(padx=10, pady=10)
            except Exception as e:
                ctk.CTkLabel(qr_frame, text=f"Lỗi tải ảnh QR: {e}", font=FONT_LABEL).pack(pady=40)
        else:
            ctk.CTkLabel(qr_frame, text="Vui lòng quét mã VietQR MB Bank bên trên!", font=FONT_LABEL).pack(pady=40)

        # Footer note
        ctk.CTkLabel(
            dlg,
            text="Ngân hàng: MB Bank (VietQR Nạp 24/7) — Chúc bạn ngày tốt lành! ✨",
            font=FONT_LABEL,
            text_color=THEME["text_muted"]
        ).pack(pady=(4, 6))

        def open_hangho_dlg():
            import webbrowser
            webbrowser.open("https://hangho.com/")

        btn_hangho_dlg = ctk.CTkButton(
            dlg,
            text="🛒 Dùng Thử PM Quản Lý Bán Hàng (HangHo.com) ⚡",
            font=FONT_LABEL_BOLD,
            fg_color="#10b981",
            hover_color="#059669",
            text_color="#ffffff",
            height=36,
            corner_radius=8,
            command=open_hangho_dlg
        )
        btn_hangho_dlg.pack(fill="x", padx=20, pady=(2, 12))

    def open_wireless_adb_dialog(self):
        """Open popup modal dialog for Wireless ADB pairing & connecting."""
        dlg = ctk.CTkToplevel(self)
        dlg.title("📶 Kết Nối ADB Wireless (Gỡ Lỗi Wi-Fi)")
        
        w, h = 460, 400
        dlg.update_idletasks()
        self.update_idletasks()
        screen_w = dlg.winfo_screenwidth()
        screen_h = dlg.winfo_screenheight()

        parent_x = self.winfo_x()
        parent_y = self.winfo_y()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()

        cx = parent_x + (parent_w - w) // 2
        cy = parent_y + (parent_h - h) // 2

        if cx < 0 or cy < 0 or cx > screen_w - 50 or cy > screen_h - 50:
            cx = (screen_w - w) // 2
            cy = (screen_h - h) // 2

        dlg.geometry(f"{w}x{h}+{max(0, cx)}+{max(0, cy)}")
        dlg.resizable(False, False)
        dlg.lift()
        dlg.focus_force()
        dlg.attributes("-topmost", True)
        dlg.after(200, lambda: dlg.attributes("-topmost", False))
        dlg.grab_set()

        lbl_title = ctk.CTkLabel(
            dlg,
            text="📶 GHÉP NỐI & KẾT NỐI ADB QUA WI-FI",
            font=FONT_CARD_TITLE,
            text_color=THEME["accent_cyan"]
        )
        lbl_title.pack(pady=(16, 8))

        lbl_info = ctk.CTkLabel(
            dlg,
            text="Bật 'Gỡ lỗi qua Wi-Fi' trong Cài đặt nhà phát triển trên điện thoại.\nChọn 'Ghép nối thiết bị bằng mã ghép nối'.",
            font=FONT_SUBTITLE,
            text_color=THEME["text_secondary"],
            justify="center"
        )
        lbl_info.pack(pady=(0, 10), padx=16)

        # 1. Pairing Section
        frame_pair = ctk.CTkFrame(dlg, fg_color=THEME["bg_card"], corner_radius=10, border_width=1, border_color=THEME["border"])
        frame_pair.pack(fill="x", padx=16, pady=6)

        ctk.CTkLabel(frame_pair, text="1. Ghép Nối (Pairing):", font=FONT_LABEL_BOLD, text_color=THEME["text_primary"]).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(8, 4))

        entry_pair_ip = ctk.CTkEntry(frame_pair, placeholder_text="IP:Port ghép nối (VD: 192.168.1.5:38195)", font=FONT_LABEL, height=32)
        entry_pair_ip.grid(row=1, column=0, padx=(10, 5), pady=4, sticky="ew")

        entry_pair_code = ctk.CTkEntry(frame_pair, placeholder_text="Mã 6 số", font=FONT_LABEL, width=90, height=32)
        entry_pair_code.grid(row=1, column=1, padx=(5, 10), pady=4, sticky="ew")

        def do_pair():
            ip = entry_pair_ip.get().strip()
            code = entry_pair_code.get().strip()
            if not ip or not code:
                messagebox.showwarning("Cảnh báo", "Vui lòng nhập đủ IP:Port ghép nối và Mã 6 số!", parent=dlg)
                return
            self.log(f"› Thử ghép nối ADB Wireless tới {ip}...", "info")
            def _thread():
                ok, msg = self.engine.pair_wireless_adb(ip, code, self.log)
                if ok:
                    self.after(0, lambda: messagebox.showinfo("Thành công", f"Ghép nối thành công!\n{msg}", parent=dlg))
                else:
                    self.after(0, lambda: messagebox.showerror("Lỗi", f"Ghép nối thất bại:\n{msg}", parent=dlg))
            self.executor.submit(_thread)

        btn_pair = ctk.CTkButton(frame_pair, text="🔗 Ghép Nối (ADB Pair)", font=FONT_BTN_GRID, fg_color=THEME["accent_indigo"], height=32, command=do_pair)
        btn_pair.grid(row=2, column=0, columnspan=2, padx=10, pady=(4, 10), sticky="ew")

        # 2. Connection Section
        frame_conn = ctk.CTkFrame(dlg, fg_color=THEME["bg_card"], corner_radius=10, border_width=1, border_color=THEME["border"])
        frame_conn.pack(fill="x", padx=16, pady=6)

        ctk.CTkLabel(frame_conn, text="2. Kết Nối (Connect):", font=FONT_LABEL_BOLD, text_color=THEME["text_primary"]).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))

        entry_conn_ip = ctk.CTkEntry(frame_conn, placeholder_text="IP:Port kết nối (VD: 192.168.1.5:41029)", font=FONT_LABEL, height=32)
        entry_conn_ip.grid(row=1, column=0, padx=10, pady=4, sticky="ew")

        def do_connect():
            ip = entry_conn_ip.get().strip()
            if not ip:
                messagebox.showwarning("Cảnh báo", "Vui lòng nhập IP:Port kết nối!", parent=dlg)
                return
            self.log(f"› Thử kết nối ADB Wireless tới {ip}...", "info")
            def _thread():
                ok, msg = self.engine.connect_wireless_adb(ip, self.log)
                if ok:
                    self.after(0, lambda: messagebox.showinfo("Thành công", f"Kết nối thành công!\n{msg}", parent=dlg))
                    self.after(0, self.refresh_devices_manual)
                    self.after(0, dlg.destroy)
                else:
                    self.after(0, lambda: messagebox.showerror("Lỗi", f"Kết nối thất bại:\n{msg}", parent=dlg))
            self.executor.submit(_thread)

        btn_conn = ctk.CTkButton(frame_conn, text="⚡ Kết Nối (ADB Connect)", font=FONT_BTN_GRID, fg_color=THEME["success"], hover_color=THEME["success_hover"], height=32, command=do_connect)
        btn_conn.grid(row=2, column=0, padx=10, pady=(4, 10), sticky="ew")

    def open_pixel_ims_panel(self):
        """Open interactive Pixel IMS control panel popup with visual toggles."""
        if not self._check_selected_device():
            return

        dlg = ctk.CTkToplevel(self)
        dlg.title("🎛️ Bảng Điều Khiển Công Tắc IMS (Pixel IMS Panel)")
        dlg.geometry("480x460")
        dlg.resizable(False, False)
        dlg.grab_set()

        lbl_title = ctk.CTkLabel(
            dlg,
            text="📱 BẢNG BẬT/TẮT CÔNG TẮC IMS (PIXEL IMS UI)",
            font=FONT_CARD_TITLE,
            text_color=THEME["accent_cyan"]
        )
        lbl_title.pack(pady=(16, 8))

        lbl_info = ctk.CTkLabel(
            dlg,
            text="Bật/Tắt riêng biệt từng tính năng VoLTE, VoWiFi và Cuộc Gọi Video HD.\nTương thích chuẩn Pixel IMS CarrierConfig Overrides.",
            font=FONT_SUBTITLE,
            text_color=THEME["text_secondary"],
            justify="center"
        )
        lbl_info.pack(pady=(0, 10), padx=16)

        # Toggle Switches Frame
        sw_frame = ctk.CTkFrame(dlg, fg_color=THEME["bg_card"], corner_radius=10, border_width=1, border_color=THEME["border"])
        sw_frame.pack(fill="x", padx=16, pady=6)

        sw_volte = ctk.CTkSwitch(sw_frame, text="Bật VoLTE (Voice over LTE)", font=FONT_LABEL_BOLD, text_color=THEME["text_primary"])
        sw_volte.pack(anchor="w", padx=16, pady=8)
        sw_volte.select()

        sw_vowifi = ctk.CTkSwitch(sw_frame, text="Bật VoWiFi (Wi-Fi Calling)", font=FONT_LABEL_BOLD, text_color=THEME["text_primary"])
        sw_vowifi.pack(anchor="w", padx=16, pady=8)
        sw_vowifi.select()

        sw_vt = ctk.CTkSwitch(sw_frame, text="Bật Cuộc Gọi Video HD (Video Telephony)", font=FONT_LABEL_BOLD, text_color=THEME["text_primary"])
        sw_vt.pack(anchor="w", padx=16, pady=8)
        sw_vt.select()

        sw_toggle = ctk.CTkSwitch(sw_frame, text="Hiện Công Tắc VoLTE Trong Cài Đặt Mạng", font=FONT_LABEL_BOLD, text_color=THEME["accent_blue"])
        sw_toggle.pack(anchor="w", padx=16, pady=8)
        sw_toggle.select()

        # Slot selector
        slot_frame = ctk.CTkFrame(dlg, fg_color="transparent")
        slot_frame.pack(fill="x", padx=16, pady=6)

        ctk.CTkLabel(slot_frame, text="Áp dụng cho:", font=FONT_LABEL_BOLD, text_color=THEME["text_muted"]).pack(side="left", padx=(0, 10))

        slot_var = tk.StringVar(value="all")
        rb_sim1 = ctk.CTkRadioButton(slot_frame, text="SIM 1", variable=slot_var, value="0", font=FONT_LABEL)
        rb_sim1.pack(side="left", padx=5)

        rb_sim2 = ctk.CTkRadioButton(slot_frame, text="SIM 2", variable=slot_var, value="1", font=FONT_LABEL)
        rb_sim2.pack(side="left", padx=5)

        rb_all = ctk.CTkRadioButton(slot_frame, text="Cả 2 SIM", variable=slot_var, value="all", font=FONT_LABEL)
        rb_all.pack(side="left", padx=5)

        def apply_custom_ims():
            is_volte = sw_volte.get() == 1
            is_vowifi = sw_vowifi.get() == 1
            is_vt = sw_vt.get() == 1
            is_show = sw_toggle.get() == 1
            target_slot = slot_var.get()

            self.log("📱 Đang nạp tùy chỉnh công tắc IMS...", "info")
            def _thread():
                if target_slot == "all":
                    self.engine.set_ims_feature_toggle(self.selected_device_id, is_volte, is_vowifi, is_vt, is_show, 0, self.log)
                    self.engine.set_ims_feature_toggle(self.selected_device_id, is_volte, is_vowifi, is_vt, is_show, 1, self.log)
                else:
                    sub = int(target_slot)
                    self.engine.set_ims_feature_toggle(self.selected_device_id, is_volte, is_vowifi, is_vt, is_show, sub, self.log)

                self.after(0, lambda: messagebox.showinfo("Thành công", "Đã áp dụng thành công tùy chỉnh công tắc IMS!", parent=dlg))
                self.after(0, dlg.destroy)

            self.executor.submit(_thread)

        btn_apply = ctk.CTkButton(
            dlg,
            text="⚡ ÁP DỤNG TÙY CHỈNH IMS",
            font=FONT_BTN_MAIN,
            fg_color=THEME["success"],
            hover_color=THEME["success_hover"],
            height=40,
            corner_radius=8,
            command=apply_custom_ims
        )
        btn_apply.pack(fill="x", padx=16, pady=(10, 16))

    def _on_action_completed(self, success: bool, action_name: str):
        self.is_working = False
        self.set_controls_enabled(True)
        if success:
            self.set_status(f"✓ Thao tác {action_name} hoàn tất!", 1.0)
        else:
            self.set_status(f"✗ Thao tác {action_name} gặp sự cố.", 0.0)
        self.executor.submit(self._fetch_device_details_async, self.selected_device_id)


def main():
    app = VoLTEFixerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
