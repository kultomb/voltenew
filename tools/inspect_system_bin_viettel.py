import os

def check_file(path, label):
    print(f"=== CHECKING {label} ({path}) ===")
    with open(path, "rb") as f:
        data = f.read()
    
    target = b'carrier="Viettel Email"'
    pos = data.find(target)
    print(f"Target pos: {pos}")
    if pos != -1:
        print("Snippet:")
        print(data[pos : pos + 120].decode("utf-8", errors="ignore"))
    print()

def main():
    s1 = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\system.bin")
    s2 = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\system_patched.bin")
    check_file(s1, "ORIGINAL system.bin")
    check_file(s2, "PATCHED system_patched.bin")

if __name__ == "__main__":
    main()
