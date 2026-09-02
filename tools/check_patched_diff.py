"""
Compare system.bin vs system_patched.bin at key VoLTE offsets
"""
import os

def check_system_patched():
    sys_orig = r"C:\Users\CMD\Desktop\volte_fixer_tool\THU_MUC_RUT_SYSTEM_OPPO\system.bin"
    sys_patch = r"C:\Users\CMD\Desktop\volte_fixer_tool\THU_MUC_RUT_SYSTEM_OPPO\system_patched.bin"

    if not os.path.exists(sys_patch):
        print(f"File {sys_patch} does not exist!")
        return

    size1 = os.path.getsize(sys_orig)
    size2 = os.path.getsize(sys_patch)

    print(f"Original system.bin size: {size1}")
    print(f"Patched system_patched.bin size: {size2}")

    offsets = [1758228424, 1804287463, 1963061643]
    keys = ["carrier_volte_available_bool", "mtk_ct_volte_status_bool", "config_device_volte_available"]

    with open(sys_orig, "rb") as f1, open(sys_patch, "rb") as f2:
        for off, key in zip(offsets, keys):
            f1.seek(off)
            b1 = f1.read(80)
            f2.seek(off)
            b2 = f2.read(80)

            diff_count = sum(1 for a, b in zip(b1, b2) if a != b)
            print(f"\nOffset {off} ({key}):")
            print(f"  Orig hex : {b1[:30].hex()}")
            print(f"  Patch hex: {b2[:30].hex()}")
            print(f"  Byte differences: {diff_count}")

if __name__ == "__main__":
    check_system_patched()
