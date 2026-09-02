import os, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def clean_oppo_folder():
    target_dir = r"c:\Users\CMD\Desktop\volte_fixer_tool\THU_MUC_RUT_SYSTEM_OPPO"
    print(f"====================================================================")
    print(f"  HBG TOOL — DỌN DẸP SẠCH SẼ THƯ MỤC {target_dir}")
    print(f"====================================================================\n")

    # Files to keep
    allowed_files = {
        "md1img.img",
        "vendor.img",
        "system.img",
        "vbmeta.img",
        "Va_System_Vendor_OPPO.bat",
        "Va_System_Bin_OPPO_A31.bat"
    }

    files = os.listdir(target_dir)
    deleted_count = 0
    kept_count = 0

    for f in files:
        fp = os.path.join(target_dir, f)
        if os.path.isfile(fp):
            if f in allowed_files:
                sz = os.path.getsize(fp)
                print(f"  ✓ GIỮ LẠI FILE CHÍNH: {f} ({sz} bytes)")
                kept_count += 1
            else:
                try:
                    os.remove(fp)
                    print(f"  🗑 ĐÃ XÓA FILE THỪA: {f}")
                    deleted_count += 1
                except Exception as e:
                    print(f"  ❌ Không thể xóa {f}: {e}")

    print(f"\n====================================================================")
    print(f"🎉 ĐÃ DỌN DẸP XONG! THƯ MỤC CHỈ CÒN ĐÚNG 4 TỆP BẢN VÁ NẠP TRÊN UNLOCKTOOL:")
    print(f"   1. md1img.img  (Firmware Modem Baseband MediaTek - 100 MiB)")
    print(f"   2. vendor.img  (Driver RIL Modem volte_support=1 - 1.09 GiB)")
    print(f"   3. system.img  (APN IMS 2026 + 8 Cờ Root init.rc - 5.06 GiB)")
    print(f"   4. vbmeta.img  (Tắt bảo vệ DM-Verity Hashtree 0x03 - 8 MiB)")
    print(f"====================================================================")

if __name__ == "__main__":
    clean_oppo_folder()
