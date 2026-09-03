"""
HBG VoLTE Fixer — Clean Customer-Friendly Vendor Patcher & Restore UI
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from vendor_engine import patch_vendor_image

class CustomerFriendlyVendorPatcherUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HBG VoLTE Fixer — Công Cụ Kích Hoạt & Khôi Phục VoLTE Chuyên Dụng")
        self.geometry("780x530")
        self.configure(bg="#0F172A")
        self.resizable(False, False)

        self.setup_ui()

    def setup_ui(self):
        # 1. Header Frame
        header = tk.Frame(self, bg="#1E293B", height=80)
        header.pack(fill="x")

        title = tk.Label(
            header,
            text="⚡ HBG VOLTE FIXER — BỘ CÔNG CỤ KÍCH HOẠT VOLTE CHUYÊN DỤNG",
            font=("Segoe UI", 15, "bold"),
            fg="#38BDF8",
            bg="#1E293B"
        )
        title.pack(anchor="w", padx=25, pady=(15, 2))

        sub = tk.Label(
            header,
            text="Hỗ trợ tự động mở khóa tính năng VoLTE & Cuộc gọi chất lượng cao HD Call cho điện thoại Android",
            font=("Segoe UI", 9),
            fg="#94A3B8",
            bg="#1E293B"
        )
        sub.pack(anchor="w", padx=25, pady=(0, 12))

        # Main Body Frame (Clean Single-Column Layout)
        body = tk.Frame(self, bg="#0F172A", padx=25, pady=18)
        body.pack(fill="both", expand=True)

        # File Selection Box
        lbl_file = tk.Label(
            body,
            text="📁 CHỌN TỆP CẤU HÌNH VENDOR (vendor.bin / vendor.img):",
            font=("Segoe UI", 10, "bold"),
            fg="#F8FAFC",
            bg="#0F172A"
        )
        lbl_file.pack(anchor="w", pady=(0, 6))

        file_box = tk.Frame(body, bg="#0F172A")
        file_box.pack(fill="x", pady=(0, 15))

        self.entry_path = tk.Entry(
            file_box,
            font=("Segoe UI", 10),
            bg="#1E293B",
            fg="#F8FAFC",
            insertbackground="#F8FAFC",
            bd=1,
            relief="solid"
        )
        self.entry_path.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 10))

        btn_browse = tk.Button(
            file_box,
            text="Chọn Tệp...",
            font=("Segoe UI", 9, "bold"),
            bg="#0EA5E9",
            fg="#FFFFFF",
            activebackground="#0284C7",
            bd=0,
            padx=16,
            command=self.browse_file
        )
        btn_browse.pack(side="right", ipady=4)

        # Action Buttons Frame (Kích Hoạt File + Live ADB Fix)
        btn_frame = tk.Frame(body, bg="#0F172A")
        btn_frame.pack(fill="x", pady=(0, 15))

        self.btn_patch = tk.Button(
            btn_frame,
            text="⚡ TẠO TỆP VÁ VENDOR VOLTE (CHO UNLOCKTOOL)",
            font=("Segoe UI", 10, "bold"),
            bg="#10B981",
            fg="#FFFFFF",
            activebackground="#059669",
            activeforeground="#FFFFFF",
            bd=0,
            pady=8,
            command=self.start_patching
        )
        self.btn_patch.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_live_fix = tk.Button(
            btn_frame,
            text="📲 SỬA VOLTE THANH SÓNG TRỰC TIẾP QUA ADB",
            font=("Segoe UI", 10, "bold"),
            bg="#8B5CF6",
            fg="#FFFFFF",
            activebackground="#7C3AED",
            activeforeground="#FFFFFF",
            bd=0,
            pady=8,
            command=self.start_live_fix
        )
        self.btn_live_fix.pack(side="right", fill="x", expand=True, padx=(5, 0))

        # Log Output Console
        lbl_log = tk.Label(
            body,
            text="📋 NHẬT KÝ THỰC THI THIẾT BỊ:",
            font=("Segoe UI", 10, "bold"),
            fg="#F8FAFC",
            bg="#0F172A"
        )
        lbl_log.pack(anchor="w", pady=(0, 5))

        self.txt_log = tk.Text(
            body,
            font=("Consolas", 9),
            bg="#020617",
            fg="#38BDF8",
            insertbackground="#38BDF8",
            bd=1,
            relief="solid",
            height=11
        )
        self.txt_log.pack(fill="both", expand=True)

        self.log_msg("=== HBG VOLTE FIXER — SẴN SÀNG ĐÓNG GÓI BẢN VÁ VENDOR & LIVE FIX ===")
        self.log_msg("👉 Chọn [TẠO TỆP VÁ VENDOR VOLTE] nếu nạp qua UnlockTool.")
        self.log_msg("👉 Hoặc chọn [SỬA VOLTE THANH SÓNG TRỰC TIẾP QUA ADB] cho máy đang cắm cáp.")

    def log_msg(self, msg):
        self.txt_log.insert(tk.END, msg + "\n")
        self.txt_log.see(tk.END)

    def browse_file(self):
        fpath = filedialog.askopenfilename(
            title="Chọn Tệp Vendor Image/Binary",
            filetypes=[("Vendor Partition Image", "*.bin *.img"), ("All Files", "*.*")]
        )
        if fpath:
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, fpath)
            self.log_msg(f"📁 Đã chọn tệp: {fpath}")

    def start_patching(self):
        fpath = self.entry_path.get().strip()
        if not fpath or not os.path.exists(fpath):
            messagebox.showerror("Lỗi", "Vui lòng chọn tệp vendor.bin hoặc vendor.img hợp lệ!")
            return

        self.btn_patch.config(state="disabled")
        self.btn_live_fix.config(state="disabled")
        threading.Thread(target=self.run_patch_thread, args=(fpath,), daemon=True).start()

    def run_patch_thread(self, fpath):
        try:
            self.log_msg(f"\n⚡ Đang tiến hành kích hoạt tính năng VoLTE cho [{os.path.basename(fpath)}]...")
            out_file = patch_vendor_image(fpath)
            if out_file:
                self.log_msg(f"🎉 KÍCH HOẠT THÀNH CÔNG! Tệp đã nạp hoàn tất tại:")
                self.log_msg(f"👉 {out_file}")
                self.log_msg("\n👉 HƯỚNG DẪN NẠP LÊN ĐIỆN THOẠI BẰNG UNLOCKTOOL:")
                self.log_msg("   1. Mở UnlockTool -> Tab MediaTek hoặc Qualcomm.")
                self.log_msg(f"   2. Chọn tệp [{os.path.basename(out_file)}] vào phân vùng vendor.")
                self.log_msg("   3. Bấm nút [FLASH] (Tia sét ⚡).")
                messagebox.showinfo("Thành công", f"Đã tạo tệp vá Vendor VoLTE thành công!\n\nTệp đầu ra:\n{out_file}")
        except Exception as ex:
            self.log_msg(f"❌ Lỗi thực thi: {ex}")
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {ex}")
        finally:
            self.btn_patch.config(state="normal")
            self.btn_live_fix.config(state="normal")

    def start_live_fix(self):
        self.btn_patch.config(state="disabled")
        self.btn_live_fix.config(state="disabled")
        threading.Thread(target=self.run_live_fix_thread, daemon=True).start()

    def run_live_fix_thread(self):
        try:
            self.log_msg("\n📲 Đang thực thi Sửa VoLTE Thanh Sóng Trực Tiếp Qua ADB...")
            script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scratch/apply_live_oppo_volte_fix.py"))
            if os.path.exists(script_path):
                import subprocess
                res = subprocess.run([sys.executable, script_path], capture_output=True, text=True, errors="ignore")
                self.log_msg(res.stdout)
                if res.stderr:
                    self.log_msg(res.stderr)
                messagebox.showinfo("Hoàn tất Live Fix", "Đã thực thi nạp cấu hình VoLTE trực tiếp qua ADB!")
            else:
                self.log_msg(f"❌ Không tìm thấy tệp script: {script_path}")
        except Exception as ex:
            self.log_msg(f"❌ Lỗi thực thi Live Fix: {ex}")
            messagebox.showerror("Lỗi", f"Lỗi thực thi Live Fix: {ex}")
        finally:
            self.btn_patch.config(state="normal")
            self.btn_live_fix.config(state="normal")

    def start_restore(self):
        self.log_msg("\n🛡️ Đang thực hiện khôi phục về cài đặt mặc định...")
        try:
            from restore_engine import main as run_restore
            run_restore()
            self.log_msg("🎉 Đã hoàn tất khôi phục cài đặt gốc mặc định!")
            messagebox.showinfo("Khôi Phục", "Đã hoàn tất khôi phục cài đặt VoLTE về mặc định!")
        except Exception as ex:
            self.log_msg(f"⚠ Lỗi khôi phục: {ex}")

if __name__ == "__main__":
    app = CustomerFriendlyVendorPatcherUI()
    app.mainloop()
