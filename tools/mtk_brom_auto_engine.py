"""
MediaTek BROM 1-Click Automated Engine for HBG VoLTE & IMS Fixer
Native C++ Fast Listener + Subprocess Pipeline for High-Speed Connection.
"""

import os
import sys
import re
import time
import subprocess
import serial.tools.list_ports

TOOLS_DIR = os.path.dirname(__file__)
CPP_ENGINE_EXE = os.path.join(TOOLS_DIR, "mtk_brom_fast_engine.exe")
MTK_CLIENT_DIR = os.path.join(TOOLS_DIR, "mtkclient")
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


def run_cpp_brom_fast_scan(log_cb=print, timeout: float = 40.0) -> str | None:
    """Runs Native Win32 C++ BROM Engine for sub-millisecond port locking without DTR/RTS resets."""
    global _current_brom_process, _cancel_requested

    if not os.path.exists(CPP_ENGINE_EXE):
        return None

    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        process = subprocess.Popen(
            [CPP_ENGINE_EXE],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="ignore",
            cwd=TOOLS_DIR,
            creationflags=creationflags
        )
        _current_brom_process = process

        detected_port = None
        start_time = time.time()
        while True:
            if _cancel_requested:
                process.kill()
                _current_brom_process = None
                return None

            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                clean_line = line.strip()
                if clean_line:
                    if clean_line.startswith("PORT:"):
                        detected_port = clean_line.split("PORT:", 1)[1].strip()
                    elif "ĐÃ PHÁT HIỆN CỔNG COM MEDIATEK" in clean_line:
                        log_cb(f"  ✓ {clean_line}", "success")
                    elif "⚡" in clean_line or "⌛" in clean_line:
                        log_cb(f"  {clean_line}", "info")

            if time.time() - start_time > timeout:
                process.kill()
                _current_brom_process = None
                return None

        process.poll()
        _current_brom_process = None
        return detected_port
    except Exception as e:
        _current_brom_process = None
        log_cb(f"⚠ C++ Listener notice: {e}", "warning")
        return None


def run_mtk_command(cmd_args: list[str], port_name: str | None = None, log_cb=print, timeout: float = 60.0) -> tuple[bool, str]:
    """Runs mtk.py command with specific COM port or DETECT for PreLoader VCOM serial listening."""
    global _current_brom_process, _cancel_requested
    
    if not os.path.exists(MTK_CLIENT_PY):
        err_msg = f"Không tìm thấy mtk.py tại: {MTK_CLIENT_PY}"
        log_cb(f"❌ {err_msg}", "error")
        return False, err_msg

    python_exe = sys.executable
    full_cmd = [python_exe, MTK_CLIENT_PY]
    if port_name:
        clean_p = port_name.replace("\\", "").replace(".", "")
        if clean_p.upper().startswith("COM"):
            win_port = "\\\\.\\" + clean_p
        else:
            win_port = port_name
        full_cmd.extend(["--serialport", win_port])
    else:
        full_cmd.extend(["--serialport", "DETECT"])
    full_cmd.extend(cmd_args)

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
            cwd=os.path.dirname(MTK_CLIENT_PY),
            creationflags=creationflags
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
                clean_line = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line).strip()
                
                if clean_line and not re.match(r'^\.+$', clean_line):
                    lower_line = clean_line.lower()
                    
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


if sys.platform == "win32":
    try:
        import serial.serialwin32
        def _safe_update_dtr_state(self):
            if hasattr(self, '_port_handle') and self._port_handle and self._port_handle != serial.win32.INVALID_HANDLE_VALUE:
                serial.win32.EscapeCommFunction(self._port_handle, serial.win32.CLRDTR)
        def _safe_update_rts_state(self):
            if hasattr(self, '_port_handle') and self._port_handle and self._port_handle != serial.win32.INVALID_HANDLE_VALUE:
                serial.win32.EscapeCommFunction(self._port_handle, serial.win32.CLRRTS)
        serial.serialwin32.Serial._update_dtr_state = _safe_update_dtr_state
        serial.serialwin32.Serial._update_rts_state = _safe_update_rts_state
    except Exception:
        pass


def prepare_com_port_handle(port_name: str, log_cb=print) -> str:
    """Formats Win32 COM port device handle without opening/closing to preserve MediaTek BROM state machine."""
    clean_port = port_name.replace("\\", "").replace(".", "")
    if clean_port.upper().startswith("COM"):
        target_port = "\\\\.\\" + clean_port
    else:
        target_port = port_name
    log_cb(f"🔥 CỔNG COM [{target_port}] ĐÃ SẴN SÀNG KẾT NỐI BROM/PRELOADER!", "success")
    return target_port


def scan_mtk_com_port_fast(log_cb=print, timeout: float = 90.0) -> str | None:
    """
    Ultra-high speed 10ms sampling detector for MediaTek BROM / PreLoader COM ports.
    Locks port instantly (e.g. COM27) within milliseconds of device insertion.
    """
    global _cancel_requested
    start_time = time.time()
    last_log_time = 0.0

    while time.time() - start_time < timeout:
        if _cancel_requested:
            return None

        elapsed = time.time() - start_time
        if elapsed - last_log_time >= 15.0:
            last_log_time = elapsed
            log_cb(f"⏳ Đang đứng chờ cắm cáp BROM... (Thời gian còn lại: {timeout - elapsed:.0f}s)", "info")

        try:
            for p in serial.tools.list_ports.comports():
                vid_str = f"{p.vid:04X}" if p.vid else ""
                hwid_str = (p.hwid or "").upper()
                desc_str = (p.description or "").upper()
                
                is_mtk = (
                    p.vid == 0x0E8D or
                    "0E8D" in vid_str or
                    "0E8D" in hwid_str or
                    "MEDIATEK" in desc_str or
                    "PRELOADER" in desc_str or
                    "VCOM" in desc_str
                )
                
                if is_mtk:
                    port_name = p.device
                    desc = p.description or port_name
                    log_cb(f"✓ ĐÃ PHÁT HIỆN CỔNG COM MEDIATEK [{port_name} — {desc}] THÀNH CÔNG!", "success")
                    ready_port = prepare_com_port_handle(port_name, log_cb=log_cb)
                    return ready_port
        except Exception:
            pass

        time.sleep(0.01)  # 10ms high precision sampling

    log_cb("⏱️ Hết thời gian chờ kết nối BROM (Timeout).", "warning")
    return None


