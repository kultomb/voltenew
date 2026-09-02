import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    base_dir = r"C:\Users\CMD\Desktop\volte_fixer_tool"
    
    # List of files/folders to delete that are unrelated documentation or temporary
    items_to_remove = [
        "TAI_LIEU_PHAN_TICH_KY_THUAT_VOLTE_OPPO.md",
        "OppoSimSettings_dump.apk",
        "ChanDoan_OPPO_Deep_Diagnostic.bat",
        "MTK_BROM_VoLTE_Fixer.bat",
        "VolteFixer.class",
        "VolteFixer.java",
        "classes.dex",
        "mtk_brom_helper.py",
        "tao_goi_nap_oppo_unlocktool.py",
        "va_system_vendor_universal.py",
        "build_protected_tools.py",
        "build_version.py",
        "run_fix_exe.py",
        "run_restore_exe.py"
    ]

    print("=== HBG TOOL: DỌN DẸP SẠCH TÀI LIỆU VÀ TỆP KHÔNG LIÊN QUAN ===")
    
    for item in items_to_remove:
        fpath = os.path.join(base_dir, item)
        if os.path.exists(fpath):
            try:
                if os.path.isfile(fpath):
                    os.remove(fpath)
                    print(f"  ✓ Đã xóa file: {item}")
                elif os.path.isdir(fpath):
                    import shutil
                    shutil.rmtree(fpath, ignore_errors=True)
                    print(f"  ✓ Đã xóa thư mục: {item}")
            except Exception as ex:
                print(f"  ⚠ Không thể xóa {item}: {ex}")

    print("\n🎉 ĐÃ DỌN DẸP TOÀN BỘ TỆP VÀ TÀI LIỆU KHÔNG LIÊN QUAN!")

if __name__ == "__main__":
    main()
