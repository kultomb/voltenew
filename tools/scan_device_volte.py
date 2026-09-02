"""
Scan system.bin and vendor.bin for config_device_volte_available
"""
import os

def scan_config_device_volte():
    sys_path = os.path.abspath(r"C:\Users\CMD\Desktop\volte_fixer_tool\THU_MUC_RUT_SYSTEM_OPPO\system.bin")
    ven_path = os.path.abspath(r"C:\Users\CMD\Desktop\volte_fixer_tool\THU_MUC_RUT_SYSTEM_OPPO\vendor.bin")

    key = b"config_device_volte_available"

    print("=== SEARCHING config_device_volte_available IN SYSTEM.BIN ===")
    with open(sys_path, "rb") as f:
        data = f.read()
        pos = 0
        while True:
            idx = data.find(key, pos)
            if idx == -1:
                break
            print(f"  Found at offset {idx} in system.bin")
            snippet = data[max(0, idx-20):min(len(data), idx+len(key)+40)]
            clean = "".join([chr(b) if 32 <= b <= 126 else "." for b in snippet])
            print(f"  Snippet: {clean}")
            pos = idx + len(key)

    print("\n=== SEARCHING config_device_volte_available IN VENDOR.BIN ===")
    with open(ven_path, "rb") as f:
        data = f.read()
        pos = 0
        while True:
            idx = data.find(key, pos)
            if idx == -1:
                break
            print(f"  Found at offset {idx} in vendor.bin")
            snippet = data[max(0, idx-20):min(len(data), idx+len(key)+40)]
            clean = "".join([chr(b) if 32 <= b <= 126 else "." for b in snippet])
            print(f"  Snippet: {clean}")
            pos = idx + len(key)

if __name__ == "__main__":
    scan_config_device_volte()
