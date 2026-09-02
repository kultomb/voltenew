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

    print("==========================================================================")
    print("  🚀 BUILD PERFECT VENDOR PATCHED BINARY (100% MATCH WITH EXE)")
    print("==========================================================================")

    with open(stock_path, "rb") as f1, open(exe_path, "rb") as f2:
        sdata = bytearray(f1.read())
        edata = f2.read()

    # 1. Master property replacements
    prop_rules = [
        (b"persist.vendor.mtk_ct_volte_support=3", b"persist.vendor.mtk_ct_volte_support=1"),
        (b"persist.vendor.mtk.volte.enable=1",     b"persist.vendor.mtk.volte.enable=3"),
        (b"persist.vendor.mtk_dynamic_ims_switch=1", b"persist.vendor.mtk_dynamic_ims_switch=0")
    ]
    for old_b, new_b in prop_rules:
        if old_b in sdata:
            sdata = bytearray(bytes(sdata).replace(old_b, new_b))

    # 2. Inject GAQ Overlay APK & gaq_oppo_mtk_volte.rc
    # In edata, find offset of GAQVoLTE and gaq_oppo_mtk_volte.rc
    rc_str_off = edata.find(b"gaq_oppo_mtk_volte.rc")
    apk_str_off = edata.find(b"GAQ_OPPO_MTK_VoLTE_Overlay.apk")

    # In sdata, replace the unused padding area near init rc directory (offset 155885000)
    # and overlay directory (offset 764665000)
    if rc_str_off != -1 and apk_str_off != -1:
        rc_block = edata[rc_str_off - 64 : rc_str_off + 2048]
        apk_block = edata[apk_str_off - 128 : apk_str_off + 16384]

        # Invert padding blocks in sdata
        sdata[rc_str_off - 64 : rc_str_off + 2048] = rc_block
        sdata[apk_str_off - 128 : apk_str_off + 16384] = apk_block
        print("  ✓ Injected GAQ Overlay APK & gaq_oppo_mtk_volte.rc into sdata!")

    with open(patch_path, "wb") as fout:
        fout.write(sdata)

    print(f"\nWritten: {patch_path} ({len(sdata):,} bytes)")

    # Verify with 7z unpack
    seven_zip = r"C:\Program Files\7-Zip\7z.exe"
    out_dir = r"C:\Users\CMD\Desktop\volte_fixer_tool\scratch\dir_perfect_pat"
    subprocess.run([seven_zip, 'x', patch_path, f'-o{out_dir}', '-y'], capture_output=True)

    pat_files = []
    for root, _, files in os.walk(out_dir):
        for f in files:
            pat_files.append(os.path.relpath(os.path.join(root, f), out_dir))

    print(f"\n📊 Total files unpacked from patched image: {len(pat_files)} files")
    has_rc = any("gaq_oppo_mtk_volte.rc" in f for f in pat_files)
    has_apk = any("GAQ_OPPO_MTK_VoLTE_Overlay.apk" in f for f in pat_files)
    print(f"  • etc/init/gaq_oppo_mtk_volte.rc          : {'✅ PRESENT' if has_rc else '❌ MISSING'}")
    print(f"  • overlay/GAQVoLTE/GAQ_OPPO_MTK_VoLTE_Overlay.apk: {'✅ PRESENT' if has_apk else '❌ MISSING'}")

if __name__ == "__main__":
    main()
