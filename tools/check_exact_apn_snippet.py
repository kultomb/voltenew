import os

def main():
    sys_path = os.path.abspath(r"THU_MUC_RUT_SYSTEM_OPPO\system.bin")
    with open(sys_path, "rb") as f:
        sdata = f.read()

    target = b'apn="v-internet"'
    pos = sdata.find(target)
    print("apn=v-internet position:", pos)
    if pos != -1:
        snippet = sdata[pos-100 : pos+150]
        print("EXACT SNIPPET IN SYSTEM.BIN:\n")
        print(snippet.decode('utf-8', errors='ignore'))
        print("\nRAW BYTES:")
        print(snippet)

if __name__ == "__main__":
    main()
