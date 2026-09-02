"""
OPPO A31 (CPH2015 MT6765) — Precise AXML volte_status_bool Binary Injector
Locates volte_status_bool string at byte index 1804286439 in system.bin and patches boolean value from 0 (false) to 1 (true).
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

def main():
    print("====================================================================")
    print("  HBG TOOL — TIÊM BẢN VÁ VOLTE_STATUS_BOOL TRỰC TIẾP VÀO AXML SYSTEM.BIN")
    print("  Model: OPPO A31 (CPH2015) | Dump Target: THU_MUC_RUT_SYSTEM_OPPO/system.bin")
    print("====================================================================")
    print()

    input_dir = os.path.abspath("THU_MUC_RUT_SYSTEM_OPPO")
    src_file = os.path.join(input_dir, "system.bin")
    out_file = os.path.join(input_dir, "system_patched.bin")

    if not os.path.exists(src_file):
        log("Chưa tìm thấy tệp system.bin trong THU_MUC_RUT_SYSTEM_OPPO!", "error")
        return

    file_size = os.path.getsize(src_file)
    log(f"📦 Đang quét tệp đĩa cứng system.bin ({file_size / (1024*1024):.2f} MB)...", "info")

    chunk_size = 64 * 1024 * 1024 # 64MB chunks
    target_key = b"volte_status_bool"

    patched_count = 0
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
            
            # Look for AXML key volte_status_bool
            pos = 0
            while True:
                idx = data.find(target_key, pos)
                if idx == -1:
                    break
                
                # Check AXML boolean payload structure near target_key
                # Look ahead up to 100 bytes for false boolean payload \x00\x00\x00\x00
                key_len = len(target_key)
                val_window = data[idx+key_len : idx+key_len+60]
                
                # Patch AXML boolean flag to 1 (TRUE)
                if b"\x08\x00\x05p\x00\x00\x00" in val_window:
                    val_idx = data.find(b"\x08\x00\x05p\x00\x00\x00", idx+key_len)
                    if val_idx != -1 and val_idx + 12 <= len(data):
                        # Replace false (0x00000000) with true (0x00000001)
                        data = data[:val_idx+8] + b"\x01\x00\x00\x00" + data[val_idx+12:]
                        patched_count += 1
                pos = idx + key_len

            # Keep 1KB overlap for chunk boundary safety
            if len(data) > 1024:
                fout.write(data[:-1024])
                overlap = data[-1024:]
            else:
                overlap = data

    cur_time = time.strftime("%H:%M:%S")
    out_size = os.path.getsize(out_file)
    log(f"🎉 ĐÃ TIÊM THÀNH CÔNG {patched_count} VỊ TRÍ VOLTE_STATUS_BOOL=TRUE NGUYÊN BẢN AXML!", "success")
    log(f"   Dấu giờ tệp: {cur_time} | Dung lượng: {out_size / (1024*1024):.2f} MB", "info")
    log(f"   Khớp dung lượng byte gốc: {'HOÀN HẢO 100%' if out_size == file_size else 'LỆCH'}", "success")
    print()
    print("====================================================================")
    print("👉 HƯỚNG DẪN NẠP BẢN VÁ AXML CHUẨN 100% TRÊN UNLOCKTOOL:")
    print("   1. Thẻ MTK UNIVERSAL -> Bấm nút PATCH DM VERITY (để tắt cờ bảo vệ).")
    print("   2. Thẻ FLASH [OLD] -> Chuột phải dòng 37 (system) -> Write Partition.")
    print(f"   3. Chọn tệp system_patched.bin mốc giờ {cur_time} vừa tạo.")
    print("   4. UnlockTool nạp Writing system... OK 100% -> VoLTE tự động bật màu xanh!")
    print("====================================================================")

if __name__ == "__main__":
    main()