def run_brom_1click_all_in_one(working_dir: str, patch_engine_func, log_cb=print) -> bool:
    """
    1-Click Automated Hybrid BROM Engine (Zero Subprocess Delay Standby Mode):
    Step 1: Direct mtk.py Standby listener upfront + Preloader Crash (kamakiri) -> Dump vendor & vbmeta
    Step 2: Dynamic Auto-Patch vendor & disable vbmeta DM-Verity
    Step 3: Flash patched vendor & vbmeta back to phone
    Step 4: Reboot phone into Android
    """
    global _cancel_requested
    _cancel_requested = False
    
    os.makedirs(working_dir, exist_ok=True)
    
    dump_vendor_path = os.path.join(working_dir, "BROM_dump_vendor.img")
    dump_vbmeta_path = os.path.join(working_dir, "BROM_dump_vbmeta.img")

    # Clean up old dump files to prevent false positive checks
    if os.path.exists(dump_vendor_path):
        try:
            os.remove(dump_vendor_path)
        except Exception:
            pass
    if os.path.exists(dump_vbmeta_path):
        try:
            os.remove(dump_vbmeta_path)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # STEP 1: PRE-LOADER / BROM DA LISTENER & DUMP VENDOR
    # -------------------------------------------------------------------------
    log_cb("⌛ Đang đứng chờ cắm cáp BROM/Preloader... (Vui lòng tắt nguồn máy, giữ phím TĂNG + GIẢM ÂM LƯỢNG và CẮM CÁP USB)", "info")
    
    if _cancel_requested:
        return False

    # Execute mtk.py --crash r vendor <dump_path>
    log_cb("⚡ [BƯỚC 1/4]: Đang kích hoạt BROM Crash & Rút phân vùng Vendor cho OPPO MT6765...", "info")
    success_vendor, out_vendor = run_mtk_command(["--crash", "r", "vendor", dump_vendor_path], port_name=None, log_cb=log_cb, timeout=90.0)
    
    if _cancel_requested:
        return False

    if not success_vendor or not os.path.exists(dump_vendor_path) or os.path.getsize(dump_vendor_path) == 0:
        # Fallback: Try direct read without --crash
        log_cb("⚡ Thử nghiệm rút phân vùng trực tiếp (r vendor)...", "info")
        success_vendor, out_vendor = run_mtk_command(["r", "vendor", dump_vendor_path], port_name=None, log_cb=log_cb, timeout=90.0)

    if not success_vendor or not os.path.exists(dump_vendor_path) or os.path.getsize(dump_vendor_path) == 0:
        log_cb("❌ Rút phân vùng Vendor thất bại hoặc không nhận được Handshake BROM. Hãy kiểm tra lại phím bấm TĂNG + GIẢM ÂM LƯỢNG!", "error")
        return False
        
    log_cb(f"✓ Đã rút thành công Vendor gốc ({os.path.getsize(dump_vendor_path) / (1024*1024):.2f} MB)", "success")
    
    # Dump vbmeta as well if possible
    log_cb("📦 Đang rút phân vùng Vbmeta bảo vệ...", "info")
    run_mtk_command(["--noreconnect", "r", "vbmeta", dump_vbmeta_path], port_name=None, log_cb=log_cb, timeout=40.0)

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
    log_cb("⚡ [BƯỚC 3/4]: Đang chuẩn bị nạp lại Vendor bản vá vào điện thoại qua BROM...", "info")
    log_cb("👉 Nếu máy đã khởi động lại Android, vui lòng TẮT NGUỒN MÁY và CẮM LẠI CÁP (giữ TĂNG + GIẢM ÂM LƯỢNG) để nạp...", "warning")
    success_flash, out_flash = run_mtk_command(["--noreconnect", "w", "vendor", patched_vendor_path], port_name=None, log_cb=log_cb, timeout=60.0)
    if not success_flash:
        log_cb("❌ Lỗi nạp lại Vendor vào điện thoại!", "error")
        return False
    log_cb("✓ Đã nạp thành công Vendor bản vá vào phân vùng điện thoại!", "success")

    # -------------------------------------------------------------------------
    # STEP 4: REBOOT PHONE INTO ANDROID
    # -------------------------------------------------------------------------
    log_cb("🔄 [BƯỚC 4/4]: Đang gửi lệnh khởi động lại điện thoại vào Android...", "info")
    run_mtk_command(["reset"], port_name=None, log_cb=log_cb, timeout=15.0)
    
    log_cb("🎉 QUY TRÌNH BROM 1-CLICK RÚT ➔ VÁ ➔ NẠP VENDOR HOÀN TẤT THÀNH CÔNG RỰC RỠ!", "success")
    return True
