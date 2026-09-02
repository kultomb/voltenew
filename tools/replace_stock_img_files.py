import os, shutil, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def sync_patched_to_stock_names(folder_path):
    print(f"=== SYNCHRONIZING PATCHED IMAGES IN: {folder_path} ===")
    if not os.path.exists(folder_path):
        print(f"Folder {folder_path} does not exist. Skipping.")
        return

    sys_patched = os.path.join(folder_path, "system_patched.bin")
    ven_patched = os.path.join(folder_path, "vendor_patched.bin")
    vbm_patched = os.path.join(folder_path, "vbmeta_patched.bin")

    targets = [
        (sys_patched, ["system.img", "system.bin"]),
        (ven_patched, ["vendor.img", "vendor.bin"]),
        (vbm_patched, ["vbmeta.img", "vbmeta.bin"])
    ]

    for src, dst_names in targets:
        if os.path.exists(src):
            for d in dst_names:
                dst_path = os.path.join(folder_path, d)
                shutil.copyfile(src, dst_path)
                print(f"   [OK] Overwrote stock [{d}] ({os.path.getsize(dst_path)} bytes) with patched [{os.path.basename(src)}]")
        else:
            print(f"   [ERROR] Source patched file {src} not found!")

def main():
    f1 = r"c:\Users\CMD\Desktop\volte_fixer_tool\THU_MUC_RUT_SYSTEM_OPPO"
    f2 = r"C:\Users\CMD\Downloads\a31"
    sync_patched_to_stock_names(f1)
    print()
    sync_patched_to_stock_names(f2)

if __name__ == "__main__":
    main()
