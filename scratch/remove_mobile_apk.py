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
    
    # 1. Delete volte_fixer_mobile directory
    mobile_dir = os.path.join(base_dir, "volte_fixer_mobile")
    if os.path.exists(mobile_dir):
        print(f"🗑️ Đang xóa thư mục [{mobile_dir}]...")
        shutil.rmtree(mobile_dir, ignore_errors=True)
        print("  ✓ Đã xóa thư mục volte_fixer_mobile thành công!")
        
    # 2. Delete hbg-volte-fixer-v1.apk if present
    apk_file = os.path.join(base_dir, "hbg-volte-fixer-v1.apk")
    if os.path.exists(apk_file):
        print(f"🗑️ Đang xóa tệp APK [{apk_file}]...")
        os.remove(apk_file)
        print("  ✓ Đã xóa hbg-volte-fixer-v1.apk thành công!")

    print("\n🎉 ĐÃ DỌN DẸP SẠCH SẼ HOÀN TOÀN TẤT CẢ CÁC TỆP DỰ ÁN MOBILE/APK CŨ!")

if __name__ == "__main__":
    main()
