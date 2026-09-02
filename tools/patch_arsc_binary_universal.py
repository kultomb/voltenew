"""
Universal ARSC ResTable & AXML Boolean In-Memory Binary Injector
Supports both AXML Layout (0x05) and ResTable ARSC (0x12) TYPE_INT_BOOLEAN entries across all system/vendor binaries.
"""

import os
import sys
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def log(msg: str, level: str = "info"):
    icon = {"info": "i", "success": "OK", "warning": "!", "error": "X"}.get(level, "*")
    print(f"[{icon}] {msg}")

TARGET_KEYS = [
    b"config_device_volte_available",
    b"config_device_vt_available",
    b"carrier_volte_available_bool",
    b"mtk_ct_volte_status_bool",
    b"mtk_default_enhanced_4g_mode_bool",
    b"volte_status_bool",
    b"carrier_volte_provisioned_bool",
    b"carrier_vt_available_bool",
    b"carrier_wfc_ims_available_bool",
    b"editable_enhanced_4g_lte_bool"
]

def patch_system_arsc():
    src_file = os.path.abspath(r"C:\Users\CMD\Desktop\volte_fixer_tool\THU_MUC_RUT_SYSTEM_OPPO\system.bin")
    out_file = os.path.abspath(r"C:\Users\CMD\Desktop\volte_fixer_tool\THU_MUC_RUT_SYSTEM_OPPO\system_patched.bin")

    if not os.path.exists(src_file):
        log(f"Không tìm thấy {src_file}", "error")
        return

    size = os.path.getsize(src_file)
    log(f"📦 Đang quét & tiêm ResTable / ARSC VoLTE Flags vào system.bin ({size / (1024*1024):.2f} MB)...", "info")

    chunk_size = 64 * 1024 * 1024
    patched_count = 0

    with open(src_file, "rb") as fin, open(out_file, "wb") as fout:
        overlap = b""
        while True:
            chunk = fin.read(chunk_size)
            if not chunk:
                if overlap:
                    fout.write(overlap)
                break
            data = overlap + chunk

            # Scan for all boolean false patterns near ARSC/AXML keys
            # Pattern 1: ResTable_entry boolean false: \x08\x00\x00\x12\x00\x00\x00\x00
            # Replace with boolean true: \x08\x00\x00\x12\xff\xff\xff\xff
            # Pattern 2: AXML boolean false: \x08\x00\x05p\x00\x00\x00\x00
            # Replace with boolean true: \x08\x00\x05p\x00\x00\x00\x01

            for key in TARGET_KEYS:
                pos = 0
                while True:
                    idx = data.find(key, pos)
                    if idx == -1:
                        break
                    
                    # Look in a 512-byte window around key index (both before and after)
                    win_start = max(0, idx - 256)
                    win_end = min(len(data), idx + len(key) + 512)
                    window = data[win_start:win_end]

                    # 1. Patch ResTable ARSC 0x12 boolean false
                    p_arsc_false = b"\x08\x00\x00\x12\x00\x00\x00\x00"
                    p_arsc_true  = b"\x08\x00\x00\x12\xff\xff\xff\xff"
                    
                    if p_arsc_false in window:
                        w_pos = 0
                        while True:
                            w_idx = window.find(p_arsc_false, w_pos)
                            if w_idx == -1:
                                break
                            abs_idx = win_start + w_idx
                            data = data[:abs_idx] + p_arsc_true + data[abs_idx+8:]
                            patched_count += 1
                            w_pos = w_idx + 8

                    # 2. Patch AXML 0x05 boolean false
                    p_axml_false = b"\x08\x00\x05p\x00\x00\x00\x00"
                    p_axml_true  = b"\x08\x00\x05p\x00\x00\x00\x01"

                    if p_axml_false in window:
                        w_pos = 0
                        while True:
                            w_idx = window.find(p_axml_false, w_pos)
                            if w_idx == -1:
                                break
                            abs_idx = win_start + w_idx
                            data = data[:abs_idx] + p_axml_true + data[abs_idx+8:]
                            patched_count += 1
                            w_pos = w_idx + 8

                    pos = idx + len(key)

            if len(data) > 1024:
                fout.write(data[:-1024])
                overlap = data[-1024:]
            else:
                overlap = data

    log(f"🎉 ĐÃ TIÊM THÀNH CÔNG {patched_count} VỊ TRÍ CỜ ARSC / AXML VOLTE (TRUE/1) VÀO SYSTEM_PATCHED.BIN!", "success")

if __name__ == "__main__":
    patch_system_arsc()
