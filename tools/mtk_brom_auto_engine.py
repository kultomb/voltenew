"""
HBG VoLTE Fixer — Integrated MediaTek BROM 1-Click Auto Engine (Dump -> Patch -> Flash)
Uses native mtkclient library from 'C:\\Users\\CMD\\Desktop\\Tool android\\mtkclient\\mtk.py'
"""

import os
import sys
import time
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

MTK_CLIENT_PY = r"C:\Users\CMD\Desktop\Tool android\mtkclient\mtk.py"

def is_mtkclient_available() -> bool:
    return os.path.exists(MTK_CLIENT_PY)

import re
import threading

_current_brom_process = None
_cancel_requested = False

def cancel_brom_process():
    global _current_brom_process, _cancel_requested
    _cancel_requested = True
    if _current_brom_process:
        try:
            _current_brom_process.kill()
        except Exception:
            pass
        _current_brom_process = None

def run_mtk_command(cmd_args: list, log_cb=print, timeout: int = 40) -> tuple[bool, str]:
    """
    Executes an mtkclient command via python launcher with clean log filtering and cancellation.
    """
    global _current_brom_process, _cancel_requested
    _cancel_requested = False

    if not is_mtkclient_available():
        err_msg = f"❌ Không tìm thấy bộ công cụ BROM mtkclient tại: {MTK_CLIENT_PY}"
        log_cb(err_msg, "error")
        return False, err_msg

    python_exe = sys.executable
    full_cmd = [python_exe, MTK_CLIENT_PY] + cmd_args
    
    # Filter list for spam lines to ignore
    ignore_keywords = [
        "hint:", "power off", "for brom mode", "for preloader mode",
        "if it is already connected", "please reconnect mobile", "metamodes",
        "couldn't get device configuration", "deviceclass", "[lib]:", "libusb", "usb.core"
    ]

    try:
        process = subprocess.Popen(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="ignore",
            cwd=os.path.dirname(MTK_CLIENT_PY)
        )
        _current_brom_process = process
        
        output_lines = []
        start_time = time.time()
        
        while True:
            if _cancel_requested:
                process.kill()
                _current_brom_process = None
                return False, "Cancelled"

            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                # Strip ANSI escape color codes
                clean_line = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line).strip()
                if clean_line:
                    lower_line = clean_line.lower()
                    # Skip verbose spam hint lines
                    if not any(kw in lower_line for kw in ignore_keywords):
                        log_cb(f"  ⚡ {clean_line}", "info")
                    output_lines.append(clean_line)
            if time.time() - start_time > timeout:
                process.kill()
                _current_brom_process = None
                log_cb("⏱️ Hết thời gian chờ kết nối BROM (Timeout).", "warning")
                return False, "Timeout"

        rc = process.poll()
        _current_brom_process = None
        full_out = "\n".join(output_lines)
        return (rc == 0), full_out

    except Exception as e:
        _current_brom_process = None
        log_cb(f"❌ Lỗi thực thi MTK BROM: {e}", "error")
        return False, str(e)

