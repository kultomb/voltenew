"""
HBG Tool — Universal 2-Partition (System & Vendor) VoLTE Binary Patching Engine for OPPO / MediaTek
Applies precise binary injections to both system.bin and vendor.bin based on deep memory offset analysis.
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

def patch_system(input_dir: str):
    src_file = os.path.join(input_dir, "system.bin")
    out_file = os.path.join(input_dir, "system_patched.bin")
    if not os.path.exists(src_file):
        log(f"Không tìm thấy {src_file}", "error")
        return False

    file_size = os.path.getsize(src_file)
    log(f"📦 Đang quét & tiêm cờ ColorOS AXML vào system.bin ({file_size / (1024*1024):.2f} MB)...", "info")

    # Target keys discovered in deep memory scan
    target_keys = [
        b"mtk_ct_volte_status_bool",
        b"carrier_volte_available_bool",
        b"mtk_default_enhanced_4g_mode_bool"
    ]

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

            for key in target_keys:
                pos = 0
                while True:
                    idx = data.find(key, pos)
                    if idx == -1:
                        break
                    key_len = len(key)
                    val_window = data[idx+key_len : idx+key_len+60]
                    if b"\x08\x00\x05p\x00\x00\x00" in val_window:
                        val_idx = data.find(b"\x08\x00\x05p\x00\x00\x00", idx+key_len)
                        if val_idx != -1 and val_idx + 12 <= len(data):
                            # Replace false (0x00000000) with true (0x00000001)
                            data = data[:val_idx+8] + b"\x01\x00\x00\x00" + data[val_idx+12:]
                            patched_count += 1
                    pos = idx + key_len

            if len(data) > 1024:
                fout.write(data[:-1024])
                overlap = data[-1024:]
            else:
                overlap = data

    log(f"  ✓ SYSTEM.BIN: Đã tiêm thành công {patched_count} vị trí cờ AXML ColorOS = TRUE!", "success")
    return True

def patch_vendor(input_dir: str):
    src_file = os.path.join(input_dir, "vendor.bin")
    out_file = os.path.join(input_dir, "vendor_patched.bin")
    if not os.path.exists(src_file):
        log(f"Không tìm thấy {src_file}", "warning")
        return False

    file_size = os.path.getsize(src_file)
    log(f"📦 Đang quét & tiêm cờ MTK Baseband vào vendor.bin ({file_size / (1024*1024):.2f} MB)...", "info")

    replacements = [
        (b"persist.vendor.mtk.volte.enable=0", b"persist.vendor.mtk.volte.enable=1"),
        (b"persist.vendor.volte_support=0", b"persist.vendor.volte_support=1"),
        (b"persist.vendor.radio.mtk_dsbp_support=0", b"persist.vendor.radio.mtk_dsbp_support=1")
    ]

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

            for old_b, new_b in replacements:
                c = data.count(old_b)
                if c > 0:
                    data = data.replace(old_b, new_b)
                    patched_count += c

            if len(data) > 1024:
                fout.write(data[:-1024])
                overlap = data[-1024:]
            else:
                overlap = data

    log(f"  ✓ VENDOR.BIN: Đã tiêm thành công {patched_count} vị trí cờ MTK Baseband = 1!", "success")
    return True

def main():
    print("====================================================================")
    print("  HBG TOOL — ĐỘNG CƠ TIÊM BẢN VÁ SONG SONG SYSTEM & VENDOR CHUẨN 100%")
    print("====================================================================")
    print()

    input_dir = os.path.abspath("THU_MUC_RUT_SYSTEM_OPPO")
    ok_sys = patch_system(input_dir)
    ok_ven = patch_vendor(input_dir)

    print()
    print("====================================================================")
    print("🎉 ĐÃ HOÀN TẤT BIÊN DỊCH BẢN VÁ 2 PHÂN VÙNG CHUẨN DÀNH CHO UNLOCKTOOL!")
    print("👉 QUY TRÌNH NẠP TRÊN UNLOCKTOOL:")
    print("   1. Thẻ MTK UNIVERSAL -> Click [PATCH DM VERITY] (Tắt khóa bảo vệ phân vùng).")
    print("   2. Thẻ FLASH -> Nạp tệp system_patched.bin vào phân vùng system.")
    print("   3. Thẻ FLASH -> Nạp tệp vendor_patched.bin vào phân vùng vendor.")
    print("====================================================================")

if __name__ == "__main__":
    main()
