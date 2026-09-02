import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    target = r"C:\Users\CMD\Desktop\volte_fixer_tool\vendor_patcher\Bấm"
    if os.path.exists(target):
        print(f"🗑️ Đang xóa file rác: {target}")
        os.remove(target)
        print("  ✓ Đã xóa file [Bấm] rác thành công!")

if __name__ == "__main__":
    main()
