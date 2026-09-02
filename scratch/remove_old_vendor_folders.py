import os
import shutil
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    base_dir = r"C:\Users\CMD\Desktop\volte_fixer_tool"
    
    target_dirs = [
        "GOI_NAP_UNLOCKTOOL_OPPO",
        "GOI_NAP_VENDOR_ONLY_UNLOCKTOOL",
        "THU_MUC_RUT_SYSTEM_OPPO"
    ]

    for d in target_dirs:
        full_path = os.path.join(base_dir, d)
        if os.path.exists(full_path):
            print(f"🗑️ Đang xóa thư mục gói nạp cũ [{d}]...")
            shutil.rmtree(full_path, ignore_errors=True)
            print(f"  ✓ Đã xóa {d} thành công!")

    print("\n🎉 ĐÃ DỌN DẸP SẠCH SẼ TẤT CẢ CÁC THƯ MỤC GÓI NẠP VENDOR CŨ!")

if __name__ == "__main__":
    main()
