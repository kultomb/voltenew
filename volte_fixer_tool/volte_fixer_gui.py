"""
HBG VoLTE Fixer GUI — Standalone Modern Tool
Dedicated, lightweight, and modern UI specialized for VoLTE fixing on Android.
100% ADB device detection parity with HBGAdBlocker.
"""

from __future__ import annotations

import os
import sys
import time
import datetime
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import ttk, messagebox

import customtkinter as ctk

# Ensure engine module can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from volte_engine import VoLTEEngine

# ---------------------------------------------------------------------------
# Color Palette & Styling Tokens (SaaS Dark Cyber Theme)
# ---------------------------------------------------------------------------
THEME = {
    "bg_app": "#0b0e14",
    "bg_card": "#151b26",
    "bg_card_hover": "#1c2433",
    "bg_inset": "#0e131d",
    "bg_terminal": "#070a0f",
    "border": "#263042",
    "border_highlight": "#3b82f6",
    "text_primary": "#f3f4f6",
    "text_secondary": "#9ca3af",
    "text_muted": "#6b7280",
    "accent_blue": "#3b82f6",
    "accent_indigo": "#6366f1",
    "accent_cyan": "#06b6d4",
    "success": "#10b981",
    "success_hover": "#059669",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "danger_hover": "#dc2626",
}

LOG_COLORS = {
    "timestamp": "#6b7280",
    "info": "#38bdf8",
    "success": "#34d399",
    "warning": "#fbbf24",
    "error": "#f87171",
}


class VoLTEFixerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Config
        self.title("HBG VoLTE & IMS Fixer ⚡ (Xiaomi, Vivo, OPPO, Samsung, Pixel)")
        self.geometry("900x520")
        self.resizable(False, False)
        
        # Configure appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.configure(fg_color=THEME["bg_app"])

        # Engine & Assets
        self.engine = VoLTEEngine()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.dex_path = os.path.join(base_dir, "assets", "hbg_volte_fixer.dex")
        if not os.path.exists(self.dex_path):
            self.dex_path = os.path.join(os.path.dirname(base_dir), "core", "assets", "hbg_volte_fixer.dex")

        # State Variables
        self.devices: list[dict] = []
        self.selected_device_id: str | None = None
        self.is_working = False
        self.is_running = True

        # Handle window close cleanly
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Build UI
        self._build_ui()

        # Print startup log to CMD console
        self.log("=== HBG VoLTE & IMS Fixer Started ===", "info")
        self.log(f"Đường dẫn ADB: {self.engine.adb_path}", "info")
        self.log("Tự động nhận diện ADB chuẩn 100% đồng bộ với HBGAdBlocker", "info")

        # Start continuous background ADB auto-detection thread
        self.start_device_auto_check()

    def _build_ui(self):
        """Construct all UI components."""
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=16, pady=12)

        # 1. Header Bar
        self._build_header()

        # 2. Main Grid Layout
        self.grid_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, pady=(12, 0))

        self.top_grid = ctk.CTkFrame(self.grid_frame, fg_color="transparent")
        self.top_grid.pack(fill="x")
        self.top_grid.columnconfigure(0, weight=4)
        self.top_grid.columnconfigure(1, weight=5)

        self._build_device_card(self.top_grid)
        self._build_actions_panel(self.top_grid)

        # 3. Progress Bar & Status Line
        self._build_progress_bar()

    def _build_header(self):
        header = ctk.CTkFrame(self.main_container, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        header.pack(fill="x")

        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        title_frame = ctk.CTkFrame(inner, fg_color="transparent")
        title_frame.pack(side="left")

        title_lbl = ctk.CTkLabel(
            title_frame,
            text="⚡ HBG VoLTE & IMS Fixer",
            font=("Segoe UI", 20, "bold"),
            text_color=THEME["text_primary"]
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            title_frame,
            text="Công cụ ép bật VoLTE / VoWiFi chuyên dụng cho Xiaomi, Vivo, OPPO, Samsung, Pixel",
            font=("Segoe UI", 12),
            text_color=THEME["text_secondary"]
        )
        sub_lbl.pack(anchor="w", pady=(2, 0))

        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(side="right")

        self.status_badge = ctk.CTkLabel(
            btn_frame,
            text="● Bị ngắt kết nối",
            font=("Segoe UI", 12, "bold"),
            text_color=THEME["danger"],
            fg_color=THEME["bg_inset"],
            corner_radius=20,
            padx=12,
            pady=4
        )
        self.status_badge.pack(side="left", padx=(0, 10))

        self.btn_refresh = ctk.CTkButton(
            btn_frame,
            text="↻ Tải lại ADB",
            font=("Segoe UI", 12, "bold"),
            fg_color=THEME["accent_indigo"],
            hover_color=THEME["accent_blue"],
            width=110,
            height=34,
            command=self.refresh_devices_manual
        )
        self.btn_refresh.pack(side="left")

    def _build_device_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=4)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=12)

        ctk.CTkLabel(
            inner,
            text="📱 THIẾT BỊ ĐANG KẾT NỐI",
            font=("Segoe UI", 12, "bold"),
            text_color=THEME["accent_cyan"]
        ).pack(anchor="w")

        self.device_option = ctk.CTkOptionMenu(
            inner,
            values=["Đang quét ADB tự động..."],
            command=self.on_device_selected,
            font=("Segoe UI", 12),
            dropdown_font=("Segoe UI", 12),
            fg_color=THEME["bg_inset"],
            button_color=THEME["accent_indigo"],
            button_hover_color=THEME["accent_blue"],
            height=34
        )
        self.device_option.pack(fill="x", pady=(8, 12))

        self.info_frame = ctk.CTkFrame(inner, fg_color=THEME["bg_inset"], corner_radius=8, border_width=1, border_color=THEME["border"])
        self.info_frame.pack(fill="both", expand=True)

        self.lbl_model = self._create_info_row("Model thiết bị:", "Chưa kết nối")
        self.lbl_brand = self._create_info_row("Hãng sản xuất:", "---")
        self.lbl_android = self._create_info_row("Phiên bản Android:", "---")
        self.lbl_sim = self._create_info_row("Nhà mạng SIM:", "---")
        self.lbl_ims = self._create_info_row("Trạng thái VoLTE:", "---")

    def _create_info_row(self, title: str, default_val: str) -> ctk.CTkLabel:
        row = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=4)

        ctk.CTkLabel(row, text=title, font=("Segoe UI", 11), text_color=THEME["text_muted"], width=130, anchor="w").pack(side="left")
        val_lbl = ctk.CTkLabel(row, text=default_val, font=("Segoe UI", 11, "bold"), text_color=THEME["text_primary"], anchor="w")
        val_lbl.pack(side="left", fill="x", expand=True)
        return val_lbl

    def _build_actions_panel(self, parent):
        card = ctk.CTkFrame(parent, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=4)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=12)

        ctk.CTkLabel(
            inner,
            text="⚙️ THAO TÁC ÉP BẬT VoLTE",
            font=("Segoe UI", 12, "bold"),
            text_color=THEME["accent_cyan"]
        ).pack(anchor="w", pady=(0, 6))

        # Main Smart Auto-Fix Button (Covers ALL brands: Xiaomi, Vivo, OPPO, Samsung, Pixel)
        self.btn_all_in_one = ctk.CTkButton(
            inner,
            text="⚡ ÉP BẬT VoLTE TỰ ĐỘNG (CHO TẤT CẢ CÁC MÁY)",
            font=("Segoe UI", 13, "bold"),
            fg_color=THEME["success"],
            hover_color=THEME["success_hover"],
            height=44,
            corner_radius=8,
            command=self.action_fix_all_in_one
        )
        self.btn_all_in_one.pack(fill="x", pady=(0, 8))

        # 2x2 Grid of Explicit Utility Buttons
        mod_grid = ctk.CTkFrame(inner, fg_color="transparent")
        mod_grid.pack(fill="x")
        mod_grid.columnconfigure(0, weight=1)
        mod_grid.columnconfigure(1, weight=1)

        # Button 1: Menu 4636 for Xiaomi, Vivo, Samsung, Pixel, AOSP
        self.btn_menu_4636 = ctk.CTkButton(
            mod_grid, text="📱 1. Mở Menu Mạng Nâng Cao (Xiaomi/Vivo/Pixel)", font=("Segoe UI", 10, "bold"),
            fg_color=THEME["bg_inset"], hover_color=THEME["bg_card_hover"],
            border_width=1, border_color=THEME["border"], height=34,
            command=self.action_open_4636
        )
        self.btn_menu_4636.grid(row=0, column=0, sticky="ew", padx=(0, 3), pady=3)

        # Button 2: MTK EngineerMode for OPPO / Realme / MTK
        self.btn_menu_mtk = ctk.CTkButton(
            mod_grid, text="🔧 2. Mở Cấu Hình Chuyên Sâu (OPPO/Realme)", font=("Segoe UI", 10, "bold"),
            fg_color=THEME["bg_inset"], hover_color=THEME["bg_card_hover"],
            border_width=1, border_color=THEME["border"], height=34,
            command=self.action_open_mtk
        )
        self.btn_menu_mtk.grid(row=0, column=1, sticky="ew", padx=(3, 0), pady=3)

        # Button 3: Diagnostic IMS Status
        self.btn_diag = ctk.CTkButton(
            mod_grid, text="🔍 3. Kiểm Tra Trạng Thái VoLTE", font=("Segoe UI", 10, "bold"),
            fg_color=THEME["bg_inset"], hover_color=THEME["bg_card_hover"],
            border_width=1, border_color=THEME["border"], height=34,
            command=self.action_diagnostics
        )
        self.btn_diag.grid(row=1, column=0, sticky="ew", padx=(0, 3), pady=3)

        # Button 4: Inject System Props Manual
        self.btn_props = ctk.CTkButton(
            mod_grid, text="📡 4. Kích Hoạt Cấu Hình Thủ Công", font=("Segoe UI", 10, "bold"),
            fg_color=THEME["bg_inset"], hover_color=THEME["bg_card_hover"],
            border_width=1, border_color=THEME["border"], height=34,
            command=self.action_fix_props
        )
        self.btn_props.grid(row=1, column=1, sticky="ew", padx=(3, 0), pady=3)

    def _build_progress_bar(self):
        prog_card = ctk.CTkFrame(self.grid_frame, fg_color=THEME["bg_card"], corner_radius=12, border_width=1, border_color=THEME["border"])
        prog_card.pack(fill="x", pady=(14, 0))

        inner = ctk.CTkFrame(prog_card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)

        status_bar = ctk.CTkFrame(inner, fg_color="transparent")
        status_bar.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            status_bar,
            text="📊 TRẠNG THÁI TIẾN TRÌNH",
            font=("Segoe UI", 11, "bold"),
            text_color=THEME["accent_cyan"]
        ).pack(side="left")

        self.lbl_status = ctk.CTkLabel(
            status_bar,
            text="Đang tự động nhận diện thiết bị ADB...",
            font=("Segoe UI", 11),
            text_color=THEME["text_secondary"]
        )
        self.lbl_status.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(
            inner,
            height=8,
            corner_radius=4,
            fg_color=THEME["bg_inset"],
            progress_color=THEME["accent_indigo"]
        )
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)



    # ---------------------------------------------------------------------------
    # ADB Device Monitor Thread (100% Parity with HBGAdBlocker DeviceManager)
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
            except Exception as e:
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

    def _fetch_device_details_async(self, device_id: str):
        try:
            info = self.engine.get_device_info(device_id)
            if self.selected_device_id == device_id:
                self.after(0, lambda: self._apply_device_specs(info))
        except Exception:
            pass

    def _on_adb_disconnected(self):
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
        print(f"{now} [{level.upper()}] {message}", flush=True)

    def set_status(self, text: str, progress: float = 0.0):
        self.after(0, lambda: self._update_status(text, progress))

    def _update_status(self, text: str, progress: float):
        self.lbl_status.configure(text=text)
        self.progress_bar.set(progress)

    def set_controls_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.btn_all_in_one.configure(state=state)
        self.btn_menu_4636.configure(state=state)
        self.btn_menu_mtk.configure(state=state)
        self.btn_diag.configure(state=state)
        self.btn_props.configure(state=state)
        self.btn_refresh.configure(state=state)

    def on_closing(self):
        self.is_running = False
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
        self.set_status("Đang thực hiện ép VoLTE tự động thông minh...", 0.2)
        self.executor.submit(self._run_all_in_one_thread)

    def _run_all_in_one_thread(self):
        dev_id = self.selected_device_id
        res = self.engine.smart_fix_all(dev_id, self.dex_path, self.log)
        self.after(0, lambda: self._on_action_completed(res, "Ép Bật VoLTE Tự Động"))

    def action_open_4636(self):
        if not self._check_selected_device():
            return
        self.executor.submit(lambda: self.engine.open_radio_info_menu(self.selected_device_id, self.log))

    def action_open_mtk(self):
        if not self._check_selected_device():
            return
        self.executor.submit(lambda: self.engine.open_mtk_engineer_menu(self.selected_device_id, self.log))

    def action_fix_props(self):
        if not self._check_selected_device():
            return
        self.is_working = True
        self.set_controls_enabled(False)
        self.set_status("Đang nạp cấu hình hệ thống...", 0.3)
        self.executor.submit(self._run_props_thread)

    def _run_props_thread(self):
        res = self.engine.fix_system_props(self.selected_device_id, self.log)
        self.after(0, lambda: self._on_action_completed(res, "Kích Hoạt Cấu Hình Thủ Công"))

    def action_diagnostics(self):
        if not self._check_selected_device():
            return
        self.executor.submit(lambda: self.engine.check_ims_diagnostics(self.selected_device_id, self.log))

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
