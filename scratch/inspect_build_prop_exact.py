import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    exe_bp_path = r"C:\Users\CMD\Desktop\volte_fixer_tool\scratch\dir_exe_vendor\build.prop"
    usr_bp_path = r"C:\Users\CMD\Desktop\volte_fixer_tool\scratch\dir_usr_vendor\build.prop"

    if not os.path.exists(exe_bp_path) or not os.path.exists(usr_bp_path):
        print("❌ Không tìm thấy build.prop để so sánh!")
        return

    with open(exe_bp_path, "r", encoding="utf-8", errors="ignore") as f1:
        exe_lines = f1.readlines()

    with open(usr_bp_path, "r", encoding="utf-8", errors="ignore") as f2:
        usr_lines = f2.readlines()

    print("==========================================================================")
    print("  🔍 DEEP BUILD.PROP COMPARISON: BẢN EXE CHUẨN VS BẢN GỐC CỦA BẠN")
    print("==========================================================================")
    print(f"Bản EXE Chuẩn  : {len(exe_lines)} dòng")
    print(f"Bản Gốc Của Bạn: {len(usr_lines)} dòng")

    # Find differences in VoLTE / IMS lines
    print("\n--- CÁC DÒNG LIÊN QUAN ĐẾN VOLTE / IMS / MTK / CARRIER ---")
    volte_keys = ["volte", "ims", "ct", "carrier", "dsbp", "mims"]

    exe_volte = [l.strip() for l in exe_lines if any(k in l.lower() for k in volte_keys)]
    usr_volte = [l.strip() for l in usr_lines if any(k in l.lower() for k in volte_keys)]

    print("\n[BẢN EXE CHUẨN - BUILD.PROP]:")
    for l in exe_volte:
        print("  ", l)

    print("\n[BẢN GỐC CỦA BẠN - BUILD.PROP]:")
    for l in usr_volte:
        print("  ", l)

    diffs = set(exe_volte) ^ set(usr_volte)
    print(f"\nDiff lines count: {len(diffs)}")

if __name__ == "__main__":
    main()
