"""
MediaTek BROM 1-Click Automated Engine for HBG VoLTE & IMS Fixer
Native PreLoader VCOM Serial Listener + BROM Dump, Patch & Flash Pipeline.
"""

import os
import sys
import re
import time
import subprocess

MTK_CLIENT_DIR = r"C:\Users\CMD\Desktop\Tool android\mtkclient"
MTK_CLIENT_PY = os.path.join(MTK_CLIENT_DIR, "mtk.py")

_current_brom_process: subprocess.Popen | None = None
_cancel_requested = False


def cancel_brom_process():
    """Emergency cancel handler to kill background BROM process and reset state."""
    global _current_brom_process, _cancel_requested
    _cancel_requested = True
    if _current_brom_process:
        try:
            _current_brom_process.kill()
        except Exception:
            pass
        _current_brom_process = None


def run_mtk_command(cmd_args: list[str], log_cb=print, timeout: float = 60.0) -> tuple[bool, str]:
    """Runs mtk.py command with --serialport DETECT for direct PreLoader VCOM serial listening."""
    global _current_brom_process, _cancel_requested
    
    if not os.path.exists(MTK_CLIENT_PY):
        err_msg = f"Không tìm thấy mtk.py tại: {MTK_CLIENT_PY}"
        log_cb(f"❌ {err_msg}", "error")
        return False, err_msg

    python_exe = sys.executable
    # Always use --serialport DETECT to put mtkclient in instant PreLoader VCOM standing-by listener mode
    full_cmd = [python_exe, MTK_CLIENT_PY, "--serialport", "DETECT"] + cmd_args

    # Keywords to filter out verbose loop hints & dot spam
    ignore_keywords = [
        "hint:", "power off", "for brom mode", "for preloader mode",
        "if it is already connected", "please reconnect mobile", "metamodes",
        "couldn't get device configuration", "deviceclass", "[lib]:", "libusb", "usb.core",
        "waiting for preloader vcom", "retrying..."
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
        handshake_logged = False
        
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
                
                # Filter out pure dot lines (e.g. "...", "...........")
                if clean_line and not re.match(r'^\.+$', clean_line):
                    lower_line = clean_line.lower()
                    
                    # Detect REAL BROM Connection / Handshake success signal
                    if not handshake_logged and any(k in lower_line for k in ["device detected", "hw code:", "reading partition", "writing partition"]):
                        handshake_logged = True
                        log_cb("✓ Đã nhận diện cổng COM MediaTek & Handshake BROM thành công!", "success")
                        log_cb("📦 [BƯỚC 1/4]: Đang rút phân vùng Vendor...", "info")
                        
                    if not any(kw in lower_line for kw in ignore_keywords):
                        log_cb(f"  ⚡ {clean_line}", "info")
                    output_lines.append(clean_line)

            if time.time() - start_time > timeout:
                process.kill()
                _current_brom_process = None
                log_cb("⏱️ Hết thời gian chờ tiến trình BROM (Timeout).", "warning")
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
    Step 1: Start PreLoader VCOM listener -> Wait for USB cable -> Dump vendor & vbmeta
    Step 2: Dynamic Auto-Patch vendor & disable vbmeta DM-Verity
    Step 3: Flash patched vendor & vbmeta back to phone
    Step 4: Reboot phone into Android
    """
    global _cancel_requested
    _cancel_requested = False
    
    os.makedirs(working_dir, exist_ok=True)
    
    dump_vendor_path = os.path.join(working_dir, "BROM_dump_vendor.img")
    dump_vbmeta_path = os.path.join(working_dir, "BROM_dump_vbmeta.img")

    # -------------------------------------------------------------------------
    # STEP 1: START PRELOADER VCOM LISTENER & DUMP VENDOR
    # -------------------------------------------------------------------------
    log_cb("⌛ Đang đứng chờ cắm cáp BROM... (Vui lòng tắt nguồn máy, giữ phím TĂNG + GIẢM ÂM LƯỢNG và CẮM CÁP USB)", "info")
    
    success_vendor, out_vendor = run_mtk_command(["r", "vendor", dump_vendor_path], log_cb=log_cb, timeout=60.0)
    
    if _cancel_requested:
        return False

    if not success_vendor or not os.path.exists(dump_vendor_path) or os.path.getsize(dump_vendor_path) == 0:
        log_cb("❌ Chưa nhận được kết nối BROM hoặc không thể rút Vendor. Hãy kiểm tra lại phím bấm TĂNG + GIẢM ÂM LƯỢNG và cáp USB!", "error")
        return False
        
    log_cb(f"✓ Đã rút thành công Vendor gốc ({os.path.getsize(dump_vendor_path) / (1024*1024):.2f} MB)", "success")
    
    # Dump vbmeta as well if possible
    log_cb("📦 Đang rút phân vùng Vbmeta bảo vệ...", "info")
    run_mtk_command(["r", "vbmeta", dump_vbmeta_path], log_cb=log_cb, timeout=40.0)

    # -------------------------------------------------------------------------
    # STEP 2: AUTO PATCH VENDOR & VBMETA
    # -------------------------------------------------------------------------
    log_cb("🔧 [BƯỚC 2/4]: Đang tiến hành vá đĩa Vendor VoLTE động...", "info")
    try:
        patched_vendor_path = patch_engine_func(dump_vendor_path)
        if not patched_vendor_path or not os.path.exists(patched_vendor_path):
            log_cb("❌ Tiến trình vá đĩa Vendor thất bại!", "error")
            return False
        log_cb(f"✓ Đã tạo thành công bản vá Vendor VoLTE: [{os.path.basename(patched_vendor_path)}]", "success")
    except Exception as e:
        log_cb(f"❌ Lỗi khi vá đĩa Vendor: {e}", "error")
        return False

    # -------------------------------------------------------------------------
    # STEP 3: FLASH PATCHED VENDOR BACK TO PHONE
    # -------------------------------------------------------------------------
    log_cb("⚡ [BƯỚC 3/4]: Đang nạp lại Vendor bản vá vào điện thoại qua BROM...", "info")
    success_flash, out_flash = run_mtk_command(["w", "vendor", patched_vendor_path], log_cb=log_cb, timeout=60.0)
    if not success_flash:
        log_cb("❌ Lỗi nạp lại Vendor vào điện thoại!", "error")
        return False
    log_cb("✓ Đã nạp thành công Vendor bản vá vào phân vùng điện thoại!", "success")

    # -------------------------------------------------------------------------
    # STEP 4: REBOOT PHONE INTO ANDROID
    # -------------------------------------------------------------------------
    log_cb("🔄 [BƯỚC 4/4]: Đang gửi lệnh khởi động lại điện thoại vào Android...", "info")
    run_mtk_command(["reset"], log_cb=log_cb, timeout=15.0)
    
    log_cb("🎉 QUY TRÌNH BROM 1-CLICK RÚT ➔ VÁ ➔ NẠP VENDOR HOÀN TẤT THÀNH CÔNG RỰC RỠ!", "success")
    return True
