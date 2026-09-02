"""
HBG Tool — Standalone AVB / DM-Verity Disabler (Patch vbmeta.bin)
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def patch_vbmeta(vbmeta_path: str):
    if not os.path.exists(vbmeta_path):
        print(f"Error: {vbmeta_path} not found!")
        return False

    with open(vbmeta_path, "rb") as f:
        data = bytearray(f.read())

    # Check AVB Magic "AVB0"
    if not data.startswith(b"AVB0"):
        print("Error: Invalid vbmeta image (AVB0 magic not found)!")
        return False

    old_flags = data[123]
    data[123] = 0x03 # Set flag to 0x03 (Disable Verity & Verification)

    dir_name = os.path.dirname(vbmeta_path)
    out_path = os.path.join(dir_name, "vbmeta_patched_disabled.img")
    same_path = os.path.join(dir_name, "vbmeta_patched.bin")

    with open(out_path, "wb") as f:
        f.write(data)

    with open(same_path, "wb") as f:
        f.write(data)

    print(f"[OK] Da Patch DM-Verity thanh cong vao vbmeta! (Flags changed: {hex(old_flags)} -> 0x03)")
    print(f"📄 Tep vbmeta da tat bao ve luu tai:\n   • {out_path}\n   • {same_path}")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        patch_vbmeta(sys.argv[1])
    else:
        target1 = r"C:\Users\CMD\Desktop\volte_fixer_tool\THU_MUC_RUT_SYSTEM_OPPO\vbmeta.bin"
        target2 = r"C:\Users\CMD\Downloads\a31\vbmeta.bin"
        if os.path.exists(target1):
            patch_vbmeta(target1)
        if os.path.exists(target2):
            patch_vbmeta(target2)
