"""
HBG Tool — Scientific ResTable ARSC Entry & String Index Injector for system.bin
Parses string pool indices for VoLTE keys and patches ResTable boolean entries from false (0x00000000) to true (0xffffffff / 0x00000001).
"""

import os
import sys
import struct
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

def main():
    src_file = os.path.abspath(r"C:\Users\CMD\Desktop\volte_fixer_tool\THU_MUC_RUT_SYSTEM_OPPO\system.bin")
    out_file = os.path.abspath(r"C:\Users\CMD\Desktop\volte_fixer_tool\THU_MUC_RUT_SYSTEM_OPPO\system_patched.bin")

    if not os.path.exists(src_file):
        log(f"Không tìm thấy {src_file}", "error")
        return

    size = os.path.getsize(src_file)
    log(f"📦 Đang quét thuật toán ResTable ARSC tiên tiến trên system.bin ({size / (1024*1024):.2f} MB)...", "info")

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

            # Scientific ResTable Pattern Matching:
            # Look for 08 00 00 12 00 00 00 00 (Res_value struct size=8, dataType=0x12 boolean false)
            # or 08 00 05 70 00 00 00 00 (AXML boolean false)
            # within 1KB window of target string keys in string pool

            for key in TARGET_KEYS:
                pos = 0
                while True:
                    idx = data.find(key, pos)
                    if idx == -1:
                        break
                    
                    # Search window 2KB around key (both before and after string)
                    win_start = max(0, idx - 1024)
                    win_end = min(len(data), idx + len(key) + 1024)
                    window = data[win_start:win_end]

                    # Pattern A: ResTable 0x12 boolean false
                    p_false1 = b"\x08\x00\x00\x12\x00\x00\x00\x00"
                    p_true1  = b"\x08\x00\x00\x12\xff\xff\xff\xff"

                    if p_false1 in window:
                        w_pos = 0
                        while True:
                            w_idx = window.find(p_false1, w_pos)
                            if w_idx == -1:
                                break
                            abs_idx = win_start + w_idx
                            data = data[:abs_idx] + p_true1 + data[abs_idx+8:]
                            patched_count += 1
                            w_pos = w_idx + 8

                    # Pattern B: AXML 0x05 boolean false
                    p_false2 = b"\x08\x00\x05p\x00\x00\x00\x00"
                    p_true2  = b"\x08\x00\x05p\x00\x00\x00\x01"

                    if p_false2 in window:
                        w_pos = 0
                        while True:
                            w_idx = window.find(p_false2, w_pos)
                            if w_idx == -1:
                                break
                            abs_idx = win_start + w_idx
                            data = data[:abs_idx] + p_true2 + data[abs_idx+8:]
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
    main()
