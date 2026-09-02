"""
Scan vendor.bin for AXML boolean keys inside RRO overlays
"""
import os

def scan_vendor_axml():
    vendor_path = os.path.abspath(r"C:\Users\CMD\Desktop\volte_fixer_tool\THU_MUC_RUT_SYSTEM_OPPO\vendor.bin")
    with open(vendor_path, "rb") as f:
        data = f.read()

    keys = [
        b"carrier_volte_available_bool",
        b"mtk_ct_volte_status_bool",
        b"mtk_default_enhanced_4g_mode_bool",
        b"volte_status_bool"
    ]

    print("=== AXML KEYS SEARCH IN VENDOR.BIN ===")
    for k in keys:
        pos = 0
        matches = 0
        while True:
            idx = data.find(k, pos)
            if idx == -1:
                break
            matches += 1
            print(f"Key '{k.decode('latin1')}' found at offset {idx}")
            pos = idx + len(k)
        if matches == 0:
            print(f"Key '{k.decode('latin1')}' NOT found in vendor.bin")

if __name__ == "__main__":
    scan_vendor_axml()
