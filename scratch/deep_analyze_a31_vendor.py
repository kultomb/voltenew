import os
import sys

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../vendor_patcher")))
from vendor_engine import patch_vendor_image, MASTER_VENDOR_RULES

def analyze_file(filepath, label):
    print(f"\n==========================================================================")
    print(f"  🔍 ANALYZING VENDOR FILE: [{label}]")
    print(f"  Path: {filepath}")
    print(f"==========================================================================")
    
    if not os.path.exists(filepath):
        print("❌ File does not exist!")
        return

    with open(filepath, "rb") as f:
        data = f.read()

    print(f"File size: {len(data):,} bytes ({len(data)/(1024*1024):.2f} MB)")

    props_to_check = [
        b"persist.vendor.mtk.volte.enable=0",
        b"persist.vendor.mtk.volte.enable=1",
        b"persist.vendor.mtk.volte.enable=3",
        b"persist.mtk.volte.enable=1",
        b"persist.mtk.volte.enable=3",
        b"persist.vendor.radio.volte_state=0",
        b"persist.vendor.radio.volte_state=1",
        b"persist.vendor.radio.volte_state=3",
        b"persist.radio.volte_state=1",
        b"persist.radio.volte_state=3",
        b"persist.vendor.mtk_ct_volte_support=1",
        b"persist.vendor.mtk_ct_volte_support=3",
        b"persist.mtk_ct_volte_support=1",
        b"persist.mtk_ct_volte_support=3",
        b"persist.vendor.mims_support=1",
        b"persist.vendor.mims_support=2",
        b"persist.vendor.radio.mtk_dsbp_support=1",
        b"persist.vendor.radio.volte_pro_sub0=1",
        b"persist.vendor.radio.volte_pro_sub1=1",
    ]

    print("\n--- MASTER VOLTE PROPERTIES IN BINARY ---")
    for p in props_to_check:
        cnt = data.count(p)
        if cnt > 0:
            print(f"  ✓ Found {cnt:3d} occurrence(s) of: [{p.decode('utf-8', errors='ignore')}]")

    # Check init script block gaq_oppo_mtk_volte.rc
    print("\n--- CHECKING INJECTED GAQ INIT SCRIPT BLOCK ---")
    rc_idx = data.find(b"gaq_oppo_mtk_volte.rc")
    if rc_idx != -1:
        print(f"  ✓ Found gaq_oppo_mtk_volte.rc at offset: {rc_idx} (0x{rc_idx:X})")
        snippet = data[rc_idx-100:rc_idx+400]
        printable = "".join([chr(b) if 32 <= b <= 126 or b in (10, 13) else "." for b in snippet])
        print("  Snippet around rc script:")
        print("  " + printable.replace("\n", "\n  "))
    else:
        print("  ❌ gaq_oppo_mtk_volte.rc NOT found in file!")

def main():
    target_dir = r"C:\Users\CMD\Downloads\a31"
    
    # 1. Analyze 10:14 AM vendor_patched.img (Old generated file)
    old_patched = os.path.join(target_dir, "vendor_patched.img")
    analyze_file(old_patched, "OLD GENERATED VENDOR_PATCHED.IMG (10:14 AM)")

    # 2. Patch stock vendor.img with NEW code
    stock_vendor = os.path.join(target_dir, "vendor.img")
    if os.path.exists(stock_vendor):
        new_patched = os.path.join(target_dir, "vendor_patched_new_dual_sim.img")
        print("\n🚀 GENERATING NEW DUAL SIM VENDOR PATCH ON C:\\Users\\CMD\\Downloads\\a31\\vendor.img ...")
        patch_vendor_image(stock_vendor, new_patched)
        analyze_file(new_patched, "NEW GENERATED VENDOR_PATCHED_NEW_DUAL_SIM.IMG")

if __name__ == "__main__":
    main()
