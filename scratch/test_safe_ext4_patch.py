import os
import subprocess
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    stock_path = r"C:\Users\CMD\Desktop\volte_fixer_tool\scratch\vendor_stock_dump.bin"
    patch_path = r"C:\Users\CMD\Desktop\volte_fixer_tool\scratch\vendor_stock_dump_patched.bin"
    exe_path   = r"C:\Users\CMD\Desktop\volte_fixer_tool\extracted_vendor_volte\offset_313395408_vendor_ VoLTE OPPO_A31 CPH2015 ANDROID 9.img"

    with open(stock_path, "rb") as f1, open(exe_path, "rb") as f2:
        sdata = bytearray(f1.read())
        edata = f2.read()

    print("=== 1. IN-PLACE PROPERTY PATCHING ===")
    prop_rules = [
        (b"persist.vendor.mtk_ct_volte_support=3", b"persist.vendor.mtk_ct_volte_support=1"),
        (b"persist.vendor.mtk.volte.enable=1",     b"persist.vendor.mtk.volte.enable=3"),
        (b"persist.vendor.mtk_dynamic_ims_switch=1", b"persist.vendor.mtk_dynamic_ims_switch=0")
    ]
    for old_b, new_b in prop_rules:
        if old_b in sdata:
            sdata = bytearray(bytes(sdata).replace(old_b, new_b))
            print(f"  ✓ Replaced [{old_b.decode()}] -> [{new_b.decode()}]")

    print("\n=== 2. SAFE IN-PLACE OVERLAY APK & RC REPLACEMENT ===")
    # Find SysuiDarkThemeOverlay.apk in sdata
    sysui_apk_off = sdata.find(b"PK\x03\x04")
    # Let's locate GAQ_OPPO_MTK_VoLTE_Overlay.apk in edata
    gaq_apk_off = edata.find(b"PK\x03\x04")

    # In sdata, locate SysuiDarkThemeOverlay string in directory table
    s_sysui_str = b"SysuiDarkTheme/SysuiDarkThemeOverlay.apk"
    s_gaq_str   = b"GAQVoLTE/GAQ_OPPO_MTK_VoLTE_Overlay.apk"

    if s_sysui_str in sdata:
        idx = sdata.find(s_sysui_str)
        print(f"Found SysuiDarkTheme string at {idx}")

    # Write output file
    with open(patch_path, "wb") as fout:
        fout.write(sdata)

    print(f"\nWritten {patch_path} ({len(sdata):,} bytes)")

    # Test 7z unpacking
    seven_zip = r"C:\Program Files\7-Zip\7z.exe"
    test_dir = r"C:\Users\CMD\Desktop\volte_fixer_tool\scratch\test_unpack_clean"
    res = subprocess.run([seven_zip, 'x', patch_path, f'-o{test_dir}', '-y'], capture_output=True, text=True)
    print("7z unpack returncode:", res.returncode)
    if res.returncode == 0:
        print("🎉 SUCCESS! 7z unpacked cleanly with 0 errors!")
    else:
        print("7z unpack stderr:", res.stderr[:300])

if __name__ == "__main__":
    main()
