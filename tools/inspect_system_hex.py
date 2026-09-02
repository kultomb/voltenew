"""
Dump 1000 bytes around config_device_volte_available in system.bin
"""
import os

def dump_hex():
    sys_path = r"C:\Users\CMD\Desktop\volte_fixer_tool\THU_MUC_RUT_SYSTEM_OPPO\system.bin"
    with open(sys_path, "rb") as f:
        f.seek(1963061643 - 100)
        data = f.read(1000)

    print(f"=== 1000 BYTES AROUND 1963061643 IN SYSTEM.BIN ===")
    print("HEX DUMP:")
    print(data.hex())
    print("\nTEXT DUMP:")
    clean = "".join([chr(b) if 32 <= b <= 126 else "." for b in data])
    print(clean)

if __name__ == "__main__":
    dump_hex()
