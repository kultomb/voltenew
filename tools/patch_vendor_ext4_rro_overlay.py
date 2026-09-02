"""
HBG Tool — Specialized EXT4 Vendor Partition & RRO Overlay Injector for OPPO / MediaTek
Directly patches /vendor/overlay/ RRO resources and MTK Baseband props inside vendor.bin EXT4 filesystem image.
"""

import os
import sys
import time
import glob

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def log(msg: str, level: str = "info"):
    icon = {"info": "i", "success": "OK", "warning": "!", "error": "X"}.get(level, "*")
    print(f"[{icon}] {msg}")

def patch_vendor_ext4(input_dir: str):
    src_file = os.path.join(input_dir, "vendor.bin")
    out_file = os.path.join(input_dir, "vendor_patched.bin")

    if not os.path.exists(src_file):
        log(f"Không tìm thấy tệp vendor.bin trong {input_dir}", "error")
        return False

    file_size = os.path.getsize(src_file)
    log(f"📦 Đang giải mã đĩa đệm EXT4 vendor.bin ({file_size / (1024*1024):.2f} MB) tại {input_dir}...", "info")

    chunk_size = 64 * 1024 * 1024
    patched_rro_count = 0
    patched_prop_count = 0

    # Key replacements inside vendor EXT4 image
    prop_replacements = [
        (b"persist.vendor.mtk.volte.enable=0", b"persist.vendor.mtk.volte.enable=1"),
        (b"persist.vendor.volte_support=0", b"persist.vendor.volte_support=1"),
        (b"persist.vendor.radio.mtk_dsbp_support=0", b"persist.vendor.radio.mtk_dsbp_support=1"),
        (b"ro.vendor.md_auto_setup_ims=0", b"ro.vendor.md_auto_setup_ims=1")
    ]

    with open(src_file, "rb") as fin, open(out_file, "wb") as fout:
        overlap = b""
        chunk_idx = 0
        while True:
            chunk = fin.read(chunk_size)
            if not chunk:
                if overlap:
                    fout.write(overlap)
                break
            data = overlap + chunk

            # 1. Patch Baseband Vendor props
            for old_p, new_p in prop_replacements:
                c = data.count(old_p)
                if c > 0:
                    data = data.replace(old_p, new_p)
                    patched_prop_count += c

            # 2. Locate embedded RRO APKs in vendor EXT4
            pos = 0
            while True:
                idx = data.find(b"PK\x03\x04", pos)
                if idx == -1:
                    break

                window = data[idx : min(len(data), idx + 250000)]
                if b"resources.arsc" in window:
                    if b"config_device_volte_available" in window or b"carrier_volte_available" in window:
                        p_false = b"\x08\x00\x00\x12\x00\x00\x00\x00"
                        p_true  = b"\x08\x00\x00\x12\xff\xff\xff\xff"
                        if p_false in window:
                            new_window = window.replace(p_false, p_true)
                            data = data[:idx] + new_window + data[idx+len(window):]
                            patched_rro_count += window.count(p_false)

                pos = idx + 4

            if len(data) > 1024:
                fout.write(data[:-1024])
                overlap = data[-1024:]
            else:
                overlap = data
            chunk_idx += 1

    cur_time = time.strftime("%H:%M:%S")
    log(f"  ✓ EXT4 VENDOR: Đã tiêm {patched_rro_count} cờ RRO Overlay VoLTE (True)", "success")
    log(f"  ✓ EXT4 VENDOR: Đã tiêm {patched_prop_count} cờ MTK Baseband (1)", "success")
    log(f"🎉 ĐÃ BIÊN DỊCH THÀNH CÔNG VENDOR_PATCHED.BIN ({os.path.getsize(out_file) / (1024*1024):.2f} MB) LÚC {cur_time}!", "success")
    return True

def main():
    print("====================================================================")
    print("  HBG TOOL — ĐỘNG CƠ TIÊM VENDOR EXT4 RRO OVERLAY DÀNH CHO OPPO / MTK")
    print("====================================================================")
    print()

    input_dir = os.path.abspath("THU_MUC_RUT_SYSTEM_OPPO")
    if not os.path.exists(input_dir):
        matches = glob.glob("THU_MUC_RUT_SYSTEM_OPPO*")
        if matches:
            input_dir = os.path.abspath(matches[0])

    patch_vendor_ext4(input_dir)

if __name__ == "__main__":
    main()
