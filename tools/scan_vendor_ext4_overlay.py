"""
Inspect files inside vendor.bin EXT4 image
"""
import os
import sys
import re

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def scan_ext4_strings():
    vendor_path = os.path.abspath(r"C:\Users\CMD\Desktop\volte_fixer_tool\THU_MUC_RUT_SYSTEM_OPPO\vendor.bin")
    with open(vendor_path, "rb") as f:
        data = f.read()

    # Search for files under /overlay or /etc in EXT4 directory entries
    print("=== EXT4 VENDOR FILES FOUND IN VENDOR.BIN ===")
    matches = re.findall(rb'overlay/[\w\.\-]+\.apk', data)
    unique_overlays = list(set([m.decode('latin1') for m in matches]))
    print(f"Overlays found in vendor.bin EXT4: {unique_overlays}")

    apn_matches = re.findall(rb'apns-conf\.xml|mddb|oppo_carrier_config', data)
    print(f"Vendor configs found in vendor.bin EXT4: {set([m.decode('latin1') for m in apn_matches])}")

if __name__ == "__main__":
    scan_ext4_strings()
