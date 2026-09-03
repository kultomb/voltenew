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

def run_mtk_command(cmd_args: list, log_cb=print, timeout: int = 120) -> tuple[bool, str]:
    """
    Executes an mtkclient command via python launcher with clean log filtering.
    """
    if not is_mtkclient_available():
        err_msg = f"❌ Không tìm thấy bộ công cụ BROM mtkclient tại: {MTK_CLIENT_PY}"
        log_cb(err_msg, "error")
        return False, err_msg

    python_exe = sys.executable
    full_cmd = [python_exe, "-u", MTK_CLIENT_PY] + cmd_args
    
    # Filter list for spam lines to ignore
    ignore_keywords = [
        "hint:", "power off", "for brom mode", "for preloader mode",
        "if it is already connected", "please reconnect mobile", "metamodes",
        "deviceclass", "couldn't get device configuration", "handshake failed",
        "status: handshake", "retrying...", "preloader - [lib]"
    ]

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    try:
        process = subprocess.Popen(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="ignore",
            cwd=os.path.dirname(MTK_CLIENT_PY),
            env=env
        )
        
        output_lines = []
        start_time = time.time()
        last_milestone = -1
        import re
        import queue
        import threading

        def enqueue_output(out, q):
            try:
                for line in iter(out.readline, ''):
                    q.put(line)
                out.close()
            except Exception:
                pass

        q = queue.Queue()
        t = threading.Thread(target=enqueue_output, args=(process.stdout, q), daemon=True)
        t.start()

        com_check_time = time.time()

        while True:
            try:
                line = q.get_nowait()
            except queue.Empty:
                line = None

            if line is None:
                if process.poll() is not None:
                    break

                # Monitor if target COM port was unplugged
                if com_port and time.time() - com_check_time > 1.2:
                    com_check_time = time.time()
                    try:
                        import serial.tools.list_ports
                        active_ports = [p.device.upper() for p in serial.tools.list_ports.comports()]
                        if com_port.upper() not in active_ports:
                            process.kill()
                            log_cb(f"⚠️ Cáp USB [{com_port}] đã bị rút đột ngột! Đã tự động hủy tác vụ BROM an toàn.", "warning")
                            return False, "COM Unplugged"
                    except Exception:
                        pass

                if time.time() - start_time > timeout:
                    process.kill()
                    log_cb("⏱️ Hết thời gian chờ kết nối BROM (Timeout). Đã ngắt tiến trình.", "warning")
                    return False, "Timeout"

                time.sleep(0.08)
                continue

            cleaned = line.strip()
            if cleaned:
                # Strip ANSI escape codes
                clean_text = re.sub(r'\x1b\[[0-9;]*[mK]', '', cleaned).strip()
                if not clean_text or clean_text.startswith("...") or clean_text.startswith("...."):
                    continue
                    
                lower_line = clean_text.lower()
                # Skip verbose spam hint and error retry lines
                if any(kw in lower_line for kw in ignore_keywords):
                    output_lines.append(clean_text)
                    continue

                # Filter repetitive fine-grained progress lines
                if "progress:" in lower_line:
                    match = re.search(r'(\d+(?:\.\d+)?)\s*%', clean_text)
                    if match:
                        pct = float(match.group(1))
                        milestone = int(pct // 10) * 10
                        if milestone != last_milestone and milestone % 10 == 0:
                            last_milestone = milestone
                            log_cb(f"  ⚡ Tiến trình BROM: {milestone}%...", "info")
                    output_lines.append(clean_text)
                    continue

                log_cb(f"  ⚡ {clean_text}", "info")
                output_lines.append(clean_text)

        rc = process.poll()
        full_out = "\n".join(output_lines)
        return (rc == 0), full_out

    except Exception as e:
        log_cb(f"❌ Lỗi thực thi MTK BROM: {e}", "error")
        return False, str(e)

def find_mtk_com_port(timeout: int = 45, log_cb=print) -> str:
    """
    Monitors Windows COM ports for MediaTek USB VCOM / BootROM Port (VID: 0E8D).
    Returns the COM port string e.g. 'COM5' as soon as it appears.
    """
    try:
        import serial.tools.list_ports
    except ImportError:
        return None

    log_cb("⌛ Đang quét trực tiếp Cổng COM MediaTek USB (VID_0E8D)...", "info")
    start_t = time.time()
    
    while time.time() - start_t < timeout:
        for p in serial.tools.list_ports.comports():
            hwid = str(p.hwid).upper()
            desc = str(p.description).upper()
            if "0E8D" in hwid or "MEDIATEK" in desc or "PRELOADER" in desc or "MTK" in desc:
                port_name = p.device
                log_cb(f"✓ Đã phát hiện Cổng COM Chuẩn MediaTek: [{port_name}] ({p.description})!", "success")
                return port_name
        time.sleep(0.15)
        
    return None

def run_brom_1click_all_in_one(working_dir: str, patch_engine_func, log_cb=print) -> bool:
    """
    1-Click Automated BROM Engine:
    Step 1: Monitor MediaTek COM Port -> Dump vendor & vbmeta from BROM
    Step 2: Auto Patch vendor & disable vbmeta DM-Verity
    Step 3: Flash patched vendor & vbmeta back to phone
    Step 4: Send reset command to reboot into Android
    """
    os.makedirs(working_dir, exist_ok=True)
    
    dump_vendor_path = os.path.join(working_dir, "BROM_dump_vendor.img")
    dump_vbmeta_path = os.path.join(working_dir, "BROM_dump_vbmeta.img")
    
    # -------------------------------------------------------------------------
    # STEP 1: MONITOR COM PORT & DUMP VENDOR
    # -------------------------------------------------------------------------
    com_port = find_mtk_com_port(timeout=40, log_cb=log_cb)
    if not com_port:
        log_cb("❌ Chưa nhận diện được Cổng COM MediaTek. Vui lòng giữ phím TĂNG + GIẢM ÂM LƯỢNG và cắm cáp lại!", "error")
        return False

    log_cb(f"📦 [BƯỚC 1/4]: Đang kết nối trực tiếp Cổng [{com_port}] để rút phôi Vendor...", "info")
    log_cb(f"  ⚡ [BROM {com_port}]: Đang thực hiện kết nối Handshake & đọc phân vùng Vendor (Vui lòng giữ nguyên cáp USB)...", "info")
    
    # Pass --noreconnect to avoid re-triggering handshake on an active COM session
    vendor_args = ["r", "vendor", dump_vendor_path, "--serialport", com_port, "--noreconnect"]
    success_vendor, out_vendor = run_mtk_command(vendor_args, log_cb=log_cb, timeout=90)
    
    # Fallback retry without --noreconnect if needed
    if not success_vendor or not os.path.exists(dump_vendor_path):
        log_cb("  ℹ️ Đang thử lại kết nối handshake tự động...", "info")
        vendor_args_retry = ["r", "vendor", dump_vendor_path, "--serialport", com_port]
        success_vendor, out_vendor = run_mtk_command(vendor_args_retry, log_cb=log_cb, timeout=60)

    if not success_vendor or not os.path.exists(dump_vendor_path):
        log_cb("⚠️ [GHI CHÚ CHI PHÍ BROM KHÓA AN NINH CAO - DA SECURE BOOT]:", "warning")
        log_cb("👉 Máy OPPO/Realme chip MediaTek đời mới (SLA/DAA Secure Boot) đã khóa lệnh Nút BROM trực tiếp.", "warning")
        log_cb("👉 VUI LÒNG DÙNG UNLOCKTOOL NẠP 1 SÂU THÀNH CÔNG NGHỆ BẰNG HƯỚNG DẪN DƯỚI:", "warning")
        log_cb("   1. Nhấp nút [TẠO TỆP VÁ VENDOR VOLTE] trên Tool để xuất tệp PATCHED_vendor.img.", "info")
        log_cb("   2. Mở UnlockTool -> Tab MTK -> Boot Device -> Chuột phải Vendor chọn Write -> Trỏ tệp vá!", "info")
        return False
        
    log_cb(f"✓ Đã rút thành công Vendor gốc ({os.path.getsize(dump_vendor_path) / (1024*1024):.2f} MB)", "success")
    
    # Dump vbmeta as well if possible
    log_cb("📦 Đang rút phân vùng Vbmeta bảo vệ...", "info")
    vbmeta_args = ["r", "vbmeta", dump_vbmeta_path, "--serialport", com_port]
    run_mtk_command(vbmeta_args, log_cb=log_cb, timeout=40)

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
    
    flash_vendor_args = ["w", "vendor", patched_vendor_path, "--serialport", com_port]
    success_flash, out_flash = run_mtk_command(flash_vendor_args, log_cb=log_cb, timeout=120)
    if not success_flash:
        log_cb("❌ Lỗi khi nạp Vendor đã vá vào điện thoại!", "error")
        return False
        
    log_cb("✓ Đã nạp xong Vendor đã vá vào máy!", "success")
    
    if patched_vbmeta_path and os.path.exists(patched_vbmeta_path):
        log_cb("🚀 Đang nạp Vbmeta đã tắt DM-Verity vào máy...", "info")
        flash_vbmeta_args = ["w", "vbmeta", patched_vbmeta_path, "--serialport", com_port]
        run_mtk_command(flash_vbmeta_args, log_cb=log_cb, timeout=40)

    # -------------------------------------------------------------------------
    # STEP 4: REBOOT PHONE BACK INTO ANDROID
    # -------------------------------------------------------------------------
    log_cb("🔄 [BƯỚC 4/4]: Đang gửi lệnh khởi động lại điện thoại vào Android...", "info")
    reset_args = ["reset", "--serialport", com_port]
    run_mtk_command(reset_args, log_cb=log_cb, timeout=15)
    
    log_cb("==================================================================", "success")
    log_cb("🎉 HOÀN THÀNH 100%! QUY TRÌNH BROM 1-CLICK ĐÃ VÁ VOLTE THÀNH CÔNG!", "success")
    log_cb("👉 Điện thoại đang tự khởi động lại. Giữ phím Nguồn 10 giây nếu máy chưa tự lên!", "success")
    log_cb("==================================================================", "success")
    return True
