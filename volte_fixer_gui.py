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
FONT_FAMILY = ("Segoe UI", "Montserrat", "Arial", "sans-serif")
FONT_TITLE = (FONT_FAMILY[0], 19, "bold")
FONT_SUBTITLE = (FONT_FAMILY[0], 11)
FONT_CARD_TITLE = (FONT_FAMILY[0], 12, "bold")
FONT_LABEL = (FONT_FAMILY[0], 11)
FONT_LABEL_BOLD = (FONT_FAMILY[0], 11, "bold")
FONT_BTN_MAIN = (FONT_FAMILY[0], 13, "bold")
FONT_BTN_GRID = (FONT_FAMILY[0], 11, "bold")
FONT_MONO = ("Consolas", 10)

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

        # Window Configuration
        self.title("HBG VoLTE & IMS Fixer ⚡ (Professional Android Controller & VoLTE Auto-Fix)")
        self.geometry("820x560")
        self.resizable(False, False)

        # CustomTkinter Appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.configure(fg_color=THEME["bg_app"])

        # Engine & Multi-threading
        self.engine = VoLTEEngine()
        self.executor = ThreadPoolExecutor(max_workers=6)

        base_dir = os.path.dirname(os.path.abspath(__file__))
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

        # Logs
        self.log("=== HBG VoLTE & IMS Fixer Started ===", "info")
        self.log(f"Đường dẫn ADB: {self.engine.adb_path}", "info")
        if os.path.exists(self.scrcpy_bin):
            self.log("✓ Đã nạp Engine Scrcpy v2.7 60 FPS Standalone Live Streamer", "success")

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

        # 3. Actions Panel (Single Hero 1-Click Fix Button)
        self._build_actions_panel(self.main_container)

        # 4. Progress Status Bar
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

        badge_ver = ctk.CTkLabel(
            title_row,
            text="v3.5 ULTRA",
            font=FONT_LABEL_BOLD,
            text_color=THEME["accent_cyan"],
            fg_color=THEME["bg_inset"],
            corner_radius=6,
            padx=8,
            pady=2
        )
        badge_ver.pack(side="left", padx=(8, 0))

        sub_lbl = ctk.CTkLabel(
            title_frame,
            text="Công cụ ép bật cờ VoLTE & IMS 1-Click tự động chuyên nghiệp cho Android",
            font=FONT_SUBTITLE,
            text_color=THEME["text_secondary"]
        )
        sub_lbl.pack(anchor="w", pady=(2, 0))

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
            text="📱 Màn Hình Live (60 FPS)",
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
        self.btn_live_screen.pack(side="left")

    def _build_device_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        card.pack(fill="x", pady=(0, 8))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(
            inner,
            text="❖ THIẾT BỊ ĐANG KẾT NỐI",
            font=FONT_CARD_TITLE,
            text_color=THEME["accent_cyan"]
        ).pack(anchor="w")

        self.device_option = ctk.CTkOptionMenu(
            inner,
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
            height=32,
            corner_radius=8
        )
        self.device_option.pack(fill="x", pady=(6, 8))

        self.info_frame = ctk.CTkFrame(inner, fg_color=THEME["bg_inset"], corner_radius=8, border_width=1, border_color=THEME["border"])
        self.info_frame.pack(fill="x")

        info_grid = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        info_grid.pack(fill="x", padx=10, pady=6)
        info_grid.columnconfigure(0, weight=1)
        info_grid.columnconfigure(1, weight=1)

        self.lbl_model = self._create_info_cell(info_grid, 0, 0, "Model:", "Chưa kết nối")
        self.lbl_brand = self._create_info_cell(info_grid, 0, 1, "Hãng sản xuất:", "---")
        self.lbl_android = self._create_info_cell(info_grid, 1, 0, "Android:", "---")
        self.lbl_sim = self._create_info_cell(info_grid, 1, 1, "Nhà mạng SIM:", "---")
        self.lbl_ims = self._create_info_cell(info_grid, 2, 0, "Trạng thái VoLTE:", "---", col_span=2)

    def _create_info_cell(self, parent, row: int, col: int, title: str, default_val: str, col_span: int = 1) -> ctk.CTkLabel:
        cell = ctk.CTkFrame(parent, fg_color="transparent")
        cell.grid(row=row, column=col, columnspan=col_span, sticky="ew", padx=4, pady=2)

        ctk.CTkLabel(cell, text=title, font=FONT_LABEL, text_color=THEME["text_muted"], width=110, anchor="w").pack(side="left")
        val_lbl = ctk.CTkLabel(cell, text=default_val, font=FONT_LABEL_BOLD, text_color=THEME["text_primary"], anchor="w")
        val_lbl.pack(side="left", fill="x", expand=True)
        return val_lbl

    def _build_actions_panel(self, parent):
        card = ctk.CTkFrame(parent, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        card.pack(fill="x", pady=(0, 8))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(
            inner,
            text="⚙ KÍCH HOẠT VoLTE & CÀI ĐẶT THỦ CÔNG",
            font=FONT_CARD_TITLE,
            text_color=THEME["accent_cyan"]
        ).pack(anchor="w", pady=(0, 8))

        # Main Hero 1-Click Auto-Fix Button
        self.btn_all_in_one = ctk.CTkButton(
            inner,
            text="⚡ KÍCH HOẠT VoLTE TỰ ĐỘNG (1-CLICK FIX)",
            font=FONT_BTN_MAIN,
            fg_color=THEME["success"],
            hover_color=THEME["success_hover"],
            height=46,
            corner_radius=10,
            command=self.action_fix_all_in_one
        )
        self.btn_all_in_one.pack(fill="x", pady=(0, 8))

        # Secondary row with 4 buttons grid
        grid_sub = ctk.CTkFrame(inner, fg_color="transparent")
        grid_sub.pack(fill="x")
        grid_sub.columnconfigure(0, weight=1)
        grid_sub.columnconfigure(1, weight=1)

        self.btn_cmw500 = ctk.CTkButton(
            grid_sub,
            text="🧪 BẬT CMW500 & ViLTE (CỔ)",
            font=FONT_BTN_GRID,
            fg_color=THEME["bg_inset"],
            hover_color=THEME["bg_card_hover"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["accent_cyan"],
            height=36,
            corner_radius=8,
            command=self.action_enable_cmw500
        )
        self.btn_cmw500.grid(row=0, column=0, padx=(0, 4), pady=(0, 4), sticky="ew")

        self.btn_ims_apn = ctk.CTkButton(
            grid_sub,
            text="📡 NẠP APN IMS TỰ ĐỘNG",
            font=FONT_BTN_GRID,
            fg_color=THEME["bg_inset"],
            hover_color=THEME["bg_card_hover"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["accent_cyan"],
            height=36,
            corner_radius=8,
            command=self.action_inject_ims_apn
        )
        self.btn_ims_apn.grid(row=0, column=1, padx=(4, 0), pady=(0, 4), sticky="ew")

        self.btn_install_apks = ctk.CTkButton(
            grid_sub,
            text="📦 CÀI ĐẶT BỘ ỨNG DỤNG SHIZUKU & PIXEL IMS",
            font=FONT_BTN_GRID,
            fg_color=THEME["bg_inset"],
            hover_color=THEME["bg_card_hover"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["accent_cyan"],
            height=36,
            corner_radius=8,
            command=self.action_install_both_apks
        )
        self.btn_install_apks.grid(row=1, column=0, columnspan=2, pady=(2, 0), sticky="ew")

    def _build_progress_bar(self, parent):
        prog_card = ctk.CTkFrame(parent, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        prog_card.pack(fill="x", pady=(0, 8))

        inner = ctk.CTkFrame(prog_card, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=8)

        status_bar = ctk.CTkFrame(inner, fg_color="transparent")
        status_bar.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            status_bar,
            text="► TRẠNG THÁI TIẾN TRÌNH",
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
            text="💻 NHẬT KÝ VÀ TIẾN TRÌNH LỆNH (LOG CONSOLE)",
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

    # ---------------------------------------------------------------------------
    # Scrcpy Native Hardware Streaming Engine (Standalone Native Window Mode)
    # ---------------------------------------------------------------------------
    def start_scrcpy_stream(self, device_id: str):
        """Launch Scrcpy ultra-fast 60 FPS stream in a standalone native window."""
        if not os.path.exists(self.scrcpy_bin):
            self.log("⚠ Không tìm thấy Engine Scrcpy v2.7 để truyền luồng 60 FPS.", "warning")
            return

        self.stop_scrcpy_stream()

        # Dynamically calculate window position to open Scrcpy balanced on the RIGHT side of main tool window
        try:
            self.update_idletasks()
            tool_x = self.winfo_x()
            tool_y = self.winfo_y()
            tool_w = self.winfo_width()
            target_x = tool_x + tool_w + 14
            target_y = max(0, tool_y)
        except Exception:
            target_x = 850
            target_y = 100

        cmd = [
            self.scrcpy_bin,
            "-s", device_id,
            "--no-audio",
            "--window-title", f"Màn Hình Android Live — [{device_id}]",
            f"--window-x={target_x}",
            f"--window-y={target_y}",
            "--always-on-top"
        ]

        try:
            self.scrcpy_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
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
        self.set_status("Sẵn sàng thực hiện ép cờ VoLTE.", 1.0)
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
        self.lbl_model.configure(text=info.get("model", "Unknown"))
        self.lbl_brand.configure(text=info.get("brand", "Unknown"))
        self.lbl_android.configure(text=f"{info.get('android_ver', '')} ({info.get('sdk', '')})")
        self.lbl_sim.configure(text=info.get("operator", "Chưa rõ"))
        self.lbl_ims.configure(text=info.get("ims_status", "---"))

    # ---------------------------------------------------------------------------
    # Logging & Status Helpers
    # ---------------------------------------------------------------------------
    def log(self, message: str, level: str = "info"):
        now = datetime.datetime.now().strftime("[%H:%M:%S]")
        line = f"{now} [{level.upper()}] {message}\n"
        self.after(0, lambda: self._append_log_to_txt(line))

    def _append_log_to_txt(self, line: str):
        if hasattr(self, "txt_log") and self.txt_log:
            self.txt_log.configure(state="normal")
            self.txt_log.insert("end", line)
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
            getattr(self, "btn_cmw500", None),
            getattr(self, "btn_ims_apn", None),
            getattr(self, "btn_install_apks", None),
            getattr(self, "btn_refresh", None),
            getattr(self, "btn_live_screen", None),
        ]
        for btn in buttons:
            if btn is not None:
                btn.configure(state=state)

    def on_closing(self):
        self.is_running = False
        self.stop_scrcpy_stream()
        self.destroy()

    # ---------------------------------------------------------------------------
    # Action Handlers
    # ---------------------------------------------------------------------------
    def _check_selected_device(self) -> bool:
        if not self.selected_device_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng kết nối và bật ADB Debugging trên điện thoại Android trước!")
            return False
        return True

    def action_fix_all_in_one(self):
        """Single Smart Auto-Fix Button action for ALL brands."""
        if not self._check_selected_device():
            return
        self.is_working = True
        self.set_controls_enabled(False)
        self.set_status("Đang thực hiện kích hoạt VoLTE tự động 1-Click...", 0.2)
        self.executor.submit(self._run_all_in_one_thread)

    def _run_all_in_one_thread(self):
        dev_id = self.selected_device_id
        res = self.engine.smart_fix_all(dev_id, self.dex_path, self.log)
        self.after(0, lambda: self._on_action_completed(res, "Kích Hoạt VoLTE Tự Động"))

    def action_enable_cmw500(self):
        """Force-enable CMW500 Lab Test mode and ViLTE on legacy Android."""
        if not self._check_selected_device():
            return
        self.is_working = True
        self.set_controls_enabled(False)
        self.set_status("Đang kích hoạt Chế Độ CMW500 Mode & ViLTE Enable...", 0.4)
        self.executor.submit(self._run_enable_cmw500_thread)

    def _run_enable_cmw500_thread(self):
        dev_id = self.selected_device_id
        res = self.engine.enable_cmw500_legacy_fix(dev_id, self.log)
        self.after(0, lambda: self._on_action_completed(res, "Bật Chế Độ CMW500 Mode & ViLTE"))

    def action_inject_ims_apn(self):
        """Auto-inject IMS APN profile into Android database."""
        if not self._check_selected_device():
            return
        self.is_working = True
        self.set_controls_enabled(False)
        self.set_status("Đang tự động nạp cấu hình APN IMS cho các nhà mạng...", 0.4)
        self.executor.submit(self._run_inject_ims_apn_thread)

    def _run_inject_ims_apn_thread(self):
        dev_id = self.selected_device_id
        res = self.engine.inject_ims_apn(dev_id, self.log)
        self.after(0, lambda: self._on_action_completed(res, "Nạp Cấu Hình APN IMS"))

    def action_install_both_apks(self):
        """Install both Shizuku and Pixel IMS APKs manually onto target Android device in correct order."""
        if not self._check_selected_device():
            return
        base_dir = os.path.dirname(os.path.abspath(__file__))
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

    def open_wireless_adb_dialog(self):
        """Open popup modal dialog for Wireless ADB pairing & connecting."""
        dlg = ctk.CTkToplevel(self)
        dlg.title("📶 Kết Nối ADB Wireless (Gỡ Lỗi Wi-Fi)")
        dlg.geometry("460x400")
        dlg.resizable(False, False)
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
