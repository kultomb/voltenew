import os
import subprocess
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    exe_img = r"C:\Users\CMD\Desktop\volte_fixer_tool\extracted_vendor_volte\offset_313395408_vendor_ VoLTE OPPO_A31 CPH2015 ANDROID 9.img"
    usr_img = r"C:\Users\CMD\Desktop\volte_fixer_tool\scratch\vendor_stock_dump.bin"

    print("==========================================================================")
    print("  🔍 DEEP COMPARISON: XÁC ĐỊNH KHÁC BIỆT KỸ THUẬT GIỮA 2 BẢN VENDOR")
    print("  Bản 1 (Có VoLTE): offset_313395408_vendor_ VoLTE OPPO_A31 CPH2015 ANDROID 9.img")
    print("  Bản 2 (Gốc của bạn): vendor_stock_dump.bin")
    print("==========================================================================")

    seven_zip = r"C:\Program Files\7-Zip\7z.exe"

    out_exe_dir = r"C:\Users\CMD\Desktop\volte_fixer_tool\scratch\dir_exe_vendor"
    out_usr_dir = r"C:\Users\CMD\Desktop\volte_fixer_tool\scratch\dir_usr_vendor"

    os.makedirs(out_exe_dir, exist_ok=True)
    os.makedirs(out_usr_dir, exist_ok=True)

    print("\n📦 [1/3] Đang giải nén 7z cả 2 bản vendor để so sánh từng file...")
    subprocess.run([seven_zip, 'x', exe_img, f'-o{out_exe_dir}', '-y'], capture_output=True)
    subprocess.run([seven_zip, 'x', usr_img, f'-o{out_usr_dir}', '-y'], capture_output=True)

    # Walk both directories
    exe_files = {}
    for root, _, files in os.walk(out_exe_dir):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, out_exe_dir)
            exe_files[rel] = (full, os.path.getsize(full))

    usr_files = {}
    for root, _, files in os.walk(out_usr_dir):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, out_usr_dir)
            usr_files[rel] = (full, os.path.getsize(full))

    print(f"\n📊 Tổng số tệp trong bản EXE (Có VoLTE) : {len(exe_files)} files")
    print(f"📊 Tổng số tệp trong bản Gốc (Chưa VoLTE): {len(usr_files)} files")

    # 1. Files ONLY in EXE (Working) vendor
    only_in_exe = set(exe_files.keys()) - set(usr_files.keys())
    print(f"\n✨ [2/3] CÁC TỆP CHỈ CÓ TRONG BẢN HOẠT ĐỘNG (EXE) MÀ BẢN GỐC CỦA BẠN KHÔNG CÓ ({len(only_in_exe)} files):")
    for k in sorted(only_in_exe):
        full, sz = exe_files[k]
        print(f"  + [MỚI] {k:<55} ({sz:,} bytes)")

    # 2. Files ONLY in User Stock vendor
    only_in_usr = set(usr_files.keys()) - set(exe_files.keys())
    if only_in_usr:
        print(f"\n🗑️ CÁC TỆP BỊ XÓA HOẶC KHÔNG CÓ TRONG BẢN EXE ({len(only_in_usr)} files):")
        for k in sorted(only_in_usr):
            full, sz = usr_files[k]
            print(f"  - [THIẾU] {k:<55} ({sz:,} bytes)")

    # 3. Files with DIFFERENT size or contents
    common_files = set(exe_files.keys()) & set(usr_files.keys())
    diff_content_files = []

    for k in common_files:
        path_exe, sz_exe = exe_files[k]
        path_usr, sz_usr = usr_files[k]

        if sz_exe != sz_usr:
            diff_content_files.append((k, sz_exe, sz_usr, "Size Diff"))
        else:
            # Check content hash / bytes for text files like build.prop, rc, xml
            if k.endswith((".prop", ".rc", ".xml", ".txt", ".conf", ".sh", ".json")):
                with open(path_exe, 'rb') as f1, open(path_usr, 'rb') as f2:
                    if f1.read() != f2.read():
                        diff_content_files.append((k, sz_exe, sz_usr, "Content Diff"))

    print(f"\n📝 [3/3] CÁC TỆP CÓ NỘI DUNG/KÍCH THƯỚC KHÁC NHAU GIỮA 2 BẢN ({len(diff_content_files)} files):")
    for k, sz1, sz2, reason in sorted(diff_content_files):
        print(f"  * {k:<55} (EXE: {sz1:,} vs GỐC: {sz2:,} bytes) -> [{reason}]")

if __name__ == "__main__":
    main()
