"""
HBG VoLTE Fixer — Direct Patching for Downloads a31
"""

import os
import sys

# Add parent workspace
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from tools.patch_oppo_simsettings_zip_perfect import patch_oppo_simsettings_zip
from tools.patch_vendor_bin_modem_perfect import patch_vendor_bin_modem

def main():
    target_dir = os.path.abspath(r"C:\Users\CMD\Downloads\a31")
    sys_bin = os.path.join(target_dir, "system.bin")
    sys_out = os.path.join(target_dir, "system_patched.bin")
    
    ven_bin = os.path.join(target_dir, "vendor.bin")
    ven_out = os.path.join(target_dir, "vendor_patched.bin")

    print("====================================================================")
    print("  HBG TOOL — DA VÁ TRUC TIEP CHO THU MUC C:\\Users\\CMD\\Downloads\\a31")
    print("====================================================================\n")

    if os.path.exists(sys_bin):
        print("📦 Dang xu ly [system.bin] trong Downloads\\a31...")
        patch_oppo_simsettings_zip(sys_bin, sys_out)

    if os.path.exists(ven_bin):
        print("\n📦 Dang xu ly [vendor.bin] trong Downloads\\a31...")
        patch_vendor_bin_modem(ven_bin, ven_out)

    print("\n====================================================================")
    print("🎉 DA VA THANH CONG VA TAO TEP PATCHED TRONG C:\\Users\\CMD\\Downloads\\a31:")
    print(f"   • {sys_out}")
    print(f"   • {ven_out}")
    print("====================================================================")

if __name__ == "__main__":
    main()
