"""
OPPO A31 (CPH2015 MT6765) — Ultimate Both-Layer System.bin Binary Injector
Patches BOTH framework-res.apk (volte_status_bool) AND OppoSimSettings.apk (comm_simsettings_volte_config_list.xml) inside system.bin simultaneously!
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
    print("  HBG TOOL — TIÊM BẢN VÁ DỨT ĐIỂM CẢ 2 TẦNG BẢO MẬT VÀO SYSTEM.BIN")
    print("  Model: OPPO A31 (CPH2015) | Target: THU_MUC_RUT_SYSTEM_OPPO/system.bin")
    print("====================================================================")
    print()

    input_dir = os.path.abspath("THU_MUC_RUT_SYSTEM_OPPO")
    src_file = os.path.join(input_dir, "system.bin")
    out_file = os.path.join(input_dir, "system_patched.bin")

    if not os.path.exists(src_file):
        log("Chưa tìm thấy tệp system.bin trong THU_MUC_RUT_SYSTEM_OPPO!", "error")
        return

    file_size = os.path.getsize(src_file)
    log(f"📦 Đang tiêm song song 2 tầng bảo mật vào đĩa cứng system.bin ({file_size / (1024*1024):.2f} MB)...", "info")

    chunk_size = 64 * 1024 * 1024 # 64MB chunks
    
    # Layer 1: OppoSimSettings.apk Plain Text XML Patterns
    p1 = b'plmn="45204"  volte_status="0"'
    r1 = b'plmn="45204"  volte_status="1"'
    p2 = b'plmn="45205"  volte_status="0"'
    r2 = b'plmn="45205"  volte_status="1"'

    # Layer 2: AXML String Key
    target_key = b"volte_status_bool"

    count_l1 = 0
    count_l2 = 0

    with open(src_file, "rb") as fin, open(out_file, "wb") as fout:
        overlap = b""
        while True:
            chunk = fin.read(chunk_size)
            if not chunk:
                if overlap:
                    fout.write(overlap)
                break

            data = overlap + chunk

            # 1. Patch Layer 1 (Plain Text XML in OppoSimSettings.apk)
            c1 = data.count(p1)
            c2 = data.count(p2)
            if c1 > 0 or c2 > 0:
                data = data.replace(p1, r1)
                data = data.replace(p2, r2)
                count_l1 += (c1 + c2)
            else:
                c_gen = data.count(b'volte_status="0"')
                if c_gen > 0:
                    data = data.replace(b'volte_status="0"', b'volte_status="1"')
                    count_l1 += c_gen

            # 2. Patch Layer 2 (AXML Boolean in framework-res.apk / CarrierConfig.apk)
            pos = 0
            while True:
                idx = data.find(target_key, pos)
                if idx == -1:
                    break
                key_len = len(target_key)
                val_window = data[idx+key_len : idx+key_len+60]
                if b"\x08\x00\x05p\x00\x00\x00" in val_window:
                    val_idx = data.find(b"\x08\x00\x05p\x00\x00\x00", idx+key_len)
                    if val_idx != -1 and val_idx + 12 <= len(data):
                        data = data[:val_idx+8] + b"\x01\x00\x00\x00" + data[val_idx+12:]
                        count_l2 += 1
                pos = idx + key_len

            # Stream write with 1KB overlap
            if len(data) > 1024:
                fout.write(data[:-1024])
                overlap = data[-1024:]
            else:
                overlap = data

    cur_time = time.strftime("%H:%M:%S")
    out_size = os.path.getsize(out_file)
    log(f"  ✓ Tầng 1 (OppoSimSettings.apk): Đã vá {count_l1} vị trí XML volte_status=\"1\"", "success")
    log(f"  ✓ Tầng 2 (Framework/CarrierConfig): Đã vá {count_l2} vị trí AXML volte_status_bool=true", "success")
    log(f"🎉 ĐÃ BIÊN DỊCH THÀNH CÔNG TỆP SYSTEM_PATCHED.BIN SONG SONG 2 TẦNG BẢO MẬT!", "success")
    log(f"   Dấu giờ tệp: {cur_time} | Dung lượng: {out_size / (1024*1024):.2f} MB", "info")
    log(f"   Khớp dung lượng byte gốc: {'HOÀN HẢO 100%' if out_size == file_size else 'LỆCH'}", "success")
    print()
    print("====================================================================")
    print("👉 HƯỚNG DẪN NẠP DỨT ĐIỂM TRÊN UNLOCKTOOL:")
    print("   1. Thẻ MTK UNIVERSAL -> Bấm nút PATCH DM VERITY (để tắt cờ bảo vệ).")
    print("   2. Thẻ FLASH [OLD] -> Chuột phải dòng 37 (system) -> Write Partition.")
    print(f"   3. Chọn tệp system_patched.bin mốc giờ {cur_time} vừa tạo.")
    print("   4. UnlockTool nạp Writing system... OK 100% -> VoLTE tự động bật màu xanh!")
    print("====================================================================")

if __name__ == "__main__":
    main()
