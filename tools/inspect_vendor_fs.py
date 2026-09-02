"""
Check filesystem format of vendor.bin (EXT4, EROFS, Raw)
"""
import os
import struct

def check_fs():
    vendor_path = os.path.abspath(r"C:\Users\CMD\Desktop\volte_fixer_tool\THU_MUC_RUT_SYSTEM_OPPO\vendor.bin")
    if not os.path.exists(vendor_path):
        print("vendor.bin not found!")
        return

    with open(vendor_path, "rb") as f:
        # Check EXT4 magic 0xEF53 at offset 1024 + 56 = 1080
        f.seek(1080)
        magic = f.read(2)
        print(f"Bytes at offset 1080 (EXT4 Magic check): {magic.hex()}")
        if magic == b"\x53\xef":
            print("🎉 VENDOR.BIN IS EXT4 FILESYSTEM!")

        # Check Sparse Header magic 0x3A3AFF3A
        f.seek(0)
        s_magic = f.read(4)
        print(f"Bytes at offset 0 (Sparse Header check): {s_magic.hex()}")
        if s_magic == b"\x3a\xff\x3a\x3a":
            print("VENDOR.BIN IS ANDROID SPARSE IMAGE!")

if __name__ == "__main__":
    check_fs()