def run_brom_1click_all_in_one(working_dir: str, patch_engine_func, log_cb=print) -> bool:
    """
    1-Click Automated BROM Engine:
    Step 1: Wait for BROM connection -> Dump vendor & vbmeta from BROM
    Step 2: Auto Patch vendor & disable vbmeta DM-Verity
    Step 3: Flash patched vendor & vbmeta back to phone
    Step 4: Send reset command to reboot into Android
    """
    os.makedirs(working_dir, exist_ok=True)
    
    dump_vendor_path = os.path.join(working_dir, "BROM_dump_vendor.img")
    dump_vbmeta_path = os.path.join(working_dir, "BROM_dump_vbmeta.img")
    
    # -------------------------------------------------------------------------
    # STEP 1: WAIT FOR BROM CONNECTION & DUMP VENDOR
    # -------------------------------------------------------------------------
    connected_detected = False
    
    def log_filter_cb(msg_text: str, msg_type: str = "info"):
        nonlocal connected_detected
        lower = msg_text.lower()
        if not connected_detected and ("device" in lower or "chip" in lower or "read" in lower or "handshake" in lower or "sync" in lower or "connected" in lower):
            connected_detected = True
            log_cb("✓ Đã nhận tín hiệu BROM Mode MediaTek thành công!", "success")
            log_cb("📦 [BƯỚC 1/4]: Đang rút (Dump) phân vùng Vendor...", "info")
        log_cb(msg_text, msg_type)

    success_vendor, out_vendor = run_mtk_command(["r", "vendor", dump_vendor_path], log_cb=log_filter_cb, timeout=90)
    if not success_vendor or not os.path.exists(dump_vendor_path):
        log_cb("❌ Chưa nhận được kết nối BROM hoặc không thể rút Vendor. Hãy kiểm tra lại phím bấm TĂNG + GIẢM ÂM LƯỢNG và cáp USB!", "error")
        return False
        
    log_cb(f"✓ Đã rút thành công Vendor gốc ({os.path.getsize(dump_vendor_path) / (1024*1024):.2f} MB)", "success")
    
    # Dump vbmeta as well if possible
    log_cb("📦 Đang rút phân vùng Vbmeta bảo vệ...", "info")
    run_mtk_command(["r", "vbmeta", dump_vbmeta_path], log_cb=log_cb, timeout=40)

    # -------------------------------------------------------------------------
    # STEP 2: AUTO PATCH VENDOR & VBMETA
    # -------------------------------------------------------------------------
    log_cb("🛠️ [BƯỚC 2/4]: Đang chạy thuật toán tự động vá VoLTE trên đĩa vừa rút...", "info")
    
    patched_vendor_path = patch_engine_func(dump_vendor_path)
    if not patched_vendor_path or not os.path.exists(patched_vendor_path):
        log_cb("❌ Lỗi trong quá trình vá tệp Vendor vừa rút!", "error")
        return False
        
    log_cb(f"✓ Đã tạo xong bản vá Vendor: [{os.path.basename(patched_vendor_path)}]", "success")
    
    # Patch vbmeta to disable DM-Verity if vbmeta exists
    patched_vbmeta_path = None
    if os.path.exists(dump_vbmeta_path):
        try:
            from tools.patch_vbmeta_dm_verity import patch_vbmeta
            patch_vbmeta(dump_vbmeta_path)
            candidate = os.path.join(working_dir, "vbmeta_patched_disabled.img")
            if os.path.exists(candidate):
                patched_vbmeta_path = candidate
                log_cb("✓ Đã tắt cờ bảo vệ DM-Verity trong Vbmeta!", "success")
        except Exception as ex:
            log_cb(f"  ℹ️ Bỏ qua patch vbmeta: {ex}", "info")

    # -------------------------------------------------------------------------
    # STEP 3: FLASH PATCHED VENDOR & VBMETA BACK TO PHONE
    # -------------------------------------------------------------------------
    log_cb("🚀 [BƯỚC 3/4]: Đang tự động nạp bản vá Vendor đã vá trở lại điện thoại qua BROM...", "info")
    
    success_flash, out_flash = run_mtk_command(["w", "vendor", patched_vendor_path], log_cb=log_cb, timeout=120)
    if not success_flash:
        log_cb("❌ Lỗi khi nạp Vendor đã vá vào điện thoại!", "error")
        return False
        
    log_cb("✓ Đã nạp xong Vendor đã vá vào máy!", "success")
    
    if patched_vbmeta_path and os.path.exists(patched_vbmeta_path):
        log_cb("🚀 Đang nạp Vbmeta đã tắt DM-Verity vào máy...", "info")
        run_mtk_command(["w", "vbmeta", patched_vbmeta_path], log_cb=log_cb, timeout=40)

    # -------------------------------------------------------------------------
    # STEP 4: REBOOT PHONE BACK INTO ANDROID
    # -------------------------------------------------------------------------
    log_cb("🔄 [BƯỚC 4/4]: Đang gửi lệnh khởi động lại điện thoại vào Android...", "info")
    run_mtk_command(["reset"], log_cb=log_cb, timeout=15)
    
    log_cb("==================================================================", "success")
    log_cb("🎉 HOÀN THÀNH 100%! QUY TRÌNH BROM 1-CLICK ĐÃ VÁ VOLTE THÀNH CÔNG!", "success")
    log_cb("👉 Điện thoại đang tự khởi động lại. Giữ phím Nguồn 10 giây nếu máy chưa tự lên!", "success")
    log_cb("==================================================================", "success")
    return True
